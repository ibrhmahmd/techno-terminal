"""
Connection pool exhaustion load script (manual, not a pytest suite).
Targets localhost by default and refuses non-local hosts unless --allow-remote.
Env: BASE_URL, TOKEN. Flags: --http --direct --scheduler --uow --stale --slow --all-direct --allow-remote.
"""

import asyncio
import os
import time
import sys
from urllib.parse import urlparse

# Keep app settings off .env (production) before any `app.*` import.
os.environ.setdefault("TESTING", "true")

# Ensure project root is importable when run as a plain script.
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import httpx

# Configuration via environment
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000/api/v1")
TOKEN = os.environ.get("TOKEN", "")

# Test endpoints that hit the database
ENDPOINTS = [
    "/hr/staff-accounts",
    "/crm/students",
    "/academics/groups",
    "/analytics/dashboard",
]


async def make_request(client: httpx.AsyncClient, endpoint: str, delay: float = 0):
    """Make a single request with optional delay to simulate slow query."""
    await asyncio.sleep(delay)  # Stagger requests
    
    headers = {"Authorization": f"Bearer {TOKEN}"}
    url = f"{BASE_URL}{endpoint}"
    
    try:
        start = time.time()
        response = await client.get(url, headers=headers, timeout=30)
        elapsed = time.time() - start
        
        status = response.status_code
        if status == 200:
            return f"✅ {endpoint}: {status} ({elapsed:.2f}s)"
        elif status == 500:
            return f"❌ {endpoint}: {status} ({elapsed:.2f}s) - SERVER ERROR"
        elif status in (401, 403):
            return f"⚠️  {endpoint}: {status} - AUTH ERROR (check token)"
        else:
            return f"⚠️  {endpoint}: {status} ({elapsed:.2f}s)"
    except httpx.TimeoutException:
        return f"⏱️  {endpoint}: TIMEOUT (30s) - Pool exhausted!"
    except Exception as e:
        return f"💥 {endpoint}: {type(e).__name__}: {str(e)[:50]}"


async def run_concurrent_requests(num_concurrent: int, delay_per_request: float = 0):
    """Fire N concurrent requests to stress the pool."""
    print(f"\n🔥 Testing {num_concurrent} concurrent requests...")
    print(f"   Pool size: 5 + 5 overflow = 10 max")
    print(f"   Expected: Errors when concurrent > 10\n")
    
    async with httpx.AsyncClient() as client:
        tasks = []
        
        # Create concurrent requests
        for i in range(num_concurrent):
            endpoint = ENDPOINTS[i % len(ENDPOINTS)]
            delay = delay_per_request * (i % 5)  # Stagger by position
            task = make_request(client, endpoint, delay)
            tasks.append(task)
        
        start = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start
        
        # Report results
        success_count = sum(1 for r in results if isinstance(r, str) and "✅" in r)
        error_count = num_concurrent - success_count
        timeout_count = sum(1 for r in results if isinstance(r, str) and "TIMEOUT" in r)
        server_error_count = sum(1 for r in results if isinstance(r, str) and "SERVER ERROR" in r)
        
        print(f"\n📊 Results ({elapsed:.2f}s total):")
        print(f"   Success:   {success_count}/{num_concurrent}")
        print(f"   Errors:    {error_count}/{num_concurrent}")
        print(f"   Timeouts:  {timeout_count}")
        print(f"   500s:      {server_error_count}")
        
        if timeout_count > 0 or server_error_count > 0:
            print(f"\n🚨 Pool exhaustion detected!")
        
        # Show first few results
        for i, result in enumerate(results[:5]):
            print(f"   #{i+1}: {result}")
        if len(results) > 5:
            print(f"   ... and {len(results) - 5} more")


async def run_sequential_vs_concurrent():
    """Compare sequential vs concurrent performance."""
    print("\n" + "="*60)
    print("TEST 1: Sequential Requests (should always work)")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        for endpoint in ENDPOINTS[:3]:
            result = await make_request(client, endpoint)
            print(f"   {result}")
    
    print("\n" + "="*60)
    print("TEST 2: 12 Concurrent Requests (exceeds pool of 10)")
    print("="*60)
    await run_concurrent_requests(12)
    
    print("\n" + "="*60)
    print("TEST 3: 20 Concurrent Requests (heavy overload)")
    print("="*60)
    await run_concurrent_requests(20)


