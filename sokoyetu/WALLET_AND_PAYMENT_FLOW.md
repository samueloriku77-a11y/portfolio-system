# SokoYetu Wallet & Delivery Payment Flow

## Overview

The SokoYetu platform implements a complete wallet system with M-Pesa integration and an escrow-based delivery payment flow. This document describes how customers, vendors, and drivers interact with the wallet system and how funds move through the platform during order fulfillment.

---

## 1. Wallet System Architecture

### User Wallet Balances

Every user in the system (customer, vendor, driver) has a `wallet_balance` field stored in the User model. This represents:
- **Customers**: Available funds to spend + balance from previous deposits
- **Vendors**: Revenue from completed deliveries minus withdrawals
- **Drivers**: Earnings from completed deliveries minus withdrawals

### Wallet Transactions

All wallet activity is tracked in the `WalletTransaction` model with the following structure:

```python
WalletTransaction:
  - id: integer (primary key)
  - user_id: integer (foreign key to User)
  - amount: float (transaction amount in KES)
  - transaction_type: enum (DEPOSIT or WITHDRAWAL)
  - status: enum (PENDING, COMPLETED, or FAILED)
  - phone_number: string (M-Pesa number for transaction)
  - reference: string (unique transaction reference)
  - transaction_metadata: JSON (API response data)
  - created_at: timestamp
```

### Transaction Statuses

- **PENDING**: Awaiting IntaSend API confirmation
- **COMPLETED**: Transaction successfully processed
- **FAILED**: Transaction failed or was rejected

---

## 2. Customer Deposit Flow

### HTTP Endpoints

```
POST /api/wallet/deposit
Request:
{
  "amount": 1000,
  "transaction_type": "DEPOSIT",
  "phone_number": "254712345678"
}

Response:
{
  "id": 123,
  "user_id": 1,
  "amount": 1000,
  "transaction_type": "DEPOSIT",
  "status": "PENDING",
  "phone_number": "254712345678",
  "reference": "WD_<timestamp>_<random>",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Step-by-Step Flow

1. **Customer enters amount** on Wallet page (frontend)
2. **Frontend validates**: amount > 0 and phone number format
3. **POST to `/api/wallet/deposit`** with amount and phone
4. **Backend creates WalletTransaction**:
   - Status: `PENDING`
   - Type: `DEPOSIT`
   - Reference: `WD_<timestamp>_<random>`
5. **Backend calls IntaSend Checkout API**:
   ```
   POST https://api.intasend.co/v1/checkout/create
   Headers: Authorization: Bearer <INTASEND_API_KEY>
   Body:
   {
     "first_name": "<user.name>",
     "last_name": "Payment",
     "email": "<user.email>",
     "amount": 1000,
     "currency": "KES",
     "phone_number": "254712345678",
     "callback_url": "https://yourdomain.com/api/wallet/callback",
     "redirect_url": "<frontend_url>",
     "reference": "WD_<timestamp>_<random>"
   }
   ```
6. **IntaSend returns checkout_url**
7. **Frontend redirects to M-Pesa prompt**
8. **Customer enters M-Pesa PIN** on phone
9. **M-Pesa processes payment**
10. **IntaSend webhook callback** to POST `/api/wallet/callback`:
    - Updates `WalletTransaction.status = COMPLETED`
    - Increments `user.wallet_balance += amount`
11. **Success**: Customer's wallet balance increases

### Configuration

Required environment variables in `.env`:
```
INTASEND_API_URL=https://sandbox.intasend.co/v1  # development
INTASEND_API_KEY=<your-api-key>
INTASEND_API_SECRET=<your-api-secret>
INTASEND_CALLBACK_URL=https://yourdomain.com/api/wallet/callback
```

---

## 3. Customer Withdrawal Flow

### HTTP Endpoints

```
POST /api/wallet/withdraw
Request:
{
  "amount": 500,
  "transaction_type": "WITHDRAWAL",
  "phone_number": "254712345678"
}

