"""
Connection Pool Exhaustion Test Script

This script reproduces the QueuePool limit error by creating
concurrent database requests that exceed your pool capacity.

Usage:
    python test_connection_exhaustion.py

Requires:
    pip install httpx
"""

import asyncio
import time
import sys

import httpx

# Configuration - adjust to your setup
BASE_URL = "https://techno-terminal-5c255cfe.fastapicloud.dev/api/v1"  # Or your deployed URL
TOKEN = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjRmN2U4ODliLWNkNWItNDZlOS1hZDc1LWI4ZDMyY2I3YzI4NCIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3NyYnBwa2N2cmdpb25laXRrdGRqLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJjY2JjYTA2My01Y2UzLTRiNGYtOTdhMy03OTE1MTU0ZWRiOTIiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzc4MzIwMDU1LCJpYXQiOjE3NzgzMTY0NTUsImVtYWlsIjoiYWRtaW4ubmV0QHRlY2huby5jcm0iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsX3ZlcmlmaWVkIjp0cnVlfSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc3ODMxNjQ1NX1dLCJzZXNzaW9uX2lkIjoiMTY0MzRmNTktYjMxMy00ZmVmLTg2ZjAtOWUxM2EwNmRkNDQwIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.FL1ThYuK_jdjGemXyeXDWCoShhumKr3w5w9VTqzeUn4LQ8NNAWSXrArfvluw9vltbeVeGAmEvh7uQFrC_akbBg"  # Get from login response

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


async def test_concurrent_requests(num_concurrent: int, delay_per_request: float = 0):
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


async def test_sequential_vs_concurrent():
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
    await test_concurrent_requests(12)
    
    print("\n" + "="*60)
    print("TEST 3: 20 Concurrent Requests (heavy overload)")
    print("="*60)
    await test_concurrent_requests(20)


async def test_slow_query_buildup():
    """Simulate slow queries that hold connections."""
    print("\n" + "="*60)
    print("TEST 4: Slow Query Buildup (connections held > 30s)")
    print("="*60)
    print("   Sending 15 requests with 5s stagger delays...")
    print("   This simulates long-running database queries")
    
    await test_concurrent_requests(15, delay_per_request=5)


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


def test_scheduler_leak_simulation():
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


def test_stale_connection_resurrection():
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


def test_uow_pattern_abuse():
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


def test_long_running_transaction_hold():
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


def main():
    print("="*60)
    print("CONNECTION POOL EXHAUSTION TEST SUITE")
    print("="*60)
    print(f"\nTarget: {BASE_URL}")
    print(f"Pool config: size=5, max_overflow=5, timeout=30s")
    
    # Parse arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == "--direct":
            # Basic pool exhaustion test
            direct_sqlalchemy_test()
        elif arg == "--scheduler":
            # Test 6: Scheduler leak simulation
            test_scheduler_leak_simulation()
        elif arg == "--stale":
            # Test 7: Stale connection resurrection (250s!)
            test_stale_connection_resurrection()
        elif arg == "--uow":
            # Test 8: UoW pattern abuse
            test_uow_pattern_abuse()
        elif arg == "--slow":
            # Test 9: Long-running transaction hold
            test_long_running_transaction_hold()
        elif arg == "--all-direct":
            # Run all SQLAlchemy tests
            print("\n🧪 Running all direct SQLAlchemy tests...")
            direct_sqlalchemy_test()
            test_scheduler_leak_simulation()
            test_uow_pattern_abuse()
            test_long_running_transaction_hold()
            print("\n⚠️  Skipping --stale test (250s). Run manually with: python test_connection_exhaustion.py --stale")
        elif arg == "--http":
            # HTTP API tests only
            print("\n⚠️  Make sure to set TOKEN in this script!")
            print("   Get a token by logging in via POST /auth/login")
            asyncio.run(test_sequential_vs_concurrent())
            asyncio.run(test_slow_query_buildup())
        elif arg in ("--help", "-h"):
            print("\n📖 Usage:")
            print("   python test_connection_exhaustion.py [OPTION]")
            print("\nOptions:")
            print("   --direct        Basic pool exhaustion test")
            print("   --scheduler     Test 6: Scheduler leak simulation (60s)")
            print("   --stale         Test 7: Stale connection test (250s!)")
            print("   --uow           Test 8: UoW pattern abuse test")
            print("   --slow          Test 9: Long-running query test")
            print("   --all-direct    Run all SQLAlchemy tests (except --stale)")
            print("   --http          HTTP API tests only")
            print("   --help          Show this help")
        else:
            print(f"\n❌ Unknown argument: {arg}")
            print("   Use --help for usage information")
    else:
        # Default: Show help and basic info
        print("\n⚠️  No test specified. Use --help for options.")
        print("\nQuick start:")
        print("   python test_connection_exhaustion.py --direct     # Basic test")
        print("   python test_connection_exhaustion.py --scheduler  # Scheduler leak")
        print("   python test_connection_exhaustion.py --uow        # UoW pattern")
        print("\n� Recommended for production debugging:")
        print("   python test_connection_exhaustion.py --all-direct")


if __name__ == "__main__":
    main()