async def run_slow_query_buildup():
    """Simulate slow queries that hold connections."""
    print("\n" + "="*60)
    print("TEST 4: Slow Query Buildup (connections held > 30s)")
    print("="*60)
    print("   Sending 15 requests with 5s stagger delays...")
    print("   This simulates long-running database queries")
    
    await run_concurrent_requests(15, delay_per_request=5)


def direct_sqlalchemy_test():
    """Test raw SQLAlchemy connection exhaustion (no HTTP)."""
    print("\n" + "="*60)
    print("TEST 5: Direct SQLAlchemy Pool Exhaustion")
    print("="*60)
    
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from app.db.connection import get_engine, get_session
    from sqlalchemy import text
    
    def hold_connection(seconds: int, name: str):
        """Hold a connection open for N seconds."""
        try:
            with get_session() as session:
                # Execute a query to checkout a connection
                result = session.exec(text("SELECT pg_backend_pid(), :name as name").bindparams(name=name)).first()
                pid = result[0] if result else "?"
                print(f"   🔌 {name}: Got connection PID {pid}, holding for {seconds}s...")
                
                # Keep connection open
                time.sleep(seconds)
                
                # Another query to verify connection still works
                session.exec(text("SELECT 1"))
                return f"✅ {name}: Released connection (held {seconds}s)"
        except Exception as e:
            return f"❌ {name}: {type(e).__name__}: {str(e)[:80]}"
    
    print(f"   Pool status: size=5, overflow=5, max=10")
    print(f"   Launching 12 threads to hold connections...")
    
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = []
        for i in range(12):
            future = executor.submit(hold_connection, 5, f"Thread-{i+1}")
            futures.append(future)
            time.sleep(0.1)  # Slight stagger
        
        print(f"   ⏳ Waiting for results...\n")
        
        for future in as_completed(futures):
            print(f"   {future.result()}")


