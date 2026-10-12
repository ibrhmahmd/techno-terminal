import streamlit as st
from datetime import date
from app.modules.audit.constants import SCENARIOS, SEVERITY_PRIORITY
from app.modules.audit.ui.components import severity_badge, render_metric, format_egp_cols, render_download_button
from app.modules.audit.ui.data import query_view
from app.modules.audit.ui.styles import SEVERITY_ICON

def query_audit_counts() -> dict[str, int]:
    try:
        df = query_view("v_audit_summary", ["code", "anomaly_count"], order_by="code")
        return dict(zip(df["code"], df["anomaly_count"]))
    except Exception as e:
        st.error(f"Failed to query audit counts: {e}")
        return {}

def query_scenario_detail(view: str, start_date: date | None) -> st.delta_generator.DeltaGenerator:
    return query_view(view, since=start_date)

def render_audit_page():
    st.markdown("## 🔍 Student Balance Integrity Audit")
    st.markdown(
        "Real-time anomaly detection across 9 key risk scenarios. "
        "Work from errors (🔴) to warnings (🟡) to info items (🔵)."
    )
    st.markdown("---")

    # Render page-specific sidebar elements
    start_date = st.sidebar.date_input(
        "Exclude historical data before",
        value=None,
        help="Useful to exclude June 2026 bulk-import records.",
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Severity Level Reference**")
    from app.modules.audit.ui.styles import SEVERITY_COLOR
    for sev, color in SEVERITY_COLOR.items():
        st.sidebar.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
            f'<div style="width:10px;height:10px;background:{color};border-radius:50%;box-shadow:0 0 6px {color}aa"></div>'
            f'<span style="font-size:0.8rem;color:#B4B9DC;font-weight:500">{sev}</span></div>',
            unsafe_allow_html=True,
        )

    with st.spinner("Analyzing database integrity..."):
        counts = query_audit_counts()

    if not counts:
        st.warning("No audit summary data returned. Ensure migrations are fully applied.")
        return

    # Aggregate counts
    total_errors   = sum(counts.get(s["code"], 0) for s in SCENARIOS if s["severity"] == "ERROR")
    total_warnings = sum(counts.get(s["code"], 0) for s in SCENARIOS if s["severity"] == "WARNING")
    total_info     = sum(counts.get(s["code"], 0) for s in SCENARIOS if s["severity"] == "INFO")
    total_all      = sum(counts.values())

    # Top KPI Strip
    k1, k2, k3, k4 = st.columns(4)
    render_metric(k1, "Total Anomalies", total_all, "WARNING" if total_all > 0 else "INFO")
    render_metric(k2, "🔴 Critical Errors", total_errors, "ERROR")
    render_metric(k3, "🟡 Warnings", total_warnings, "WARNING")
    render_metric(k4, "🔵 Info Items", total_info, "INFO")
    
    st.markdown("---")

    # Summary Grid
    st.markdown("### Summary Directory")
    sorted_scenarios = sorted(SCENARIOS, key=lambda s: (SEVERITY_PRIORITY[s["severity"]], s["code"]))
    
    cols = st.columns(3)
    for i, sc in enumerate(sorted_scenarios):
        render_metric(cols[i % 3], f"[{sc['code']}] {sc['label']}", counts.get(sc["code"], 0), sc["severity"])

    st.markdown("---")
    st.markdown("### Scenario Detail & Resolution Insights")

    nonzero = [s for s in sorted_scenarios if counts.get(s["code"], 0) > 0]
    zero    = [s for s in sorted_scenarios if counts.get(s["code"], 0) == 0]
    ordered = nonzero + zero

    if not nonzero:
        st.success("0 balance integrity anomalies detected across all checks.")
        return

    # Render Tabs
    tab_labels = [
        f"{SEVERITY_ICON[s['severity']]} {s['code']}: {s['label']} ({counts.get(s['code'], 0)})"
        for s in ordered
    ]
    tabs = st.tabs(tab_labels)

    for tab, sc in zip(tabs, ordered):
        with tab:
            count = counts.get(sc["code"], 0)
            
            # Scenario Sub-Header
            st.markdown(
                f"<div style='margin-bottom:12px'>"
                f"<h4>{severity_badge(sc['severity'])} &nbsp; Scenario {sc['code']} — {sc['label']}</h4>"
                f"</div>",
                unsafe_allow_html=True
            )
            st.markdown(f"*{sc['description']}*")

            if count == 0:
                st.success("✅ Clean — No anomalies found.")
                continue

            st.markdown(
                f'<div class="tip-box">💡 <strong>Remediation Tip:</strong> {sc["tip"]}</div>',
                unsafe_allow_html=True,
            )

            # Query data
            with st.spinner(f"Loading anomaly logs for Scenario {sc['code']}..."):
                df = query_scenario_detail(sc["view"], start_date)

            if df.empty:
                st.info("No rows match after date cut-off filter.")
                continue

            st.markdown(f"**Identified Records ({len(df)}):**")
            
            # Styled Dataframe
            st.dataframe(format_egp_cols(df), use_container_width=True, hide_index=True)
            
            # Action controls (csv download)
            col_dl, _ = st.columns([1, 3])
            with col_dl:
                render_download_button(df, f"audit_scenario_{sc['code'].lower()}", "Export Logs to CSV")
