# Quickstart: Employee Creation Endpoint Audit & Fixes

**Feature**: 039-audit-employee-creation | **Date**: 2026-08-23

## Prerequisites

- Python 3.10+ venv activated at repo root.
- Dependencies installed: `pip install -e .`
- A reachable PostgreSQL database (local or test instance). Tests auto-load `.env.test`
  via `app/core/config.py:106` — no manual env switching needed under pytest.

## Run the audit regression suite

```powershell
# Existing HR coverage must stay green
pytest tests/test_hr.py tests/test_hr_full.py -v

# New per-defect regression checks (created during implementation; IDs mirror findings.md)
pytest tests/test_hr_audit_regressions.py -v
```

Auth in tests needs no real Supabase JWTs: use the `override_auth` fixture paired with
`mock_admin_headers` / `system_admin_headers` (HS256 mocks from
`tests/utils/jwt_mocks.py`). Only if a test must exercise real Supabase validation,
regenerate a token: `python scripts/get_test_jwt.py` (expires ~1h) and update
`admin_token` in `tests/conftest.py`.

## Manual verification flow (running server)

Start dev server: `python run_api.py`. With an admin JWT in `$headers`:

```powershell
# 1. Create employee — duplicate submission twice; second call must name EVERY colliding field
$body = @{ full_name="Test Employee"; phone="+201000000001"; national_id="12345678901234";
           university="Cairo"; major="CS"; employment_type="contract"; contract_percentage=50 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/hr/employees" -Headers $headers -Body $body -ContentType "application/json"

# 2. Provision account — invalid email / short password must be rejected BEFORE any remote call
# 3. Provision account — success, then repeat → "already has an account"
# 4. Deactivate employee (is_active=false) → GET /api/v1/hr/staff-accounts shows account is_active=false
# 5. GET /api/v1/hr/staff-accounts → every entry shows complete fields (no null placeholders)
```

Expected outcomes per step are specified in `contracts/hr-staff-api.md`.

## Verifying the zero-partial-state guarantee (F-02/F-03/F-04)

Automated coverage (tests/test_hr_audit_regressions.py) maps every manual step:
duplicates/race → `TestF01*`/`TestF04*`; credential rejection → `TestF08*`;
forced remote failure & compensation → `TestF02*`/`TestF03*`; deactivation
linkage → `TestF07*`; complete overview → `TestF06*`. The live-server walk below
requires reachable Supabase credentials; run it when credentials are available.

- Simulated remote failure: run with an unreachable `SUPABASE_URL`; create-account must
  return the clear "provisioning unavailable — nothing created" failure (409 envelope),
  and no local User row may appear afterward.
- Race duplicates: two rapid identical creates must yield one 201 and one 409 naming the
  conflicting field(s) — never a 500.

## Definition of Done for this feature

1. All ERROR-tier findings in `findings.md` fixed with regression tests passing (SC-006).
2. Full HR suite green: `pytest tests/test_hr.py tests/test_hr_full.py tests/test_hr_audit_regressions.py -v`.
3. Findings catalog complete: every defect has severity, evidence, repro steps, status.
