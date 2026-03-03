import streamlit as st
import pandas as pd
from datetime import date
from app.db.connection import get_session
from app.modules.crm.models import Student
from app.modules.attendance import service as att_srv

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
    st.markdown("### Attendance")
    st.caption("Click a cell to toggle: ◻️ (Unmarked) ➔ ✅ (Present) ➔ ❌ (Absent)")

    # Construct columns headers
    cols = st.columns([2] + [1] * len(sessions))
    cols[0].markdown("**Student Name**")
    for i, sess in enumerate(sessions):
        cols[i + 1].markdown(
            f"**S{sess.session_number}**<br/><small>{sess.session_date}</small>",
            unsafe_allow_html=True,
        )

    # Render rows
    for enr in roster:
        sid = enr.student_id
        row_cols = st.columns([2] + [1] * len(sessions))
        row_cols[0].write(student_map[sid])

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
