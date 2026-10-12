---
status: accepted
---

# audit is the twelfth module, on top, and Streamlit is only its demo UI

The Streamlit "Finance & Audit Hub" (`audit_dashboard.py` + `dashboard/`) lived outside `app/`: it opened its own psycopg2 connection, read `.env` with `load_dotenv()`, and queried about 45 SQL views directly. Its integrity checks (scenarios A–I) had no API, and `streamlit` was a runtime dependency of the API, so it was installed on FastAPI Cloud. We decided the dashboard becomes **`audit`, the twelfth module, at the top of the order** (ADR-0003 amended), with the standard layers plus a **`ui/` layer** for the Streamlit pages. The module's real deliverable is an API (#114); Streamlit is a local demo that calls the module's services directly and is never deployed.

## Consequences

- `app/modules/audit/` has `constants.py` (the scenario and view catalogue), `schemas/`, `repositories/`, `services/` and `ui/`. Reads go through the app settings, engine and unit of work; the module never opens its own connection or reads `.env`.
- `ui` is a presentation layer like `api`: no other layer may import it (enforced in `tests/architecture`). `create_app()` must never import `audit.ui` or `streamlit` (`tests/architecture/test_audit_ui_not_deployed.py`), and `app/modules/audit/ui/` is in `.fastapicloudignore`.
- `streamlit` and `pandas` move to the optional `dashboard` dependency group (`uv sync --extra dashboard`). The root `audit_dashboard.py` is a three-line launcher, so `streamlit run audit_dashboard.py` still works.
- View and column names are interpolated into SQL, so the service accepts only views on the catalogue's allow-list and plain identifiers.
- Until #115, the finance and BI view reads also sit in audit; ADR-0012 assigns them to analytics.
