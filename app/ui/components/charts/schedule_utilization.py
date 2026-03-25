import streamlit as st
import pandas as pd
import app.modules.analytics as att_srv

def render_schedule_utilization():
    st.markdown("#### 📅 Schedule Capacity Hotspots")
    data = att_srv.get_schedule_utilization()
    if not data:
        st.info("No schedule data.")
        return

    df = pd.DataFrame([d.model_dump() for d in data])
    # Pivot for heatmap: index=time_start, columns=day
    pivot = df.pivot_table(index="time_start", columns="day", values="utilization_pct", fill_value=0)
    
    # Map percentages to formatted strings
    pivot_fmt = pivot.map(lambda x: f"{x:.1f}%")
    st.dataframe(pivot_fmt, use_container_width=True)
