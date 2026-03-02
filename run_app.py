import os
import sys
import subprocess

if __name__ == "__main__":
    # Add the project root to PYTHONPATH so imports from 'app' always work
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.environ["PYTHONPATH"] = (
        project_root + os.pathsep + os.environ.get("PYTHONPATH", "")
    )

    # Run the database seeding process
    from app.db.seed import seed_admin_account

    seed_admin_account()

    # Execute Streamlit programmatically using the same Python executable
    args = [sys.executable, "-m", "streamlit", "run", "app/ui/main.py"]
    print(f"Starting Techno Kids App: {' '.join(args)}")

    try:
        subprocess.run(args)
    except KeyboardInterrupt:
        print("\nShutdown complete.")
