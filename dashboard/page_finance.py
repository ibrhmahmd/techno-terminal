import streamlit as st
from datetime import date
from dashboard.config import FINANCE_VIEWS, FINANCE_CATEGORIES, FINANCE_CATEGORY_ICONS, query
from dashboard.ui_components import render_egp_metric, render_count_metric, format_egp_cols, render_download_button

def query_finance_summary() -> dict:
    try:
        df = query("SELECT * FROM v_finance_summary")
        if df.empty:
            return {}
        return df.iloc[0].to_dict()
    except Exception as e:
        st.error(f"Failed to query finance summary: {e}")
        return {}

def render_finance_page():
    st.markdown("## 💰 Financial Intelligence Dashboard")
    st.markdown("Real-time metrics tracking revenue flow, outstanding balances (AR), and instructor payroll.")
    st.markdown("---")

    with st.spinner("Loading financial metrics..."):
        fsummary = query_finance_summary()

    if not fsummary:
        st.warning("No financial summary data found. Ensure migration 075 is applied.")
        return

    # Top-level KPIs
    st.markdown("### Executive Summary")
    c1, c2, c3, c4 = st.columns(4)
    render_egp_metric(c1, "Month-To-Date Revenue", fsummary.get("revenue_this_month"), "📅", "#4CAF50")
    render_egp_metric(c2, "Total Net Revenue", fsummary.get("total_net_revenue"), "💵", "#4B9EFF")
    render_egp_metric(c3, "Outstanding AR", fsummary.get("ar_total_owed"), "💳", "#FFA500")
    render_egp_metric(c4, "High Risk AR (>30d)", fsummary.get("high_risk_total_owed"), "⚠️", "#FF4B4B")

    c5, c6, c7, c8 = st.columns(4)
    render_count_metric(c5, "Active AR Accounts", fsummary.get("ar_enrollment_count"), "📋", "#FFA500")
    render_count_metric(c6, "High-Risk Overdue Accounts", fsummary.get("high_risk_count"), "🚨", "#FF4B4B")
    render_egp_metric(c7, "Discounts Given (MTD)", fsummary.get("discounts_this_month"), "🏷️", "#9B59B6")
    render_egp_metric(c8, "Active Payroll Obligations", fsummary.get("active_contract_payroll"), "👷", "#E67E22")

    st.markdown("---")

    # Financial Categories Section
    st.markdown("### Operational Registers")
    
    for cat in FINANCE_CATEGORIES:
        views_in_cat = [v for v in FINANCE_VIEWS if v["category"] == cat]
        cat_icon = FINANCE_CATEGORY_ICONS.get(cat, "📊")
        
        st.markdown(f"#### {cat_icon} {cat}")
        
        tab_labels = [v["label"] for v in views_in_cat]
        tabs = st.tabs(tab_labels)

        for tab, fv in zip(tabs, views_in_cat):
            with tab:
                st.markdown(f"*{fv['description']}*")

                if "tip" in fv:
                    st.markdown(
                        f'<div class="tip-box">💡 <strong>Analysis Tip:</strong> {fv["tip"]}</div>',
                        unsafe_allow_html=True,
                    )

                # Query view data
                with st.spinner(f"Loading {fv['label']}..."):
                    df = query(f"SELECT * FROM {fv['view']}")

                if df.empty:
                    st.info("No records found in this register.")
                    continue

                st.markdown(f"**Active Records ({len(df)}):**")
                st.dataframe(format_egp_cols(df), use_container_width=True, hide_index=True)

                # Export controls
                col_dl, _ = st.columns([1, 3])
                with col_dl:
                    render_download_button(df, f"finance_{fv['key']}", "Export Register to CSV")
        
        # Whitespace spacing between sections
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
