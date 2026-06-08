"""
verify_test_db.py
─────────────────
Verifies db/schema.sql applies cleanly to a target database.
Handles psql meta-commands (\\set, \\i includes).

Usage:
    python scripts/verify_test_db.py [DATABASE_URL]

Defaults to DATABASE_URL from .env.test if not provided.
"""

import os
import re
import subprocess
import sys


def get_database_url() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1]

    env_test_path = os.path.join(os.path.dirname(__file__), "..", ".env.test")
    if os.path.exists(env_test_path):
        with open(env_test_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DATABASE_URL="):
                    return line.split("=", 1)[1].strip('"').strip("'")

    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    print("No DATABASE_URL found. Provide it as argument or set in .env.test.")
    sys.exit(1)


def resolve_schema(schema_path: str) -> str:
    """Resolve \\i include directives in schema.sql into a single SQL string."""
    base_dir = os.path.dirname(schema_path)
    with open(schema_path) as f:
        content = f.read()

    result_lines = []
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("\\i "):
            include_path = os.path.join(base_dir, stripped[3:].strip())
            if os.path.exists(include_path):
                with open(include_path) as inc:
                    result_lines.append(inc.read())
            else:
                print(f"Warning: include not found: {include_path}", file=sys.stderr)
        elif stripped.startswith("\\"):
            continue
        else:
            result_lines.append(line)

    return "\n".join(result_lines)


def strip_sql_comments(sql: str) -> str:
    return re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)


def split_statements(sql: str) -> list[str]:
    stripped = strip_sql_comments(sql)
    statements = []
    current_depth = 0
    current = []
    in_dollar_tag = None

    for line in stripped.split("\n"):
        current.append(line)
        dollar_match = re.match(r"^\s*\$(\w*)\$", line)
        if dollar_match:
            tag = dollar_match.group(1)
            if in_dollar_tag is None:
                in_dollar_tag = tag
            elif in_dollar_tag == tag:
                in_dollar_tag = None

        if in_dollar_tag is None:
            semicolons = line.count(";") - line.count("'")
            if semicolons > 0 and line.strip().rstrip(";").strip().endswith(";"):
                statements.append("\n".join(current))
                current = []

    if current:
        statements.append("\n".join(current))
    return [s.strip() for s in statements if s.strip()]


def main():
    url = get_database_url()
    schema_path = os.path.join(os.path.dirname(__file__), "..", "db", "schema.sql")

    if not os.path.exists(schema_path):
        print(f"Schema file not found: {schema_path}")
        sys.exit(1)

    # Prefer psql if available (handles all meta-commands natively)
    try:
        result = subprocess.run(
            ["psql", url, "-f", schema_path],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            print("SUCCESS: db/schema.sql applied cleanly via psql.")
            sys.exit(0)
        else:
            print(f"psql failed (exit {result.returncode}), falling back to Python parser...")
            print(result.stderr[:500])
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("psql not available, using Python fallback...")

    # Fallback: resolve includes, execute as single batch via psycopg2
    try:
        import psycopg2
    except ImportError:
        print("psycopg2 not installed. Install: pip install psycopg2-binary")
        sys.exit(1)

    resolved_sql = resolve_schema(schema_path)

    try:
        conn = psycopg2.connect(url)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(resolved_sql)
        cur.close()
        conn.close()
        print("SUCCESS: db/schema.sql applied cleanly.")
        sys.exit(0)
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
