import streamlit as st
import pandas as pd
import app.modules.analytics as att_srv

def render_instructor_matrix():
    st.markdown("#### 👨‍🏫 Instructor Value Matrix")
    data = att_srv.get_instructor_value_matrix()
    if not data:
        st.info("No instructor data.")
        return

    df = pd.DataFrame([d.model_dump() for d in data])
    # Scatter plot mapping Revenue (x) vs Attendance Pct (y)
    
    st.scatter_chart(
        df,
        x="total_revenue",
        y="avg_attendance_pct",
        color="instructor_name"
    )
    
    st.dataframe(
        df.rename(columns={
            "instructor_name": "Instructor",
            "total_revenue": "Generated Revenue (EGP)",
            "avg_attendance_pct": "Avg Attendance % (Retention Marker)"
        }).style.format({"Generated Revenue (EGP)": "{:,.0f}", "Avg Attendance % (Retention Marker)": "{:.1f}%"}),
        hide_index=True,
        use_container_width=True
    )
