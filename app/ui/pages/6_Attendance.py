import streamlit as st
from app.ui.components.auth_guard import require_auth
from app.modules.academics import service as acad_srv
from app.modules.enrollments import service as enroll_srv
from app.modules.crm import repository as crm_repo
from app.modules.crm.models import Student
from app.modules.attendance import service as att_srv
from app.db.connection import get_session

require_auth()

st.title("✅ Attendance")
st.markdown(
    "Mark attendance for a session. Select a group, then a session, then submit statuses."
)

# ─── Step 1: Select group ──────────────────────────────────────────────────────
groups = acad_srv.get_all_active_groups()
if not groups:
    st.warning("No active groups found.")
    st.stop()

group_opts = {f"{g.name}": g.id for g in groups}
sel_group_label = st.selectbox("1. Select Group", list(group_opts.keys()))
sel_group_id = group_opts[sel_group_label]
sel_group = next(g for g in groups if g.id == sel_group_id)

# ─── Step 2: Select session ─────────────────────────────────────────────────────
sessions = acad_srv.list_group_sessions(sel_group_id)
if not sessions:
    st.info(
        "No sessions for this group yet. Go to Session Management to generate them."
    )
    st.stop()

session_opts = {
    f"L{s.level_number} · Session #{s.session_number} — {s.session_date}{'  ⭐' if s.is_extra_session else ''}": s.id
    for s in sessions
}
sel_session_label = st.selectbox("2. Select Session", list(session_opts.keys()))
sel_session_id = session_opts[sel_session_label]
sel_session = next(s for s in sessions if s.id == sel_session_id)

st.divider()

# ─── Step 3: Mark attendance ─────────────────────────────────────────────────────
st.subheader(f"3. Mark Attendance — {sel_session.session_date}")

# Get roster for this group+level
roster = enroll_srv.get_group_roster(sel_group_id, sel_session.level_number)
if not roster:
    st.warning("No active enrollments for this group level. Enroll students first.")
    st.stop()

# Pre-load existing attendance for this session
existing = att_srv.get_session_roster_with_attendance(sel_session_id)
existing_map = {r["student_id"]: r["status"] for r in existing}

# Build attendance form
STATUS_OPTIONS = ["present", "absent", "late", "excused"]

student_statuses = {}

with st.form("attendance_form"):
    # Header row
    h1, h2, h3 = st.columns([3, 2, 1])
    h1.markdown("**Student**")
    h2.markdown("**Status**")
    h3.markdown("**Enrollment ID**")

    for enrollment in roster:
        student_id = enrollment.student_id
        # Get student name
        with get_session() as db:
            student = db.get(Student, student_id)
            student_name = student.full_name if student else f"Student #{student_id}"

        prior_status = existing_map.get(student_id, "present")
        prior_idx = (
            STATUS_OPTIONS.index(prior_status) if prior_status in STATUS_OPTIONS else 0
        )

        c1, c2, c3 = st.columns([3, 2, 1])
        c1.write(student_name)
        status = c2.selectbox(
            label="status",
            options=STATUS_OPTIONS,
            index=prior_idx,
            key=f"att_{student_id}",
            label_visibility="collapsed",
        )
        c3.caption(f"#{enrollment.id}")
        student_statuses[student_id] = status

    st.divider()
    submit = st.form_submit_button(
        "Submit Attendance", type="primary", use_container_width=True
    )

    if submit:
        try:
            result = att_srv.mark_session_attendance(
                session_id=sel_session_id,
                student_statuses=student_statuses,
                marked_by_user_id=None,  # TODO: pass current user.id in Phase 5
            )
            present = sum(1 for s in student_statuses.values() if s == "present")
            absent = sum(1 for s in student_statuses.values() if s == "absent")
            st.success(
                f"✅ Attendance saved! {result['marked']} records written. "
                f"Present: {present} · Absent: {absent}"
            )
            if result["skipped"]:
                st.warning(
                    f"⚠️ Skipped {len(result['skipped'])} student(s) with no active enrollment."
                )
        except Exception as e:
            st.error(f"❌ {e}")
