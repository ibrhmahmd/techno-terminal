import streamlit as st
import pandas as pd
from datetime import time
from app.ui.components.auth_guard import require_auth
from app.modules.academics import service as acad_srv
from app.modules.auth import service as auth_srv

# Enforce auth
require_auth()

st.set_page_config(page_title="Course Management", layout="wide")
st.title("📚 Course Management")
st.markdown("Define courses and schedule groups.")

tab_courses, tab_groups = st.tabs(["📘 Courses", "📅 Groups"])

# --- TAB 1: Courses ---
with tab_courses:
    st.subheader("Add New Course")
    with st.form("new_course_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Course Name *", placeholder="e.g. CSS L1")
            price = st.number_input("Price per Level (EGP) *", min_value=0.0, step=50.0)
            category = st.selectbox(
                "Category", ["software", "hardware", "steam", "other"]
            )
        with col2:
            sessions_pl = st.number_input("Sessions per Level *", min_value=1, value=5)
            description = st.text_area("Description (Optional)", height=68)

        submit_btn = st.form_submit_button("Create Course", type="primary")
        if submit_btn:
            if not name.strip() or price <= 0:
                st.error("Name and Price are required.")
            else:
                try:
                    course = acad_srv.add_new_course(
                        {
                            "name": name.strip(),
                            "category": category,
                            "price_per_level": price,
                            "sessions_per_level": sessions_pl,
                            "description": description.strip() if description else None,
                        }
                    )
                    st.success(f"✅ Created course: {course.name}")
                except Exception as e:
                    st.error(f"❌ {e}")

    st.divider()
    st.subheader("Active Courses")
    courses = acad_srv.get_active_courses()
    if courses:
        df_courses = pd.DataFrame([c.model_dump() for c in courses])
        st.dataframe(
            df_courses[
                ["id", "name", "category", "price_per_level", "sessions_per_level"]
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No active courses found.")

# --- TAB 2: Groups ---
with tab_groups:
    st.subheader("Schedule New Group")

    courses_list = acad_srv.get_active_courses()
    instructors = auth_srv.get_active_instructors()

    if not courses_list:
        st.warning("Please create a Course first.")
    elif not instructors:
        st.warning("No active instructors (employees) found in the system.")
    else:
        with st.form("new_group_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)

            course_opts = {c.name: c.id for c in courses_list}
            inst_opts = {i.full_name: i.id for i in instructors}

            with col1:
                selected_c = st.selectbox("Course *", options=list(course_opts.keys()))
                sel_course_id = course_opts[selected_c]

                selected_i = st.selectbox(
                    "Instructor *", options=list(inst_opts.keys())
                )
                sel_inst_id = inst_opts[selected_i]

            with col2:
                level = st.number_input("Level Number", min_value=1, value=1)
                capacity = st.number_input("Max Capacity", min_value=1, value=15)

            with col3:
                day = st.selectbox(
                    "Default Day *",
                    [
                        "Saturday",
                        "Sunday",
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                    ],
                )

                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    st_hour = st.selectbox(
                        "Start Hr", list(range(1, 13)), index=1, key="st_h"
                    )
                with sc2:
                    st_min = st.selectbox(
                        "Start Min", ["00", "15", "30", "45"], key="st_m"
                    )
                with sc3:
                    st_ampm = st.selectbox("AM/PM", ["AM", "PM"], index=1, key="st_p")

                ec1, ec2, ec3 = st.columns(3)
                with ec1:
                    en_hour = st.selectbox(
                        "End Hr", list(range(1, 13)), index=3, key="en_h"
                    )
                with ec2:
                    en_min = st.selectbox(
                        "End Min", ["00", "15", "30", "45"], key="en_m"
                    )
                with ec3:
                    en_ampm = st.selectbox("AM/PM", ["AM", "PM"], index=1, key="en_p")

            submit_grp = st.form_submit_button("Schedule Group", type="primary")
            if submit_grp:
                try:

                    def to_time(hour, minute_str, ampm):
                        from datetime import time

                        minute = int(minute_str)
                        h24 = hour % 12 + (12 if ampm == "PM" else 0)
                        return time(h24, minute)

                    grp = acad_srv.schedule_group(
                        {
                            "course_id": sel_course_id,
                            "instructor_id": sel_inst_id,
                            "level_number": int(level),
                            "max_capacity": int(capacity),
                            "default_day": day,
                            "default_time_start": to_time(st_hour, st_min, st_ampm),
                            "default_time_end": to_time(en_hour, en_min, en_ampm),
                        }
                    )
                    st.success(f"✅ Group scheduled successfully (ID: {grp.id})")
                except Exception as e:
                    st.error(f"❌ {e}")

    st.divider()
    st.subheader("Active Groups")
    all_groups = acad_srv.get_all_active_groups()
    if all_groups:
        df_groups = pd.DataFrame([g.model_dump() for g in all_groups])
        # Format times for display safely
        df_groups["default_time_start"] = df_groups["default_time_start"].astype(str)
        df_groups["default_time_end"] = df_groups["default_time_end"].astype(str)
        display_cols = [
            "id",
            "course_id",
            "instructor_id",
            "level_number",
            "default_day",
            "default_time_start",
            "default_time_end",
            "max_capacity",
        ]
        st.dataframe(df_groups[display_cols], hide_index=True, use_container_width=True)
    else:
        st.info("No active groups found.")
