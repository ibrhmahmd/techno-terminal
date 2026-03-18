import streamlit as st
import pandas as pd
from datetime import time
import datetime

from app.modules.academics import service as acad_srv
from app.modules.auth import service as auth_srv
from app.shared.exceptions import NotFoundError, BusinessRuleError, ValidationError, ConflictError

ALLOWED_HOURS = list(range(11, 22))
MINUTES = ["00", "15", "30", "45"]


def to_time(hour: int, minute_str: str, ampm: str) -> time:
    h24 = hour % 12 + (12 if ampm == "PM" else 0)
    return time(h24, int(minute_str))


@st.dialog("Create New Group")
def modal_create_group():
    courses = acad_srv.get_active_courses()
    instructors = auth_srv.get_active_instructors()

    if not courses:
        st.warning("No active courses.")
        return
    if not instructors:
        st.warning("No active instructors.")
        return

    with st.form("new_group_form"):
        course_opts = {c.name: c.id for c in courses}
        sel_course = st.selectbox("Course *", list(course_opts.keys()))

        inst_opts = {i.full_name: i.id for i in instructors}
        sel_inst = st.selectbox("Instructor *", list(inst_opts.keys()))

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

        HOUR_12 = [11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9]

        st.markdown("**Start Time**")
        sc1, sc2, sc3 = st.columns(3)
        st_h = sc1.selectbox("Hr", HOUR_12, index=3, key="sth")
        st_m = sc2.selectbox("Min", MINUTES, key="stm")
        st_p = sc3.selectbox("AM/PM", ["AM", "PM"], index=1, key="stp")

        st.markdown("**End Time**")
        ec1, ec2, ec3 = st.columns(3)
        en_h = ec1.selectbox("Hr", HOUR_12, index=5, key="enh")
        en_m = ec2.selectbox("Min", MINUTES, key="enm")
        en_p = ec3.selectbox("AM/PM", ["AM", "PM"], index=1, key="enp")

        if st.form_submit_button("Create Group", type="primary"):
            try:
                group, _ = acad_srv.schedule_group(
                    {
                        "course_id": course_opts[sel_course],
                        "instructor_id": inst_opts[sel_inst],
                        "max_capacity": int(max_cap),
                        "default_day": day,
                        "default_time_start": to_time(st_h, st_m, st_p),
                        "default_time_end": to_time(en_h, en_m, en_p),
                    }
                )
                st.success(f"Group '{group.name}' created.")
                st.session_state["group_creation_success"] = True
                st.rerun()
            except ValidationError as e:
                st.error(f"❌ Invalid input: {e.message}")
            except NotFoundError as e:
                st.warning(f"⚠️ Not found: {e.message}")
            except ConflictError as e:
                st.error(f"❌ Conflict: {e.message}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")


@st.dialog("Browse All Groups", width="large")
def modal_browse_all_groups(all_groups: list[dict]):
    if not all_groups:
        st.info("No groups found.")
        return

    PAGE_SIZE = 20
    if "bg_page" not in st.session_state:
        st.session_state["bg_page"] = 0

    total_pages = (len(all_groups) - 1) // PAGE_SIZE + 1
    start_idx = st.session_state["bg_page"] * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_data = all_groups[start_idx:end_idx]

    df = pd.DataFrame(page_data)
    display_cols = [
        "id",
        "group_name",
        "course_name",
        "instructor_name",
        "level_number",
        "default_day",
        "default_time_start",
    ]

    event = st.dataframe(
        df[display_cols],
        hide_index=True,
        use_container_width=True,
        selection_mode="single-row",
        on_select="rerun",
    )

    selected_rows = event.selection.rows
    if selected_rows:
        real_idx = selected_rows[0]
        selected_id = page_data[real_idx]["id"]
        st.session_state["selected_group_id"] = selected_id
        st.session_state["bg_page"] = 0
        st.rerun()

    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("⬅️ Prev", disabled=(st.session_state["bg_page"] == 0)):
        st.session_state["bg_page"] -= 1
        st.rerun()
    c2.markdown(
        f"<div style='text-align: center'>Page {st.session_state['bg_page'] + 1} of {total_pages}</div>",
        unsafe_allow_html=True,
    )
    if c3.button("Next ➡️", disabled=(st.session_state["bg_page"] >= total_pages - 1)):
        st.session_state["bg_page"] += 1
        st.rerun()


def render_group_overview():
    col_l, col_r = st.columns([3, 1])
    with col_l:
        st.subheader("Groups by Day")
    with col_r:
        if st.button("➕ Create Group", use_container_width=True):
            modal_create_group()

    # 7 day buttons
    days = [
        "Saturday",
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
    ]

    if "selected_day_filter" not in st.session_state:
        # Default to today's day name
        st.session_state["selected_day_filter"] = datetime.date.today().strftime("%A")

    day_cols = st.columns(7)
    for i, day in enumerate(days):
        is_selected = day == st.session_state["selected_day_filter"]
        if day_cols[i].button(
            day,
            use_container_width=True,
            type="primary" if is_selected else "secondary",
        ):
            st.session_state["selected_day_filter"] = day
            st.rerun()

    # Search bar
    search_q = st.text_input(
        "🔍 Search Groups (name, course, time)", help="Filters the list below"
    )

    # Fetch all active groups to filter by standard day
    # This solves the bug where groups wouldn't show up if their first session was missing or postponed
    all_groups = acad_srv.get_all_active_groups_enriched()
    todays_groups = [
        g
        for g in all_groups
        if g["default_day"] == st.session_state["selected_day_filter"]
    ]

    # Filter live based on search_q
    if search_q:
        q = search_q.lower()
        todays_groups = [
            g
            for g in todays_groups
            if q in g["group_name"].lower()
            or q in g["course_name"].lower()
            or q in str(g["default_time_start"]).lower()
        ]

    st.markdown("Select a row below to manage its sessions and attendance:")

    if todays_groups:
        df = pd.DataFrame(todays_groups)
        display_cols = [
            "id",
            "group_name",
            "course_name",
            "instructor_name",
            "level_number",
            "default_day",
            "default_time_start",
            "default_time_end",
        ]

        event = st.dataframe(
            df[display_cols],
            hide_index=True,
            use_container_width=True,
            selection_mode="single-row",
            on_select="rerun",
        )

        if event.selection.rows:
            sel_idx = event.selection.rows[0]
            st.session_state["selected_group_id"] = todays_groups[sel_idx]["id"]
            st.rerun()
    else:
        st.info("No groups scheduled for today or matching your search.")

    st.divider()

    if st.button("📋 Browse All Active Groups", use_container_width=True):
        all_enriched = acad_srv.get_all_active_groups_enriched()
        modal_browse_all_groups(all_enriched)