def check_scheduler_leak():
    """
    TEST 6: Scheduler Leak Simulation
    
    Simulates the production issue where the background scheduler in main.py
    holds one connection indefinitely, reducing effective pool size by 1.
    
    Pattern: 1 long-held connection + 10 concurrent requests = pool exhaustion
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from app.db.connection import get_session
    from sqlalchemy import text
    
    print("\n" + "="*60)
    print("TEST 6: Scheduler Leak Simulation (60s)")
    print("="*60)
    print("   1 thread holds connection for 60s (simulates scheduler)")
    print("   10 threads try to get connections immediately")
    print("   Expected: 1 timeout (pool effectively 9, not 10)")
    
    scheduler_connection = [None]  # Shared state to track scheduler
    stop_scheduler = [False]
    
    def scheduler_simulation():
        """Holds one connection open like the scheduler does."""
        with get_session() as session:
            result = session.exec(text("SELECT pg_backend_pid()")).first()
            pid = result[0] if result else "?"
            scheduler_connection[0] = pid
            print(f"   🔒 Scheduler: Holding connection PID {pid} for 60s...")
            
            # Hold for 60 seconds (simulates long-running scheduler)
            for i in range(60):
                if stop_scheduler[0]:
                    break
                time.sleep(1)
            print(f"   🔓 Scheduler: Released connection PID {pid}")
            return f"Scheduler held PID {pid} for 60s"
    
    def user_request(name: str):
        """Simulates a user API request needing a connection."""
        try:
            with get_session() as session:
                result = session.exec(text("SELECT pg_backend_pid(), :name as name").bindparams(name=name)).first()
                pid = result[0] if result else "?"
                print(f"   ✅ {name}: Got connection PID {pid}")
                time.sleep(0.5)  # Quick query
                return f"✅ {name}: Success (PID {pid})"
        except Exception as e:
            return f"❌ {name}: {type(e).__name__}: {str(e)[:50]}"
    
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=11) as executor:
        # Start scheduler first
        scheduler_future = executor.submit(scheduler_simulation)
        time.sleep(0.5)  # Let scheduler get connection first
        
        # Now fire 10 "user requests"
        user_futures = [executor.submit(user_request, f"User-{i+1}") for i in range(10)]
        
        # Wait for user requests to complete (or timeout)
        user_results = []
        for future in as_completed(user_futures, timeout=35):
            user_results.append(future.result())
            print(f"   {future.result()}")
        
        # Stop scheduler
        stop_scheduler[0] = True
        scheduler_result = scheduler_future.result()
    
    elapsed = time.time() - start
    
    # Report results
    success_count = sum(1 for r in user_results if "✅" in r)
    error_count = len(user_results) - success_count
    timeout_count = sum(1 for r in user_results if "TimeoutError" in r or "QueuePool" in r)
    
    print(f"\n📊 Results ({elapsed:.1f}s):")
    print(f"   Scheduler held: 1 connection (PID {scheduler_connection[0]})")
    print(f"   User requests:  {success_count}/10 succeeded")
    print(f"   Failures:       {error_count}/10")
    print(f"   Timeouts:       {timeout_count}")
    
    if timeout_count > 0:
        print(f"\n🚨 SCHEDULER LEAK DETECTED!")
        print(f"   1 background connection reduced effective pool from 10 to 9")
    else:
        print(f"\n✅ Pool handled scheduler leak (requests completed quickly)")


def check_stale_connection_resurrection():
    """
    TEST 7: Stale Connection Resurrection
    
    Tests pool_pre_ping=True by holding connections past pool_recycle=240s.
    SQLAlchemy should transparently recycle stale connections.
    
    Production issue: Supabase closes idle connections after ~300s.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from app.db.connection import get_session
    from sqlalchemy import text
    
    print("\n" + "="*60)
    print("TEST 7: Stale Connection Resurrection (250s)")
    print("="*60)
    print(f"   Holding 5 connections for 250s (exceeds pool_recycle=240s)")
    print(f"   Then executing queries to test pre-ping recycling")
    print(f"   Production issue: 'SSL connection has been closed unexpectedly'")
    
    def hold_then_query(name: str, hold_seconds: int):
        """Hold connection, then try to use it (may be stale)."""
        try:
            with get_session() as session:
                # Initial query
                result = session.exec(text("SELECT pg_backend_pid(), :name as name").bindparams(name=name)).first()
                pid = result[0] if result else "?"
                print(f"   🔌 {name}: Got PID {pid}, holding {hold_seconds}s...")
                
                # Hold (connection may go stale)
                time.sleep(hold_seconds)
                
                # Try to use again (triggers pre-ping if stale)
                result2 = session.exec(text("SELECT 1 as test")).first()
                print(f"   ✅ {name}: Query succeeded after {hold_seconds}s (pre-ping worked)")
                return f"✅ {name}: Survived stale period"
        except Exception as e:
            error_msg = str(e)
            if "SSL connection has been closed" in error_msg:
                print(f"   ❌ {name}: SSL connection closed (pre-ping failed!)")
                return f"❌ {name}: SSL closed - pre-ping failed"
            elif "QueuePool" in error_msg:
                print(f"   ⏱️  {name}: Pool timeout")
                return f"⏱️  {name}: Pool timeout"
            else:
                print(f"   💥 {name}: {type(e).__name__}: {error_msg[:50]}")
                return f"💥 {name}: {type(e).__name__}"
    
    print(f"\n⏳ Phase 1: Holding 5 connections for 250s...")
    print(f"   (This tests if pool_recycle=240s works correctly)")
    
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(hold_then_query, f"Conn-{i+1}", 250)
            for i in range(5)
        ]
        
        results = []
        for future in as_completed(futures):
            results.append(future.result())
    
    elapsed = time.time() - start
    
    # Report results
    success_count = sum(1 for r in results if "✅" in r)
    ssl_errors = sum(1 for r in results if "SSL closed" in r)
    other_errors = len(results) - success_count - ssl_errors
    
    print(f"\n📊 Results ({elapsed:.1f}s):")
    print(f"   Successful:  {success_count}/5")
    print(f"   SSL errors:  {ssl_errors}/5 (pre-ping failed)")
    print(f"   Other errors: {other_errors}/5")
    
    if ssl_errors > 0:
        print(f"\n🚨 PRE-PING NOT WORKING!")
        print(f"   Connections went stale and weren't recycled properly")
        print(f"   This causes 'SSL connection has been closed unexpectedly' in production")
    elif success_count == 5:
        print(f"\n✅ All connections survived stale period")
        print(f"   pool_pre_ping=True and pool_recycle=240s working correctly")


