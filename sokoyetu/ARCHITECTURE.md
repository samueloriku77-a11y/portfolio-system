# System Architecture - SokoYetu

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React/Vite)                     │
│  Customer Dashboard | Vendor Dashboard | Driver Dashboard       │
└──────────────────────────────────┬──────────────────────────────┘
                                   │
                    HTTP API (FastAPI) + WebSocket
                                   │
┌──────────────────────────────────▼──────────────────────────────┐
│                    Backend (FastAPI)                             │
│  ├─ Authentication (JWT)                                        │
│  ├─ Products & Orders                                           │
│  ├─ Payment Processing                                          │
│  ├─ GPS & Security                                              │
│  └─ Notifications                                               │
└──────────────────────────────────┬──────────────────────────────┘
                                   │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
    Database              External Services            WebSocket
 (PostgreSQL/SQLite)    (M-Pesa, SMTP, SMS)       (Real-time tracking)
```

## Layered Architecture

### 1. Presentation Layer (Frontend)

**Technology:** React 18 + Vite + TypeScript

**Components:**
- **Pages**
  - `customer/Dashboard.jsx` - Shopping, orders, impact stats
  - `vendor/Dashboard.jsx` - Order management, analytics
  - `driver/Dashboard.jsx` - Job discovery, tracking, earnings
  - `Login.jsx` - Authentication
  - `Register.jsx` - User registration

- **Context**
  - `AuthContext.jsx` - JWT token and user state management

- **API Client**
  - `api.js` - Axios configuration with interceptors

**State Management:**
- Context API for authentication
- Local state for UI components
- LocalStorage for JWT token persistence

**Features:**
- Role-based routing
- Real-time location updates (WebSocket)
- QR code display
- Responsive design

### 2. Application Layer (Backend)

**Technology:** FastAPI + Pydantic

**Structure:**

```
main.py                    # FastAPI app definition
├── Authentication Endpoints
├── Product Endpoints
├── Order Endpoints
├── Vendor Endpoints
├── Driver Endpoints
├── Dispute Endpoints
├── Security Endpoints
└── WebSocket Endpoints

auth.py                    # JWT & RBAC utilities
├── create_access_token() - Generate JWT
├── get_password_hash() - Hash passwords
├── verify_password() - Validate passwords
├── decode_token() - Extract user from JWT
└── role_required() - Decorator for protected routes

schemas.py                 # Pydantic request/response models
├── UserRegister
├── UserLogin
├── OrderCreate
├── OrderResponse
├── PaymentCreate
├── PaymentResponse
└── 25+ more models
```

**API Endpoints (40+):**

| Category | Endpoints | Count |
|----------|-----------|-------|
| Auth | register, login, me | 3 |
| Products | list, get, create, update, delete | 5 |
| Orders | create, list, get, cancel, get_qr, complete | 6 |
| Vendor | accept, ready, mark_delivered | 3 |
| Driver | nearby_jobs, accept, location, qr_scan, complete | 6 |
| Disputes | create, get, update | 3 |
| Security | geofence, qr, handshake | 3 |
| Customer | community_impact, stats | 2 |
| Admin | stats, analytics | 2 |
| WebSocket | /ws/driver-tracking/{driver_id} | 1 |
| Health | health check | 1 |

### 3. Business Logic Layer (Services)

**payment.py** - Escrow & M-Pesa Integration
```
├── initiate_stk_push()      - Create payment and start STK
├── cancel_order_and_refund() - CRITICAL: Refund gate logic
├── release_funds()          - Vendor payout after delivery
├── process_callback()       - M-Pesa transaction callback
└── calculate_fees()         - Platform fees calculation
```

**security.py** - GPS & Handshake Verification
```
├── verify_geofence()        - Haversine distance check
├── generate_qr_base64()     - Create QR code
├── process_double_blind_handshake() - Part A + B verification
├── register_no_show()       - GPS-verified no-show
└── detect_spoofing()        - Anti-GPS spoofing
```

**notifications.py** - Email & SMS
```
├── send_delivery_email()    - Styled HTML receipt
├── send_delivery_sms()      - SMS notification
├── send_notification()      - Queue notification
└── render_email_template()  - Jinja2 templates
```

### 4. Data Layer (Database)

**Technology:** SQLAlchemy ORM + PostgreSQL/SQLite

**Database Schema (11 Tables):**

```
users
├── id (UUID, Primary Key)
├── email (String, Unique)
├── role (Enum: CUSTOMER, VENDOR, DRIVER)
├── student_id (String, Unique for drivers)
└── relationships: products, orders, payments, ledgers

