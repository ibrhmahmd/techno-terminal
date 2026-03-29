# Phase 1 — Technical Plan: Core Foundation & Security

---

## 1. Revised Full Project Structure

The UI is a **Delivery Layer** — one of potentially many (Streamlit today, FastAPI tomorrow).
Both delivery layers call into `modules/` (the Core). Neither knows about the other.

```
techno_data_ Copy/
├── app/
│   │
│   ├── modules/                   # Core Logic (business rules, data access)
│   │   ├── auth/
│   │   │   ├── models.py
│   │   │   ├── repository.py
│   │   │   └── service.py
│   │   ├── crm/                   # Phase 2
│   │   ├── academics/             # Phase 2
│   │   ├── enrollments/           # Phase 3
│   │   ├── attendance/            # Phase 3
│   │   ├── finance/               # Phase 4
│   │   └── competitions/          # Phase 5
│   │
│   ├── ui/                        # Streamlit Delivery Layer (MVP)
│   │   ├── main.py                # Entry point, sidebar, routing
│   │   ├── state.py               # Centralized session state helpers
│   │   ├── pages/
│   │   │   ├── login.py
│   │   │   └── dashboard.py       # Placeholder pages for future phases
│   │   └── components/
│   │       └── auth_guard.py      # Decorator/check to enforce login
│   │
│   ├── api/                       # Future FastAPI Delivery Layer (empty for now)
│   │   └── .gitkeep
│   │
│   └── db/
│       ├── connection.py          # Engine factory, Session context manager
│       └── base.py                # SQLModel shared Base, metadata
│
├── db/
│   └── schema.sql                 # SQL definition (already done)
│
├── docs/
│   └── memory_bank/               # (already structured)
│
├── .env                           # DATABASE_URL, SECRET_KEY
├── .env.example                   # Template for new developers
├── requirements.txt
└── README.md
```

---

## 2. File-by-File Breakdown

### `app/db/base.py`

**Mission:** Single shared SQLModel metadata base. All models import from here. Prevents circular imports.

```python
from sqlmodel import SQLModel

# All table models must inherit from SQLModel directly.
# This file is imported by db/connection.py to create tables.
```

---

### `app/db/connection.py`

**Mission:** Database engine creation and session lifecycle management. The only file that reads `DATABASE_URL`. All repositories receive a session — they never create one.

**Functions:**

- `get_engine()` — creates the SQLAlchemy engine from `.env`, cached (singleton)
- `get_session()` — context manager yielding a `Session`, commits on exit, rolls back on error

**Code style:**

```python
from sqlmodel import create_engine, Session
from contextlib import contextmanager
import os

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        url = os.environ["DATABASE_URL"]
        _engine = create_engine(url)
    return _engine

@contextmanager
def get_session():
    with Session(get_engine()) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
```

**Interaction:** Imported by every `repository.py` file. Never imported by service or UI files directly.

---

### `app/modules/auth/models.py`

**Mission:** SQLModel definitions that mirror the `users` and `employees` tables exactly.
**Rule:** These are read-only models in Phase 1. Write operations on auth are limited to `change_password`.

**Classes:**

- `Employee(SQLModel, table=True)` — maps to `employees` table, all columns
- `User(SQLModel, table=True)` — maps to `users` table, all columns

**Note:** No `__tablename__` conflicts because both map exactly to the schema column names.

---

### `app/modules/auth/repository.py`

**Mission:** Raw database access for auth entities. Zero business logic.

**Functions:**

- `get_user_by_username(session, username: str) → User | None`
- `get_employee_by_id(session, employee_id: int) → Employee | None`
- `update_password_hash(session, user_id: int, new_hash: str) → None`
  - Sets `users.password_hash`, sets `users.updated_at` to `datetime.now(UTC)`

**Code style:**

```python
from sqlmodel import Session, select
from .models import User

def get_user_by_username(session: Session, username: str) -> User | None:
    stmt = select(User).where(User.username == username)
    return session.exec(stmt).first()
```

---

### `app/modules/auth/service.py`

**Mission:** Business logic for authentication. The only file that uses `passlib`. Calls repository functions. Returns plain Python objects — never a Streamlit widget.

**Functions:**

- `authenticate(username: str, password: str) → User | None`
  - Opens a session
  - Calls `repo.get_user_by_username()`
  - Returns `None` if user not found or not active
  - Verifies password hash using `passlib`
  - Updates `last_login` timestamp
  - Returns the `User` object on success

- `change_password(user_id: int, current_password: str, new_password: str) → bool`
  - Re-authenticates with current password first
  - Validates new password meets minimum length
  - Calls `repo.update_password_hash()` with newly hashed value
  - Returns `True` on success, raises `ValueError` on validation failure

**Code style:**

```python
from passlib.context import CryptContext
from datetime import datetime, timezone
from app.db.connection import get_session
from . import repository as repo

pwd_context = CryptContext(schemes=["bcrypt"])

def authenticate(username: str, password: str):
    with get_session() as session:
        user = repo.get_user_by_username(session, username)
        if not user or not user.is_active:
            return None
        if not pwd_context.verify(password, user.password_hash):
            return None
        user.last_login = datetime.now(timezone.utc)
        session.add(user)
        return user
```

