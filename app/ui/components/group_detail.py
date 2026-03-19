import streamlit as st
from datetime import date, timedelta
from app.modules.academics import academics_service as acad_srv
from app.modules.enrollments import enrollment_service as enroll_srv
from .attendance_grid import render_attendance_grid

WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def _next_weekday(from_date: date, day_name: str) -> date:
    target = WEEKDAYS.index(day_name)
    delta = (target - from_date.weekday()) % 7
    if delta <= 0:
        delta += 7
    return from_date + timedelta(days=delta)


def render_group_detail(group_id: int):
    # Retrieve group info
    group_info = acad_srv.get_group_by_id(group_id)
    if not group_info:
        st.error("Group not found.")
        if st.button("⬅️ Back to Overview"):
            del st.session_state["selected_group_id"]
            st.rerun()
        return

    # Header section
    st.subheader(f"Manage: {group_info.name}")

    st.markdown(
        f"**Day:** {group_info.default_day} | **Time:** {group_info.default_time_start} - {group_info.default_time_end} | **Level:** {group_info.level_number}"
    )

    level_filter = st.number_input(
        "View Level", min_value=1, value=int(group_info.level_number), key="gdtl_level"
    )

    with st.expander("✏️ Edit Group Settings"):
        with st.form(f"edit_group_{group_info.id}"):
            c1, c2 = st.columns(2)
            with c1:
                eg_name = st.text_input("Group Name *", value=group_info.name)
                eg_cap = st.number_input("Max Capacity", value=group_info.max_capacity, min_value=1)
                
                from app.modules.auth.auth_service import get_active_instructors
                instructors = get_active_instructors()
                cur_inst_idx = next((i for i, inst in enumerate(instructors) if inst.id == group_info.instructor_id), 0) if instructors else 0
                eg_inst = st.selectbox("Instructor", options=instructors, format_func=lambda x: x.full_name, index=cur_inst_idx) if instructors else None
                
            with c2:
                eg_day = st.selectbox("Default Day", WEEKDAYS, index=WEEKDAYS.index(group_info.default_day) if group_info.default_day in WEEKDAYS else 0)
                eg_start = st.time_input("Start Time", value=group_info.default_time_start)
                eg_end = st.time_input("End Time", value=group_info.default_time_end)

            if st.form_submit_button("Save Changes", type="primary"):
                try:
                    acad_srv.update_group(group_info.id, {
                        "name": eg_name.strip(),
                        "max_capacity": eg_cap,
                        "instructor_id": eg_inst.id if eg_inst else group_info.instructor_id,
                        "default_day": eg_day,
                        "default_time_start": eg_start,
                        "default_time_end": eg_end
                    })
                    st.success("Group settings updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update: {e}")

    st.divider()

    # Fetch sessions for attendance grid
    sessions = acad_srv.list_group_sessions(group_id, int(level_filter))

    # 2. Attendance Grid (Now Full Width below sessions)
    roster = enroll_srv.get_group_roster(group_id, int(level_filter))
    render_attendance_grid(sessions, roster)

    st.divider()

    # Suggest next date for extra session
    next_date = date.today()
    if sessions:
        last_date_val = max(s.session_date for s in sessions)
        if isinstance(last_date_val, str):
            last_date = date.fromisoformat(last_date_val)
        else:
            last_date = last_date_val

        if group_info.default_day:
            next_date = _next_weekday(last_date, group_info.default_day)
        else:
            next_date = last_date + timedelta(days=7)

    with st.expander("➕ Add Extra Session"):
        ex_date = st.date_input("Date", value=next_date, key="ex_dt")
        if st.button("Add Session"):
            acad_srv.add_extra_session(group_id, int(level_filter), ex_date)
            st.success("Added.")
            st.rerun()

    # 3. Level advance check
    if acad_srv.check_level_complete(group_id, int(level_filter)):
        st.divider()
        st.success(f"🎓 Level {level_filter} complete!")
        if st.button(f"Advance to Level {level_filter + 1}", type="primary"):
            acad_srv.advance_group_level(group_id)
            st.rerun()

    st.divider()

    # Bottom Back Button
    if st.button("⬅️ Back to Overview", use_container_width=True):
        del st.session_state["selected_group_id"]
        st.rerun()