products
├── id (UUID)
├── vendor_id (FK → users)
├── name, description, price
├── category (LocalMarket / Restaurant)
├── stock_qty, is_available
└── relationships: orders, order_items

orders
├── id (UUID)
├── customer_id, vendor_id, driver_id (FKs)
├── status (Enum: PENDING → ACCEPTED → DELIVERED)
├── total_amount, delivery_fee
├── delivery_location (lat, lng)
└── relationships: items, payment, ledger, handshake, disputes

order_items
├── id, order_id, product_id
├── quantity, unit_price, subtotal
└── relationships: order, product

payments
├── id (UUID)
├── order_id (FK)
├── amount, status
├── mpesa_transaction_id
└── relationships: order, ledger

ledgers (Escrow Tracking)
├── id (UUID)
├── order_id, user_id (FKs)
├── status (HOLDING → RELEASED → REFUNDED)
├── amount, platform_fee, driver_fee
└── timestamps (created, updated)

handshake_keys (Double-Blind Verification)
├── id (UUID)
├── order_id (FK)
├── part_a_code (Vendor QR)
├── part_b_code (Customer QR)
├── is_verified, verified_at
└── relationships: order

delivery_verifications (No-Show Protection)
├── id (UUID)
├── order_id (FK)
├── driver_photo_url
├── gps_lat, gps_lng
├── timestamp, is_no_show
└── relationships: order

disputes (Manual Escalation)
├── id (UUID)
├── order_id (FK)
├── reason, status, resolution
└── timestamps

driver_locations (Real-time Tracking)
├── driver_id (FK)
├── lat, lng, timestamp
├── speed, accuracy
└── relationships: users

notifications (Queue)
├── id (UUID)
├── user_id, order_id (FKs)
├── type (EMAIL / SMS)
├── message, sent_at
└── relationships: users, orders
```

## Request/Response Flow

### Order Creation Flow

```
┌───────────────┐
│  Customer     │
│  POST /orders │
└───────┬───────┘
        │
        ▼
┌──────────────────────────────────────────┐
│  FastAPI Endpoint: create_order()        │
│  ├─ Validate JWT token                   │
│  ├─ Parse OrderCreate schema             │
│  ├─ Check customer exists                │
│  └─ Check products in stock              │
└──────────────────┬───────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
   Database          Payment Service
   ├─ Create Order   │
   ├─ Create Items   └─→ initiate_stk_push()
   ├─ Create Ledger      ├─ Call M-Pesa API
   │ (HOLDING)           ├─ Store transaction ID
   └─ Status: PENDING    ├─ Return STK token
                         └─ Customer gets prompt
        │
        ▼
   Response (200)
   {
     "id": "order-uuid",
     "status": "PENDING_PAYMENT",
     "stk_checkout_request_id": "..."
   }
```

### Order Completion & Payment Release

```
┌──────────────┐
│  Driver      │
│  Complete    │
│  Delivery    │
└───────┬──────┘
        │
        ▼
┌────────────────────────────────┐
│ Scan QR Code                   │
│ + Verify Geofence (15m)        │
└───────┬────────────────────────┘
        │
        ▼
┌────────────────────────────────┐
│ Double-Blind Handshake        │
│ ├─ Part A (Vendor) matches   │
│ ├─ Part B (Customer) matches │
│ └─ Location verified         │
└───────┬────────────────────────┘
        │
        ▼
┌────────────────────────────────┐
│ Order Status: DELIVERED        │
└───────┬────────────────────────┘
        │
        ▼
┌────────────────────────────────┐
│ Payment Service                │
│ release_funds()                │
├─ Ledger: HOLDING → RELEASED   │
├─ Vendor payout                │
├─ Driver commission            │
└─ Platform fee deducted        │
        │
        ▼
