import os
import sys

# Ensure project root is in PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.supabase_clients import get_supabase_admin
from app.db.connection import get_session
from app.modules.auth.models.auth_models import User
from sqlmodel import select

def setup_admin():
    supabase = get_supabase_admin()
    
    email = "testadmin@techno.crm"
    password = "Password123!"
    
    print(f"Checking if user {email} exists in Supabase...")
    # List users to see if it exists
    response = supabase.auth.admin.list_users()
    existing_user = next((u for u in response if u.email == email), None)
    
    if existing_user:
        print(f"User already exists with UID: {existing_user.id}")
        uid = existing_user.id
    else:
        print("Creating user in Supabase...")
        res = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"role": "system_admin"}
        })
        uid = res.user.id
        print(f"Created user with UID: {uid}")
        
    print("Ensuring user exists in local test database...")
    with get_session() as session:
        # Check if user exists in local DB
        stmt = select(User).where(User.supabase_uid == uid)
        db_user = session.exec(stmt).first()
        
        if db_user:
            print(f"User already exists in local DB with role: {db_user.role}")
            db_user.role = "system_admin"
            db_user.is_active = True
            session.add(db_user)
            session.commit()
            print("Updated existing DB user to system_admin.")
        else:
            db_user = User(
                username="testadmin",
                role="system_admin",
                is_active=True,
                supabase_uid=uid
            )
            session.add(db_user)
            session.commit()
            print("Created new user in local DB.")
            
    print("\n" + "="*50)
    print("SUCCESS: Setup complete!")
    print(f"Email:    {email}")
    print(f"Password: {password}")
    print("="*50 + "\n")

if __name__ == "__main__":
    setup_admin()
