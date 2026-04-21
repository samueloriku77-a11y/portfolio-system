# SokoYetu Wallet System - Developer Quick Reference

## Most Important Files

| File | Purpose | Key Functions/Components |
|------|---------|--------------------------|
| `backend/models.py` | ORM definitions | `User.wallet_balance`, `WalletTransaction`, `Ledger` |
| `backend/services/payment.py` | Payment logic | `initiate_intasend_checkout()`, `release_funds()` |
| `backend/main.py` | API endpoints | POST `/wallet/deposit`, `/wallet/withdraw`, `/driver/orders/{}/arrived` |
| `frontend/src/pages/customer/Wallet.jsx` | Customer wallet UI | Deposit/withdraw forms |
| `frontend/src/pages/driver/Earnings.jsx` | Driver earnings UI | Transaction history, withdraw |
| `frontend/src/pages/vendor/Revenue.jsx` | Vendor revenue UI | Stats cards, withdraw |

## Critical Code Snippets

### Deposit Flow
```python
# 1. Backend receives deposit request
POST /api/wallet/deposit → {amount: 1000, phone_number: "254712345678"}

# 2. Create pending transaction
tx = WalletTransaction(
    user_id=user.id,
    amount=1000,
    transaction_type=WalletTransactionType.DEPOSIT.value,
    status=WalletTransactionStatus.PENDING.value,
    phone_number=phone,
    reference=f"WD_{timestamp}_{random}"
)

# 3. Call IntaSend checkout
initiate_intasend_checkout(amount=1000, phone=phone, reference=tx.reference)

# 4. Webhook confirms → user.wallet_balance += 1000, tx.status = COMPLETED
```

### Payment Release After Delivery
```python
def release_funds(db: Session, order_id: int):
    order = db.query(Order).filter(Order.id == order_id).first()
    vendor = db.query(User).filter(User.id == order.vendor_id).first()
    driver = db.query(User).filter(User.id == order.driver_id).first()
    
    # TWO WALLETS CREDITED
    vendor.wallet_balance += order.total_amount
    driver.wallet_balance += order.driver_earnings
    
    # Update escrow
    ledger = db.query(Ledger).filter(Ledger.order_id == order_id).first()
    ledger.status = LedgerStatus.RELEASED.value
    order.status = OrderStatus.DELIVERED.value
    db.commit()
```

### QR Code Timing (CRITICAL)
```python
@app.get("/api/orders/{order_id}/qr")
def get_order_qr(order_id: int):
    order = db.query(Order).filter(Order.id == order_id).first()
    
    # STRICT REQUIREMENT: Only OUT_FOR_DELIVERY status
    if order.status != OrderStatus.OUT_FOR_DELIVERY.value:
        raise HTTPException(status_code=403, detail="QR not yet available")
    
    return {"qr_data": "ORDER_123_VENDOR_5_DRIVER_7_<checksum>"}
```

### Driver Arrival (Unlocks QR)
```python
@app.post("/api/driver/orders/{order_id}/arrived")
def driver_arrived(order_id: int, body: DriverArrivalRequest):
    order = db.query(Order).filter(Order.id == order_id).first()
    vendor = db.query(User).filter(User.id == order.vendor_id).first()
    
    # Geofence CHECK
    distance = verify_geofence(
        lat1=body.driver_lat,
        lng1=body.driver_lng,
        lat2=vendor.location_lat,
        lng2=vendor.location_lng,
        radius_meters=100
    )
    
    if distance > 100:
        raise HTTPException(status_code=403, detail="Too far from vendor")
    
    # Transition to OUT_FOR_DELIVERY
    order.status = OrderStatus.OUT_FOR_DELIVERY.value
    db.commit()
    
    # NOW QR available
    return {"success": True}
```

## Enum Values (ALWAYS Use .value)

```python
# CORRECT ✓
status=WalletTransactionStatus.PENDING.value      # "PENDING"
status=WalletTransactionType.DEPOSIT.value        # "DEPOSIT"
status=LedgerStatus.HOLDING.value                 # "HOLDING"
status=OrderStatus.OUT_FOR_DELIVERY.value         # "OUT_FOR_DELIVERY"

# WRONG ✗
status=WalletTransactionStatus.PENDING             # <enum object>
status=OrderStatus.OUT_FOR_DELIVERY                # <enum object>
```

## Environment Variables Needed

```bash
# IntaSend Configuration
INTASEND_API_URL=https://sandbox.intasend.co/v1     # Change to production
INTASEND_API_KEY=your_api_key_here
INTASEND_API_SECRET=your_api_secret_here
INTASEND_CALLBACK_URL=https://yourdomain.com/api/wallet/callback

# Database (existing)
DATABASE_URL=sqlite:///sokoyetu.db

# JWT (existing)
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24
```

## Common Tasks

### Task: Add new transaction type (e.g., REFUND)
1. Add to `WalletTransactionType` enum in `models.py`
2. Update `WalletTransactionType` enum class
3. Update request schema in `schemas.py`
4. Add handling in `main.py` endpoint
5. Add test case in `test_payment.py`

### Task: Change geofence radius
```python
# File: frontend/src/pages/driver/Dashboard.jsx or services/security.py
# Change from 100m to 200m
distance = verify_geofence(..., radius_meters=200)  # 100m → 200m
```

