import streamlit as st
import pandas as pd

from app.modules.finance import service as fin_srv
from app.modules.crm import service as crm_srv


def render_receipt_detail(receipt_id: int):
    """Renders a read-only receipt detail view with the option to issue a refund."""

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("⬅️ Back"):
            del st.session_state["selected_receipt_id"]
            st.rerun()
    with col2:
        st.subheader(f"Receipt Detail #{receipt_id}")

    data = fin_srv.get_receipt_detail(receipt_id)
    if not data:
        st.error("Receipt not found.")
        return

    r = data["receipt"]
    lines: list = data["lines"]
    total: float = data["total"]

    # Header info
    guardian_name = "—"
    if r.guardian_id:
        from app.modules.crm.repository import get_guardian_by_id
        from app.db.connection import get_session

        with get_session() as db:
            g = get_guardian_by_id(db, r.guardian_id)
            if g:
                guardian_name = g.full_name

    st.markdown(
        f"**Receipt #:** `{r.receipt_number or 'N/A'}` | "
        f"**Guardian:** {guardian_name} | "
        f"**Method:** {(r.payment_method or 'N/A').capitalize()} | "
        f"**Date:** {str(r.paid_at)[:10] if r.paid_at else 'N/A'}"
    )
    st.markdown(f"**Total Collected: {total:.0f} EGP**")

    st.divider()

    # Payment lines
    st.markdown("#### Payment Lines")
    if lines:
        df_data = []
        for p in lines:
            df_data.append(
                {
                    "Payment ID": p.id,
                    "Student ID": p.student_id,
                    "Enrollment ID": p.enrollment_id or "—",
                    "Type": p.transaction_type.capitalize(),
                    "Payment For": (p.payment_type or "—")
                    .replace("_", " ")
                    .capitalize(),
                    "Amount (EGP)": p.amount,
                    "Discount (EGP)": p.discount_amount,
                    "Notes": p.notes or "",
                }
            )
        st.dataframe(pd.DataFrame(df_data), hide_index=True, use_container_width=True)
    else:
        st.info("No payment lines on this receipt.")

    st.divider()

    # Refund section
    with st.expander("↩️ Issue a Refund"):
        st.caption("Select an enrollment from this receipt to refund.")
        enrollment_lines = [
            p for p in lines if p.enrollment_id and p.transaction_type != "refund"
        ]
        if not enrollment_lines:
            st.info("No refundable lines on this receipt.")
        else:
            enr_opts = {
                f"Enrollment #{p.enrollment_id} — Student #{p.student_id} ({p.amount:.0f} EGP)": p.enrollment_id
                for p in enrollment_lines
            }
            sel_enr_label = st.selectbox(
                "Select Enrollment", list(enr_opts.keys()), key="refund_enr"
            )
            sel_enr_id = enr_opts[sel_enr_label]
            refund_amount = st.number_input(
                "Refund Amount (EGP)", min_value=1.0, step=50.0, key="refund_amt"
            )
            refund_reason = st.text_input("Reason for Refund", key="refund_reason")

            if st.button("Confirm Refund", type="primary"):
                try:
                    result = fin_srv.issue_refund(
                        enrollment_id=sel_enr_id,
                        amount=refund_amount,
                        reason=refund_reason or "Refund",
                        received_by_user_id=None,
                    )
                    st.success(
                        f"✅ Refund issued! Receipt: **{result['receipt_number']}** | "
                        f"Amount: {result['refunded_amount']:.0f} EGP | "
                        f"New balance: {result.get('new_balance', 'N/A')}"
                    )
                except Exception as e:
                    st.error(f"❌ {e}")
