import streamlit as st
import app.modules.academics as acad_srv

def render_edit_course_form(course):
    with st.expander("✏️ Edit Course Information"):
        with st.form(f"edit_course_{course.id}"):
            c1, c2 = st.columns(2)
            with c1:
                ec_name = st.text_input("Course Name *", value=course.name)
                cat_opts = ["programming", "robotics", "design", "other"]
                ec_cat = st.selectbox("Category", cat_opts, index=cat_opts.index(course.category) if course.category in cat_opts else 3)
                es_active = st.checkbox("Course Active", value=course.is_active)
            with c2:
                # To prevent editing logic break if the user manually tries to mess it up
                ec_sess = st.number_input("Sessions per Level", value=course.sessions_per_level, min_value=1, step=1)
                
            ec_desc = st.text_area("Description", value=course.description or "")
            
            if st.form_submit_button("Save Changes", type="primary"):
                from app.modules.academics.schemas import UpdateCourseDTO
                try:
                    acad_srv.update_course(course.id, UpdateCourseDTO(
                        name=ec_name.strip(),
                        category=ec_cat,
                        description=ec_desc.strip() or None,
                        sessions_per_level=ec_sess,
                        is_active=es_active
                    ))
                    st.success("Course details updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update: {e}")
