import streamlit as st
import pandas as pd
from app.ui import state
from app.modules.crm import crm_service as crm_srv
from app.modules.enrollments import enrollment_service as enroll_srv
from app.modules.finance import finance_service as fin_srv
from app.modules.finance.finance_schemas import ReceiptLineInput
from app.shared.constants import PAYMENT_METHODS

def render_finance_overview():
    st.subheader("💳 Financial Desk")
    st.markdown("Search for a parent to view balances and issue receipts.")
    
    # ── 1. Find Parent ─────────────────────────────────────────────────────────
    parent_q = st.text_input("🔍 Search Parent (name or phone)", key="fd_gq", placeholder="Enter name or phone...")
    selected_parent = None

    if parent_q and len(parent_q) >= 2:
        parents = crm_srv.search_guardians(parent_q)
        if parents:
            # Use format_func for cleaner data binding
            sel_parent = st.selectbox(
                "Select Parent",
                options=parents,
                format_func=lambda g: f"{g.full_name} ({g.phone_primary})",
                key="fd_gsel"
            )
            selected_parent = sel_parent
        else:
            st.warning("No parents found.")

    if not selected_parent:
        return

    st.divider()
    
    # ── 2. Payment Builder ─────────────────────────────────────────────────────
    st.markdown(f"#### 👨‍👩‍👧 Family Account: **{selected_parent.full_name}**")
    
    children = crm_srv.get_guardian_students(selected_parent.id)
    if not children:
        st.info("No students linked to this parent.")
        return

    method = st.selectbox("Payment Method", PAYMENT_METHODS, key="fd_method")
    
    # Build payment lines in session state to survive reruns
    if "fd_lines" not in st.session_state:
        st.session_state["fd_lines"] = {}

    st.markdown("##### Enrolled Students & Balances")
    
    has_active_enrollments = False
    
    for student in children:
        enrollments = enroll_srv.get_student_enrollments(student.id)
        active_enrs = [e for e in enrollments if e.status == "active"]
        
        if not active_enrs:
            continue
            
        has_active_enrollments = True
        
        with st.expander(f"👤 {student.full_name}", expanded=True):
            for enr in active_enrs:
                balance_data = fin_srv.get_enrollment_balance(enr.id)
                balance = balance_data["balance"] if balance_data else 0.0
                net_due = balance_data["net_due"] if balance_data else (enr.amount_due or 0.0)
                # P6: negative balance = debt, positive = credit; default pay = amount owed
                debt_egp = max(-balance, 0.0)

                col_chk, col_amt, col_info = st.columns([1, 1.5, 3])
                line_key = f"fd_line_{enr.id}"

                checked = col_chk.checkbox(
                    f"Enr #{enr.id}",
                    key=f"fd_chk_{enr.id}",
                    value=line_key in st.session_state["fd_lines"],
                )

                amount = col_amt.number_input(
                    "Amount (EGP)",
                    min_value=0.0,
                    value=float(debt_egp),
                    step=50.0,
                    key=f"fd_amt_{enr.id}",
                    label_visibility="collapsed",
                )

                col_info.markdown(
                    f"**Group:** {enr.group_id} L{enr.level_number} | "
                    f"**Net Due:** {net_due:.0f} | **Account balance:** {balance:.0f} EGP "
                    f"(negative = debt)"
                )

                if checked and amount > 0:
                    st.session_state["fd_lines"][line_key] = {
                        "student_id": student.id,
                        "student_name": student.full_name,
                        "enrollment_id": enr.id,
                        "amount": amount,
                    }
                elif line_key in st.session_state["fd_lines"]:
                    del st.session_state["fd_lines"][line_key]

    if not has_active_enrollments:
        st.info("This family has no active enrollments (nothing to pay for).")
        return
        
    # ── 3. Finalize Receipt ────────────────────────────────────────────────────
    lines = list(st.session_state.get("fd_lines", {}).values())
    if lines:
        st.markdown("---")
        total = sum(l['amount'] for l in lines)
        st.markdown(f"#### 🧾 Receipt Summary: **{total:.0f} EGP**")
        
        if st.button("✅ Confirm Payment & Print Receipt", type="primary", use_container_width=True):
            try:
                line_specs = [
                    ReceiptLineInput(
                        student_id=line["student_id"],
                        enrollment_id=line["enrollment_id"],
                        amount=line["amount"],
                    )
                    for line in lines
                ]
                summary = fin_srv.create_receipt_with_charge_lines(
                    guardian_id=selected_parent.id,
                    method=method,
                    received_by_user_id=state.get_current_user_id(),
                    lines=line_specs,
                )
                st.success(f"✅ Receipt **{summary['receipt_number']}** finalized strictly!")
                
                # Clear lines from state
                st.session_state["fd_lines"] = {}
                # Set target receipt to show the print view
                st.session_state["selected_receipt_id"] = summary["receipt_id"]
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Payment Failed: {e}")
