import streamlit as st
from datetime import date, timedelta
from app.modules.academics import service as acad_srv
from app.modules.enrollments import service as enroll_srv
from app.modules.auth import service as auth_srv
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

    st.divider()

    # 1. Sessions Management panel (Full Width or Centered)
    sessions = acad_srv.list_group_sessions(group_id, int(level_filter))

    # Pre-fetch instructor names for sessions
    instructors = auth_srv.get_active_instructors()
    inst_map = {i.id: i.full_name for i in instructors}

    st.markdown("#### Sessions")
    if sessions:
        for s in sessions:
            delete_key = f"del_confirm_{s.id}"
            actual_instructor_name = inst_map.get(s.actual_instructor_id, "Unassigned")

            # Session row
            sc1, sc2, sc3 = st.columns([4, 2, 1])
            lbl = f"**S{s.session_number}:** {s.session_date} | Instructor: {actual_instructor_name}"
            if s.is_extra_session:
                lbl += " ⭐"
            sc1.write(lbl)

            # Delete logic with confirmation state
            if delete_key not in st.session_state:
                st.session_state[delete_key] = False

            if not st.session_state[delete_key]:
                if sc3.button("🗑️", key=f"del_init_{s.id}"):
                    st.session_state[delete_key] = True
                    st.rerun()
            else:
                st.error(f"Delete S{s.session_number}?")
                cc1, cc2 = sc3.columns(2)
                if cc1.button("Yes", key=f"del_yes_{s.id}", type="primary"):
                    acad_srv.delete_session(s.id)
                    del st.session_state[delete_key]
                    st.rerun()
                if cc2.button("No", key=f"del_no_{s.id}"):
                    st.session_state[delete_key] = False
                    st.rerun()
    else:
        st.info("No sessions yet.")

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

    # 2. Attendance Grid (Now Full Width below sessions)
    roster = enroll_srv.get_group_roster(group_id, int(level_filter))
    render_attendance_grid(sessions, roster)

    st.divider()

    # Bottom Back Button
    if st.button("⬅️ Back to Overview", use_container_width=True):
        del st.session_state["selected_group_id"]
        st.rerun()
