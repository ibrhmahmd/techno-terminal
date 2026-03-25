import streamlit as st
from datetime import date, timedelta
import app.modules.academics as acad_srv
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

    from app.ui.components.forms.edit_group_form import render_edit_group_form
    from app.modules.hr.hr_service import get_active_instructors
    from app.modules.academics import get_active_courses
    instructors = get_active_instructors()
    courses = get_active_courses()
    render_edit_group_form(group_info, instructors, courses)

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
            with st.spinner("Adding session..."):
                acad_srv.add_extra_session(
                    AddExtraSessionInput(
                        group_id=group_id,
                        level_number=int(level_filter),
                        extra_date=ex_date
                    )
                )
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
