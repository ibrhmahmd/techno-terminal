import streamlit as st
import pandas as pd
from datetime import date
from dashboard.config import SEVERITY_COLOR, SEVERITY_ICON

def severity_badge(severity: str) -> str:
    color = SEVERITY_COLOR.get(severity, "#4B9EFF")
    icon = SEVERITY_ICON.get(severity, "🔵")
    return (
        f'<span style="background:{color};color:white;padding:3px 10px;'
        f'border-radius:20px;font-size:0.75rem;font-weight:600;display:inline-block;'
        f'box-shadow: 0 2px 8px {color}33">'
        f'{icon} {severity}</span>'
    )

def render_metric(col, label: str, value: int, severity: str):
    color = SEVERITY_COLOR.get(severity, "#4B9EFF")
    icon = SEVERITY_ICON.get(severity, "🔵")
    
    num_color = (
        "#FF4B4B" if value > 0 and severity == "ERROR"
        else "#FFA500" if value > 0 and severity == "WARNING"
        else "#4B9EFF" if value > 0
        else "#4CAF50"
    )
    
    col.markdown(
        f"""
        <div class="metric-card" style="--accent-color: {color}">
            <div class="metric-title">{icon} {label}</div>
            <div class="metric-value" style="color: {num_color}">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_egp_metric(col, label: str, value, icon: str = "💰", color: str = "#4B9EFF"):
    try:
        val_f = float(value) if value is not None else 0.0
        formatted = f"{val_f:,.0f} EGP"
        num_color = "#FF4B4B" if val_f > 0 and color == "#FF4B4B" else color
    except (TypeError, ValueError):
        formatted = str(value)
        num_color = color
        
    col.markdown(
        f"""
        <div class="metric-card" style="--accent-color: {color}">
            <div class="metric-title">{icon} {label}</div>
            <div class="metric-value" style="color: {num_color}; font-size: 1.8rem;">{formatted}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_count_metric(col, label: str, value, icon: str = "📊", color: str = "#4B9EFF"):
    try:
        val_i = int(value) if value is not None else 0
        num_color = "#FF4B4B" if val_i > 0 and color == "#FF4B4B" else color
    except (TypeError, ValueError):
        val_i = value
        num_color = color
        
    col.markdown(
        f"""
        <div class="metric-card" style="--accent-color: {color}">
            <div class="metric-title">{icon} {label}</div>
            <div class="metric-value" style="color: {num_color}">{val_i}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def format_egp_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with EGP numeric columns formatted as strings."""
    egp_keywords = ["amount", "revenue", "collected", "billed", "due", "paid",
                    "cost", "salary", "discount", "balance", "owed", "outstanding",
                    "potential", "profit", "refund", "charged", "overpaid", "net_",
                    "price_per_level"]
    display = df.copy()
    for col in display.columns:
        col_lower = col.lower()
        # Handle formatting for numeric columns matching keywords
        if display[col].dtype in ["float64", "int64"] and any(k in col_lower for k in egp_keywords):
            display[col] = display[col].apply(
                lambda x: f"{x:,.2f} EGP" if pd.notnull(x) else ""
            )
        # Handle formatting for percentages
        elif "pct" in col_lower or "rate" in col_lower or "percent" in col_lower:
            if display[col].dtype in ["float64", "int64"]:
                display[col] = display[col].apply(
                    lambda x: f"{x:.1f}%" if pd.notnull(x) else ""
                )
    return display

def render_download_button(df: pd.DataFrame, file_prefix: str, label: str = "Download CSV"):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"⬇️ {label}",
        data=csv,
        file_name=f"{file_prefix}_{date.today()}.csv",
        mime="text/csv",
        use_container_width=True,
        key=f"dl_{file_prefix}_{hash(file_prefix)}"
    )