def check_uow_pattern_abuse():
    """
    TEST 8: UoW Pattern Abuse
    
    Simulates the problematic pattern in dependencies.py where:
    1. UoW is created in a 'with' block
    2. Service is returned OUTSIDE the 'with' block
    3. UoW session is already closed when service tries to use it
    
    This is the root cause of many production issues.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from app.db.connection import get_session
    from sqlalchemy import text
    from typing import Optional
    from sqlmodel import Session
    
    # Minimal mock UoW to avoid circular imports
    class MockUnitOfWork:
        """Simplified UoW that demonstrates the same pattern as StudentUnitOfWork."""
        def __init__(self, session: Optional[Session] = None) -> None:
            self._session = session
            self._own_session = session is None
        
        def __enter__(self):
            if self._own_session:
                self._session_cm = get_session()
                self._session = self._session_cm.__enter__()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self._own_session:
                self._session_cm.__exit__(exc_type, exc_val, exc_tb)
                self._session = None  # Simulate session being closed
    
    class MockService:
        """Service that holds UoW reference - same pattern as real services."""
        def __init__(self, uow):
            self._uow = uow
    
    print("\n" + "="*60)
    print("TEST 8: UoW Pattern Abuse (dependencies.py anti-pattern)")
    print("="*60)
    print("   Simulates: with MockUnitOfWork() as uow:")
    print("                  return MockService(uow)  # uow exits here!")
    print("              service._uow._session.exec()  # session closed!")
    
    def get_service_with_closed_uow():
        """Mimics get_student_crud_service() pattern."""
        with MockUnitOfWork() as uow:
            svc = MockService(uow)
            # uow exits here, session closed!
            return svc  # Service holds reference to closed UoW
    
    def try_use_closed_service(name: str):
        """Try to use service after its UoW was closed."""
        try:
            # Get service (UoW already closed)
            svc = get_service_with_closed_uow()
            print(f"   🔍 {name}: Got service, attempting to use closed UoW...")
            
            # Try to use the session (this will fail because session was closed by __exit__)
            if svc._uow._session is None:
                print(f"   ✅ {name}: Session is None (correctly closed by UoW)")
                return f"✅ {name}: Session correctly closed"
            
            # If session exists, try to query (should fail)
            result = svc._uow._session.exec(text("SELECT 1")).first()
            
            print(f"   ⚠️  {name}: Query succeeded (unexpected - session wasn't closed?)")
            return f"⚠️  {name}: Query succeeded"
        except Exception as e:
            error_msg = str(e)
            if "closed" in error_msg.lower():
                print(f"   ✅ {name}: Detected closed session - {type(e).__name__}")
                return f"✅ {name}: Closed session detected (expected)"
            elif "SSL" in error_msg:
                print(f"   ❌ {name}: SSL error - {error_msg[:50]}")
                return f"❌ {name}: SSL error"
            else:
                print(f"   💥 {name}: {type(e).__name__}: {error_msg[:50]}")
                return f"💥 {name}: {type(e).__name__}"
    
    print(f"\n🧪 Testing UoW pattern with 5 concurrent services...")
    
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(try_use_closed_service, f"Service-{i+1}")
            for i in range(5)
        ]
        
        results = []
        for future in as_completed(futures):
            results.append(future.result())
            print(f"   {future.result()}")
    
    elapsed = time.time() - start
    
    # Report results
    closed_detected = sum(1 for r in results if "closed" in r.lower() or "correctly closed" in r)
    unexpected_success = sum(1 for r in results if "unexpected" in r.lower() or "succeeded" in r.lower())
    errors = len(results) - closed_detected - unexpected_success
    
    print(f"\n📊 Results ({elapsed:.2f}s):")
    print(f"   Closed session detected: {closed_detected}/5")
    print(f"   Unexpected success:      {unexpected_success}/5")
    print(f"   Other errors:            {errors}/5")
    
    if closed_detected > 0:
        print(f"\n🚨 UoW PATTERN ISSUE CONFIRMED!")
        print(f"   Services are being returned with closed sessions")
        print(f"   This causes failures when services try to use the database")
        print(f"\n💡 Fix: Create services WITHIN the 'with' block:")
        print(f"       with StudentUnitOfWork() as uow:")
        print(f"           svc = StudentService(uow)")
        print(f"           return svc.get_student()  # Use while session open")
    elif unexpected_success == 5:
        print(f"\n⚠️  UoW sessions weren't closed (check UoW __exit__ implementation)")


def check_long_running_transaction_hold():
    """
    TEST 9: Long-Running Transaction Hold
    
    Tests capacity planning: slow queries consume pool slots,
    causing fast queries to queue or timeout.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from app.db.connection import get_session
    from sqlalchemy import text
    
    print("\n" + "="*60)
    print("TEST 9: Long-Running Transaction Hold")
    print("="*60)
    print("   5 slow queries (pg_sleep 10s) + 10 fast queries")
    print("   Expected: Fast queries queue, some timeout")
    
    def slow_query(name: str):
        """Simulates slow report query."""
        try:
            with get_session() as session:
                pid = session.exec(text("SELECT pg_backend_pid()")).first()[0]
                print(f"   🐌 {name}: Started (PID {pid}), sleeping 10s...")
                session.exec(text("SELECT pg_sleep(10)"))
                print(f"   ✅ {name}: Completed after 10s")
                return f"✅ {name}: Slow query completed"
        except Exception as e:
            return f"❌ {name}: {type(e).__name__}: {str(e)[:40]}"
    
    def fast_query(name: str):
        """Simulates quick API request."""
        try:
            start = time.time()
            with get_session() as session:
                pid = session.exec(text("SELECT pg_backend_pid()")).first()[0]
                result = session.exec(text("SELECT 1 as data")).first()
                elapsed = time.time() - start
                print(f"   ⚡ {name}: Completed in {elapsed:.2f}s (PID {pid})")
                if elapsed > 5:
                    return f"⏱️  {name}: Slow ({elapsed:.1f}s) - was queued"
                return f"✅ {name}: Fast ({elapsed:.2f}s)"
        except Exception as e:
            return f"❌ {name}: {type(e).__name__}: {str(e)[:40]}"
    
    print(f"\n⏳ Starting 5 slow + 10 fast queries...")
    
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=15) as executor:
        # Start slow queries first
        slow_futures = [executor.submit(slow_query, f"Slow-{i+1}") for i in range(5)]
        time.sleep(0.5)
        
        # Immediately start fast queries
        fast_futures = [executor.submit(fast_query, f"Fast-{i+1}") for i in range(10)]
        
        # Collect results
        all_results = []
        for future in as_completed(slow_futures + fast_futures):
            result = future.result()
            all_results.append(result)
    
    elapsed = time.time() - start
    
    # Categorize results
    slow_completed = sum(1 for r in all_results if "Slow" in r and "✅" in r)
    fast_fast = sum(1 for r in all_results if "Fast" in r and "Fast" in r)
    fast_slow = sum(1 for r in all_results if "Fast" in r and "Slow" in r)
    fast_failed = sum(1 for r in all_results if "Fast" in r and ("❌" in r or "⏱️" in r))
    
    print(f"\n📊 Results ({elapsed:.1f}s):")
    print(f"   Slow queries:     {slow_completed}/5 completed")
    print(f"   Fast queries:")
    print(f"     - Actually fast: {fast_fast}/10 (< 1s)")
    print(f"     - Queued slow:   {fast_slow}/10 (waited for slot)")
    print(f"     - Failed:        {fast_failed}/10")
    
    if fast_slow + fast_failed > 3:
        print(f"\n🚨 POOL CAPACITY ISSUE!")
        print(f"   Slow queries are blocking fast queries")
        print(f"   Consider: separate pools for reports vs API, or increase pool size")
    else:
        print(f"\n✅ Pool handled mixed workload well")


LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
HTTP_MODES = {"--http"}
DIRECT_MODES = {"--direct", "--scheduler", "--stale", "--uow", "--slow", "--all-direct"}
SCRIPT = "python scripts/load/connection_exhaustion.py"


def _is_local_host(host: str | None) -> bool:
    return host in LOCAL_HOSTS


def _guard_http_target(allow_remote: bool) -> None:
    """Refuse non-local BASE_URL hosts unless --allow-remote is set."""
    host = urlparse(BASE_URL).hostname
    if allow_remote or _is_local_host(host):
        return
    print(
        f"\n❌ Refusing to target non-local host '{host}'.\n"
        f"   BASE_URL={BASE_URL}\n"
        f"   Pass --allow-remote to override.",
        file=sys.stderr,
    )
    sys.exit(2)


def _guard_db_target(allow_remote: bool) -> None:
    """Refuse non-local database hosts unless --allow-remote is set."""
    if allow_remote:
        return
    from app.core.config import settings

    host = urlparse(settings.database_url).hostname
    if _is_local_host(host):
        return
    print(
        f"\n❌ Refusing to target non-local database host '{host}'.\n"
        f"   DATABASE_URL points at a remote server; pass --allow-remote to override.",
        file=sys.stderr,
    )
    sys.exit(2)


