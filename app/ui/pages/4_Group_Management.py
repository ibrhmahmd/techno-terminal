import streamlit as st
import pandas as pd
from datetime import date, time
from app.ui.components.auth_guard import require_auth
from app.modules.academics import service as acad_srv
from app.modules.auth import service as auth_srv
from app.modules.enrollments import service as enroll_srv
from app.modules.attendance import service as att_srv
from app.modules.crm.models import Student
from app.db.connection import get_session

require_auth()

st.title("🗂️ Group Management")
st.markdown("Create groups, manage their sessions, and mark student attendance.")

# ─── Allowed hours: 11 AM – 9 PM = hours 11..21 ─────────────────────────────
ALLOWED_HOURS = list(range(11, 22))  # 11, 12, ..., 21
MINUTES = ["00", "15", "30", "45"]


def to_time(hour: int, minute_str: str, ampm: str) -> time:
    h24 = hour % 12 + (12 if ampm == "PM" else 0)
    return time(h24, int(minute_str))


# ─────────────────────────────────────────────────────────────────────────────
tab_create, tab_manage = st.tabs(["Create Group", "Manage Groups"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: Create Group
# ══════════════════════════════════════════════════════════════════════════════
with tab_create:
    st.subheader("New Group")
    st.caption("Sessions for Level 1 are generated automatically after creation.")

    courses = acad_srv.get_active_courses()
    instructors = auth_srv.get_active_instructors()

    if not courses:
        st.warning("No active courses. Create a course in Course Management first.")
    elif not instructors:
        st.warning("No active instructors found.")
    else:
        with st.form("new_group_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                course_opts = {c.name: c.id for c in courses}
                sel_course = st.selectbox("Course *", list(course_opts.keys()))
                sel_course_id = course_opts[sel_course]

                inst_opts = {i.full_name: i.id for i in instructors}
                sel_inst = st.selectbox("Instructor *", list(inst_opts.keys()))
                sel_inst_id = inst_opts[sel_inst]

            with col2:
                max_cap = st.number_input("Max Capacity", min_value=1, value=12)
                day = st.selectbox(
                    "Day *",
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

            with col3:
                # 12h time pickers, hours 11AM–9PM only
                HOUR_12_OPTIONS = [11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9]
                AMPM_START_OPTIONS = ["AM", "PM"]

                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    st_h = st.selectbox(
                        "Start Hr", HOUR_12_OPTIONS, index=3, key="grp_sth"
                    )
                with sc2:
                    st_m = st.selectbox("Start Min", MINUTES, key="grp_stm")
                with sc3:
                    st_p = st.selectbox(
                        "Start AM/PM", ["AM", "PM"], index=1, key="grp_stp"
                    )

                ec1, ec2, ec3 = st.columns(3)
                with ec1:
                    en_h = st.selectbox(
                        "End Hr", HOUR_12_OPTIONS, index=5, key="grp_enh"
                    )
                with ec2:
                    en_m = st.selectbox("End Min", MINUTES, key="grp_enm")
                with ec3:
                    en_p = st.selectbox(
                        "End AM/PM", ["AM", "PM"], index=1, key="grp_enp"
                    )

            submit = st.form_submit_button(
                "Create Group & Generate Sessions", type="primary"
            )
            if submit:
                try:
                    group, sessions = acad_srv.schedule_group(
                        {
                            "course_id": sel_course_id,
                            "instructor_id": sel_inst_id,
                            "max_capacity": int(max_cap),
                            "default_day": day,
                            "default_time_start": to_time(st_h, st_m, st_p),
                            "default_time_end": to_time(en_h, en_m, en_p),
                        }
                    )
                    st.success(
                        f"✅ Group **'{group.name}'** created (ID: {group.id}) "
                        f"with {len(sessions)} sessions auto-generated."
                    )
                except ValueError as e:
                    st.error(f"❌ {e}")
                except Exception as e:
                    st.error(f"❌ Unexpected error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: Manage Groups (details, sessions, attendance)
# ══════════════════════════════════════════════════════════════════════════════
with tab_manage:
    # ── Group selector with enriched names ────────────────────────────────────
    enriched = acad_srv.get_all_active_groups_enriched()
    if not enriched:
        st.info("No active groups found.")
        st.stop()

    # Active groups summary table
    st.subheader("Active Groups")
    df_groups = pd.DataFrame(enriched)
    display_cols = [
        "id",
        "group_name",
        "course_name",
        "instructor_name",
        "level_number",
        "default_day",
        "default_time_start",
        "default_time_end",
        "max_capacity",
    ]
    st.dataframe(df_groups[display_cols], hide_index=True, use_container_width=True)

    st.divider()

    # ── Select one group to drill into ────────────────────────────────────────
    group_opts = {f"{g['group_name']} (ID: {g['id']})": g["id"] for g in enriched}
    sel_g_label = st.selectbox("Select Group to Manage", list(group_opts.keys()))
    sel_g_id = group_opts[sel_g_label]
    sel_g_info = next(g for g in enriched if g["id"] == sel_g_id)

    st.markdown(
        f"**Group:** {sel_g_info['group_name']} · "
        f"**Instructor:** {sel_g_info['instructor_name']} · "
        f"**Current Level:** {sel_g_info['level_number']}"
    )

    level_filter = st.number_input(
        "View Level",
        min_value=1,
        value=int(sel_g_info["level_number"]),
        key="level_filter",
    )

    # ─── Sessions sub-section ─────────────────────────────────────────────────
    st.subheader(f"Sessions — Level {level_filter}")
    sessions = acad_srv.list_group_sessions(sel_g_id, int(level_filter))

    if sessions:
        sessions_data = []
        for s in sessions:
            sessions_data.append(
                {
                    "id": s.id,
                    "session_number": s.session_number,
                    "date": s.session_date,
                    "start": str(s.start_time or ""),
                    "end": str(s.end_time or ""),
                    "extra": "⭐" if s.is_extra_session else "",
                    "substitute": "🔄" if s.is_substitute else "",
                }
            )
        df_sess = pd.DataFrame(sessions_data)
        st.dataframe(df_sess, hide_index=True, use_container_width=True)

        # Remove session
        with st.expander("🗑️ Remove a Session"):
            del_opts = {
                f"Session #{s.session_number} — {s.session_date}": s.id
                for s in sessions
            }
            del_sel = st.selectbox(
                "Session to Remove", list(del_opts.keys()), key="del_sess"
            )
            if st.button("Remove Session", type="secondary"):
                if acad_srv.delete_session(del_opts[del_sel]):
                    st.success("Session removed.")
                    st.rerun()
                else:
                    st.error("Could not find that session.")
    else:
        st.info("No sessions for this level.")

    # Add extra session
    with st.expander("➕ Add Extra Session"):
        extra_date = st.date_input(
            "Extra Session Date", value=date.today(), key="extra_date"
        )
        extra_notes = st.text_input("Notes (optional)", key="extra_notes")
        if st.button("Add Extra Session", key="btn_extra"):
            try:
                cs = acad_srv.add_extra_session(
                    sel_g_id, int(level_filter), extra_date, extra_notes or None
                )
                st.success(
                    f"✅ Extra session #{cs.session_number} added on {extra_date}."
                )
                st.rerun()
            except Exception as e:
                st.error(f"❌ {e}")

    # Generate full level sessions
    with st.expander("🗓️ Generate Full Level Sessions"):
        gen_start = st.date_input(
            "Start From Date", value=date.today(), key="gen_start"
        )
        if st.button("Generate Sessions", type="primary", key="btn_gen"):
            try:
                created = acad_srv.generate_level_sessions(
                    sel_g_id, int(level_filter), gen_start
                )
                st.success(f"✅ {len(created)} sessions generated.")
                st.rerun()
            except ValueError as e:
                st.error(f"❌ {e}")

    # ── Level advance ─────────────────────────────────────────────────────────
    if acad_srv.check_level_complete(sel_g_id, int(level_filter)):
        st.divider()
        st.success(
            f"🎓 Level {level_filter} is complete! "
            f"**Instructor:** {sel_g_info['instructor_name']}"
        )
        if st.button(f"Advance to Level {level_filter + 1}", type="primary"):
            try:
                acad_srv.advance_group_level(sel_g_id)
                st.success(f"Group advanced to Level {level_filter + 1}!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ {e}")

    # ─── Attendance sub-section ───────────────────────────────────────────────
    if sessions:
        st.divider()
        st.subheader("Mark Attendance")

        sess_opts = {
            f"Session #{s.session_number} — {s.session_date}{'  ⭐' if s.is_extra_session else ''}": s.id
            for s in sessions
        }
        sel_sess_label = st.selectbox(
            "Select Session", list(sess_opts.keys()), key="att_sess"
        )
        sel_sess_id = sess_opts[sel_sess_label]

        roster = enroll_srv.get_group_roster(sel_g_id, int(level_filter))
        if not roster:
            st.info(
                "No enrolled students for this level. Enroll students in the Enrollment page."
            )
        else:
            existing = att_srv.get_session_roster_with_attendance(sel_sess_id)
            existing_map = {r["student_id"]: r["status"] for r in existing}
            STATUS_OPTIONS = ["present", "absent", "late", "excused"]

            student_statuses = {}
            with st.form(f"att_form_{sel_sess_id}"):
                h1, h2 = st.columns([3, 2])
                h1.markdown("**Student**")
                h2.markdown("**Status**")

                for enrollment in roster:
                    sid = enrollment.student_id
                    with get_session() as db:
                        student = db.get(Student, sid)
                        sname = student.full_name if student else f"Student #{sid}"

                    prior = existing_map.get(sid, "present")
                    idx = STATUS_OPTIONS.index(prior) if prior in STATUS_OPTIONS else 0

                    c1, c2 = st.columns([3, 2])
                    c1.write(sname)
                    status = c2.selectbox(
                        "",
                        STATUS_OPTIONS,
                        index=idx,
                        key=f"att_{sel_sess_id}_{sid}",
                        label_visibility="collapsed",
                    )
                    student_statuses[sid] = status

                submitted = st.form_submit_button(
                    "Save Attendance", type="primary", use_container_width=True
                )
                if submitted:
                    try:
                        result = att_srv.mark_session_attendance(
                            session_id=sel_sess_id,
                            student_statuses=student_statuses,
                            marked_by_user_id=None,
                        )
                        present_n = sum(
                            1 for v in student_statuses.values() if v == "present"
                        )
                        absent_n = sum(
                            1 for v in student_statuses.values() if v == "absent"
                        )
                        st.success(
                            f"✅ Saved! {result['marked']} records. "
                            f"Present: {present_n} · Absent: {absent_n}"
                        )
                        if result["skipped"]:
                            st.warning(
                                f"⚠️ Skipped {len(result['skipped'])} student(s) with no valid enrollment."
                            )

                        # Check level completion after attendance
                        if acad_srv.check_level_complete(sel_g_id, int(level_filter)):
                            st.info(
                                f"🎓 All Level {level_filter} sessions are now populated. You can advance the group level above."
                            )
                    except Exception as e:
                        st.error(f"❌ {e}")
