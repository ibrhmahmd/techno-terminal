"""
scripts/ci_seed_database.py
───────────────────────────
Simple script for CI: applies seed data and prints summary.
"""

import os
import sys

# Ensure project root is in PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tests.seed_data import seed_database
from app.db.connection import get_session

with get_session() as session:
    result = seed_database(session)
    print(f"✅ Seeded {len(result)} records OK")
    for name, obj in result.items():
        print(f"  • {name}: {obj.__class__.__name__} (id={obj.id})")
