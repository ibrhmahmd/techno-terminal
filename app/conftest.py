"""
Test configuration and shared fixtures.
"""
import os

# Tests must never send real email or SMS: blank the messaging credentials
# before the app (and its settings) are imported.
for _name in (
    "GMAIL_SENDER_ADDRESS",
    "GMAIL_APP_PASSWORD",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
):
    os.environ[_name] = ""

import pytest
from fastapi.testclient import TestClient
from app.api.main import create_app
from app.testing.jwt_mocks import generate_mock_supabase_token


def pytest_collection_modifyitems(config, items):
    """Auto-mark any test that requests the real-Supabase admin_token fixture."""
    for item in items:
        if "admin_token" in getattr(item, "fixturenames", ()):
            item.add_marker(pytest.mark.supabase)


def _smtp_blocked(*args, **kwargs):
    raise RuntimeError("Test tried to open a real SMTP connection; patch smtplib in the test.")


@pytest.fixture(autouse=True)
def dispatch_recorder(request, monkeypatch):
    """Keep tests off the network: dispatchers record in memory, smtplib refuses to connect.

    Tests of the dispatcher code itself opt out of the recording with
    @pytest.mark.real_dispatchers; the smtplib guard stays and their own patches win.
    """
    import smtplib

    from app.modules.notifications.dispatchers.email_dispatcher import GmailEmailDispatcher
    from app.modules.notifications.dispatchers.whatsapp_dispatcher import TwilioWhatsAppDispatcher
    from app.testing.notification_mocks import MockEmailDispatcher, MockWhatsAppDispatcher

    email, whatsapp = MockEmailDispatcher(), MockWhatsAppDispatcher()
    if request.node.get_closest_marker("real_dispatchers") is None:
        monkeypatch.setattr(
            GmailEmailDispatcher, "send",
            lambda self, *a, **kw: email.send(*a, **kw),
        )
        monkeypatch.setattr(
            TwilioWhatsAppDispatcher, "send",
            lambda self, *a, **kw: whatsapp.send(*a, **kw),
        )
    monkeypatch.setattr(smtplib, "SMTP_SSL", _smtp_blocked)
    monkeypatch.setattr(smtplib, "SMTP", _smtp_blocked)
    return email, whatsapp


@pytest.fixture(scope="session")
def app():
    """FastAPI application instance."""
    return create_app()


@pytest.fixture(scope="function")
def client(app):
    """FastAPI TestClient instance — fresh for each test."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def uow():
    """A UnitOfWork bound to an outer transaction that is rolled back on teardown.

    A commit inside the test releases only a SAVEPOINT (``join_transaction_mode
    ="create_savepoint"``); the outer transaction is rolled back at teardown,
    so even committed work leaves zero rows behind. Function-scoped.
    """
    from sqlmodel import Session
    from app.db.connection import get_engine
    from app.db.uow import UnitOfWork

    connection = get_engine().connect()
    outer = connection.begin()
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    try:
        yield UnitOfWork(session)
    finally:
        session.close()
        outer.rollback()
        connection.close()


@pytest.fixture
def client_with_uow(app, uow):
    """TestClient whose ``get_uow`` override yields the rollback-only ``uow``.

    Deliberately built WITHOUT the context-manager form so the app lifespan
    (schedulers) does not start. The dependency override is always popped.
    """
    from app.api.deps import get_uow

    app.dependency_overrides[get_uow] = lambda: uow
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_uow, None)


@pytest.fixture
def admin_token():
    """
    Real Supabase JWT token for testing, from the TEST_ADMIN_JWT environment
    variable.

    Generate one (against the cloud *testing* project) with:
        TESTING=true TEST_ENV_FILE=.env.test python scripts/get_test_jwt.py
    """
    token = os.environ.get("TEST_ADMIN_JWT")
    if not token:
        pytest.skip(
            "TEST_ADMIN_JWT not set — generate one with "
            "TESTING=true TEST_ENV_FILE=.env.test python scripts/get_test_jwt.py"
        )
    return token


@pytest.fixture
def mock_admin_token():
    """Generate valid admin mock JWT for testing (bypasses Supabase auth)."""
    return generate_mock_supabase_token(
        user_id="test-admin-001",
        role="admin",
        email="admin@test.com"
    )


@pytest.fixture
def system_admin_token():
    """Generate valid system_admin JWT for testing."""
    return generate_mock_supabase_token(
        user_id="test-sysadmin-001",
        role="system_admin",
        email="sysadmin@test.com"
    )


@pytest.fixture
def instructor_token():
    """Generate valid instructor mock JWT (a non-admin role)."""
    return generate_mock_supabase_token(
        user_id="test-instructor-001",
        role="instructor",
        email="instructor@test.com"
    )


@pytest.fixture
def admin_headers(admin_token):
    """Auth headers with admin token."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def mock_admin_headers(mock_admin_token):
    """Auth headers with mock admin token."""
    return {"Authorization": f"Bearer {mock_admin_token}"}


