# Features - SokoYetu Hyperlocal Delivery

## Table of Contents

1. [Authentication & User Management](#authentication--user-management)
2. [Customer Features](#customer-features)
3. [Vendor Features](#vendor-features)
4. [Driver Features](#driver-features)
5. [Payment & Escrow System](#payment--escrow-system)
6. [Security & Anti-Fraud](#security--anti-fraud)
7. [Real-Time Features](#real-time-features)
8. [Notification System](#notification-system)
9. [Community & Impact](#community--impact)

---

## Authentication & User Management

### User Roles

#### 1. Customer
- Browse and purchase products
- Track orders in real-time
- View community impact contribution
- Request refunds (before vendor accepts)
- Receive order updates via email/SMS

**Registration Fields:**
- Email (unique)
- Password (hashed with Passlib)
- Name
- Phone number
- Delivery address (lat/lng)

#### 2. Vendor
- Manage product inventory
- Accept/reject orders
- View order analytics
- Track earnings
- Manage store details

**Registration Fields:**
- Email (unique)
- Password
- Store name
- Business phone
- Physical location (lat/lng)
- Store hours

#### 3. Driver
- Find nearby delivery jobs
- Accept deliveries
- Track real-time earnings
- Maintain student profile
- Complete deliveries with QR verification

**Registration Fields:**
- Email (unique)
- Password
- Name
- Student ID (unique - prevents multiple accounts)
- University/School name
- Major/Course
- Phone number
- Vehicle info (optional)

### Authentication Methods

#### JWT Token Authentication
- **Algorithm:** HS256
- **Expiration:** 24 hours (configurable)
- **Token Payload:**
  ```json
  {
    "sub": "user_uuid",
    "role": "CUSTOMER|VENDOR|DRIVER",
    "exp": 1234567890,
    "iat": 1234567890
  }
  ```

#### Password Security
- **Hashing:** Passlib with PBKDF2
- **Iterations:** 100,000
- **Minimum length:** 8 characters
- **Requirements:** Mixed case, numbers, special characters (optional)

#### Role-Based Access Control (RBAC)
- `/api/customer/*` - Customer endpoints only
- `/api/vendor/*` - Vendor endpoints only
- `/api/driver/*` - Driver endpoints only
- Public endpoints: `/api/products`, `/api/health`

---

## Customer Features

### 1. Product Browsing

**Features:**
- ✓ View all products
- ✓ Sort by category (Local Market, Restaurant)
- ✓ Price range filtering
- ✓ Product availability status
- ✓ Vendor rating display
- ✓ Product images and descriptions

**Endpoints:**
```
GET /api/products
GET /api/products/{id}
GET /api/products?category=LOCAL_MARKET
GET /api/products?price_min=100&price_max=500
```

### 2. Shopping Cart

**Features:**
- ✓ Add to cart
- ✓ Update quantity
- ✓ Remove items
- ✓ Clear cart
- ✓ Persistent storage (localStorage)
- ✓ Cart total calculation

**Client-Side Implementation:**
```javascript
// React component manages cart state
const cart = [
  { productId: "uuid", quantity: 2, price: 200 },
  { productId: "uuid", quantity: 1, price: 500 }
];
totalAmount = 900 + deliveryFee;
```

### 3. Order Placement

**Workflow:**
```
1. Confirm delivery address
2. Review order items & total
3. Initiate M-Pesa STK Push payment
4. Vendor receives notification
5. Order status: PENDING_VENDOR_APPROVAL
```

**Endpoints:**
```
POST /api/orders
{
  "items": [
    {"product_id": "uuid", "quantity": 2},
    {"product_id": "uuid", "quantity": 1}
  ],
  "delivery_address": {
    "lat": -1.2866,
    "lng": 36.8172,
    "notes": "Gate code 1234"
  }
}
```

### 4. Order Tracking

**Real-Time Updates:**
- ✓ Order status changes
- ✓ Vendor acceptance notification
- ✓ Driver location tracking (WebSocket)
- ✓ Estimated delivery time (ETA)
- ✓ Order history

**Status Flow:**
```
PENDING_PAYMENT
    ↓ (payment successful)
PENDING_VENDOR_APPROVAL
    ↓ (vendor accepts)
ACCEPTED_BY_VENDOR
    ↓ (driver accepts)
OUT_FOR_DELIVERY
    ↓ (driver arrives)
AWAITING_DELIVERY_VERIFICATION
    ↓ (QR handshake complete)
DELIVERED
    ↓
CLOSED
```

### 5. Cancellation & Refunds

**Refund Policy:**
- ✓ Full refund if cancelled **before vendor acceptance**
- ✗ No refund after vendor has accepted
- ✓ Automatic refund within 5 minutes
- ✓ Refund to original M-Pesa account

**Business Logic:**
```python
def cancel_order(order_id):
    order = get_order(order_id)
    if order.status == "PENDING_VENDOR_APPROVAL":
        refund_amount(order.transaction_id)
        order.status = "CANCELLED_BY_CUSTOMER"
        return "Refund initiated"
    else:
        return "Refund not allowed"
```

### 6. QR Code Verification

**For Customer:**
- ✓ View unique QR code for order
- ✓ Allows driver to scan for delivery verification
- ✓ Part B of double-blind handshake
- ✓ Includes order ID and security token

**QR Code Format:**
```
Data: {
  "order_id": "uuid",
  "customer_id": "uuid",
  "part_b_code": "random_code_123",
  "timestamp": "2024-01-15T10:00:00"
}
```

### 7. Community Impact Dashboard

**Metrics Displayed:**
- ✓ Total orders completed
- ✓ Number of vendors supported
- ✓ Total spent locally (KHS)
- ✓ Driver income generated
- ✓ Community contribution percentage
- ✓ Personal impact message

**Calculation Example:**
```
Vendor Support: 3 vendors
Personal Spend: 5,000 KHS
Driver Earnings: 500 KHS (from this customer)
Impact Message: "You've supported 3 community vendors
                 and helped drivers earn 500 KHS!"
```

---

## Vendor Features

### 1. Inventory Management

**Features:**
- ✓ Add new products
- ✓ Update stock quantity
- ✓ Edit product details (name, price, description)
- ✓ Set availability (available/unavailable)
- ✓ Manage product categories
- ✓ Batch operations

**Product Data:**
```json
{
  "name": "Fresh Tomatoes",
  "description": "Ripe, locally grown",
  "price": 150.00,
  "category": "LOCAL_MARKET",
  "stock_qty": 100,
  "is_available": true,
  "image_url": "s3://uploads/..."
}
```

### 2. Order Management

**Dashboard Views:**
- ✓ Pending orders (awaiting acceptance)
- ✓ Accepted orders (awaiting driver pickup)
- ✓ In-delivery orders (driver en route)
- ✓ Completed orders (delivered)
- ✓ Cancelled orders (customer cancelled)

**Order Actions:**
- ✓ **[ACCEPT]** - Confirm order, reserve stock
- ✓ **[REJECT]** - Decline order (refund issued)
- ✓ **[READY]** - Notify customer order is packed
- ✓ **[MARK DELIVERED]** - Complete order (escrow released)

**Workflow:**
```
1. Customer pays → Order created in PENDING_VENDOR_APPROVAL
2. Vendor clicks [ACCEPT] → Status: ACCEPTED_BY_VENDOR
3. Vendor packs → Clicks [READY] → Status: OUT_FOR_DELIVERY
4. Driver collects order
5. Driver delivers & QR handshake → Driver clicks [COMPLETE]
6. Order marked DELIVERED → Escrow funds released to vendor
```

### 3. Order Notifications

**Real-Time Alerts:**
- ✓ New order placed (sound + notification)
- ✓ Customer message/special instructions
- ✓ Estimated pickup time
- ✓ Driver assignment notification
- ✓ Driver location in real-time
- ✓ Delivery estimated time

**Notification Channels:**
- ✓ In-app notifications
- ✓ Email receipt
- ✓ SMS alert
- ✓ WhatsApp message (optional)

### 4. Sales Analytics

**Dashboard Metrics:**
- ✓ Total orders received
- ✓ Total orders completed
- ✓ Total revenue (KHS)
- ✓ Average order value
- ✓ Today's sales
- ✓ This week's sales
- ✓ Popular products
- ✓ Cancellation rate
- ✓ Customer satisfaction rating

**Time Series Charts:**
- ✓ Revenue over time
- ✓ Orders per day
- ✓ Hourly breakdown

### 5. Store Settings

**Configurable Options:**
- ✓ Store operating hours
- ✓ Delivery radius (km)
- ✓ Minimum order amount
- ✓ Delivery fee
- ✓ Store description
- ✓ Store phone number
- ✓ Store location (lat/lng)
- ✓ Store image/logo

### 6. Driver & Delivery Management

**Features:**
- ✓ View assigned drivers
- ✓ Driver rating display
- ✓ Real-time driver location
- ✓ Estimated pickup time
- ✓ Driver contact info
- ✓ Delivery history with this driver

---

## Driver Features

### 1. Job Discovery

**Finding Deliveries:**
- ✓ Nearby jobs (within 5 km)
- ✓ Distance to pickup (calculated)
- ✓ Distance to delivery (calculated)
- ✓ Estimated earnings
- ✓ Order summary (items, weight estimate)
- ✓ Customer ratings
- ✓ Vendor ratings

**Job Listing:**
```json
{
  "order_id": "uuid",
  "vendor_name": "Fresh Market",
  "vendor_rating": 4.8,
  "distance_to_pickup": "2.3 km",
  "distance_to_delivery": "4.5 km",
  "estimated_earnings": 100,
  "items_count": 3,
  "special_instructions": "Fragile items"
}
```

### 2. Accept & Pick Up

**Workflow:**
1. Driver views nearby jobs
2. Clicks **[ACCEPT JOB]**
3. Order assigned to driver
4. Driver navigates to vendor
5. Driver collects order
6. Driver confirms pickup

**Endpoints:**
```
GET /api/driver/nearby-jobs
POST /api/driver/orders/{id}/accept
POST /api/driver/pickup/{id}/confirm
```

### 3. Real-Time Tracking

**GPS Location Updates:**
- ✓ Current location (lat/lng)
- ✓ Update frequency: 30 seconds
- ✓ Speed calculation
- ✓ Heading direction
- ✓ Location history (last 24 hours)

**WebSocket Broadcasting:**
```javascript
// Driver app sends location
POST /api/driver/location/update
{
  "driver_id": "uuid",
  "lat": -1.2866,
  "lng": 36.8172
}

// Customer app receives updates via WebSocket
ws://localhost:8000/ws/driver-tracking/{driver_id}
```

**Vendor View:**
- ✓ See driver on map
- ✓ Real-time ETA
- ✓ Driver's phone available
- ✓ Pause/resume delivery option

**Customer View:**
- ✓ Driver location on map
- ✓ Live ETA countdown
- ✓ Driver's vehicle info
- ✓ Driver's rating
- ✓ Contact driver button

### 4. Delivery Completion

**QR Code Scanning:**
1. Driver arrives at delivery location
2. Customer shows QR code (Part B)
3. Driver scans with phone camera
4. System verifies:
   - ✓ Within geofence (15m radius)
   - ✓ QR code valid
   - ✓ Timestamp within window
5. Delivery marked complete

**Double-Blind Handshake:**
```
Vendor Generated (at acceptance):
├─ Part A QR code
├─ Includes vendor random key
└─ Embedded delivery location & window

Customer Has (at order):
├─ Part B QR code
├─ Includes customer random key
└─ Valid only for this order

Driver Verifies (at delivery):
├─ Scan Part A (vendor)
├─ Scan Part B (customer)
├─ System matches both parts
├─ Confirms location within 15m
└─ ✓ Delivery verified
```

### 5. No-Show Reporting

**If Customer Unavailable:**
1. Driver arrives at location
2. Waits for customer (escalation window)
3. If customer doesn't appear:
   - Driver clicks **[NO-SHOW]**
   - Takes photo as evidence
   - GPS location recorded
   - Sends final notification
4. System creates dispute
5. Admin reviews evidence

**Evidence Requirements:**
- ✓ GPS location (within 50m delivery radius)
- ✓ Photo timestamp (current time)
- ✓ Photo showing delivery location
- ✓ Message timestamp

**Endpoint:**
```
POST /api/driver/orders/{id}/no-show
{
  "photo_url": "s3://uploads/no-show-123.jpg",
  "lat": -1.2866,
  "lng": 36.8172,
  "message": "Customer not available"
}
```

### 6. Earnings Tracking

**Dashboard Metrics:**
- ✓ Today's earnings
- ✓ This week's earnings
- ✓ This month's earnings
- ✓ Total earnings (lifetime)
- ✓ Average per delivery
- ✓ Tips received
- ✓ Bonuses earned

**Earnings Breakdown:**
```
Commission: 10% of order value
Example: 500 KHS order → 50 KHS commission
Tips: Variable (customer decides)
Bonuses: Incentives for completing X orders/week
Deductions: None (platform covers payment processing)
```

**Earnings History:**
- ✓ Detailed transactions
- ✓ Date and time
- ✓ Order reference
- ✓ Customer name
- ✓ Amount earned
- ✓ Tip amount
- ✓ Status (pending/paid)

### 7. Student Profile

**Information Displayed:**
- ✓ Student name
- ✓ University/School
- ✓ Major/Course
- ✓ Year of study
- ✓ Verification badge
- ✓ Join date

**Purpose:**
- ✓ Build trust with customers
- ✓ Community support for students
- ✓ Potential student discounts
- ✓ Help track driver identity

**Registration:**
- ✓ Requires valid student ID
- ✓ Student ID must be unique (prevents duplicate accounts)
- ✓ School verification (optional)

---

## Payment & Escrow System

### 1. M-Pesa Integration

**STK Push Workflow:**
```
Customer places order ($500)
    ↓
System calls M-Pesa STK Push API
    ↓
Customer's phone shows payment prompt
    ↓
Customer enters PIN
    ↓
Payment confirmed/failed
    ↓
System receives callback
    ↓
Order status updated
```

**Endpoints:**
```
POST /api/mpesa/callback
- Receives M-Pesa transaction status
- Updates order payment status
- Triggers order notifications

GET /api/mpesa/transaction/{id}
- Check payment status
```

### 2. Escrow System

**States:**
```
HOLDING
├─ Order placed, payment pending
├─ Funds in escrow (not available)
└─ Refund possible if cancelled

RELEASED
├─ Delivery verified
├─ Funds released to vendor
├─ Driver commission calculated
└─ Final state

REFUNDED
├─ Customer cancelled before acceptance
├─ Funds returned to customer
└─ No fees charged
```

**Ledger Entry:**
```json
{
  "order_id": "uuid",
  "status": "HOLDING",
  "amount": 500.00,
  "platform_fee": 25.00,
  "driver_commission": 50.00,
  "vendor_receives": 425.00,
  "created_at": "2024-01-15T10:00:00",
  "updated_at": "2024-01-15T10:00:00"
}
```

### 3. Fee Structure

**Order Value: 500 KHS**

```
Subtotal:           500 KHS
Platform Fee (5%):  -25 KHS
Driver Commission: -50 KHS (10%)
────────────────────────────
Vendor Receives:    425 KHS
```

**Payment Breakdown (Customer perspective):**
```
Order Total:        500 KHS
Delivery Fee:       100 KHS (vendor's fee)
────────────────────────────
Customer Pays:      600 KHS
```

### 4. Refund Logic

**Allowed Cases:**
- ✓ Customer cancels BEFORE vendor accepts
- ✓ Full refund to customer's M-Pesa account
- ✓ Immediate (within 5 minutes)
- ✓ No cancellation fee

**Not Allowed Cases:**
- ✗ After vendor has accepted
- ✗ After driver has accepted
- ✗ After delivery started
- ✗ After delivery completed

**Code Protection:**
```python
def cancel_order_and_refund(order_id):
    order = db.get_order(order_id)
    
    # Refund gate - prevents abuse
    if order.status == "PENDING_VENDOR_APPROVAL":
        payment_service.refund(order.transaction_id, order.amount)
        order.status = "CANCELLED_BY_CUSTOMER"
        ledger = db.get_ledger(order_id)
        ledger.status = "REFUNDED"
        return {"status": "Success", "message": "Refund initiated"}
    else:
        return {"status": "Error", "message": "Refund not allowed"}
```

---

## Security & Anti-Fraud

### 1. GPS Geofencing

**Delivery Verification (15m radius):**
```
Delivery Location: -1.2866, 36.8172

Driver arrives at: -1.2868, 36.8174
Distance: 322 meters (3.2 km) ❌ OUTSIDE RADIUS
Result: Delivery blocked

Driver arrives at: -1.28663, 36.81722
Distance: 3 meters ✓ WITHIN RADIUS
Result: Delivery allowed
```

**Formula (Haversine):**
```python
def calculate_distance(lat1, lng1, lat2, lng2):
    R = 6371  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    
    a = sin²(dlat/2) + cos(lat1) × cos(lat2) × sin²(dlng/2)
    c = 2 × asin(√a)
    distance = R × c × 1000  # Convert to meters
    
    return distance
```

### 2. Double-Blind Handshake

**Prevents Delivery Fraud:**

**Part A (Vendor):**
- Generated when vendor accepts order
- Contains: vendor_key_a + order_id + timestamp
- Encoded as QR code
- Vendor keeps Part A

**Part B (Customer):**
- Generated when customer views order
- Contains: customer_key_b + order_id + timestamp
- Encoded as QR code
- Customer shows Part B at delivery

**Verification:**
- Driver scans both codes at delivery location
- System verifies:
  - ✓ Part A and Part B match order ID
  - ✓ Keys match expected values
  - ✓ Timestamp within window (±2 minutes)
  - ✓ GPS location within geofence
- ✗ Any mismatch → Dispute created

**Prevents:**
- ✗ Delivery to wrong address
- ✗ Vendor giving order to wrong driver
- ✗ Customer claiming non-receipt
- ✗ Driver keeping order without proof
- ✗ Collusion between parties

### 3. No-Show Protection

**GPS-Verified Evidence:**
1. Driver clicks "No-Show"
2. Takes photo at delivery location
3. System captures:
   - GPS coordinates
   - Photo timestamp
   - Driver's device ID
4. Verification checks:
   - ✓ GPS within 50m of delivery location
   - ✓ Photo timestamp within last 2 minutes
   - ✓ Photo geotag matches location
5. Creates dispute with evidence
6. Admin reviews and decides:
   - Refund customer (no fee)
   - Pay driver (full commission)
   - OR investigate further

**Prevents:**
- ✗ Driver falsely claiming no-show
- ✗ Driver collecting multiple payments
- ✗ Customer disputing legitimate delivery

### 4. Anti-GPS Spoofing

**Velocity Check:**
```
Previous location: -1.2866, 36.8172 (10:00:00)
Current location:  -1.3000, 36.8300 (10:00:05)
Time elapsed: 5 seconds
Distance: 1.5 km

Velocity: 1500m / 5s = 300 m/s = 1080 km/h ❌ IMPOSSIBLE
Result: Location rejected, possible spoof detected
```

**Threshold:** Max 150 km/h (allows highways)

**Historical Check:**
- Track last 10 locations
- Verify realistic path
- Detect sudden jumps
- Flag suspicious patterns

### 5. Student ID Uniqueness

**Prevents Multiple Driver Accounts:**
- Each student ID unique in database
- Driver registration fails if ID already exists
- Database constraint: UNIQUE(student_id)

**Benefit:**
- One person can't create multiple driver accounts
- Prevents earning exploitation
- Helps track driver identity

---

## Real-Time Features

### 1. WebSocket Live Tracking

**Connection:**
```
Driver App:
├─ Updates location every 30 seconds
├─ POST /api/driver/location/update
│  {lat, lng, timestamp, speed}
└─ Server broadcasts to connected clients

Vendor/Customer Apps:
├─ Connect to WebSocket: /ws/driver-tracking/{driver_id}
├─ Receive location updates in real-time
└─ Update driver marker on map
```

**Benefits:**
- ✓ No polling (efficient)
- ✓ Real-time delivery tracking
- ✓ ETA calculation
- ✓ Driver location history

**Frontend Implementation:**
```javascript
// Connect to real-time tracking
const ws = new WebSocket(
  `ws://localhost:8000/ws/driver-tracking/${driverId}`
);

ws.onmessage = (event) => {
  const { lat, lng, timestamp } = JSON.parse(event.data);
  // Update map marker
  updateMapMarker(lat, lng);
  // Calculate ETA
  calculateETA(lat, lng, deliveryLat, deliveryLng);
};

ws.onerror = (error) => {
  console.error('Connection lost, retrying...');
  reconnect();
};
```

### 2. Real-Time Notifications

**Order Events:**
- ✓ Order placed (vendor notification)
- ✓ Order accepted (customer notification)
- ✓ Order ready (customer notification)
- ✓ Driver assigned (vendor & customer)
- ✓ Driver arriving soon (customer)
- ✓ Order delivered (all parties)
- ✓ Payment released (vendor)

**Delivery:**
- ✓ In-app notifications (instant)
- ✓ Email notifications (within 30 seconds)
- ✓ SMS notifications (within 1 minute)

### 3. Live Order Status

**Real-Time Updates:**
- ✓ Order status changes
- ✓ Driver location updates
- ✓ ETA countdown
- ✓ Notifications bell
- ✓ Activity timeline

**Activity Timeline:**
```
10:00 - Order placed by customer
10:02 - Payment received
10:05 - Vendor accepted order
10:15 - Order ready for delivery
10:16 - Driver James assigned
10:25 - Driver arriving (2 min away)
10:26 - Driver at vendor
10:27 - Driver collected order
10:35 - Driver arriving at delivery (3 min away)
10:37 - Driver at location
10:38 - QR verified, delivery complete
10:40 - Payment released to vendor
```

---

## Notification System

### 1. Email Notifications

**Styled HTML Receipts:**
- ✓ Order confirmation
- ✓ Vendor accepted notification
- ✓ Driver assigned notification
- ✓ Delivery complete receipt
- ✓ Receipt with itemization
- ✓ Vendor and driver info
- ✓ Community impact statement

**Template Variables:**
```
{{ order_id }}
{{ order_date }}
{{ customer_name }}
{{ vendor_name }}
{{ driver_name }}
{{ items_list }}
{{ delivery_address }}
{{ total_amount }}
{{ platform_fee_breakdown }}
{{ driver_earnings }}
{{ estimated_delivery_time }}
```

**Example HTML:**
```html
<body style="font-family: Arial; background: #f5f5f5;">
  <div class="container">
    <header style="background: #1a1a2e; color: white; padding: 20px;">
      <h1>ORDER CONFIRMED</h1>
      <p>Order #{{ order_id }}</p>
    </header>
    
    <section class="items">
      <h2>Order Details</h2>
      {% for item in items %}
      <div class="item-row">
        <span>{{ item.product_name }}</span>
        <span>{{ item.quantity }}x</span>
        <span>{{ item.subtotal }} KHS</span>
      </div>
      {% endfor %}
    </section>
    
    <section class="vendor">
      <h2>From: {{ vendor_name }}</h2>
      <p>📍 {{ vendor_location }}</p>
      <p>⭐ {{ vendor_rating }} rating</p>
    </section>
    
    <section class="driver">
      <h2>Delivered by: {{ driver_name }}</h2>
      <p>🎓 {{ driver_year }} year at {{ driver_university }}</p>
      <p>⭐ {{ driver_rating }} rating</p>
    </section>
    
    <section class="impact">
      <h2>Your Impact</h2>
      <p>You've supported 1 community vendor</p>
      <p>You've helped {{ driver_name }} earn 50 KHS</p>
    </section>
    
    <footer>
      <p>Thank you for supporting local!</p>
    </footer>
  </div>
</body>
```

### 2. SMS Notifications

**Messages Sent To:**
- **Vendor:** "Order confirmed! #123456. Accept in app."
- **Vendor:** "Driver James arriving to pickup soon"
- **Vendor:** "Driver marked delivery complete. Funds released!"
- **Customer:** "Payment received. Vendor confirmed!"
- **Customer:** "Driver James is on the way (2 mins)"
- **Customer:** "Order delivered! Thank you for your purchase"
- **Driver:** "Order accepted. Pickup at Fresh Market. Earn 50 KHS"
- **Driver:** "Delivery delivered! 50 KHS added to wallet"

### 3. WhatsApp Notifications (Optional)

- ✓ Rich media messages
- ✓ Order confirmation with image
- ✓ Driver status updates
- ✓ Delivery photo confirmation
- ✓ Payment receipt

---

## Community & Impact

### 1. Community Dashboard

**Customer View:**
- ✓ Total purchases (count and value)
- ✓ Vendors supported (count)
- ✓ Driver earnings contributed
- ✓ Personal impact score
- ✓ Global impact leaderboard

**Metrics Calculation:**
```
Deliveries Completed: Count of DELIVERED orders
Vendors Supported: Count of unique vendor_ids
Total Spent (KHS): Sum of order amounts
Driver Earnings Funded: Sum of driver commissions
Impact Score: (deliveries × 10) + (vendors × 50) + (amount/100)
```

### 2. Vendor Community

**Features:**
- ✓ Vendor rating system
- ✓ Review comments from customers
- ✓ Total orders delivered
- ✓ Response time statistics
- ✓ Customer satisfaction rating

**Rating Calculation:**
```
Rating = (Sum of all ratings) / Count of ratings
(1.0 to 5.0 stars)
```

### 3. Driver Community

**Features:**
- ✓ Driver rating and reviews
- ✓ Deliveries completed
- ✓ Total earnings
- ✓ Student profile verification badge
- ✓ Specialization (fast delivery, careful handling, etc.)

### 4. Global Impact Summary

**Platform-Wide Stats:**
- ✓ Total orders completed
- ✓ Total local spending
- ✓ Total vendor earnings
- ✓ Total driver earnings
- ✓ "X orders | Y KHS supported" banner

---

## Advanced Features

### 1. Dispute Resolution

**Dispute Creation:**
- Customer claims non-receipt
- Driver claims no-show
- Quality complaint
- Wrong item delivered

**Resolution Process:**
1. Auto-collect evidence:
   - GPS location
   - Photographic evidence
   - Transaction history
   - Messages between parties
2. Admin review dashboard
3. Decision options:
   - Refund customer
   - Pay driver
   - Split decision
   - Investigate further
4. Automated payout on decision

### 2. Analytics Dashboard (Admin)

**Key Metrics:**
- ✓ Daily active users (by role)
- ✓ Orders per day
- ✓ Revenue trends
- ✓ Top vendors
- ✓ Top drivers
- ✓ Customer acquisition cost
- ✓ Churn rate
- ✓ Dispute rate
- ✓ Payment success rate

### 3. Performance Bonuses

**Driver Bonuses:**
- ✓ 10 deliveries/week → 5% bonus
- ✓ 25 deliveries/week → 10% bonus
- ✓ 50 deliveries/week → 15% bonus
- ✓ 5-star rating (10+ reviews) → 5% bonus
- ✓ Emergency rush hour deliveries → 20% surge

**Vendor Bonuses:**
- ✓ 50 orders/month → featured listing
- ✓ 4.5+ rating → "Trusted Vendor" badge
- ✓ 100% on-time delivery → discount on fees

---

## API Endpoints Summary

| Category | Method | Endpoint | Role |
|----------|--------|----------|------|
| Auth | POST | /api/auth/register | All |
| Auth | POST | /api/auth/login | All |
| Auth | GET | /api/auth/me | Auth'd |
| Products | GET | /api/products | All |
| Products | GET | /api/products/{id} | All |
| Products | POST | /api/vendor/products | Vendor |
| Orders | POST | /api/orders | Customer |
| Orders | GET | /api/orders | Auth'd |
| Orders | POST | /api/orders/{id}/cancel | Customer |
| Orders | GET | /api/orders/{id}/qr | Customer |
| Vendor | POST | /api/vendor/orders/{id}/accept | Vendor |
| Vendor | POST | /api/vendor/orders/{id}/ready | Vendor |
| Driver | GET | /api/driver/nearby-jobs | Driver |
| Driver | POST | /api/driver/orders/{id}/accept | Driver |
| Driver | POST | /api/driver/location/update | Driver |
| Driver | POST | /api/driver/orders/{id}/complete | Driver |
| Disputes | POST | /api/disputes | Auth'd |
| Security | POST | /api/security/geofence-check | Driver |
| Community | GET | /api/customer/community-impact | Customer |

---

See [TESTING.md](TESTING.md) to verify all features with 56+ test cases.
See [ARCHITECTURE.md](ARCHITECTURE.md) for technical implementation details.
