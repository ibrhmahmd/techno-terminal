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
    st.markdown("Search for a student, review debt/credit, and issue receipts.")

    # ── 1. Find Student Context ────────────────────────────────────────────────
    debt_only = st.toggle("Show owed money only (debt < 0)", value=False, key="fd_debt_only")

    focus_student = None
    student_q = st.text_input(
        "🔎 Search Student (name)",
        key="fd_sq",
        placeholder="Enter student name...",
    )
    if student_q and len(student_q) >= 2:
        students = crm_srv.search_students(student_q)
        if students:
            focus_student = st.selectbox(
                "Select Student",
                options=students,
                format_func=lambda s: f"{s.full_name} (#{s.id})",
                key="fd_ssel",
            )
        else:
            st.caption("No students found.")

    if not focus_student:
        return

    st.divider()
    
    # ── 2. Payment Builder ─────────────────────────────────────────────────────
    st.markdown(f"#### 👤 Student Account: **{focus_student.full_name}**")

    payer_name = st.text_input(
        "Payer Name", 
        value=focus_student.full_name, 
        help="Name printed on the receipt"
    )

    method = st.selectbox("Payment Method", PAYMENT_METHODS, key="fd_method")

    if "fd_lines" not in st.session_state:
        st.session_state["fd_lines"] = {}

    # Reset draft lines when switching student.
    if st.session_state.get("fd_active_student_id") != focus_student.id:
        st.session_state["fd_active_student_id"] = focus_student.id
        st.session_state["fd_lines"] = {}
        st.session_state.pop("fd_overpay_preview", None)

    st.markdown("##### Enrolled Courses & Balances")
    
    enrollments = enroll_srv.get_student_enrollments(focus_student.id)
    active_enrs = [e for e in enrollments if e.status == "active"]

    if not active_enrs:
        st.info("This student has no active enrollments.")

    student_has_debt = False
    total_student_balance = 0.0

    for enr in active_enrs:
        balance_data = fin_srv.get_enrollment_balance(enr.id)
        balance = float((balance_data or {}).get("balance") or 0.0)
        net_due = float((balance_data or {}).get("net_due") or (enr.amount_due or 0.0))
        debt_egp = max(-balance, 0.0)
        
        if balance < 0:
            student_has_debt = True
            
        total_student_balance += balance
        
        if debt_only and balance >= 0:
            continue
            
        line_key = f"fd_line_{enr.id}"
        col_chk, col_amt, col_info = st.columns([1, 1.5, 3])
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
            f"(negative=debt)"
        )
        if checked and amount > 0:
            st.session_state["fd_lines"][line_key] = {
                "student_id": focus_student.id,
                "student_name": focus_student.full_name,
                "enrollment_id": enr.id,
                "amount": amount,
            }
        elif line_key in st.session_state["fd_lines"]:
            del st.session_state["fd_lines"][line_key]

    st.caption(f"Total student account balance: **{total_student_balance:.0f} EGP**")

    if debt_only and not student_has_debt:
        st.info("This student has no debt. Turn off 'owed money only' to view all enrollments.")

    # ── 2b. Competition Fees ───────────────────────────────────────────────────
    comp_fees = fin_srv.get_unpaid_competition_fees(focus_student.id)
    if comp_fees:
        st.markdown("##### 🏆 Pending Competition Fees")
        for cf in comp_fees:
            line_key = f"fd_comp_{cf['team_member_id']}"
            col_chk, col_amt, col_info = st.columns([1, 1.5, 3])
            checked = col_chk.checkbox(
                f"TM #{cf['team_member_id']}",
                key=f"fd_comp_chk_{cf['team_member_id']}",
                value=line_key in st.session_state["fd_lines"],
            )
            amount = col_amt.number_input(
                "Amount (EGP)",
                min_value=0.0,
                value=float(cf["member_share"]),
                step=50.0,
                key=f"fd_comp_amt_{cf['team_member_id']}",
                label_visibility="collapsed",
            )
            col_info.markdown(
                f"**{cf['competition_name']}** — {cf['category_name']} | "
                f"Team: **{cf['team_name']}** | Fee: **{cf['member_share']:.0f} EGP**"
            )
            if checked and amount > 0:
                st.session_state["fd_lines"][line_key] = {
                    "student_id": focus_student.id,
                    "enrollment_id": None,
                    "team_member_id": cf["team_member_id"],
                    "amount": amount,
                    "payment_type": "competition",
                    "notes": f"Competition fee — {cf['competition_name']} / {cf['team_name']}",
                }
            elif line_key in st.session_state["fd_lines"]:
                del st.session_state["fd_lines"][line_key]

    if not active_enrs and not comp_fees:
        st.info("This student has no outstanding fees.")
        return

    # ── 3. Finalize Receipt ────────────────────────────────────────────────────
    lines = list(st.session_state.get("fd_lines", {}).values())
    if lines:
        st.markdown("---")
        total = sum(l["amount"] for l in lines)
        st.markdown(f"#### 🧾 Receipt Summary: **{total:.0f} EGP**")

        preview = st.session_state.get("fd_overpay_preview")
        if preview:
            st.warning("Overpayment detected. Confirm to credit the enrollment.")
            st.dataframe(pd.DataFrame(preview), hide_index=True, use_container_width=True)
            c_ok, c_cancel = st.columns(2)
            if c_ok.button("✅ Confirm Overpayment", type="primary", use_container_width=True):
                try:
                    summary = fin_srv.create_receipt_with_charge_lines(
                        payer_name=payer_name,
                        method=method,
                        received_by_user_id=state.get_current_user_id(),
                        lines=[ReceiptLineInput(**line) for line in lines],
                        allow_credit=True,
                    )
                    st.success(f"✅ Receipt **{summary['receipt_number']}** issued!")
                    st.session_state["fd_lines"] = {}
                    st.session_state.pop("fd_overpay_preview", None)
                    st.session_state["selected_receipt_id"] = summary["receipt_id"]
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Payment Failed: {e}")
            if c_cancel.button("✏️ Cancel", use_container_width=True):
                st.session_state.pop("fd_overpay_preview", None)
                st.rerun()
            return

        if st.button("✅ Confirm Payment & Print Receipt", type="primary", use_container_width=True):
            if not payer_name:
                st.error("Payer Name cannot be blank.")
                return
            try:
                line_specs = [ReceiptLineInput(**line) for line in lines]
                risks = fin_srv.preview_overpayment_risk(line_specs)
                if risks:
                    st.session_state["fd_overpay_preview"] = risks
                    st.rerun()

                summary = fin_srv.create_receipt_with_charge_lines(
                    payer_name=payer_name,
                    method=method,
                    received_by_user_id=state.get_current_user_id(),
                    lines=line_specs,
                    allow_credit=False,
                )
                st.success(f"✅ Receipt **{summary['receipt_number']}** issued!")
                st.session_state["fd_lines"] = {}
                st.session_state["selected_receipt_id"] = summary["receipt_id"]
                st.rerun()
            except Exception as e:
                st.error(f"❌ Payment Failed: {e}")
