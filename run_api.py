import uvicorn
import os
import sys

# Ensure the root project directory is in the PYTHONPATH
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if __name__ == "__main__":
    print("Starting Techno Future CRM FastAPI Backend...")
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)
