# Connection Pool Test Suite

Expanded test suite to detect 4 critical database connection failure patterns.

## Quick Start

```bash
# See all options
python test_connection_exhaustion.py --help

# Run all direct SQLAlchemy tests (fast)
python test_connection_exhaustion.py --all-direct

# Run individual tests
python test_connection_exhaustion.py --uow        # UoW pattern abuse (10s)
python test_connection_exhaustion.py --scheduler  # Scheduler leak (60s)
python test_connection_exhaustion.py --stale      # Stale connections (250s!)
python test_connection_exhaustion.py --slow       # Long-running queries (15s)

# HTTP API tests (requires TOKEN in script)
python test_connection_exhaustion.py --http
```

## Tests Implemented

### Test 6: Scheduler Leak Simulation ⏱️ 60s
**What it tests:** Background task holds connection indefinitely (like `main.py` scheduler)

**Pattern:**
- 1 thread holds connection for 60s (simulates scheduler)
- 10 threads request connections

**Expected:** All 10 succeed if requests are fast (slot recycling)
**Production issue:** If scheduler holds connection AND 10+ concurrent users arrive → 1 user times out

**Status:** ✅ Implemented & tested

---

### Test 7: Stale Connection Resurrection ⏱️ 250s
**What it tests:** `pool_pre_ping=True` and `pool_recycle=240s` work correctly

**Pattern:**
- Hold 5 connections for 250s (exceeds recycle time)
- Try to use them again

**Expected:** All succeed (pre-ping recycles stale connections)
**Production issue:** `SSL connection has been closed unexpectedly`

**Status:** ✅ Implemented (run manually with `--stale`)

---

### Test 8: UoW Pattern Abuse ⏱️ 10s
**What it tests:** The problematic `dependencies.py` DI pattern

**Pattern:**
```python
with StudentUnitOfWork() as uow:     # Session opened
    svc = StudentService(uow)
    return svc                        # Session closed here!
svc.get_student()                     # Uses closed session!
```

**Expected:** Session detected as closed/None
**Production issue:** Services fail randomly when using "dead" UoW

**Status:** ✅ Implemented & tested - **CONFIRMS ISSUE EXISTS**

**Result:**
```
🚨 UoW PATTERN ISSUE CONFIRMED!
   Services are being returned with closed sessions
   
💡 Fix: Create services WITHIN the 'with' block:
       with StudentUnitOfWork() as uow:
           svc = StudentService(uow)
           result = svc.get_student()  # Use while session open
           return result               # Return data, not service
```

---

### Test 9: Long-Running Transaction Hold ⏱️ 15s
**What it tests:** Slow queries blocking fast queries

**Pattern:**
- 5 slow queries (10s each via `pg_sleep`)
- 10 fast queries (immediate)

**Expected:** Fast queries queue, some timeout if slow queries hog pool
**Production issue:** Report generation blocks API requests

**Status:** ✅ Implemented (run with `--slow`)

---

## Original Tests (Still Available)

| Test | Flag | Time | Description |
|------|------|------|-------------|
| Basic pool exhaustion | `--direct` | 10s | 12 threads, 10 pool slots |
| HTTP sequential | `--http` | 10s | Sequential API requests |
| HTTP concurrent | `--http` | 15s | 12/20 concurrent requests |
| HTTP slow buildup | `--http` | 25s | 15 requests with delays |

## CI/CD Integration

Add to your test pipeline:

```yaml
# .github/workflows/test.yml
- name: Connection Pool Tests
  run: |
    python test_connection_exhaustion.py --uow
    python test_connection_exhaustion.py --direct
    # --scheduler and --slow for nightly builds
```

## Key Findings

| Test | Finding | Action Needed |
|------|---------|---------------|
| UoW Pattern | ✅ **CONFIRMED BUG** | Refactor 11 DI factories in `dependencies.py` |
| Scheduler | ⚠️ Risk present | Fix `main.py` to use `with get_session()` per report |
| Stale Conn | TBD | Run `--stale` test overnight |
| Pool Capacity | TBD | Run `--slow` test during peak hours |

## Next Steps

1. **Immediate:** Run `python test_connection_exhaustion.py --uow` to confirm pattern issue
2. **Fix:** Refactor DI factories to return data, not service-with-closed-UoW
3. **Monitor:** Run `--scheduler` test with slower user requests to trigger timeout
4. **Nightly:** Run `--stale` test to verify `pool_recycle` works
