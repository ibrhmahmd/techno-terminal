import streamlit as st
import pandas as pd
from app.modules.crm import crm_service as crm_srv, RegisterParentInput
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
            data = RegisterParentInput(
                full_name=full_name.strip(),
                phone_primary=phone_primary.strip(),
                phone_secondary=phone_secondary.strip() if phone_secondary else None,
                email=email.strip() if email else None,
                relation=relation,
                notes=notes.strip() if notes else None,
            )

            try:
                new_parent = crm_srv.register_parent(data)
                st.success(
                    f"✅ Successfully registered {new_parent.full_name} (ID: {new_parent.id})!"
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

@st.dialog("Browse All Families", width="large")
def modal_browse_all_parents():
    parents = crm_srv.list_all_parents(limit=1000)
    if not parents:
        st.info("No parents found.")
        return

    PAGE_SIZE = 15
    if "bp_page" not in st.session_state:
        st.session_state["bp_page"] = 0

    total_pages = (len(parents) - 1) // PAGE_SIZE + 1
    start_idx = st.session_state["bp_page"] * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_data = parents[start_idx:end_idx]

    df = pd.DataFrame([p.model_dump() for p in page_data])
    display_cols = ["id", "full_name", "phone_primary", "relation", "email"]
    
    st.markdown("Select a row to view the family profile:")
    event = st.dataframe(
        df[display_cols],
        hide_index=True,
        use_container_width=True,
        selection_mode="single-row",
        on_select="rerun",
    )

    if event.selection.rows:
        sel_idx = event.selection.rows[0]
        st.session_state["nav_target_parent_id"] = page_data[sel_idx].id
        st.session_state["bp_page"] = 0
        st.rerun()

    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("⬅️ Prev", disabled=(st.session_state["bp_page"] == 0), key="bp_prev"):
        st.session_state["bp_page"] -= 1
        st.rerun()
    c2.markdown(
        f"<div style='text-align: center'>Page {st.session_state['bp_page'] + 1} of {total_pages}</div>",
        unsafe_allow_html=True,
    )
    if c3.button("Next ➡️", disabled=(st.session_state["bp_page"] >= total_pages - 1), key="bp_next"):
        st.session_state["bp_page"] += 1
        st.rerun()


def render_parent_overview():
    col_l, col_btn1, col_btn2 = st.columns([2, 1, 1])
    with col_l:
        st.subheader("Search parents")
    with col_btn1:
        if st.button("📋 Browse All", key="btn_browse_parents", use_container_width=True):
            modal_browse_all_parents()
    with col_btn2:
        if st.button("➕ Register Parent", key="btn_register_parent", use_container_width=True):
            modal_register_parent()

    search_query = st.text_input(
        "🔍 Search by Name or Phone (min 2 chars)",
        placeholder="e.g. 01012345678 or Ahmed",
    )

    if search_query and len(search_query) >= 2:
        results = crm_srv.search_parents(search_query)
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
