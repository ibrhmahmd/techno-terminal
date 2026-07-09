"""
Techno Terminal — Finance & Audit Dashboard
Main entry point. Orchestrates navigation and renders pages.

Run:   streamlit run audit_dashboard.py
"""

import streamlit as st
from datetime import datetime

# Configure page metadata
st.set_page_config(
    page_title="Techno Terminal — Finance & Audit Hub",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import sub-modules
from dashboard.config import CUSTOM_CSS, SEVERITY_COLOR
from dashboard.page_audit import render_audit_page
from dashboard.page_finance import render_finance_page
from dashboard.page_bi import render_bi_page

# Inject styles
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar Navigation & General Controls
# ---------------------------------------------------------------------------
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

    # High fidelity radio selector
    page = st.radio(
        "Navigation",
        ["🔍 Audit Desk", "💰 Finance Hub", "📊 BI Reports"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Additional contextual sidebar settings
    if page == "🔍 Audit Desk":
        st.markdown("### Filter Settings")
        start_date = st.date_input(
            "Exclude historical data before",
            value=None,
            help="Useful to exclude June 2026 bulk-import records.",
        )
        
        st.markdown("---")
        st.markdown("**Severity Level Reference**")
        for sev, color in SEVERITY_COLOR.items():
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
                f'<div style="width:10px;height:10px;background:{color};border-radius:50%;box-shadow:0 0 6px {color}aa"></div>'
                f'<span style="font-size:0.8rem;color:#B4B9DC;font-weight:500">{sev}</span></div>',
                unsafe_allow_html=True,
            )
    else:
        start_date = None

    # Global actions
    st.markdown("### System Diagnostics")
    refresh = st.button("🔄 Reload Local Cache", use_container_width=True)
    if refresh:
        st.cache_resource.clear()
        st.rerun()

    st.markdown(
        f'<div style="color:#5C5F77;font-size:0.72rem;margin-top:12px;text-align:center">'
        f'Last loaded: {datetime.now().strftime("%I:%M:%S %p")}</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Router & Main Window Rendering
# ---------------------------------------------------------------------------
if page == "🔍 Audit Desk":
    render_audit_page(start_date)
elif page == "💰 Finance Hub":
    render_finance_page()
else:
    render_bi_page()
