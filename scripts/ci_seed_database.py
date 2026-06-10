"""
scripts/ci_seed_database.py
───────────────────────────
Simple script for CI: applies seed data and prints summary.
"""

from tests.seed_data import seed_database
from app.db.connection import get_session

with get_session() as session:
    result = seed_database(session)
    print(f"✅ Seeded {len(result)} records OK")
    for name, obj in result.items():
        print(f"  • {name}: {obj.__class__.__name__} (id={obj.id})")
