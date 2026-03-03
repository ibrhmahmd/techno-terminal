import streamlit as st
from app.ui.components.auth_guard import require_auth

require_auth()

# Simple router for Finance page
if "selected_receipt_id" in st.session_state:
    from app.ui.components.finance_receipt import render_receipt_detail

    render_receipt_detail(st.session_state["selected_receipt_id"])
else:
    from app.ui.components.finance_overview import render_finance_overview

    render_finance_overview()