Response:
{
  "id": 124,
  "user_id": 1,
  "amount": 500,
  "transaction_type": "WITHDRAWAL",
  "status": "PENDING",
  "phone_number": "254712345678",
  "reference": "WW_<timestamp>_<random>"
}
```

### Step-by-Step Flow

1. **Customer initiates withdrawal** on Wallet page
2. **Frontend validates**:
   - Amount > 0
   - Amount ≤ current wallet_balance
   - Phone number format is valid
3. **POST to `/api/wallet/withdraw`** with amount and phone
4. **Backend immediately deducts balance**:
   - `user.wallet_balance -= amount`
5. **Backend creates WalletTransaction**:
   - Status: `PENDING`
   - Type: `WITHDRAWAL`
6. **Backend calls IntaSend Payout API**:
   ```
   POST https://api.intasend.co/v1/payouts
   Headers: Authorization: Bearer <INTASEND_API_KEY>
   Body:
   {
     "amount": 500,
     "phone_number": "254712345678",
     "reference": "WW_<timestamp>_<random>",
     "currency": "KES"
   }
   ```
7. **IntaSend processes payout** (typically within 5 minutes)
8. **IntaSend webhook callback** updates transaction status to `COMPLETED`
9. **Funds arrive** in customer's M-Pesa account

### Key Differences from Deposits

- **Balance deducted immediately** (prevents overspending)
- **No callback needed** for customer experience (balance already deducted)
- **Payout processing** handled by IntaSend backend

---

## 4. Order Fulfillment & Escrow System

### Order Ledger Tracking

The `Ledger` model tracks escrow for all orders:

```python
Ledger:
  - id: integer
  - order_id: integer (foreign key)
  - amount: float (total_amount + delivery_fee)
  - status: enum (HOLDING, RELEASED, or REFUNDED)
  - created_at: timestamp
```

### Ledger Statuses

- **HOLDING**: Funds in escrow, awaiting delivery confirmation
- **RELEASED**: Funds disbursed to vendor and driver after delivery
- **REFUNDED**: Funds returned to customer if order cancelled before delivery

---

## 5. Delivery Flow with QR Code & Payment Release

### Phase 1: Order Placement (Customer → Vendor)

```
POST /api/orders
Request:
{
  "items": [...],
  "delivery_lat": -1.2345,
  "delivery_lng": 36.7890,
  "delivery_fee": 150
}
```

1. **Customer creates order** with items and delivery location
2. **Total amount calculated**: `total_amount + delivery_fee`
3. **Ledger entry created**:
   ```
   Ledger(
     order_id=order.id,
     amount=order.total_amount + order.delivery_fee,
     status='HOLDING'  # Escrow
   )
   ```
4. **Order status**: `PENDING_VENDOR_APPROVAL`
5. **Funds held in escrow** (not touching user wallets yet)

### Phase 2: Vendor Approval

```
POST /api/orders/{order_id}/approve
```

1. **Vendor reviews order** on dashboard
2. **Vendor clicks "Accept Order"**
3. **Order status**: `ACCEPTED_BY_VENDOR`
4. **Vendor prepares items** for pickup by driver

### Phase 3: Driver Acceptance & Geofence Arrival

```
POST /api/driver/orders/{job_id}/accept
```

1. **Driver views nearby jobs**
2. **Driver accepts job**
3. **Order status**: `ACCEPTED_BY_VENDOR` (still waiting for pickup)

### Phase 4: Driver Marks Arrival (NEW - Geofence Trigger)

```
POST /api/driver/orders/{order_id}/arrived
Headers:
{
  "Authorization": "Bearer <token>"
}
Body:
{
  "driver_lat": -1.2340,
  "driver_lng": 36.7895
}

