from sqlmodel import select
from app.db.connection import get_session
from app.modules.auth.models import User
from app.modules.auth.service import hash_password


def seed_admin_account():
    with get_session() as session:
        statement = select(User).where(User.username == "admin")
        admin_user = session.exec(statement).first()

        if not admin_user:
            print("🌱 Seeding default 'admin' account...")
            new_admin = User(
                username="admin",
                password_hash=hash_password("admin123"),
                role="admin",
                is_active=True,
            )
            session.add(new_admin)
            session.commit()
            print(
                "✅ Default admin account created. Username: 'admin', Password: 'admin123'"
            )
        else:
            print("✅ Admin account already exists. Skipping seeding.")


if __name__ == "__main__":
    seed_admin_account()