### Task: Debug QR code not appearing
1. Check order.status == "OUT_FOR_DELIVERY"
2. Verify `/api/driver/orders/{id}/arrived` was called successfully
3. Check geofence validation (driver within 100m of vendor)
4. Verify order exists in database

### Task: Test withdrawal flow locally
```python
# 1. Create test user with wallet_balance > 0
user = User(name="test", email="test@test.com", wallet_balance=1000)

# 2. POST /api/wallet/withdraw
{
  "amount": 500,
  "transaction_type": "WITHDRAWAL",
  "phone_number": "254712345678"
}

# 3. Verify user.wallet_balance = 500 (deducted immediately)
# 4. Wait for IntaSend webhook or mock it
# 5. Verify WalletTransaction.status = COMPLETED
```

## Frontend Hooks & Utils

### useAuth() - Get user data
```javascript
const { user, refreshUser } = useAuth()
console.log(user.wallet_balance)     // Check balance
refreshUser()                         // Sync from backend
```

### api client - API calls
```javascript
// Deposit
const { data } = await api.post('/wallet/deposit', {
  amount: 1000,
  transaction_type: 'DEPOSIT',
  phone_number: '254712345678'
})

// Withdraw
const { data } = await api.post('/wallet/withdraw', {
  amount: 500,
  transaction_type: 'WITHDRAWAL',
  phone_number: '254712345678'
})

// Get balance & history
const { data } = await api.get('/wallet')
console.log(data.wallet_balance)
console.log(data.transactions)
```

### toast notifications
```javascript
import toast from 'react-hot-toast'

toast.success('Withdrawal initiated!')
toast.error('Insufficient balance')
toast.loading('Processing...')
```

## Testing Workflow

### Unit Test Template
```python
def test_wallet_deposit():
    # 1. Create user
    user = User(name="test", wallet_balance=0)
    db.add(user)
    db.commit()
    
    # 2. Call endpoint
    response = client.post('/wallet/deposit', {
        "amount": 1000,
        "phone_number": "254712345678",
        "transaction_type": "DEPOSIT"
    })
    
    # 3. Assert transaction created
    assert response.status_code == 200
    tx = db.query(WalletTransaction).filter(
        WalletTransaction.user_id == user.id
    ).first()
    assert tx.status == WalletTransactionStatus.PENDING.value
    assert tx.amount == 1000
```

### Integration Test Template
```python
def test_end_to_end_delivery():
    # 1. Customer places order
    order = Order(customer_id=1, vendor_id=2, driver_id=3, total_amount=5000)
    
    # 2. Vendor approves
    order.status = OrderStatus.ACCEPTED_BY_VENDOR.value
    
    # 3. Driver arrives (triggers OUT_FOR_DELIVERY)
    client.post('/driver/orders/123/arrived', {
        "driver_lat": -1.234, "driver_lng": 36.789
    })
    
    # 4. Get QR
    qr = client.get('/orders/123/qr')
    assert qr['qr_data'] != None
    
    # 5. Scan QR (triggers payment release)
    client.post('/driver/orders/123/handshake', {
        "qr_data": qr['qr_data'],
        "driver_lat": -1.234, "driver_lng": 36.789
    })
    
    # 6. Verify payment released
    vendor = db.query(User).filter(User.id == 2).first()
    driver = db.query(User).filter(User.id == 3).first()
    assert vendor.wallet_balance >= 5000
    assert driver.wallet_balance > 0
```

## Debugging Checklist

### QR Code Not Showing
- [ ] Order status is OUT_FOR_DELIVERY?
- [ ] Driver called `/arrived` endpoint?
- [ ] Geofence within 100m of vendor?
- [ ] Check browser console for API errors

### Payment Not Released
- [ ] QR scanned with correct code?
- [ ] Customer within 15m of delivery location?
- [ ] Order status transitioned to OUT_FOR_DELIVERY?
- [ ] Check backend logs for handshake validation errors

### Balance Not Updating
- [ ] Check user.wallet_balance in database
- [ ] Verify transaction created in WalletTransaction table
- [ ] Check transaction status (PENDING vs COMPLETED)
- [ ] IntaSend webhook might not have fired (check status endpoint)

### Withdrawal Stuck in PENDING
- [ ] Check IntaSend API response
- [ ] Verify phone number format (should be 254XXXXXXXXX)
- [ ] Check INTASEND_API_KEY is set correctly
- [ ] Look for IntaSend webhook delivery logs

## Performance Notes

- Transaction history limited to 20 most recent (update in main.py:wallet_get)
- Geofence calculations use Haversine (accurate to ~1% for earth distances)
- Ledger queries indexed on order_id for fast lookup
- Wallet balance denormalized on User (no aggregation queries)

## Security Reminders

1. **NEVER** store raw phone numbers without validation
2. **ALWAYS** use .value when storing enum to database
3. **QR code** must include checksum to prevent forgery
4. **Geofence** validation mandatory before payment release
5. **Balance** deducted immediately on withdrawal to prevent double-spend
6. **Ledger status** prevents duplicate fund release

## Contact & Issues

**API Integration Questions**: Check WALLET_AND_PAYMENT_FLOW.md
**Frontend Component Issues**: Review Earnings.jsx or Revenue.jsx as examples
**Database Questions**: Refer to models.py for schema
**IntaSend Issues**: See IntaSend documentation: https://documentation.intasend.com/