Response:
{
  "success": true,
  "message": "Driver arrived at vendor location"
}
```

**Geofence Check**: Distance to vendor < 100 meters

**Result**: Order status changes to `OUT_FOR_DELIVERY`

**Key Point**: QR code becomes available ONLY after this endpoint is called.

### Phase 5: QR Code Retrieval (Driver at Customer)

```
GET /api/orders/{order_id}/qr
```

**Validation**:
- Order status MUST be `OUT_FOR_DELIVERY` (strict requirement)
- No other states accepted

**Response**:
```json
{
  "order_id": 123,
  "vendor_id": 5,
  "driver_id": 7,
  "qr_data": "ORDER_123_VENDOR_5_DRIVER_7_<checksum>",
  "qr_code_url": "data:image/png;base64,..."
}
```

**QR Code Format**: Machine-readable string containing:
- Order ID
- Vendor ID
- Driver ID
- Checksum (prevents forgery)

### Phase 6: Customer Scans QR & Confirms Delivery

```
POST /api/driver/orders/{order_id}/handshake
Headers:
{
  "Authorization": "Bearer <driver_token>"
}
Body:
{
  "order_id": 123,
  "qr_data": "ORDER_123_VENDOR_5_DRIVER_7_<checksum>",
  "driver_lat": -1.2356,
  "driver_lng": 36.7912
}
```

**Validation Steps** (in `process_double_blind_handshake`):

1. **QR Code Verification**
   - Decode QR string
   - Extract order_id, vendor_id, driver_id
   - Verify checksum matches

2. **Geofence Verification**
   - Customer location ≤ 15 meters from delivery address
   - Uses Haversine distance formula

3. **Order Status Check**
   - Status must be `OUT_FOR_DELIVERY`

**Success Response**:
```json
{
  "success": true,
  "message": "Delivery confirmed! Payment released."
}
```

### Phase 7: Payment Release to Vendor & Driver

Called from `release_funds()` function:

```python
def release_funds(db: Session, order_id: int):
    order = db.query(Order).filter(Order.id == order_id).first()
    vendor = db.query(User).filter(User.id == order.vendor_id).first()
    driver = db.query(User).filter(User.id == order.driver_id).first()
    
    # Credit vendor's wallet
    vendor.wallet_balance += order.total_amount
    
    # Credit driver's wallet
    driver.wallet_balance += order.driver_earnings
    
    # Update ledger
    ledger = db.query(Ledger).filter(Ledger.order_id == order_id).first()
    ledger.status = 'RELEASED'
    
    # Mark order delivered
    order.status = 'DELIVERED'
    db.commit()
```

**Result**:
- ✅ `vendor.wallet_balance += order.total_amount`
- ✅ `driver.wallet_balance += order.driver_earnings`
- ✅ `Ledger.status = 'RELEASED'`
- ✅ `Order.status = 'DELIVERED'`
- ✅ Both vendor and driver see updated balances on their dashboards

### Full Order Timeline

```
PENDING_VENDOR_APPROVAL
  ↓ (vendor clicks accept)
ACCEPTED_BY_VENDOR
  ↓ (driver picks up from vendor)
  ↓ (driver calls /arrived endpoint → geofence verified)
OUT_FOR_DELIVERY
  ↓ (QR code now available)
  ↓ (customer scans QR → geofence verified)
DELIVERED
  ↓ (funds released to vendor & driver)
