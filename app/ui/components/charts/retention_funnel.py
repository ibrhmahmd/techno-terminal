import streamlit as st
import pandas as pd
import app.modules.analytics as att_srv

def render_retention_funnel():
    st.markdown("#### 🎯 Level-to-Level Retention Churn")
    data = att_srv.get_level_retention_funnel()
    if not data:
        st.info("No retention data yet.")
        return

    df = pd.DataFrame([d.model_dump() for d in data])
    # df has 'course_name', 'level_number', 'student_count'
    # Pivot so each row is a course, each column is a level
    pivot = df.pivot_table(index="course_name", columns="level_number", values="student_count", fill_value=0)
    
    st.dataframe(pivot, use_container_width=True)
    st.caption("Rows: Course | Columns: Level Number | Values: Active/Graduated Students")
