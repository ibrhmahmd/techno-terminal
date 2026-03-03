import streamlit as st
import pandas as pd
from app.ui.components.auth_guard import require_auth
from app.modules.academics import service as acad_srv

require_auth()

st.title("📚 Course Management")
st.markdown("Define and manage courses.")

tab_add, tab_list = st.tabs(["Add New Course", "Active Courses"])

# ─── Tab 1: Add New Course ────────────────────────────────────────────────────
with tab_add:
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

        submit = st.form_submit_button("Create Course", type="primary")
        if submit:
            if not name.strip() or price <= 0:
                st.error("Name and Price are required.")
            else:
                try:
                    course = acad_srv.add_new_course(
                        {
                            "name": name.strip(),
                            "category": category,
                            "price_per_level": price,
                            "sessions_per_level": int(sessions_pl),
                            "description": description.strip() if description else None,
                        }
                    )
                    st.success(
                        f"✅ Created course: **{course.name}** (ID: {course.id})"
                    )
                except Exception as e:
                    st.error(f"❌ {e}")

# ─── Tab 2: Active Courses + Edit Price ───────────────────────────────────────
with tab_list:
    courses = acad_srv.get_active_courses()
    if not courses:
        st.info("No active courses yet.")
    else:
        df = pd.DataFrame([c.model_dump() for c in courses])
        st.dataframe(
            df[["id", "name", "category", "price_per_level", "sessions_per_level"]],
            hide_index=True,
            use_container_width=True,
        )

        st.divider()
        st.subheader("✏️ Edit Course Price")
        edit_opts = {f"{c.name} (ID: {c.id})": c.id for c in courses}
        edit_sel = st.selectbox("Select Course", list(edit_opts.keys()))
        edit_id = edit_opts[edit_sel]
        selected_course = next(c for c in courses if c.id == edit_id)

        new_price = st.number_input(
            "New Price per Level (EGP)",
            value=float(selected_course.price_per_level),
            min_value=0.0,
            step=50.0,
            key="edit_price",
        )
        if st.button("Update Price", type="primary"):
            try:
                acad_srv.update_course_price(edit_id, new_price)
                st.success(f"✅ Price updated to {new_price} EGP.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ {e}")
