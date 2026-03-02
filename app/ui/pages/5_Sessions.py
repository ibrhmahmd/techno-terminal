import streamlit as st
import pandas as pd
from datetime import date
from app.ui.components.auth_guard import require_auth
from app.modules.academics import service as acad_srv
from app.modules.auth import service as auth_srv

require_auth()

st.title("📅 Session Management")
st.markdown("Generate sessions for a group level and manage substitutes.")

# ─── Group selector ───────────────────────────────────────────────────────────
groups = acad_srv.get_all_active_groups()
if not groups:
    st.warning("No active groups found. Create a group in Course Management first.")
    st.stop()

group_opts = {f"{g.name} (ID: {g.id})": g.id for g in groups}
sel_group_label = st.selectbox("Select Group", list(group_opts.keys()))
sel_group_id = group_opts[sel_group_label]
sel_group = next(g for g in groups if g.id == sel_group_id)

level_number = st.number_input(
    "Level Number", min_value=1, value=sel_group.level_number
)

st.divider()

# ─── Existing sessions table ───────────────────────────────────────────────────
st.subheader(f"Sessions — Level {level_number}")
sessions = acad_srv.list_group_sessions(sel_group_id, level_number)

if sessions:
    df = pd.DataFrame([s.model_dump() for s in sessions])
    display_cols = [
        "id",
        "session_number",
        "session_date",
        "start_time",
        "end_time",
        "is_extra_session",
        "is_substitute",
        "actual_instructor_id",
    ]
    st.dataframe(df[display_cols], hide_index=True, use_container_width=True)
else:
    st.info("No sessions yet for this level. Generate them below.")

st.divider()

# ─── Generate sessions ─────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Generate Level Sessions")
    start_date = st.date_input("Start From Date", value=date.today())
    if st.button("Generate Sessions", type="primary", use_container_width=True):
        try:
            created = acad_srv.generate_level_sessions(
                sel_group_id, int(level_number), start_date
            )
            st.success(f"✅ Created {len(created)} sessions starting {start_date}.")
            st.rerun()
        except ValueError as e:
            st.error(f"❌ {e}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")

with col2:
    st.subheader("Add Extra Session")
    extra_date = st.date_input("Extra Session Date", value=date.today(), key="extra_d")
    extra_notes = st.text_input("Notes (Optional)", key="extra_n")
    if st.button("Add Extra Session", use_container_width=True):
        try:
            cs = acad_srv.add_extra_session(
                sel_group_id, int(level_number), extra_date, extra_notes or None
            )
            st.success(f"✅ Extra session #{cs.session_number} added on {extra_date}.")
            st.rerun()
        except ValueError as e:
            st.error(f"❌ {e}")

st.divider()

# ─── Mark substitute instructor ────────────────────────────────────────────────
if sessions:
    st.subheader("Mark Substitute Instructor")
    sess_opts = {
        f"Session #{s.session_number} — {s.session_date}{'  ⭐ Extra' if s.is_extra_session else ''}": s.id
        for s in sessions
    }
    sel_sess_label = st.selectbox(
        "Select Session", list(sess_opts.keys()), key="sub_sess"
    )
    sel_sess_id = sess_opts[sel_sess_label]

    instructors = auth_srv.get_active_instructors()
    if instructors:
        inst_opts = {i.full_name: i.id for i in instructors}
        sel_inst_label = st.selectbox(
            "Substitute Instructor", list(inst_opts.keys()), key="sub_inst"
        )
        sel_inst_id = inst_opts[sel_inst_label]

        if st.button("Mark Substitute", use_container_width=True):
            try:
                acad_srv.mark_substitute_instructor(sel_sess_id, sel_inst_id)
                st.success(f"✅ Substitute marked for session #{sel_sess_id}.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ {e}")
    else:
        st.warning("No active instructors found.")