---

### `app/ui/state.py`

**Mission:** All `st.session_state` reads and writes go through this file. Prevents magic string keys scattered across pages.

**Functions:**

- `set_user(user: User) → None` — stores authenticated user in session
- `get_user() → User | None` — returns current user or None
- `clear_session() → None` — logout: clears all session state keys
- `is_authenticated() → bool` — returns `True` if a valid user is in session
- `require_role(role: str) → bool` — checks if current user has the given role

**Code style:**

```python
import streamlit as st

_USER_KEY = "_current_user"

def set_user(user) -> None:
    st.session_state[_USER_KEY] = user

def get_user():
    return st.session_state.get(_USER_KEY)

def is_authenticated() -> bool:
    return get_user() is not None

def clear_session() -> None:
    st.session_state.clear()
```

---

### `app/ui/components/auth_guard.py`

**Mission:** A single reusable function called at the top of every protected page. If the user is not authenticated, it stops rendering and redirects to login.

**Functions:**

- `require_auth() → User` — calls `state.is_authenticated()`, calls `st.stop()` and switches page if not auth'd, otherwise returns the current user

**Code style:**

```python
import streamlit as st
from app.ui import state

def require_auth():
    if not state.is_authenticated():
        st.warning("Please log in to continue.")
        st.switch_page("pages/login.py")
        st.stop()
    return state.get_user()
```

---

### `app/ui/pages/login.py`

**Mission:** Authentication page. The only page accessible without being logged in.

**Renders:**

- Logo / app title
- Username and password inputs
- "Login" button → calls `auth_service.authenticate()` → saves to `state.set_user()` → `st.switch_page(dashboard)`
- Displays error on failed login without revealing whether username or password was wrong

**Interactions:**

```
login.py → auth_service.authenticate() → auth_repo → DB
login.py → state.set_user()
login.py → st.switch_page(dashboard)
```

---

### `app/ui/main.py`

**Mission:** Streamlit entry point. Defines the sidebar navigation and the multi-page app routing.

**Responsibilities:**

- Call `require_auth()` at the top
- Render sidebar with navigation links grouped by domain
- Show logged-in user name and role in sidebar footer
- Logout button → `state.clear_session()` → switch to login

**Code style:**

```python
import streamlit as st
from app.ui.components.auth_guard import require_auth
from app.ui import state

st.set_page_config(page_title="Techno Terminal", layout="wide")

user = require_auth()

with st.sidebar:
    st.title("Techno Terminal")
    st.caption(f"Logged in as **{user.username}** · {user.role}")

    st.page_link("pages/dashboard.py", label="Dashboard", icon="🏠")
    # Phase 2+ pages added here as they are built

    if st.button("Logout"):
        state.clear_session()
        st.switch_page("pages/login.py")
```

---

## 3. File Interaction Map

```
.env
 └─► db/connection.py (reads DATABASE_URL)
      └─► auth/repository.py (receives session)
           └─► auth/service.py (calls repo functions)
                └─► ui/pages/login.py (calls service)
                     └─► ui/state.py (stores result)
                          └─► ui/components/auth_guard.py (reads state)
                               └─► ui/main.py (uses guard on every page)
```

---

## 4. Design Pattern for Phase 1 Features

**Pattern: "3-File Module + Stateless Services"**

Every service function:

1. Opens its own DB session (using `get_session()` context manager)
2. Calls one or more repo functions, passing the session
3. Applies business logic in pure Python
4. Returns a plain Python object (Pydantic/SQLModel model or None)
5. Raises a named Python exception on validation failure

Every repository function:

1. Accepts a `session` parameter — never creates one
2. Runs one exact SQL/SQLModel query
3. Returns the ORM object or None

This means the service is always the correct entry point for any feature. The UI never touches the repository directly.

---

## 5. Dependencies (`requirements.txt`)

```
streamlit>=1.32.0
sqlmodel>=0.0.16
psycopg2-binary>=2.9.9
python-dotenv>=1.0.0
passlib[bcrypt]>=1.7.4
```

---

## 6. Phase 1 Completion Checklist

- [ ] `app/db/base.py` — shared SQLModel base
- [ ] `app/db/connection.py` — engine + session context manager
- [ ] `app/modules/auth/models.py` — `User`, `Employee` SQLModel classes
- [ ] `app/modules/auth/repository.py` — `get_user_by_username`, `update_password_hash`
- [ ] `app/modules/auth/service.py` — `authenticate`, `change_password`
- [ ] `app/ui/state.py` — session state abstraction
- [ ] `app/ui/components/auth_guard.py` — `require_auth()`
- [ ] `app/ui/pages/login.py` — login form page
- [ ] `app/ui/pages/dashboard.py` — placeholder home page post-login
- [ ] `app/ui/main.py` — sidebar navigation + routing
- [ ] `.env` + `.env.example` — environment config
- [ ] `requirements.txt` — dependencies
- [ ] Verify Phase 1 end-to-end: login → dashboard → logout
