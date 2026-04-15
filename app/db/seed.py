from sqlmodel import select
from app.db.connection import get_session
from app.modules.auth import User
from app.modules.auth import UserRole
from app.core.supabase_clients import get_supabase_admin


def seed_admin_account():
    with get_session() as session:
        statement = select(User).where(User.username == "admin")
        admin_user = session.exec(statement).first()

        if not admin_user:
            print("Seeding default 'admin' account into Supabase Cloud...")
            try:
                supabase_admin = get_supabase_admin()
                admin_email = "ibrahim.net@techno.crm"

                # We attempt to create the identity natively in Supabase
                try:
                    auth_response = supabase_admin.auth.admin.create_user(
                        {
                            "email": admin_email,
                            "password": "qwertyuiop12",
                            "email_confirm": True,
                        }
                    )
                    uid = auth_response.user.id
                except Exception as e:
                    print(
                        f"⚠️ Supabase identity creation failed (It might already exist in your Supabase project): {e}"
                    )
                    
                    # Try to fetch existing user
                    users = supabase_admin.auth.admin.list_users()
                    uid = None
                    # Next-gen supabase python clients return a list directly or a UserList object with a .users attribute
                    user_iterable = getattr(users, 'users', users)
                    for u in user_iterable:
                        # Depending on the client version, u might be a dict or a Pydantic object
                        u_email = getattr(u, 'email', None) or (isinstance(u, dict) and u.get('email'))
                        if u_email == admin_email:
                            uid = getattr(u, 'id', None) or (isinstance(u, dict) and u.get('id'))
                            break
                            
                    if not uid:
                        print("❌ Could not find the existing admin user in Supabase. Returning.")
                        return
                    print(f"✅ Found existing Supabase identity with UID {uid}. Proceeding with mapping.")

                # Map the created Supabase identity to our local PostgreSQL database
                new_admin = User(
                    username="admin",
                    supabase_uid=uid,
                    role=UserRole.ADMIN,
                    is_active=True,
                )
                session.add(new_admin)
                session.commit()
                print(
                    f"✅ Default admin account securely mapped.\n"
                    f"   Login Email: {admin_email}\n"
                    f"   Login Password: qwertyuiop12"
                )

            except Exception as e:
                print(f"❌ Failed to interface with Supabase during seeding: {e}")
        else:
            print("✅ Admin account is already natively mapped. Skipping seeding.")


if __name__ == "__main__":
    seed_admin_account()
