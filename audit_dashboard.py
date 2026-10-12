"""Launcher for the audit demo UI: `streamlit run audit_dashboard.py` (needs `uv sync --extra dashboard`)."""
import runpy

runpy.run_module("app.modules.audit.ui.app", run_name="__main__")
