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
    st.markdown("Search by parent or student, review debt/credit, and issue receipts.")

    # ── 1. Find Family Context ─────────────────────────────────────────────────
    debt_only = st.toggle("Show owed money only (debt < 0)", value=False, key="fd_debt_only")

    focus_student = None
    focus_guardian_id = None
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
            links = crm_srv.get_student_guardians(focus_student.id)
            primary = next((l for l in links if l.is_primary), None)
            if primary:
                focus_guardian_id = primary.guardian_id
            elif links:
                focus_guardian_id = links[0].guardian_id
        else:
            st.caption("No students found.")

    parent_q = st.text_input(
        "🔍 Search Parent (name or phone)",
        key="fd_gq",
        placeholder="Enter parent name or phone...",
    )
    selected_parent = None

    if focus_guardian_id:
        selected_parent = crm_srv.get_guardian_by_id(focus_guardian_id)
        if selected_parent and focus_student:
            st.caption(
                f"Student context: **{focus_student.full_name}** -> "
                f"family **{selected_parent.full_name}**"
            )
    elif parent_q and len(parent_q) >= 2:
        parents = crm_srv.search_guardians(parent_q)
        if parents:
            sel_parent = st.selectbox(
                "Select Parent",
                options=parents,
                format_func=lambda g: f"{g.full_name} ({g.phone_primary})",
                key="fd_gsel",
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

    if "fd_lines" not in st.session_state:
        st.session_state["fd_lines"] = {}

    # Reset draft lines when switching family.
    if st.session_state.get("fd_active_guardian_id") != selected_parent.id:
        st.session_state["fd_active_guardian_id"] = selected_parent.id
        st.session_state["fd_lines"] = {}
        st.session_state.pop("fd_overpay_preview", None)

    st.markdown("##### Enrolled Students & Balances")
    has_active_enrollments = False
    household_balance = 0.0
    family_has_debt = False

    for student in children:
        enrollments = enroll_srv.get_student_enrollments(student.id)
        active_enrs = [e for e in enrollments if e.status == "active"]
        if not active_enrs:
            continue

        has_active_enrollments = True
        student_rows = []
        student_has_debt = False
        for enr in active_enrs:
            balance_data = fin_srv.get_enrollment_balance(enr.id)
            balance = float((balance_data or {}).get("balance") or 0.0)
            net_due = float((balance_data or {}).get("net_due") or (enr.amount_due or 0.0))
            debt_egp = max(-balance, 0.0)
            if balance < 0:
                student_has_debt = True
                family_has_debt = True
            household_balance += balance
            student_rows.append((enr, balance, net_due, debt_egp))

        if debt_only and not student_has_debt:
            continue

        expanded = bool(focus_student and focus_student.id == student.id)
        with st.expander(f"👤 {student.full_name}", expanded=expanded):
            if student_has_debt:
                st.caption("Status: debt on at least one active enrollment.")
            else:
                st.caption("Status: settled/credit only.")

            for enr, balance, net_due, debt_egp in student_rows:
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
                    f"(negative=debt, positive=credit)"
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

    st.caption(
        f"Household account balance: **{household_balance:.0f} EGP** "
        "(negative=family owes, positive=family credit)."
    )
    if debt_only and not family_has_debt:
        st.info("This family has no debt. Turn off 'owed money only' to view all students.")

    if not has_active_enrollments:
        st.info("This family has no active enrollments (nothing to pay for).")
        return

    # ── 3. Finalize Receipt ────────────────────────────────────────────────────
    lines = list(st.session_state.get("fd_lines", {}).values())
    if lines:
        st.markdown("---")
        total_charges = sum(l["amount"] for l in lines)
        
        # --- Credit Suggestion UI ---
        available_credits = fin_srv.suggest_household_credits(selected_parent.id)
        applied_credits_spec = []
        total_credit_applied = 0.0
        
        if available_credits:
            total_avail = sum(c["available_credit"] for c in available_credits)
            st.info(f"💡 **Household has {total_avail:g} EGP total credit available.**")
            
            with st.expander("Apply Credit to this Receipt"):
                st.write("Specify how much credit to apply from each source:")
                for cr in available_credits:
                    max_amt = cr["available_credit"]
                    slider_key = f"fd_credit_{cr['enrollment_id']}"
                    
                    amt_to_apply = st.number_input(
                        f"From {cr['student_name']} (Enr #{cr['enrollment_id']}, Max: {max_amt:g} EGP)",
                        min_value=0.0,
                        max_value=float(max_amt),
                        value=0.0,
                        step=50.0,
                        key=slider_key,
                    )
                    
                    if amt_to_apply > 0:
                        applied_credits_spec.append({
                            "student_id": cr["student_id"],
                            "student_name": cr["student_name"],
                            "enrollment_id": cr["enrollment_id"],
                            "applied_amount": amt_to_apply
                        })
                        total_credit_applied += amt_to_apply
        
        net_to_collect = max(total_charges - total_credit_applied, 0.0)
        
        # Display Summary
        st.markdown(f"#### 🧾 Receipt Summary")
        st.markdown(f"- **Total Charges:** {total_charges:g} EGP")
        if total_credit_applied > 0:
            st.markdown(f"- **Credit Applied:** -{total_credit_applied:g} EGP")
        st.markdown(f"### 💰 Net to Collect: **{net_to_collect:g} EGP**")

        # Overpayment preview gate (U9 / P8 phase A)
        preview = st.session_state.get("fd_overpay_preview")
        if preview:
            st.warning(
                "Overpayment detected. Confirm to create credit on one or more enrollments."
            )
            pv_df = pd.DataFrame(preview).rename(
                columns={
                    "student_id": "Student ID",
                    "enrollment_id": "Enrollment ID",
                    "amount": "Entered (EGP)",
                    "debt_before": "Debt Before (EGP)",
                    "excess_credit": "New Credit (EGP)",
                    "projected_balance": "Projected Balance (EGP)",
                }
            )
            st.dataframe(pv_df, hide_index=True, use_container_width=True)
            c_ok, c_cancel = st.columns(2)
            if c_ok.button(
                "✅ Confirm Overpayment & Finalize",
                type="primary",
                use_container_width=True,
                key="fd_overpay_confirm_btn",
            ):
                try:
                    line_specs = [
                        ReceiptLineInput(
                            student_id=line["student_id"],
                            enrollment_id=line["enrollment_id"],
                            amount=line["amount"],
                        )
                        for line in lines
                    ]
                    
                    structured_notes = fin_srv.build_receipt_notes(
                        lines, applied_credits_spec, net_to_collect
                    )
                    
                    summary = fin_srv.create_receipt_with_charge_lines(
                        guardian_id=selected_parent.id,
                        method=method,
                        received_by_user_id=state.get_current_user_id(),
                        lines=line_specs,
                        notes=structured_notes,
                        allow_credit=True,
                    )
                    st.success(f"✅ Receipt **{summary['receipt_number']}** finalized!")
                    st.session_state["fd_lines"] = {}
                    st.session_state.pop("fd_overpay_preview", None)
                    st.session_state["selected_receipt_id"] = summary["receipt_id"]
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Payment Failed: {e}")
            if c_cancel.button(
                "✏️ Cancel and Adjust Amounts",
                use_container_width=True,
                key="fd_overpay_cancel_btn",
            ):
                st.session_state.pop("fd_overpay_preview", None)
                st.rerun()
            return

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
                risks = fin_srv.preview_overpayment_risk(line_specs)
                if risks:
                    st.session_state["fd_overpay_preview"] = risks
                    st.rerun()

                structured_notes = fin_srv.build_receipt_notes(
                    lines, applied_credits_spec, net_to_collect
                )

                summary = fin_srv.create_receipt_with_charge_lines(
                    guardian_id=selected_parent.id,
                    method=method,
                    received_by_user_id=state.get_current_user_id(),
                    lines=line_specs,
                    notes=structured_notes,
                    allow_credit=False,
                )
                st.success(f"✅ Receipt **{summary['receipt_number']}** finalized!")

                st.session_state["fd_lines"] = {}
                st.session_state["selected_receipt_id"] = summary["receipt_id"]
                st.rerun()
            except Exception as e:
                st.error(f"❌ Payment Failed: {e}")

