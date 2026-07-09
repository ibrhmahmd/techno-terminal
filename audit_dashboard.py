"""
Techno Terminal — Finance & Audit Dashboard
Main entry point. Orchestrates native navigation and renders pages.

Run:   streamlit run audit_dashboard.py
"""

import streamlit as st
from datetime import datetime

# Set page config once
st.set_page_config(
    page_title="Techno Terminal — Finance & Audit Hub",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

from dashboard.config import CUSTOM_CSS, SEVERITY_COLOR
from dashboard.page_audit import render_audit_page
from dashboard.page_finance import render_finance_page
from dashboard.page_bi import render_bi_page

# Sidebar custom styles
SIDEBAR_CSS = """
<style>
    /* Force high visibility for native navigation items in the sidebar */
    [data-testid="stSidebarNav"] * {
        color: #b4b9dc !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.92rem !important;
    }
    
    /* Highlight the selected/active page */
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background-color: rgba(255, 255, 255, 0.08) !important;
        border-left: 3px solid #006a61 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    [data-testid="stSidebarNav"] a:hover {
        background-color: rgba(255, 255, 255, 0.04) !important;
        color: #ffffff !important;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)

# Render Global Sidebar Header
with st.sidebar:
    st.markdown(
        """
        <div style="text-align: center; padding: 10px 0 20px 0;">
            <h2 style="margin: 0; color: #FFF; font-weight: 700; letter-spacing: -0.03em;">🚀 TECHNO KIDS</h2>
            <p style="margin: 0; font-size: 0.8rem; color: #8E92B2; text-transform: uppercase; letter-spacing: 0.1em;">Management Portal</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")

# Page wrappers
def show_audit():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)
    render_audit_page()

def show_finance():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)
    render_finance_page()

def show_bi():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)
    render_bi_page()

# Setup pages
pages = [
    st.Page(show_audit, title="Audit Desk", icon="🔍", default=True),
    st.Page(show_finance, title="Finance Hub", icon="💰"),
    st.Page(show_bi, title="BI Reports", icon="📊"),
]

# Run Navigation
pg = st.navigation(pages)

# Render Global Sidebar Footer (below the navigation links)
with st.sidebar:
    st.markdown("---")
    st.markdown("### System Diagnostics")
    refresh = st.button("🔄 Reload Local Cache", use_container_width=True)
    if refresh:
        st.cache_resource.clear()
        st.rerun()

    st.markdown(
        f'<div style="color:#8E92B2;font-size:0.72rem;margin-top:12px;text-align:center">'
        f'Last loaded: {datetime.now().strftime("%I:%M:%S %p")}</div>',
        unsafe_allow_html=True,
    )

pg.run()
