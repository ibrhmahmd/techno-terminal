# Data Migration Plan: Local PostgreSQL → Supabase

## Executive Summary

**Source:** Local PostgreSQL (`postgresql://postgres:34373839@localhost:5432/techno`)  
**Target:** Supabase Hosted (`postgresql://postgres.srbppkcvrgioneitktdj:***@aws-1-eu-north-1.pooler.supabase.com:6543/postgres`)  
**Approach:** pg_dump → psql restore  
**Estimated Time:** 15-30 minutes depending on data size

---

## Pre-Migration Checklist

### 1. Backup Local Database
```bash
# Create backup of local database
pg_dump -h localhost -p 5432 -U postgres -d techno -F c -f techno_local_backup.dump

# Or plain SQL format (more compatible)
pg_dump -h localhost -p 5432 -U postgres -d techno -f techno_local_backup.sql
```

### 2. Verify Target Database is Empty
```bash
# Connect to Supabase and check
psql "postgresql://postgres.srbppkcvrgioneitktdj:67OYU5HZeBYiVBs5@aws-1-eu-north-1.pooler.supabase.com:6543/postgres" -c "\dt"
```

### 3. Install Required Tools
Ensure you have PostgreSQL client tools installed:
- `pg_dump` - for exporting local data
- `psql` - for importing to Supabase
- `pg_restore` - for custom format restore (optional)

**Windows:** Download from https://www.postgresql.org/download/windows/  
**macOS:** `brew install postgresql`  
**Linux:** `sudo apt-get install postgresql-client`

---

## Migration Approaches

### Option A: SQL Dump (Recommended - Simplest)

**Pros:** Works with Supabase's connection pooling, human-readable, easy to debug  
**Cons:** Slower for large databases (>1GB)

**Steps:**

1. **Export local database to SQL:**
```bash
pg_dump \
  -h localhost \
  -p 5432 \
  -U postgres \
  -d techno \
  --no-owner \
  --no-privileges \
  --clean \
  --if-exists \
  -f techno_migration.sql
```

2. **Import to Supabase:**
```bash
psql \
  "postgresql://postgres.srbppkcvrgioneitktdj:67OYU5HZeBYiVBs5@aws-1-eu-north-1.pooler.supabase.com:6543/postgres" \
  -f techno_migration.sql
```

---

### Option B: Compressed Custom Format (For Large Databases)

**Pros:** Faster, compressed, selective restore possible  
**Cons:** Requires `pg_restore`, may have issues with connection poolers

**Steps:**

1. **Export with custom format:**
```bash
pg_dump \
  -h localhost \
  -p 5432 \
  -U postgres \
  -d techno \
  -F c \
  -f techno_migration.dump
```

2. **Restore to Supabase:**
```bash
pg_restore \
  --dbname="postgresql://postgres.srbppkcvrgioneitktdj:67OYU5HZeBYiVBs5@aws-1-eu-north-1.pooler.supabase.com:6543/postgres" \
  --no-owner \
  --no-privileges \
  --clean \
  --if-exists \
  techno_migration.dump
```

---

## pg_dump Options Explained

| Flag | Purpose |
|------|---------|
| `--no-owner` | Skip ownership commands (Supabase handles this) |
| `--no-privileges` | Skip privilege grants (Supabase uses its own roles) |
| `--clean` | Drop existing objects before creating new ones |
| `--if-exists` | Use IF EXISTS with DROP commands |
| `--data-only` | Export only data (no schema) |
| `--schema-only` | Export only schema (no data) |

---

## Handling Supabase-Specific Constraints

### 1. Extensions
Supabase pre-installs common extensions. Your dump may try to create them again.

