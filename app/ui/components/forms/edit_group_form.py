import streamlit as st
from app.modules.academics import academics_service as acad_srv

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def render_edit_group_form(group_info, instructors, courses):
    with st.expander("✏️ Edit Group Settings"):
        with st.form(f"edit_group_{group_info.id}"):
            c1, c2 = st.columns(2)
            with c1:
                eg_name = st.text_input("Group Name *", value=group_info.name)
                
                # Courses dropdown
                cur_course_idx = next((i for i, c in enumerate(courses) if c.id == group_info.course_id), 0) if courses else 0
                eg_course = st.selectbox("Course", options=courses, format_func=lambda c: c.name, index=cur_course_idx) if courses else None
                
                # Instructor dropdown
                cur_inst_idx = next((i for i, inst in enumerate(instructors) if inst.id == group_info.instructor_id), 0) if instructors else 0
                eg_inst = st.selectbox("Instructor", options=instructors, format_func=lambda x: x.full_name, index=cur_inst_idx) if instructors else None
                
                eg_cap = st.number_input("Max Capacity", value=group_info.max_capacity, min_value=1)
                
            with c2:
                eg_day = st.selectbox("Default Day", WEEKDAYS, index=WEEKDAYS.index(group_info.default_day) if group_info.default_day in WEEKDAYS else 0)
                eg_start = st.time_input("Start Time", value=group_info.default_time_start)
                eg_end = st.time_input("End Time", value=group_info.default_time_end)
                
                eg_level = st.number_input("Level Number", value=int(group_info.level_number), min_value=1, step=1)
                
                status_opts = ["active", "archived", "completed"]
                eg_status = st.selectbox("Status", status_opts, index=status_opts.index(group_info.status) if group_info.status in status_opts else 0)

            if st.form_submit_button("Save Changes", type="primary"):
                from app.modules.academics.academics_schemas import UpdateGroupDTO
                try:
                    acad_srv.update_group(group_info.id, UpdateGroupDTO(
                        name=eg_name.strip(),
                        course_id=eg_course.id if eg_course else group_info.course_id,
                        level_number=eg_level,
                        max_capacity=eg_cap,
                        instructor_id=eg_inst.id if eg_inst else group_info.instructor_id,
                        default_day=eg_day,
                        default_time_start=eg_start,
                        default_time_end=eg_end,
                        status=eg_status
                    ))
                    st.success("Group settings updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update: {e}")
