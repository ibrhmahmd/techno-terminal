import streamlit as st
import pandas as pd

from app.modules.finance import finance_service as fin_srv
from app.modules.crm import crm_service as crm_srv


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
    parent_name = "—"
    if r.guardian_id:
        from app.modules.crm.crm_service import get_guardian_by_id

        g = get_guardian_by_id(r.guardian_id)
        if g:
            parent_name = g.full_name

    st.markdown(
        f"**Receipt #:** `{r.receipt_number or 'N/A'}` | "
        f"**Parent:** {parent_name} | "
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
        st.caption("Select a payment line from this receipt to refund.")
        refundable_lines = [p for p in lines if p.transaction_type != "refund"]
        if not refundable_lines:
            st.info("No refundable lines on this receipt.")
        else:
            line_opts = {
                f"{(p.payment_type or 'Course Level').replace('_', ' ').capitalize()} — Student #{p.student_id} ({p.amount:.0f} EGP)": p.id
                for p in refundable_lines
            }
            sel_line_label = st.selectbox(
                "Select Payment Line", list(line_opts.keys()), key="refund_line"
            )
            sel_line_id = line_opts[sel_line_label]
            refund_amount = st.number_input(
                "Refund Amount (EGP)", min_value=1.0, step=50.0, key="refund_amt"
            )
            refund_reason = st.text_input("Reason for Refund", key="refund_reason")

            if st.button("Confirm Refund", type="primary"):
                try:
                    result = fin_srv.issue_refund(
                        payment_id=sel_line_id,
                        amount=refund_amount,
                        reason=refund_reason or "Refund",
                        received_by_user_id=None,
                    )

                    bal_str = (
                        f"| New balance: {result['new_balance']:.0f} EGP"
                        if result.get("new_balance") is not None
                        else ""
                    )

                    st.success(
                        f"✅ Refund issued! Receipt: **{result['receipt_number']}** | "
                        f"Amount: {result['refunded_amount']:.0f} EGP {bal_str}"
                    )
                except Exception as e:
                    st.error(f"❌ {e}")