Order.status = DELIVERED
Vendor.wallet_balance += total_amount
Driver.wallet_balance += driver_earnings
Ledger.status = RELEASED
```

---

## 6. Cancellation & Refund Flow

### Customer Cancellation (Before Delivery)

```
POST /api/orders/{order_id}/cancel
```

**Allowed only if**:
- Order status == `PENDING_VENDOR_APPROVAL`

**Result**:
- Ledger created with status `REFUNDED`
- Order status changed to `CANCELLED_BY_USER`
- **No wallet changes** (funds return to escrow, not customer wallet)

**Why**: Prevents exploit where customer deposits → cancels → withdraws immediately.

### Cancelled Order Reversal

In production, implement:
1. Customer requests reissue (admin approval)
2. Manual ledger audit
3. Wallet refund with verification

---

## 7. Frontend Components

### Customer Wallet (Wallet.jsx)

**Location**: `frontend/src/pages/customer/Wallet.jsx`

**Features**:
- Display current balance
- Deposit form (amount + phone number)
- Withdrawal form (amount + phone number)
- Transaction history with status badges

**State**:
```javascript
{
  balance: number,
  transactions: WalletTransaction[],
  activeTab: 'balance' | 'deposit' | 'withdraw',
  depositForm: { amount, phone },
  withdrawForm: { amount, phone },
  processing: boolean
}
```

**API Calls**:
- `GET /api/wallet` → Load balance + transactions
- `POST /api/wallet/deposit` → Initiate M-Pesa deposit
- `POST /api/wallet/withdraw` → Withdraw to M-Pesa

### Driver Earnings (Earnings.jsx)

**Location**: `frontend/src/pages/driver/Earnings.jsx`

**Features**:
- Display total earnings (wallet_balance)
- Withdrawal form
- Earnings history filtered to DEPOSIT transactions
- Statistics (delivery count, etc.)

**Integrated into**: `frontend/src/pages/driver/Dashboard.jsx`

### Vendor Revenue (Revenue.jsx)

**Location**: `frontend/src/pages/vendor/Revenue.jsx`

**Features**:
- Revenue overview cards (balance, orders today, total orders, avg order value)
- Withdrawal form
- Revenue history table
- Performance snapshot

**Integrated into**: `frontend/src/pages/vendor/Dashboard.jsx`

---

## 8. API Endpoints Summary

### Wallet Management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/wallet` | GET | Fetch balance + transaction history |
| `/api/wallet/deposit` | POST | Initiate deposit (IntaSend checkout) |
| `/api/wallet/withdraw` | POST | Initiate withdrawal (deduct balance, IntaSend payout) |
| `/api/wallet/callback` | POST | IntaSend webhook for transaction confirmation |

### Delivery Payment Flow

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/orders` | POST | Create order (escrow held) |
| `/api/orders/{id}/approve` | POST | Vendor approves order |
| `/api/driver/orders/{id}/accept` | POST | Driver accepts job |
| `/api/driver/orders/{id}/arrived` | POST | Driver marks arrival at vendor (geofence check, OFD status) |
| `/api/orders/{id}/qr` | GET | Retrieve QR code (only if OUT_FOR_DELIVERY) |
| `/api/driver/orders/{id}/handshake` | POST | Customer scans QR, payment released |
| `/api/orders/{id}/cancel` | POST | Cancel order, refund to escrow |

---

## 9. Geofencing Rules

| Checkpoint | Radius | Action |
|-----------|--------|--------|
| Vendor arrival | 100m | Order → OUT_FOR_DELIVERY |
| Customer delivery | 15m | Release payment |
| No-show report | 50m | Mark as no-show |

**Distance Calculation**: Haversine formula converting lat/lng to kilometers

---

## 10. IntaSend Integration

### Endpoints Used

**Development**:
```
Base URL: https://sandbox.intasend.co/v1
```

**Production**:
```
Base URL: https://api.intasend.co/v1
```

### Authentication

```
Headers:
Authorization: Bearer <INTASEND_API_KEY>
Content-Type: application/json
```

### Deposit Checkout

```
POST /checkout/create
Body:
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "user@example.com",
  "amount": 1000,
  "currency": "KES",
  "phone_number": "254712345678",
  "callback_url": "https://yourdomain.com/api/wallet/callback",
  "redirect_url": "https://frontend.com/wallet",
  "reference": "WD_1705313400_abc123"
}

Response:
{
  "checkout_url": "https://sandbox.intasend.co/...checkout_session_id",
  "session_id": "checkout_session_id"
}
```

### Payout (Withdrawal)

```
POST /payouts
Body:
{
  "amount": 500,
  "phone_number": "254712345678",
  "reference": "WW_1705313400_def456",
  "currency": "KES"
}

