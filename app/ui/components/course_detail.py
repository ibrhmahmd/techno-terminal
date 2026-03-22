import streamlit as st
import pandas as pd
from app.db.connection import get_session
from app.modules.academics.academics_models import Course
from app.modules.academics import academics_service as acad_srv
from app.modules.hr.hr_service import get_active_instructors


def render_course_detail(course_id: int):
    with get_session() as db:
        course = db.get(Course, course_id)

    if not course:
        st.error("Course not found.")
        if st.button("⬅️ Back"):
            del st.session_state["nav_target_course_id"]
            st.rerun()
        return

    groups = acad_srv.get_groups_by_course(course_id)

    # Header section
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("⬅️ Back"):
            del st.session_state["nav_target_course_id"]
            st.rerun()
    with col2:
        status_icon = "🟢" if course.is_active else "🔴"
        st.subheader(f"Course: {course.name} {status_icon}")

    # Course Details
    st.markdown(
        f"**Category:** {course.category.capitalize()} | **Sessions/Level:** {course.sessions_per_level}"
    )
    if course.description:
        st.info(f"**Description:** {course.description}")

    from app.ui.components.forms.edit_course_form import render_edit_course_form
    render_edit_course_form(course)

    st.divider()

    # Edit Price inline
    c_price1, c_price2 = st.columns([1, 2])
    with c_price1:
        new_price = st.number_input(
            "Price per Level (EGP)",
            value=float(course.price_per_level),
            min_value=0.0,
            step=50.0,
            key=f"edit_price_{course_id}",
        )
    with c_price2:
        st.write("")  # Spacing
        st.write("")
        if st.button("💾 Update Price", type="primary"):
            try:
                acad_srv.update_course_price(course_id, new_price)
                st.success(f"✅ Price updated to {new_price} EGP.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ {e}")

    st.divider()

    # Active Groups running this course
    st.markdown("#### Active Groups Running This Course")

    if groups:
        instructors = get_active_instructors()
        inst_map = {i.id: i.full_name for i in instructors}

        group_data = []
        for g in groups:
            group_data.append(
                {
                    "Group ID": g.id,
                    "Name": g.name,
                    "Level": g.level_number,
                    "Day": g.default_day,
                    "Time": f"{g.default_time_start} - {g.default_time_end}",
                    "Instructor": inst_map.get(g.instructor_id, "Unassigned"),
                }
            )

        st.dataframe(
            pd.DataFrame(group_data), hide_index=True, use_container_width=True
        )
    else:
        st.info("No active groups are currently running this course.")

    with st.expander("➕ Create Group for this Course"):
        st.markdown("Use the dedicated Group Management page to schedule a new group.")
        if st.button("Go to Group Management", type="primary"):
            st.switch_page("pages/4_Group_Management.py")

    st.divider()
    if st.button("⬅️ Back to Search", use_container_width=True):
        del st.session_state["nav_target_course_id"]
        st.rerun()
