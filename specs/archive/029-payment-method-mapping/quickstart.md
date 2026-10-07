# Quickstart: Payment Method Mapping — Reproduction & Verification

## Prerequisites

- Python 3.10+ with virtual environment activated
- Dependencies installed: `pip install -e .`
- Database schema applied: `psql "$DATABASE_URL" -f db/schema.sql`
- Test JWT or mock tokens

## Running Tests

```bash
# Run the payment method mapping tests
pytest tests/test_finance.py -v -k "payment_method"

# Run all finance tests
pytest tests/test_finance.py -v
```

## Manual Reproduction via cURL

```bash
# Test 1: icon name "bolt" → should normalize to "instapay"
curl -X POST http://localhost:8000/api/v1/finance/receipts \
  -H "Authorization: Bearer $(python scripts/get_test_jwt.py)" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "bolt",
    "payer_name": "Test",
    "allow_credit": true,
    "lines": [{"student_id": 1, "amount": 100.0, "payment_type": "course_level"}]
  }'

# Test 2: display label "E-Wallet" → should normalize to "ewallet"
curl -X POST http://localhost:8000/api/v1/finance/receipts \
  -H "Authorization: Bearer $(python scripts/get_test_jwt.py)" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "E-Wallet",
    "payer_name": "Test",
    "allow_credit": true,
    "lines": [{"student_id": 2, "amount": 200.0, "payment_type": "course_level"}]
  }'

# Test 3: lowercase "account_balance_wallet" → should normalize to "ewallet"
curl -X POST http://localhost:8000/api/v1/finance/receipts \
  -H "Authorization: Bearer $(python scripts/get_test_jwt.py)" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "account_balance_wallet",
    "payer_name": "Test",
    "allow_credit": true,
    "lines": [{"student_id": 3, "amount": 150.0, "payment_type": "course_level"}]
  }'

# Test 4: invalid method → 422
curl -X POST http://localhost:8000/api/v1/finance/receipts \
  -H "Authorization: Bearer $(python scripts/get_test_jwt.py)" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "cryptocurrency",
    "payer_name": "Test",
    "allow_credit": true,
    "lines": [{"student_id": 4, "amount": 100.0, "payment_type": "course_level"}]
  }'
```

## Expected Behavior

| Input | Status | Stored As |
|-------|--------|-----------|
| `"cash"` | 201 | `"cash"` |
| `"bolt"` | 201 | `"instapay"` |
| `"instaPay"` | 201 | `"instapay"` |
| `"E-Wallet"` | 201 | `"ewallet"` |
| `"account_balance_wallet"` | 201 | `"ewallet"` |
| `"more_horiz"` | 201 | `"other"` |
| `"card"` | 201 | `"card"` |
| `"transfer"` | 201 | `"transfer"` |
| `"online"` | 201 | `"online"` |
| `"cryptocurrency"` | 422 | — |