Response:
{
  "id": "payout_id",
  "status": "PENDING",
  "amount": 500
}
```

---

## 11. Error Handling

### Deposit Failures

1. **Invalid phone number**: Validation error from IntaSend
2. **Insufficient M-Pesa balance**: M-Pesa rejection (user retries)
3. **Network timeout**: Transaction remains PENDING (user can retry)
4. **API key invalid**: 401 response (check environment config)

**Recovery**: Transaction stays in PENDING state; user can try again.

### Withdrawal Failures

1. **Insufficient balance**: Caught before API call
2. **Invalid phone number**: Validation error
3. **Payout rejection**: Status remains PENDING (manual review)

**Recovery**: Balance already deducted; admin must refund if payout fails.

### Delivery Payment Failures

1. **QR code mismatch**: Invalid QR data error
2. **Geofence miss**: "Too far from location" error
3. **Order status wrong**: "Cannot complete this delivery" error

**Recovery**: Driver stays at SCANNING stage, retries with valid QR at correct location.

---

## 12. Security Considerations

### QR Code Forgery Prevention

- QR contains: `ORDER_ID_VENDOR_ID_DRIVER_ID_<SHA256_HASH>`
- Hash includes: order secret + driver secret + timestamp
- Cannot be generated without database access

### Double-Spend Prevention

- Ledger status transition prevents duplicate payment
- Once RELEASED, Ledger cannot be re-processed
- Order.status prevents repeated handshakes

### Geofence Attacks

- GPS coordinates checked against known delivery address
- 15m radius tight enough for street-level verification
- Driver can't claim delivery from far away

### Withdrawal Balance Exploits

- Balance deducted immediately on POST (no double-withdraw)
- Transaction remains PENDING until IntaSend confirms
- Failed payouts don't restore balance (manual admin review)

---

## 13. Testing Checklist

- [ ] Customer deposits 100 KES, balance increases
- [ ] Customer sees transaction in history
- [ ] Customer withdraws 50 KES, balance decreases immediately
- [ ] Vendor creates order, ledger in HOLDING state
- [ ] Vendor approves order, status ACCEPTED_BY_VENDOR
- [ ] Driver accepts job, prepares for pickup
- [ ] Driver marks arrival (geofence check within 100m of vendor)
- [ ] Order transitions to OUT_FOR_DELIVERY
- [ ] QR code unavailable before OUT_FOR_DELIVERY
- [ ] QR code available after OUT_FOR_DELIVERY
- [ ] Customer scans QR at delivery location (geofence within 15m)
- [ ] Payment released: vendor.wallet_balance += total, driver.wallet_balance += earnings
- [ ] Order status = DELIVERED
- [ ] Ledger status = RELEASED
- [ ] Vendor can withdraw earnings
- [ ] Driver can withdraw earnings

---

## 14. Production Deployment Checklist

- [ ] Update INTASEND_API_URL to production endpoint
- [ ] Set INTASEND_API_KEY and INTASEND_API_SECRET from IntaSend account
- [ ] Configure INTASEND_CALLBACK_URL to public domain
- [ ] Test deposit workflow with small amount (100 KES)
- [ ] Test withdrawal workflow
- [ ] Verify QR code generation on delivery
- [ ] Monitor IntaSend webhook callbacks
- [ ] Set up error alerting for failed transactions
- [ ] Document admin refund procedure for failed payouts
- [ ] Train support team on wallet troubleshooting

---

## References

- **IntaSend API Docs**: https://documentation.intasend.com/
- **Models**: [backend/models.py](../backend/models.py)
- **Payment Service**: [backend/services/payment.py](../backend/services/payment.py)
- **Main Routes**: [backend/main.py](../backend/main.py)
- **Frontend Wallet**: [frontend/src/pages/customer/Wallet.jsx](../frontend/src/pages/customer/Wallet.jsx)
- **Driver Earnings**: [frontend/src/pages/driver/Earnings.jsx](../frontend/src/pages/driver/Earnings.jsx)
- **Vendor Revenue**: [frontend/src/pages/vendor/Revenue.jsx](../frontend/src/pages/vendor/Revenue.jsx)