┌────────────────────────────────┐
│ Notifications Service          │
├─ Email receipt to customer    │
├─ SMS to vendor (funds ready)  │
└─ SMS to driver (tip earned)   │
└────────────────────────────────┘
```

## Security Architecture

### Authentication Flow

```
┌──────────────────┐
│  User Registers  │
│  (Email/Pass)    │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────┐
│  Hash Password (Passlib)         │
│  ✓ PBKDF2 algorithm              │
│  ✓ 100,000 iterations            │
└────────┬────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  Store User in Database          │
│  - email (unique, indexed)       │
│  - hashed_password               │
│  - role (CUSTOMER/VENDOR/DRIVER) │
│  - student_id (drivers only)     │
└────────┬────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  JWT Token Created               │
│  jwt.encode({                    │
│    "sub": user_id,               │
│    "role": user_role,            │
│    "exp": timestamp              │
│  }, SECRET_KEY, "HS256")         │
└────────┬────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  Return JWT to Client            │
│  Client stores in localStorage   │
│  Client adds to Auth header      │
│  Authorization: Bearer <token>   │
└──────────────────────────────────┘
```

### Payment Security (Escrow)

```
Order Created
├─ Amount HELD in escrow
│
├─ Scenario 1: Customer Cancels (Before Vendor Accepts)
│  ├─ Ledger status: HOLDING → REFUNDED
│  ├─ Funds returned to customer
│  └─ No fee charged
│
└─ Scenario 2: Delivery Completed
   ├─ Handshake verified
   ├─ Ledger status: HOLDING → RELEASED
   ├─ Platform fee deducted (5%)
   ├─ Driver commission calculated (10%)
   └─ Vendor receives: amount - fees
```

### GPS Spoofing Prevention

```
Driver Updates Location
├─ Timestamp recorded
├─ Previous location cached
│
├─ Speed Calculation
│ distance = haversine(prev, current)
│ speed = distance / time_elapsed
│ if speed > 150 km/h → ❌ FRAUD
│
├─ Geofence Verification
│ distance = haversine(current, delivery_location)
│ if distance > 15m → ❌ OUTSIDE RADIUS
│
└─ Accept & Store
   ├─ Location history updated
   └─ Map marker updated
```

## Data Flow Diagrams

### Real-Time Driver Tracking

```
Driver App
├─ Get current GPS location
│  (navigator.geolocation.getCurrentPosition)
│
└─→ POST /api/driver/location/update
    {
      "driver_id": "uuid",
      "lat": -1.2866,
      "lng": 36.8172,
      "timestamp": "2024-01-15T10:00:00"
    }
    │
    ▼
Backend
├─ Save to database (driver_locations)
│
└─→ WebSocket Broadcast
    broadcast_data({
      "driver_id": "uuid",
      "lat": -1.2866,
      "lng": 36.8172
    })
    │
    ▼
Connected Clients
├─ Vendor watching orders
│  └─ Updates order tracking map
│
├─ Customer watching delivery
│  └─ Updates delivery ETA
│
└─ Other drivers
   └─ Updates nearby drivers (optional)
```

### Email Notification Flow

```
Order Event (Created/Completed)
│
▼
Notifications Service (async tasks)
├─ Fetch order details
├─ Fetch user email
│
▼
Render Jinja2 Template
├─ customer/order_receipt.html
├─ Inject variables:
│  ├─ order_id, items, total
│  ├─ vendor_name, driver_name
│  ├─ delivery_address, ETA
│  └─ community_impact
│
▼
SMTP Connection (Gmail/SendGrid)
├─ Subject: "Order Confirmed - #123456"
├─ To: customer@email.com
├─ Body-HTML: rendered template
│
▼
Email Sent ✓
└─ Notification marked as delivered

```

## Scalability Considerations

### Current Architecture (Single Instance)

```
┌─────────────────────────────────────┐
│  FastAPI Server (1 instance)        │
├─────────────────────────────────────┤
│  SQLAlchemy ORM                     │
│  ├─ Connection pool: 20 connections │
│  └─ Max concurrent: ~20 requests    │
├─────────────────────────────────────┤
│  Database (Single PostgreSQL)       │
├─────────────────────────────────────┤
│  Estimated: 500-2000 concurrent     │
│            requests per hour        │
└─────────────────────────────────────┘
```

### Scalable Architecture (Production)

```
┌─────────────────────────────────────────┐
│         Load Balancer (Nginx)           │
└────────────┬─────────────────┬──────────┘
             │                   │
     ┌───────▼────┐      ┌──────▼──────┐
     │ FastAPI-1  │      │ FastAPI-2   │
     │ FastAPI-3  │      │ FastAPI-4   │
     └───────┬────┘      └──────┬──────┘
             │                   │
             └───────┬───────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
      ┌──▼──┐  ┌────▼─────┐  ┌─▼────┐
      │Cache│  │ Database │  │Queue │
      │Redis│  │PostgreSQL│  │Redis │
      │     │  │Primary-  │  │Celery│
      │     │  │Replica   │  │      │
      └─────┘  └──────────┘  └──────┘