def _print_usage() -> None:
    print("\n📖 Usage:")
    print(f"   {SCRIPT} [OPTION] [--allow-remote]")
    print("\nOptions:")
    print("   --direct        Basic pool exhaustion test")
    print("   --scheduler     Test 6: Scheduler leak simulation (60s)")
    print("   --stale         Test 7: Stale connection test (250s!)")
    print("   --uow           Test 8: UoW pattern abuse test")
    print("   --slow          Test 9: Long-running query test")
    print("   --all-direct    Run all SQLAlchemy tests (except --stale)")
    print("   --http          HTTP API tests only (needs BASE_URL + TOKEN)")
    print("   --allow-remote  Permit non-localhost targets (default: refuse)")
    print("   --help          Show this help")
    print("\nEnv:")
    print("   BASE_URL        API base URL (default http://localhost:8000/api/v1)")
    print("   TOKEN           Supabase JWT for --http modes (no default)")


def _run_http() -> None:
    if not TOKEN:
        print(
            "\n❌ --http requires a TOKEN environment variable (Supabase JWT).\n"
            "   Get one by logging in via POST /auth/login.",
            file=sys.stderr,
        )
        sys.exit(2)
    asyncio.run(run_sequential_vs_concurrent())
    asyncio.run(run_slow_query_buildup())


def main() -> int:
    args = sys.argv[1:]
    allow_remote = "--allow-remote" in args
    modes = [a for a in args if a != "--allow-remote"]

    print("="*60)
    print("CONNECTION POOL EXHAUSTION TEST SUITE")
    print("="*60)

    if not modes:
        print("\n⚠️  No test specified. Use --help for options.")
        _print_usage()
        return 0

    if len(modes) != 1:
        print(f"\n❌ Expected exactly one mode, got: {' '.join(modes)}")
        _print_usage()
        return 2

    mode = modes[0]

    if mode in ("--help", "-h"):
        _print_usage()
        return 0

    if mode not in HTTP_MODES | DIRECT_MODES:
        print(f"\n❌ Unknown argument: {mode}")
        _print_usage()
        return 2

    if mode in HTTP_MODES:
        _guard_http_target(allow_remote)
        print(f"\nTarget: {BASE_URL}")
        _run_http()
        return 0

    _guard_db_target(allow_remote)

    if mode == "--direct":
        direct_sqlalchemy_test()
    elif mode == "--scheduler":
        check_scheduler_leak()
    elif mode == "--stale":
        check_stale_connection_resurrection()
    elif mode == "--uow":
        check_uow_pattern_abuse()
    elif mode == "--slow":
        check_long_running_transaction_hold()
    elif mode == "--all-direct":
        print("\n🧪 Running all direct SQLAlchemy tests...")
        direct_sqlalchemy_test()
        check_scheduler_leak()
        check_uow_pattern_abuse()
        check_long_running_transaction_hold()
        print(f"\n⚠️  Skipping --stale test (250s). Run manually with: {SCRIPT} --stale")
    return 0


if __name__ == "__main__":
    sys.exit(main())
