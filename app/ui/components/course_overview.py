import streamlit as st
import pandas as pd
from app.modules.academics import academics_service as acad_srv
from app.modules.academics.schemas import AddNewCourseInput


@st.dialog("Create New Course")
def modal_create_course():
    with st.form("new_course_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Course Name *", placeholder="e.g. HTML L1")
            price = st.number_input("Price per Level (EGP) *", min_value=0.0, step=50.0)
            category = st.selectbox(
                "Category *", ["software", "hardware", "steam", "other"]
            )
        with col2:
            sessions_pl = st.number_input("Sessions per Level *", min_value=1, value=5)
            description = st.text_area("Description (Optional)", height=94)

        if st.form_submit_button("Create Course", type="primary"):
            if not name.strip() or price <= 0:
                st.error("Name and Price are required.")
            else:
                try:
                    course = acad_srv.add_new_course(
                        AddNewCourseInput(
                            name=name.strip(),
                            category=category,
                            price_per_level=price,
                            sessions_per_level=int(sessions_pl),
                            description=description.strip() if description else None,
                        )
                    )
                    st.success(
                        f"✅ Created course: **{course.name}** (ID: {course.id})"
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")


def render_course_overview():
    col_l, col_r = st.columns([3, 1])
    with col_l:
        st.subheader("Active Courses")
    with col_r:
        if st.button("➕ Create Course", use_container_width=True):
            modal_create_course()

    search_query = st.text_input("🔍 Search Courses by Name", placeholder="e.g. HTML")

    courses = acad_srv.get_active_courses()
    stats_list = acad_srv.get_all_course_stats()
    stats_map = {s.course_id: s for s in stats_list}

    if search_query:
        query = search_query.lower()
        courses = [c for c in courses if query in c.name.lower()]

    if not courses:
        st.info("No courses found.")
    else:
        st.markdown("Select a course below to view its details and active groups:")

        rows = []
        for c in courses:
            s = stats_map.get(c.id, {})
            rows.append({
                "ID": c.id,
                "Name": c.name,
                "Category": c.category.capitalize(),
                "Price (EGP)": c.price_per_level,
                "Sessions/Level": c.sessions_per_level,
                "Groups": getattr(s, "active_groups", 0),
                "Active Students": getattr(s, "active_students", 0),
            })

        df = pd.DataFrame(rows)

        event = st.dataframe(
            df,
            hide_index=True,
            use_container_width=True,
            selection_mode="single-row",
            on_select="rerun",
        )

        if event.selection.rows:
            sel_idx = event.selection.rows[0]
            st.session_state["nav_target_course_id"] = courses[sel_idx].id
            st.rerun()

