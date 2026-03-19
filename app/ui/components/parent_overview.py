import streamlit as st
import pandas as pd
from app.modules.crm import crm_service as crm_srv
from app.shared.exceptions import NotFoundError, BusinessRuleError, ConflictError, ValidationError


@st.dialog("Register New Parent", width="large")
def modal_register_parent():
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

        if st.form_submit_button("Register Parent", type="primary"):
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
                st.rerun()
            except ConflictError as e:
                st.error(f"❌ Conflict: {e.message}")
            except ValidationError as e:
                st.error(f"❌ Invalid input: {e.message}")
            except NotFoundError as e:
                st.warning(f"⚠️ Not found: {e.message}")
            except Exception as e:
                st.error(f"❌ An unexpected error occurred: {str(e)}")


def render_parent_overview():
    col_l, col_r = st.columns([3, 1])
    with col_l:
        st.subheader("Search parents")
    with col_r:
        if st.button("➕ Register Parent", use_container_width=True):
            modal_register_parent()

    search_query = st.text_input(
        "🔍 Search by Name or Phone (min 2 chars)",
        placeholder="e.g. 01012345678 or Ahmed",
    )

    if search_query and len(search_query) >= 2:
        results = crm_srv.search_guardians(search_query)
        if results:
            st.markdown(
                "Select a parent below to view their profile and registered children:"
            )
            df = pd.DataFrame([r.model_dump() for r in results])
            display_cols = [
                "id",
                "full_name",
                "phone_primary",
                "phone_secondary",
                "relation",
            ]

            event = st.dataframe(
                df[display_cols],
                use_container_width=True,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
            )

            if event.selection.rows:
                sel_idx = event.selection.rows[0]
                st.session_state["nav_target_parent_id"] = results[sel_idx].id
                st.rerun()
        else:
            st.info("No parents found matching your search.")
    else:
        st.info("Start typing a name or phone to search.")
