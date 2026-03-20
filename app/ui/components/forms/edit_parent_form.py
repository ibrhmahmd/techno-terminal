import streamlit as st
from app.modules.crm import crm_service as crm_srv

def render_edit_parent_form(parent):
    with st.expander("✏️ Edit Family Information"):
        with st.form(f"edit_parent_{parent.id}"):
            c1, c2 = st.columns(2)
            with c1:
                e_name = st.text_input("Full Name *", value=parent.full_name)
                e_phone = st.text_input("Primary Phone *", value=parent.phone_primary)
                rel_opts = ["Father", "Mother", "Guardian", "Other"]
                e_rel = st.selectbox("Relationship", rel_opts, index=rel_opts.index(parent.relation) if parent.relation in rel_opts else 3)
            with c2:
                e_phone_sec = st.text_input("Secondary Phone", value=parent.phone_secondary or "")
                e_email = st.text_input("Email", value=parent.email or "")
            
            e_notes = st.text_area("Notes", value=parent.notes or "")
            
            if st.form_submit_button("Save Changes", type="primary"):
                try:
                    crm_srv.update_guardian(parent.id, {
                        "full_name": e_name.strip(),
                        "phone_primary": e_phone.strip(),
                        "phone_secondary": e_phone_sec.strip() or None,
                        "email": e_email.strip() or None,
                        "relation": e_rel,
                        "notes": e_notes.strip() or None
                    })
                    st.success("Family details updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update: {e}")