**Fix:** Edit the SQL file and remove or comment out:
```sql
-- Remove these lines if they cause errors
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

### 2. Roles and Users
Supabase manages roles differently. Use `--no-owner --no-privileges` flags.

### 3. Connection Pooling (Port 6543)
The pooler on port 6543 works in **transaction mode**. For large dumps, you may need to:
- Split schema and data migrations
- Use smaller batches
- Or temporarily use direct connection (port 5432) if available

---

## Step-by-Step Migration Commands

### Complete Migration Script

```bash
#!/bin/bash
# save as: migrate_to_supabase.sh

# Configuration
LOCAL_DB="techno"
LOCAL_USER="postgres"
LOCAL_HOST="localhost"
LOCAL_PORT="5432"

SUPABASE_URL="postgresql://postgres.srbppkcvrgioneitktdj:67OYU5HZeBYiVBs5@aws-1-eu-north-1.pooler.supabase.com:6543/postgres"

# Step 1: Create backup
echo "Creating local backup..."
pg_dump \
  -h $LOCAL_HOST \
  -p $LOCAL_PORT \
  -U $LOCAL_USER \
  -d $LOCAL_DB \
  --no-owner \
  --no-privileges \
  --clean \
  --if-exists \
  -f techno_migration_$(date +%Y%m%d_%H%M%S).sql

# Step 2: Verify backup
echo "Verifying backup file..."
if [ ! -f techno_migration_*.sql ]; then
    echo "Backup failed!"
    exit 1
fi

# Step 3: Restore to Supabase
echo "Restoring to Supabase..."
psql "$SUPABASE_URL" -f techno_migration_*.sql

echo "Migration complete!"
```

---

## Post-Migration Verification

### 1. Count Tables
```bash
# Local
psql -h localhost -p 5432 -U postgres -d techno -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"

# Supabase
psql "postgresql://postgres.srbppkcvrgioneitktdj:67OYU5HZeBYiVBs5@aws-1-eu-north-1.pooler.supabase.com:6543/postgres" -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"
```

### 2. Check Row Counts
```sql
-- Run on both databases and compare
SELECT 
    schemaname,
    tablename,
    pg_catalog.pg_total_relation_size(schemaname||'.'||tablename) AS size,
    (SELECT count(*) FROM pg_catalog.pg_stat_user_tables WHERE schemaname = s.schemaname AND relname = s.tablename) AS row_estimate
FROM pg_catalog.pg_tables s
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 3. Test Application Connection
```bash
# Test from your Python app
python -c "
from app.db.connection import get_engine
from sqlalchemy import text
engine = get_engine()
with engine.connect() as conn:
    result = conn.execute(text('SELECT count(*) FROM information_schema.tables WHERE table_schema=\'public\''))
    print(f'Tables in Supabase: {result.scalar()}')
"
```

---

## Troubleshooting

### Error: "Too many connections"
**Fix:** The pooler limits concurrent connections. Use single connection mode:
```bash
psql "$SUPABASE_URL" -c "SET session_replication_role = replica;" -f migration.sql
```

### Error: "Relation already exists"
**Fix:** Ensure you use `--clean --if-exists` flags

### Error: "Permission denied"
**Fix:** Use `--no-owner --no-privileges` flags

### Error: "Connection reset"
**Fix:** Large dumps may timeout. Split into schema and data:
```bash
# Schema only
pg_dump --schema-only -f schema.sql

# Data only  
pg_dump --data-only -f data.sql

# Apply separately
psql "$SUPABASE_URL" -f schema.sql
psql "$SUPABASE_URL" -f data.sql
```

---

## Rollback Plan

If migration fails:

1. **Keep local database running** until verification complete
2. **Revert .env** to local connection string
3. **Investigate errors** in migration log
4. **Retry with fixes**

---

## Next Steps After Migration

1. ✅ Verify all data migrated correctly
2. ✅ Run application tests
3. ✅ Update `.env` to use Supabase (already done)
4. ✅ Restart API server
5. ⏳ (Optional) Set up Supabase backups
6. ⏳ (Optional) Configure Row Level Security (RLS)