@pytest.fixture
def system_admin_headers(system_admin_token):
    """Auth headers with system_admin token."""
    return {"Authorization": f"Bearer {system_admin_token}"}


@pytest.fixture
def instructor_headers(instructor_token):
    """Auth headers with instructor token."""
    return {"Authorization": f"Bearer {instructor_token}"}


@pytest.fixture
def override_auth(app, db_session):
    """
    Override the get_current_user dependency to bypass real Supabase JWT validation.
    Also creates the mock user in DB to satisfy FK constraints.
    Ensures a user with id=1 exists (required by admin_settings_router SYSTEM_ADMIN_ID).
    
    Use this fixture in tests that don't need real Supabase auth.
    Combine with mock_admin_headers or system_admin_headers for token-passing tests.
    """
    from app.api.deps import get_current_user
    from app.modules.auth.models.auth_models import User as UserModel
    from sqlalchemy import text
    from sqlmodel import select

    # Ensure a user with id=1 exists (SYSTEM_ADMIN_ID in admin_settings_router)
    user_id1 = db_session.get(UserModel, 1)
    if user_id1 is None:
        user_id1 = UserModel(
            id=1,
            username="system_admin",
            role="system_admin",
            supabase_uid="system-admin-001",
            is_active=True,
        )
        db_session.add(user_id1)
        db_session.commit()

    # The explicit id=1 insert above does not advance users_id_seq, so the next
    # auto-id insert would collide on users_pkey. Push the sequence past MAX(id).
    db_session.execute(
        text("SELECT setval(pg_get_serial_sequence('users','id'), (SELECT MAX(id) FROM users))")
    )
    db_session.commit()

    user = db_session.exec(
        select(UserModel).where(UserModel.supabase_uid == "test-admin-001")
    ).first()
    if user is None:
        user = UserModel(
            username="test_admin",
            role="admin",
            supabase_uid="test-admin-001",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    async def _mock_get_current_user():
        return user

    app.dependency_overrides[get_current_user] = _mock_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def override_system_admin_auth(app, db_session):
    """
    Override get_current_user with a system_admin user.
    Use with system_admin_headers for token-passing tests.
    Also creates the mock user in DB to satisfy FK constraints.
    Ensures a user with id=1 exists (required by admin_settings_router SYSTEM_ADMIN_ID).
    """
    from app.api.deps import get_current_user
    from app.modules.auth.models.auth_models import User as UserModel
    from sqlalchemy import text
    from sqlmodel import select

    # Ensure a user with id=1 exists (SYSTEM_ADMIN_ID in admin_settings_router)
    user_id1 = db_session.get(UserModel, 1)
    if user_id1 is None:
        user_id1 = UserModel(
            id=1,
            username="system_admin",
            role="system_admin",
            supabase_uid="system-admin-001",
            is_active=True,
        )
        db_session.add(user_id1)
        db_session.commit()

    # The explicit id=1 insert above does not advance users_id_seq, so the next
    # auto-id insert would collide on users_pkey. Push the sequence past MAX(id).
    db_session.execute(
        text("SELECT setval(pg_get_serial_sequence('users','id'), (SELECT MAX(id) FROM users))")
    )
    db_session.commit()

    user = db_session.exec(
        select(UserModel).where(UserModel.supabase_uid == "test-sysadmin-001")
    ).first()
    if user is None:
        user = UserModel(
            username="test_sysadmin",
            role="system_admin",
            supabase_uid="test-sysadmin-001",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    async def _mock_get_current_user():
        return user

    app.dependency_overrides[get_current_user] = _mock_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def override_instructor_auth(app, db_session):
    """Override get_current_user with an instructor user (pair with instructor_headers)."""
    from app.api.deps import get_current_user
    from app.modules.auth.models.auth_models import User as UserModel
    from sqlmodel import select

    user = db_session.exec(
        select(UserModel).where(UserModel.supabase_uid == "test-instructor-001")
    ).first()
    if user is None:
        user = UserModel(
            username="test_instructor",
            role="instructor",
            supabase_uid="test-instructor-001",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    async def _mock_get_current_user():
        return user

    app.dependency_overrides[get_current_user] = _mock_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(scope="module")
def seeded_session():
    """
    Module-scoped database session pre-seeded with minimum viable records.
    Seeds on first access, rolls back all changes when the module completes.
    
    Use this in test files that need database records (courses, students, etc.)
    but don't care about specific seed state. 
    
    The rollback on teardown ensures zero side effects between modules.
    """
    from app.db.connection import get_session
    from app.testing.seed_data import seed_database
    
    with get_session() as session:
        seed_database(session)
        yield session
        session.rollback()


@pytest.fixture
def db_session():
    """
    Database session for test data setup.
    Uses transaction rollback for test isolation.
    """
    from app.db.connection import get_session
    
    with get_session() as session:
        yield session
        # Rollback happens automatically on exception
        # Or we can explicitly rollback here for cleanup
