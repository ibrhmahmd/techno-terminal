import streamlit as st
import pandas as pd
from app.modules.analytics import analytics_service as att_srv

def render_financial_risk():
    st.markdown("#### ⚠️ Flight Risk Students")
    st.caption("Students who have missed sessions AND owe money. High priority for follow-up.")
    data = att_srv.get_flight_risk_students()
    if not data:
        st.success("No high flight risk students found.")
        return

    df = pd.DataFrame(data)
    st.dataframe(
        df.rename(columns={
            "student_name": "Student",
            "course_name": "Course",
            "amount_owed": "Debt (EGP)",
            "sessions_missed": "Sessions Missed"
        }),
        hide_index=True,
        use_container_width=True
    )
