import streamlit as st
from app.ui.components.auth_guard import require_auth

require_auth()

if "selected_competition_id" in st.session_state:
    from app.ui.components.competition_detail import render_competition_detail

    render_competition_detail(st.session_state["selected_competition_id"])
else:
    from app.ui.components.competition_overview import render_competition_overview

    render_competition_overview()
