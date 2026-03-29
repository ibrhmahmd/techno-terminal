"""
Alembic environment. Loads DATABASE_URL from app settings and registers all SQLModel tables.
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

# Import every table model so metadata is complete (mirror app/db/init_db.py)
from app.modules.hr.hr_models import Employee  # noqa: F401
from app.modules.auth.auth_models import User  # noqa: F401
from app.modules.crm.crm_models import Parent, Student, StudentParent  # noqa: F401
from app.modules.academics.academics_models import Course, Group  # noqa: F401
from app.modules.academics.academics_session_models import CourseSession  # noqa: F401
from app.modules.attendance.attendance_models import Attendance  # noqa: F401
from app.modules.enrollments.enrollment_models import Enrollment  # noqa: F401
from app.modules.finance.finance_models import Receipt, Payment  # noqa: F401
from app.modules.competitions.competition_models import (  # noqa: F401
    Competition,
    CompetitionCategory,
    Team,
    TeamMember,
)

from app.core.config import settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section) or {}
    configuration = dict(section)
    configuration["sqlalchemy.url"] = settings.database_url
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