```

**Scaling Strategies:**
- Horizontal scaling: Multiple FastAPI instances
- Database read replicas for analytics
- Redis caching for product catalog
- Task queue (Celery) for async notifications
- CDN for static assets

### Performance Optimizations

1. **Database**
   - Indexes on frequently queried columns
   - Connection pooling
   - Query optimization with eager loading

2. **Caching**
   - Product catalog in Redis
   - JWT token caching
   - Session storage in database

3. **Frontend**
   - Code splitting with Vite
   - Lazy loading routes
   - Image optimization

4. **API**
   - Pagination on list endpoints
   - Request rate limiting
   - Compression (gzip)

## Development Workflow

### Local Development Setup

```
1. Clone repository
2. Backend:
   ├─ python -m venv venv
   ├─ pip install -r requirements.txt
   ├─ cp .env.example .env
   └─ uvicorn main:app --reload
3. Frontend:
   ├─ npm install
   ├─ cp .env.example .env.local
   └─ npm run dev
4. Testing:
   └─ pytest -v (56+ tests)
```

### Testing Architecture

```
Test Database (SQLite in-memory)
├─ Isolated for each test
├─ Auto-cleanup
└─ Fast execution (~5 seconds for all tests)

Test Fixtures (conftest.py)
├─ test_customer, test_vendor, test_driver
├─ customer_token, vendor_token, driver_token
├─ test_product, test_order
└─ db (database session)

Test Modules
├─ test_auth.py (12 tests)
├─ test_payment.py (8 tests)
├─ test_security.py (16+ tests)
└─ test_orders.py (20+ tests)
```

### CI/CD Integration

```
Push to Repository
│
▼
GitHub Actions (or similar)
├─ Lint (Flake8, Pylint)
├─ Type Check (mypy)
├─ Run Tests (pytest)
├─ Coverage Check (>80%)
├─ Build Docker image
└─ Deploy to staging
```

## Error Handling

### Consistent Error Response Format

```python
{
  "status": "Error",
  "message": "Descriptive user message",
  "error_code": "SPECIFIC_CODE",
  "details": {} # Optional additional info
}
```

**Error Codes:**
- `INVALID_CREDENTIALS` - Wrong password
- `USER_NOT_FOUND` - Email doesn't exist
- `OUT_OF_STOCK` - Product unavailable
- `OUT_OF_GEOFENCE` - Outside delivery radius
- `REFUND_NOT_ALLOWED` - Order already accepted
- `INVALID_QR` - Handshake failed
- `INSUFFICIENT_BALANCE` - Payment failed

### Validation Strategy

```
Request Flow:
├─ JWT Token validation (auth.py)
├─ Request body validation (Pydantic schemas)
├─ Business logic validation (services)
├─ Database constraints
│  ├─ Unique constraints
│  ├─ Foreign key constraints
│  └─ Check constraints
│
└─ Response construction
   ├─ Success (200, 201)
   ├─ Validation error (400)
   ├─ Unauthorized (401)
   ├─ Forbidden (403)
   └─ Server error (500)
```

## Deployment Architectures

### Docker Deployment

```
Dockerfile
├─ Base: python:3.10-slim
├─ Dependencies: pip install
├─ Copy source code
└─ CMD: uvicorn main:app

docker-compose.yml
├─ fastapi service
├─ postgres service
├─ redis service (optional)
└─ nginx service (reverse proxy)
```

### Cloud Deployment (Railway/Render)

```
Backend Service
├─ Python 3.10 runtime
├─ FastAPI application
├─ Environment variables
└─ Auto-scaling enabled

Database Service
├─ PostgreSQL 15
├─ Automated backups
└─ Connection pooling

Frontend Service (Vercel/Netlify)
├─ Node.js runtime
├─ React SPA build
└─ Environment configuration
```

## Monitoring & Observability

### Metrics to Track

```
API Metrics
├─ Request count (by endpoint)
├─ Response time (p50, p95, p99)
├─ Error rate (5xx, 4xx)
└─ Throughput (requests/sec)

Business Metrics
├─ Orders created
├─ Revenue generated
├─ Popular products
├─ Driver conversion
└─ Customer retention

System Metrics
├─ CPU usage
├─ Memory usage
├─ Database query time
├─ WebSocket connections
└─ Email delivery rate
```

### Logging Strategy

```
Log Level Hierarchy:
├─ DEBUG - Detailed variable values
├─ INFO - Business events (order created, payment received)
├─ WARNING - Unexpected but recoverable (slow query)
├─ ERROR - Actionable errors (payment failed)
└─ CRITICAL - System down (database unreachable)

Log Format:
{
  "timestamp": "2024-01-15T10:00:00",
  "level": "INFO",
  "service": "sokoyetu-api",
  "event": "order_created",
  "order_id": "uuid",
  "customer_id": "uuid",
  "amount": 500.00
}
```

---

See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup details.
