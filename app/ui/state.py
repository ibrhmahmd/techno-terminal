import streamlit as st
from typing import Optional


_USER_KEY = "_current_user"
_ROLE_KEY = "_current_role"


def set_user(user) -> None:
    st.session_state[_USER_KEY] = user


def get_user():
    return st.session_state.get(_USER_KEY)


def is_authenticated() -> bool:
    return get_user() is not None


def get_role() -> Optional[str]:
    user = get_user()
    return user.role if user else None


def has_role(role: str) -> bool:
    return get_role() == role


def clear_session() -> None:
    st.session_state.clear()
