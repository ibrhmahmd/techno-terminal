import streamlit as st
import pandas as pd
from datetime import date

from app.modules.crm import service as crm_srv
from app.modules.enrollments import service as enroll_srv
from app.modules.finance import service as fin_srv

PAYMENT_METHODS = ["cash", "card", "transfer", "online"]


def render_finance_overview():
    st.title("💳 Financial Ledger")

    tab_receipt, tab_balance, tab_daily = st.tabs(
        ["💵 New Receipt", "📊 Balances", "📅 Daily Summary"]
    )

    # ── TAB 1: New Receipt ────────────────────────────────────────────────────
    with tab_receipt:
        st.subheader("Issue a Payment Receipt")
        st.caption(
            "Search for a parent/guardian, select payment method, then add payment lines for each enrolled student."
        )

        # Step 1: Find Guardian
        guardian_q = st.text_input("🔍 Search Guardian (name or phone)", key="fin_gq")
        selected_guardian = None

        if guardian_q and len(guardian_q) >= 2:
            guardians = crm_srv.search_guardians(guardian_q)
            if guardians:
                g_opts = {f"{g.full_name} ({g.phone_primary})": g for g in guardians}
                sel_g_label = st.selectbox(
                    "Select Guardian", list(g_opts.keys()), key="fin_gsel"
                )
                selected_guardian = g_opts[sel_g_label]
            else:
                st.warning("No guardians found.")

        # Step 2: Payment method
        method = st.selectbox("Payment Method", PAYMENT_METHODS, key="fin_method")

        st.divider()

        # Step 3: Add payment lines for each enrolled student of this guardian
        if selected_guardian:
            st.markdown(f"**Guardian:** {selected_guardian.full_name}")

            # Get children of this guardian
            children = crm_srv.get_guardian_students(selected_guardian.id)

            if not children:
                st.info("No students linked to this guardian.")
            else:
                st.markdown("#### Add Payment Lines")
                st.caption("Check each student you want to add a payment line for.")

                # Build payment lines in session state
                if "fin_lines" not in st.session_state:
                    st.session_state["fin_lines"] = {}

                for student in children:
                    enrollments = enroll_srv.get_student_enrollments(student.id)
                    active_enrs = [e for e in enrollments if e.status == "active"]

                    if not active_enrs:
                        continue

                    with st.expander(f"👤 {student.full_name}", expanded=True):
                        for enr in active_enrs:
                            balance_data = fin_srv.get_enrollment_balance(enr.id)
                            balance = balance_data["balance"] if balance_data else 0.0
                            net_due = (
                                balance_data["net_due"]
                                if balance_data
                                else enr.amount_due or 0.0
                            )

                            col_chk, col_amt, col_info = st.columns([1, 2, 3])
                            line_key = f"fin_line_{enr.id}"

                            checked = col_chk.checkbox(
                                f"Enr#{enr.id}",
                                key=f"fin_chk_{enr.id}",
                                value=line_key in st.session_state["fin_lines"],
                            )
                            amount = col_amt.number_input(
                                "Amount (EGP)",
                                min_value=0.0,
                                value=float(max(balance, 0.0)),
                                step=50.0,
                                key=f"fin_amt_{enr.id}",
                            )
                            col_info.markdown(
                                f"**Group:** {enr.group_id} L{enr.level_number}  \n"
                                f"**Due:** {net_due:.0f} EGP | **Balance:** {balance:.0f} EGP"
                            )

                            if checked and amount > 0:
                                st.session_state["fin_lines"][line_key] = {
                                    "student_id": student.id,
                                    "student_name": student.full_name,
                                    "enrollment_id": enr.id,
                                    "amount": amount,
                                }
                            elif line_key in st.session_state["fin_lines"]:
                                del st.session_state["fin_lines"][line_key]

                # Receipt summary & finalize
                st.divider()
                lines = list(st.session_state.get("fin_lines", {}).values())
                if lines:
                    st.markdown("#### Receipt Summary")
                    summary_df = pd.DataFrame(
                        [
                            {
                                "Student": l["student_name"],
                                "Enrollment": l["enrollment_id"],
                                "Amount (EGP)": l["amount"],
                            }
                            for l in lines
                        ]
                    )
                    st.dataframe(summary_df, hide_index=True, use_container_width=True)
                    st.markdown(
                        f"**Total: {sum(l['amount'] for l in lines):.0f} EGP** | Method: {method.capitalize()}"
                    )

                    if st.button(
                        "✅ Finalize Receipt", type="primary", use_container_width=True
                    ):
                        try:
                            receipt = fin_srv.open_receipt(
                                guardian_id=selected_guardian.id,
                                method=method,
                                received_by_user_id=None,
                            )
                            for line in lines:
                                fin_srv.add_charge_line(
                                    receipt_id=receipt.id,
                                    student_id=line["student_id"],
                                    enrollment_id=line["enrollment_id"],
                                    amount=line["amount"],
                                )
                            summary = fin_srv.finalize_receipt(receipt.id)
                            st.success(
                                f"✅ Receipt **{summary['receipt_number']}** finalized! "
                                f"Total: {summary['total']:.0f} EGP"
                            )
                            st.session_state["fin_lines"] = {}
                        except Exception as e:
                            st.error(f"❌ {e}")
                else:
                    st.info(
                        "Check students above and enter amounts to build the receipt."
                    )
        else:
            st.info("Search for a guardian above to begin.")

    # ── TAB 2: Balances ───────────────────────────────────────────────────────
    with tab_balance:
        st.subheader("Student Balance Lookup")
        bal_q = st.text_input("🔍 Search Student", key="fin_balq")
        if bal_q and len(bal_q) >= 2:
            students = crm_srv.search_students(bal_q)
            if students:
                s_opts = {f"{s.full_name} (ID:{s.id})": s.id for s in students}
                sel_s = st.selectbox(
                    "Select Student", list(s_opts.keys()), key="fin_bals"
                )
                sid = s_opts[sel_s]
                balances = fin_srv.get_student_financial_summary(sid)
                if balances:
                    df = pd.DataFrame(balances)
                    display_cols = [
                        c
                        for c in [
                            "enrollment_id",
                            "group_name",
                            "level_number",
                            "net_due",
                            "total_paid",
                            "balance",
                        ]
                        if c in df.columns
                    ]
                    st.dataframe(
                        df[display_cols].rename(
                            columns={
                                "enrollment_id": "Enrollment",
                                "group_name": "Group",
                                "level_number": "Level",
                                "net_due": "Net Due (EGP)",
                                "total_paid": "Paid (EGP)",
                                "balance": "Balance (EGP)",
                            }
                        ),
                        hide_index=True,
                        use_container_width=True,
                    )
                else:
                    st.info("No financial records found for this student.")
            else:
                st.info("No students found.")

    # ── TAB 3: Daily Summary ──────────────────────────────────────────────────
    with tab_daily:
        st.subheader("Daily Collection Summary")
        sel_date = st.date_input("Select Date", value=date.today(), key="fin_date")

        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### Collections by Method")
            collections = fin_srv.get_daily_collections(sel_date)
            if collections:
                for row in collections:
                    method_lbl = (row["payment_method"] or "Unknown").capitalize()
                    net = float(row["collected"]) - float(row["refunded"])
                    st.metric(
                        label=method_lbl,
                        value=f"{net:.0f} EGP",
                        delta=f"-{row['refunded']:.0f} refunded"
                        if float(row["refunded"]) > 0
                        else None,
                        delta_color="inverse",
                    )
            else:
                st.info("No collections recorded for this date.")

        with col_right:
            st.markdown("#### Receipts Issued")
            receipts = fin_srv.get_daily_receipts(sel_date)
            if receipts:
                df = pd.DataFrame(receipts)
                disp = [
                    "receipt_number",
                    "guardian_name",
                    "payment_method",
                    "total",
                    "id",
                ]
                df_display = df[[c for c in disp if c in df.columns]].rename(
                    columns={
                        "receipt_number": "Receipt #",
                        "guardian_name": "Guardian",
                        "payment_method": "Method",
                        "total": "Total (EGP)",
                    }
                )
                event = st.dataframe(
                    df_display.drop(columns=["id"], errors="ignore"),
                    hide_index=True,
                    use_container_width=True,
                    selection_mode="single-row",
                    on_select="rerun",
                )
                if event.selection.rows:
                    sel_idx = event.selection.rows[0]
                    receipt_id = receipts[sel_idx]["id"]
                    st.session_state["selected_receipt_id"] = receipt_id
                    st.rerun()
            else:
                st.info("No receipts for this date.")
