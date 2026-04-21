# Testing Guide - SokoYetu

## Overview

This document outlines the comprehensive testing strategy for the SokoYetu hyperlocal delivery platform. The system includes unit tests, integration tests, and end-to-end tests covering authentication, payments, security, and order management.

## Test Structure

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Fixtures and test database setup
│   ├── test_auth.py          # Authentication & authorization
│   ├── test_payment.py       # Payment & escrow logic
│   ├── test_security.py      # GPS, QR codes, handshakes
│   └── test_orders.py        # Order management APIs
```

## Prerequisites

Before running tests, ensure you have:
- Python 3.10+
- Virtual environment activated
- All dependencies installed from `requirements.txt`
- pytest and pytest-cov installed

## Environment Setup

### 1. Windows Setup

```bash
# Open PowerShell as Administrator
cd e:\sokoyetu

# Run the setup script
.\setup-backend.bat

# Verify Python virtual environment
venv\Scripts\python --version

# Verify pytest installed
venv\Scripts\pytest --version
```

### 2. Linux/Mac Setup

```bash
cd /path/to/sokoyetu

# Run the setup script
chmod +x setup-backend.sh
./setup-backend.sh

# Verify virtual environment
source venv/bin/activate
python --version
pytest --version
```

### 3. Manual Environment Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
pip install pytest pytest-cov pytest-asyncio

# Move to backend directory
cd backend
```

## Running Tests

### Run All Tests

```bash
# From project root or backend directory
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=. --cov-report=html
```

### Run Specific Test Categories

```bash
# Authentication tests only
pytest -v tests/test_auth.py

# Payment/Escrow tests
pytest -v tests/test_payment.py

# Security/Geofencing tests
pytest -v tests/test_security.py

# Order management tests
pytest -v tests/test_orders.py
```

### Run Tests by Marker

```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# Authentication marker
pytest -m auth

# Payment tests
pytest -m payment

# Security tests
pytest -m security
```

### Run Single Test Function

```bash
pytest tests/test_auth.py::TestUserRegistration::test_customer_registration -v

pytest tests/test_payment.py::TestEscrowSystem::test_ledger_created_on_order -v

pytest tests/test_security.py::TestGeofencing::test_within_geofence_boundary -v
```

## Test Coverage

Generate an HTML coverage report:

```bash
pytest --cov=. --cov-report=html

# Open the report
# Windows:
start htmlcov/index.html
# Linux/Mac:
open htmlcov/index.html
```

View coverage in terminal:

```bash
pytest --cov=. --cov-report=term-missing
```

## Test Categories

### 1. Authentication Tests (`test_auth.py`)

Tests JWT authentication, role-based access control, and user registration.

**Key Test Cases:**
- ✅ User registration for all roles (Customer, Vendor, Driver)
- ✅ Driver registration requires Student ID
- ✅ Duplicate email prevention
- ✅ Duplicate Student ID prevention
- ✅ Login with valid/invalid credentials
- ✅ Role-based access control (RBAC)
- ✅ Protected endpoints require token

**Run:**
```bash
pytest tests/test_auth.py -v
```

### 2. Payment & Escrow Tests (`test_payment.py`)

Tests the critical escrow system and refund logic.

**Key Test Cases:**
- ✅ Escrow ledger created with HOLDING status
- ✅ Refund only possible before vendor acceptance
- ✅ Refund blocked after vendor accepts
- ✅ Refund blocked during delivery
- ✅ Only customer can request refund
- ✅ STK Push initiates on order creation
- ✅ Payment amount calculation including fees

**Run:**
```bash
pytest tests/test_payment.py -v
```

**Critical: Test the refund loop protection**
```bash
pytest tests/test_payment.py::TestRefundLogic -v
```

### 3. Security & Geofencing Tests (`test_security.py`)

Tests GPS verification, anti-spoofing, QR codes, and handshakes.

**Key Test Cases:**
- ✅ Geofence verification within 15m radius
- ✅ Geofence rejection outside radius
- ✅ Custom radius support
- ✅ QR code generation as base64 PNG
- ✅ Double-blind handshake Parts A & B
- ✅ Handshake fails outside geofence
- ✅ Handshake fails with wrong QR
- ✅ No-show protection with GPS evidence
- ✅ Anti-GPS spoofing measures

**Run:**
```bash
pytest tests/test_security.py -v
```

**Critical: Test the double-blind handshake**
```bash
pytest tests/test_security.py::TestDoubleBlindHandshake -v
```

**Test no-show protection**
```bash
pytest tests/test_security.py::TestNoShowProtection -v
```

### 4. Order Management Tests (`test_orders.py`)

Tests all order-related APIs and operations.

