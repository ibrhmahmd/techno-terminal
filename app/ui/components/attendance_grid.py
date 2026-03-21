import streamlit as st
from app.db.connection import get_session
from app.modules.crm.crm_models import Student
from app.modules.attendance import attendance_service as att_srv

# Toggle cycle: unset -> present -> absent -> unset
NEXT_STATE = {
    None: "present",
    "present": "absent",
    "absent": None,
    "late": None,  # clicking late/excused resets
    "excused": None,
}

STATE_EMOJI = {
    "present": "✅",
    "absent": "❌",
    "late": "🕒",
    "excused": "➖",
    None: "◻️",
}


def render_attendance_grid(sessions: list, roster: list):
    """
    Renders an interactive attendance grid.
    Columns = sessions, Rows = students.
    Clicking a cell toggles the state.
    """
    if not roster:
        st.info("No students enrolled in this level.")
        return

    if not sessions:
        st.info("No sessions available to mark.")
        return

    # Load initial state from DB if not yet in session_state
    grid_key = f"att_grid_{sessions[0].group_id}_{sessions[0].level_number}"

    if grid_key not in st.session_state:
        # Fetch existing attendance
        db_state = {}
        for sess in sessions:
            att_records = att_srv.get_session_roster_with_attendance(sess.id)
            for r in att_records:
                if r["status"]:
                    db_state[(r["student_id"], sess.id)] = r["status"]
        st.session_state[grid_key] = db_state

    current_state = st.session_state[grid_key]

    # Pre-fetch student names
    student_map = {}
    with get_session() as db:
        for enr in roster:
            s_obj = db.get(Student, enr.student_id)
            student_map[enr.student_id] = (
                s_obj.full_name if s_obj else f"Student #{enr.student_id}"
            )

    # Build the view grid
    st.markdown("#### Attendance")
    st.caption("Click a cell to toggle: ◻️ (Unmarked) ➔ ✅ (Present) ➔ ❌ (Absent)")
    st.caption("Click a student's name to view their profile in Student Management.")

    # Pre-fetch instructor names
    from app.modules.hr import hr_service as hr_srv

    instructors = hr_srv.get_active_instructors()
    inst_map = {i.id: i.full_name for i in instructors}

    # Construct columns headers
    cols = st.columns([2] + [1] * len(sessions))
    cols[0].markdown("**Student Name**")
    for i, sess in enumerate(sessions):
        actual_instructor_name = inst_map.get(sess.actual_instructor_id, "Unassigned")
        header_html = f"**S{sess.session_number}**<br/><small>{actual_instructor_name}</small><br/><small>{sess.session_date}</small>"
        cols[i + 1].markdown(
            header_html,
            unsafe_allow_html=True,
        )

        # Edit and Delete buttons cleanly merged into a single cell row
        delete_key = f"del_confirm_{sess.id}"
        if delete_key not in st.session_state:
            st.session_state[delete_key] = False

        bc1, bc2 = cols[i + 1].columns(2)
        from app.ui.components.forms.edit_session_form import render_edit_session_form

        if not st.session_state[delete_key]:
            if bc1.button("✏️", key=f"edit_sess_{sess.id}", use_container_width=True, help="Edit"):
                render_edit_session_form(sess.id)
            if bc2.button("🗑️", key=f"del_init_{sess.id}", use_container_width=True, help="Delete"):
                st.session_state[delete_key] = True
                st.rerun()
        else:
            if bc1.button("❌", key=f"del_no_{sess.id}", use_container_width=True, help="Cancel"):
                st.session_state[delete_key] = False
                st.rerun()
            if bc2.button("⚠️", key=f"del_yes_{sess.id}", type="primary", use_container_width=True, help="Confirm"):
                from app.modules.academics import academics_service as acad_srv
                try:
                    acad_srv.delete_session(sess.id)
                    del st.session_state[delete_key]
                    st.rerun()
                except Exception as e:
                    st.error("Clear attendance first")
                    st.session_state[delete_key] = False

    # Render rows
    for enr in roster:
        sid = enr.student_id
        row_cols = st.columns([2] + [1] * len(sessions))

        # Clickable student name routing to Student Management target
        if row_cols[0].button(
            student_map[sid], key=f"nav_stu_{sid}", help="Go to Student Profile"
        ):
            st.session_state["nav_target_student_id"] = sid
            st.switch_page("pages/1_Directory.py")

        for i, sess in enumerate(sessions):
            state = current_state.get((sid, sess.id), None)
            label = STATE_EMOJI[state]

            # Button key
            btn_key = f"btn_{sid}_{sess.id}"

            if row_cols[i + 1].button(label, key=btn_key, use_container_width=True):
                # Toggle
                current_state[(sid, sess.id)] = NEXT_STATE[state]
                st.rerun()

    # Save button
    st.divider()
    if st.button("💾 Save All Attendance Changes", type="primary"):
        # We need to bulk-save by session
        try:
            total_saved = 0
            for sess in sessions:
                sess_payload = {}
                for enr in roster:
                    sid = enr.student_id
                    val = current_state.get((sid, sess.id))
                    if val is not None:
                        sess_payload[sid] = val

                if sess_payload:
                    res = att_srv.mark_session_attendance(sess.id, sess_payload, None)
                    total_saved += res["marked"]

            st.success(f"Successfully saved {total_saved} attendance records.")
        except Exception as e:
            st.error(f"Error saving attendance: {e}")
