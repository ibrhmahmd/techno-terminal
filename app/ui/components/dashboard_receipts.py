import streamlit as st
import pandas as pd
from datetime import date

from app.modules.finance import finance_service as fin_srv
from app.modules.crm import crm_service as crm_srv
from app.shared.exceptions import ValidationError


def render_receipt_browser():
    """Dashboard: date-range receipt search → row opens `render_receipt_detail` via session (Sprint 4 / U8)."""
    st.subheader("📋 Browse receipts")
    st.caption(
        "Choose a date range (UTC day boundaries) and optional filters, then **Search**. "
        "Click a row to open the receipt (receipt # shown in detail)."
    )
    today = date.today()
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        from_d = st.date_input("From", value=today, key="dash_rcpt_from")
    with c2:
        to_d = st.date_input("To", value=today, key="dash_rcpt_to")
    with c3:
        rnum = st.text_input("Receipt # contains", key="dash_rcpt_num", placeholder="Optional")

    guardian_id: int | None = None
    pq = st.text_input(
        "Parent (name or phone)",
        key="dash_rcpt_pq",
        placeholder="Optional, min 2 characters",
    )
    if pq and len(pq) >= 2:
        parents = crm_srv.search_guardians(pq)
        if parents:
            labels = ["— Any parent —"] + [f"{g.full_name} ({g.phone_primary})" for g in parents]
            idx = st.selectbox(
                "Parent match",
                range(len(labels)),
                format_func=lambda i: labels[i],
                key="dash_rcpt_pidx",
            )
            if idx > 0:
                guardian_id = parents[idx - 1].id
        else:
            st.caption("No parents match.")

    student_id: int | None = None
    sq = st.text_input(
        "Student name",
        key="dash_rcpt_sq",
        placeholder="Optional, min 2 characters",
    )
    if sq and len(sq) >= 2:
        studs = crm_srv.search_students(sq)
        if studs:
            labels_s = ["— Any student —"] + [f"{s.full_name} (#{s.id})" for s in studs]
            idxs = st.selectbox(
                "Student match",
                range(len(labels_s)),
                format_func=lambda i: labels_s[i],
                key="dash_rcpt_sidx",
            )
            if idxs > 0:
                student_id = studs[idxs - 1].id
        else:
            st.caption("No students match.")

    if st.button("🔍 Search", type="primary", key="dash_rcpt_search_btn"):
        st.session_state["dash_rcpt_last_search"] = {
            "from_d": from_d,
            "to_d": to_d,
            "rnum": rnum.strip() or None,
            "guardian_id": guardian_id,
            "student_id": student_id,
        }

    last = st.session_state.get("dash_rcpt_last_search")
    if not last:
        st.info("Use **Search** to load receipts for the selected range.")
        return

    try:
        rows = fin_srv.search_receipts(
            last["from_d"],
            last["to_d"],
            guardian_id=last["guardian_id"],
            student_id=last["student_id"],
            receipt_number_contains=last["rnum"],
            limit=200,
        )
    except ValidationError as e:
        st.error(e.message)
        return

    if not rows:
        st.warning("No receipts match.")
        return

    disp = []
    for r in rows:
        pa = r.get("paid_at")
        disp.append(
            {
                "Receipt ID": r["id"],
                "Receipt #": r.get("receipt_number") or "—",
                "Parent": r.get("guardian_name") or "—",
                "Method": (r.get("payment_method") or "—").capitalize(),
                "Paid at": str(pa)[:19] if pa else "—",
                "Total (EGP)": float(r.get("total") or 0),
            }
        )
    df = pd.DataFrame(disp)
    st.caption(f"{len(rows)} receipt(s) (max 200). Select a row to open.")
    event = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun",
        key="dash_rcpt_df",
    )
    if event.selection.rows:
        row_i = event.selection.rows[0]
        rid = int(disp[row_i]["Receipt ID"])
        st.session_state["selected_receipt_id"] = rid
        st.rerun()