**Key Test Cases:**
- ✅ Product listing and filtering
- ✅ Product CRUD by vendor
- ✅ Order creation with escrow
- ✅ Customer can view their orders
- ✅ Vendor can view their orders
- ✅ Driver can view assigned orders
- ✅ Orders isolated by customer (cannot see others')
- ✅ Vendor accept/ready operations
- ✅ Driver job acceptance
- ✅ Location tracking updates
- ✅ QR code retrieval
- ✅ Community impact stats

**Run:**
```bash
pytest tests/test_orders.py -v
```

## Test Database

Tests use an in-memory SQLite database (`:memory:`) that is:
- Fresh for each test session
- Automatically cleaned up
- Isolated from production/development databases

The test database includes:
- `conftest.py` - Test fixtures and database setup
- Test tables created via SQLAlchemy ORM

## Fixtures

### Available Fixtures

```python
# Database session
@pytest.fixture
def db():
    # Provides fresh database session

# Test users
@pytest.fixture
def test_customer(db):
    # Creates test customer user

@pytest.fixture
def test_vendor(db):
    # Creates test vendor user

@pytest.fixture
def test_driver(db):
    # Creates test driver with Student ID

# JWT Tokens
@pytest.fixture
def customer_token(test_customer):
    # JWT token for customer

@pytest.fixture
def vendor_token(test_vendor):
    # JWT token for vendor

@pytest.fixture
def driver_token(test_driver):
    # JWT token for driver

# Data
@pytest.fixture
def test_product(db, test_vendor):
    # Creates test product

@pytest.fixture
def test_order(db, test_customer, test_vendor, test_product):
    # Creates complete test order with ledger
```

### Using Fixtures in Tests

```python
def test_something(test_customer, customer_token, db):
    """Test function using multiple fixtures."""
    headers = get_auth_headers(customer_token)
    # Test code here
```

## Common Test Patterns

### Testing Protected Endpoints

```python
def test_protected_endpoint(customer_token):
    headers = get_auth_headers(customer_token)
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
```

### Testing Data Isolation

```python
def test_data_isolation(test_customer, other_customer):
    # Customer should only see their data
    customer_orders = get_customer_orders(test_customer)
    assert not any(o.customer_id == other_customer.id for o in customer_orders)
```

### Testing Database Transactions

```python
def test_database_update(test_order, db):
    test_order.status = "NEW_STATUS"
    db.commit()
    db.refresh(test_order)
    assert test_order.status == "NEW_STATUS"
```

## Common Issues & Solutions

### Issue: Import Errors

**Solution:** Ensure you're in the `backend` directory:
```bash
cd backend
pytest tests/
```

### Issue: Database Locked Error

**Solution:** Clear any existing test database:
```bash
rm sokoyetu.db
pytest
```

### Issue: ModuleNotFoundError

**Solution:** Ensure virtual environment is activated and dependencies installed:
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Issue: Fixture Not Found

**Solution:** Ensure `conftest.py` is in the `tests/` directory:
```bash
ls backend/tests/conftest.py  # Should exist
```

## Continuous Integration

For CI/CD pipelines, use:

```bash
# Run all tests and fail on any failure
pytest --tb=short -q

# Generate coverage report
pytest --cov=. --cov-report=xml

# Run only critical security tests
pytest tests/test_security.py tests/test_payment.py -v
```

## Test Metrics

Target test coverage:
- **Overall:** 80%+
- **Critical paths (payment, security):** 95%+
- **APIs:** 85%+

Current coverage is tracked in `htmlcov/index.html` after running:
```bash
pytest --cov=. --cov-report=html
```

## Best Practices

1. **Always test in isolation** - Use fresh database for each test
2. **Test edge cases** - Test boundary conditions and error states
3. **Use meaningful test names** - Test names should describe what they test
4. **Keep tests small** - Each test should test one thing
5. **Use fixtures for reusable setup** - Don't repeat test data creation
6. **Test error paths** - Not just happy paths
7. **Document complex tests** - Use docstrings for non-obvious tests

## Manual Testing Checklist

Even with automated tests, manually verify:

- [ ] Customer can browse products by category
- [ ] STK Push payment prompt appears
- [ ] Order appears in vendor dashboard
- [ ] Driver can accept and complete delivery
- [ ] QR code scans correctly
- [ ] Refund works before vendor acceptance
- [ ] Refund blocked after vendor acceptance
- [ ] Email receipt received (if SMTP configured)
- [ ] WebSocket location tracking updates
- [ ] Community impact stats update

## Performance Testing

For basic load testing:

```bash
# Install locust
pip install locust

# Create locustfile.py with test scenarios
# Run load tests
locust -f locustfile.py
```

## Debugging Tests

### Enable Debug Output

```bash
# Verbose output with prints
pytest -s -v tests/test_auth.py::TestUserRegistration::test_customer_registration

# Drop into debugger on failure
pytest --pdb tests/test_auth.py
```

### Print Debugging in Tests

```python
def test_something(test_order, db):
    print(f"\nTest order ID: {test_order.id}")
    print(f"Status: {test_order.status}")
    
    # Use pytest's caplog for logging
    assert test_order.id is not None
```

## Next Steps

1. ✅ Run all tests: `pytest -v`
2. ✅ Check coverage: `pytest --cov=. --cov-report=html`
3. ✅ Fix any failing tests
4. ✅ Start development server: `uvicorn main:app --reload`
5. ✅ Test manually in browser

## Support

For test failures or questions:
1. Check the error message carefully
2. Review the test code in `backend/tests/`
3. Check test database is clean
4. Ensure all dependencies are installed
5. Verify environment variables in `.env`
