import streamlit as st
import pandas as pd
from app.ui.components.auth_guard import require_auth
from app.modules.crm import service as crm_srv

# Enforce auth
require_auth()

st.title("👥 Parent Management")
st.markdown("Search existing parents or register a new one.")

# --- Search Section ---
st.subheader("Search Parents")
search_query = st.text_input(
    "Search by Name or Phone (min 2 chars)", placeholder="e.g. 01012345678 or Ahmed"
)

if search_query and len(search_query) >= 2:
    results = crm_srv.search_guardians(search_query)
    if results:
        # Convert objects to pandas dataframe for nice rendering
        df = pd.DataFrame([r.model_dump() for r in results])
        # Reorder/filter columns to display
        display_cols = [
            "id",
            "full_name",
            "phone_primary",
            "phone_secondary",
            "relation",
        ]
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No parents found matching your search.")

# --- Registration Form ---
st.divider()
st.subheader("Add New Parent")

with st.expander("Register Parent Form", expanded=False):
    with st.form("new_parent_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            full_name = st.text_input("Full Name *")
            phone_primary = st.text_input(
                "Primary Phone *", help="Must be at least 10 digits"
            )
            relation = st.selectbox(
                "Relation *",
                ["Father", "Mother", "Brother", "Sister", "Uncle", "Aunt", "Other"],
            )

        with col2:
            phone_secondary = st.text_input("Secondary Phone (Optional)")
            email = st.text_input("Email (Optional)")
            notes = st.text_area("Notes (Optional)", height=68)

        submit_btn = st.form_submit_button("Register Parent", type="primary")

        if submit_btn:
            # Prepare data
            data = {
                "full_name": full_name.strip(),
                "phone_primary": phone_primary.strip(),
                "phone_secondary": phone_secondary.strip() if phone_secondary else None,
                "email": email.strip() if email else None,
                "relation": relation,
                "notes": notes.strip() if notes else None,
            }

            try:
                new_guardian = crm_srv.register_guardian(data)
                st.success(
                    f"✅ Successfully registered {new_guardian.full_name} (ID: {new_guardian.id})!"
                )
            except ValueError as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                st.error(f"❌ An unexpected error occurred: {str(e)}")
