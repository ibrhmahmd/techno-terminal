import os
import sys
import subprocess

if __name__ == "__main__":
    # Add the project root to PYTHONPATH so imports from 'app' always work
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.environ["PYTHONPATH"] = (
        project_root + os.pathsep + os.environ.get("PYTHONPATH", "")
    )

    # Ensure analytics SQL views exist (ORM create_all does not create them)
    from app.db.init_db import apply_analytics_views
    from app.db.seed import seed_admin_account

    try:
        apply_analytics_views()
    except Exception as e:
        print(f"⚠️ Could not apply analytics views (is DATABASE_URL correct and DB up?): {e}")

    seed_admin_account()

    # Execute Streamlit programmatically using the same Python executable
    args = [sys.executable, "-m", "streamlit", "run", "app/ui/main.py"]
    print(f"Starting Techno Terminal App: {' '.join(args)}")

    try:
        subprocess.run(args)
    except KeyboardInterrupt:
        print("\nShutdown complete.")
