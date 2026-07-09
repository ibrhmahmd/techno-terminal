import streamlit as st
from datetime import date
from dashboard.config import SCENARIOS, SEVERITY_ICON, SEVERITY_PRIORITY, query
from dashboard.ui_components import severity_badge, render_metric, format_egp_cols, render_download_button

def query_audit_counts() -> dict[str, int]:
    try:
        df = query("SELECT code, anomaly_count FROM v_audit_summary ORDER BY code")
        return dict(zip(df["code"], df["anomaly_count"]))
    except Exception as e:
        st.error(f"Failed to query audit counts: {e}")
        return {}

def query_scenario_detail(view: str, start_date: date | None) -> st.delta_generator.DeltaGenerator:
    date_cols = {
        "v_audit_zero_charge_enrollments": "enrolled_at",
        "v_audit_overpaid_enrollments": None,
        "v_audit_orphaned_payments": "paid_at",
        "v_audit_duplicate_enrollments": "first_enrolled",
        "v_audit_dead_group_enrollments": "enrolled_at",
        "v_audit_unrefunded_exits": None,
        "v_audit_level_mismatch": "enrolled_at",
        "v_audit_ghost_payments": "paid_at",
        "v_audit_overdiscounted_enrollments": "enrolled_at",
    }
    date_col = date_cols.get(view)
    if start_date and date_col:
        sql = f"SELECT * FROM {view} WHERE {date_col} >= %s"
        return query(sql, (start_date,))
    return query(f"SELECT * FROM {view}")

def render_audit_page(start_date: date | None):
    st.markdown("## 🔍 Student Balance Integrity Audit")
    st.markdown(
        "Real-time anomaly detection across 9 key risk scenarios. "
        "Work from errors (🔴) to warnings (🟡) to info items (🔵)."
    )
    st.markdown("---")

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
        st.success("🎉 Outstanding! 0 balance integrity anomalies detected across all checks.")
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
