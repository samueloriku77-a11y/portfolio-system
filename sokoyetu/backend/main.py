from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Optional
import datetime, os, shutil, uuid

import database
import models
import schemas
from auth import (
    get_password_hash, verify_password,
    create_access_token, get_current_user, require_role,
)


###i should unquote this remind me.............................................



















'''from services.payment import ( initiate_intasend_payment as initiate_stk_push ,   cancel_order_and_refund,
    initiate_intasend_checkout,
    initiate_intasend_payout,
)'''
from services.wallet_checkout import process_wallet_checkout
from services.security import (
    generate_order_ref, generate_handshake_keys,
    generate_qr_base64, process_double_blind_handshake, register_no_show, verify_geofence,
)
from config import UPLOAD_DIR
import api_posts

engine = database.engine
Base = database.Base
get_db = database.get_db

# App Setup

Base.metadata.create_all(bind=engine)
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="SokoYetu Hyperlocal Delivery",
    description="Escrow-protected hyperlocal marketplace with GPS handshake",
    version="1.0.0",
)

# Include posts router
app.include_router(api_posts.router)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# Auth Routes

@app.post("/api/auth/register", response_model=schemas.UserOut, tags=["Auth"])
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(400, "Email already registered.")

    if user.role == "DRIVER":
        if not user.student_id:
            raise HTTPException(400, "Drivers must provide a Student ID.")
        if db.query(models.User).filter(models.User.student_id == user.student_id).first():
            raise HTTPException(400, "Student ID already linked to an account. Gaming the system is prohibited.")

    new_user = models.User(
        email=user.email,
        name=user.name,
        phone=user.phone,
        hashed_password=get_password_hash(user.password),
        role=user.role,
        student_id=getattr(user, 'student_id', None),
        university=getattr(user, 'university', None),
        course_major=getattr(user, 'course_major', None),
        year_of_study=getattr(user, 'year_of_study', None),
        profile_photo_url=getattr(user, 'profile_photo_url', None),
        business_name=getattr(user, 'business_name', None),
        location_address=getattr(user, 'location_address', None),
        location_lat=getattr(user, 'location_lat', None),
        location_lng=getattr(user, 'location_lng', None),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create wallet for new user
    wallet = models.Wallet(user_id=new_user.id)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    new_user.wallet = wallet
    
    # Convert to UserOut schema for proper serialization
    return schemas.UserOut.model_validate(new_user)


@app.post("/api/auth/login", response_model=schemas.Token, tags=["Auth"])
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials.")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    # Convert user to UserOut schema to ensure proper serialization
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "user": schemas.UserOut.model_validate(user)
    }


@app.get("/api/auth/debug", tags=["Auth"])
def debug_me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,        "email": current_user.email,
        "role": current_user.role,
        "role_type": str(type(current_user.role))
    }


@app.get("/api/auth/me", response_model=schemas.UserOut, tags=["Auth"])
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.get("/api/wallet", response_model=schemas.WalletSummaryOut, tags=["Wallet"])
def get_wallet(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wallet = db.query(models.Wallet).filter(models.Wallet.user_id == current_user.id).first()
    if not wallet:
        raise HTTPException(404, "Wallet not found. Please contact support.")
    
    transactions = db.query(models.WalletTransaction).filter(
        models.WalletTransaction.user_id == current_user.id
    ).order_by(models.WalletTransaction.created_at.desc()).limit(20).all()

    return {
        "wallet_balance": wallet.balance,
        "transactions": transactions,
    }


@app.post("/api/wallet/deposit", response_model=schemas.WalletTransactionOut, tags=["Wallet"])
def deposit_to_wallet(
    request: schemas.WalletTransactionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if request.transaction_type.upper() != "DEPOSIT":
        raise HTTPException(400, "transaction_type must be DEPOSIT.")
    if request.amount <= 0:
        raise HTTPException(400, "Deposit amount must be greater than zero.")
    if not request.phone_number:
        raise HTTPException(400, "Phone number is required for deposit.")

    reference = f"WAL-{uuid.uuid4().hex[:10].upper()}"
    tx = models.WalletTransaction(
        user_id=current_user.id,
        amount=request.amount,
        transaction_type=models.WalletTransactionType.DEPOSIT.value,
        status=models.WalletTransactionStatus.PENDING.value,
        phone_number=request.phone_number,
        reference=reference,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    wallet = db.query(models.Wallet).filter(models.Wallet.user_id == current_user.id).first()
    if not wallet:
        raise HTTPException(404, "Wallet not found.")
    
    result = initiate_intasend_checkout(
        request.amount,
        request.phone_number,
        reference,
        f"SokoYetu wallet deposit {reference}",
    )
    tx.transaction_metadata = str(result)
    if result.get("error"):
        tx.status = models.WalletTransactionStatus.FAILED.value
    else:
        tx.status = models.WalletTransactionStatus.PENDING.value
        wallet.balance += request.amount  # Credit on successful payment initiation
        db.commit()
        db.refresh(wallet)
    db.commit()
    db.refresh(tx)
    return tx


@app.post("/api/wallet/withdraw", response_model=schemas.WalletTransactionOut, tags=["Wallet"])
def withdraw_from_wallet(
    request: schemas.WalletTransactionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if request.transaction_type.upper() != "WITHDRAWAL":
        raise HTTPException(400, "transaction_type must be WITHDRAWAL.")
    if request.amount < 100:
        raise HTTPException(400, "Minimum withdrawal amount is 100 KES.")
    if request.amount <= 0:
        raise HTTPException(400, "Withdrawal amount must be greater than zero.")
    
    wallet = db.query(models.Wallet).filter(models.Wallet.user_id == current_user.id).first()
    if not wallet:
        raise HTTPException(404, "Wallet not found.")
    if request.amount > wallet.balance:
        raise HTTPException(400, "Insufficient wallet balance.")
    if not request.phone_number:
        raise HTTPException(400, "Phone number is required for withdrawal.")

    reference = f"WAL-{uuid.uuid4().hex[:10].upper()}"
    tx = models.WalletTransaction(
        user_id=current_user.id,
        amount=request.amount,
        transaction_type=models.WalletTransactionType.WITHDRAWAL.value,
        status=models.WalletTransactionStatus.PENDING.value,
        phone_number=request.phone_number,
        reference=reference,
    )
    wallet.balance -= request.amount
    db.add(tx)
    db.commit()
    db.refresh(tx)
    db.refresh(wallet)

    result = initiate_intasend_payout(
        request.amount,
        request.phone_number,
        reference,
        f"SokoYetu wallet withdrawal {reference}",
    )
    tx.transaction_metadata = str(result)
    if result.get("error"):
        tx.status = models.WalletTransactionStatus.FAILED.value
        wallet.balance += request.amount  # Rollback on failure
        db.commit()
        db.refresh(wallet)
    else:
        tx.status = models.WalletTransactionStatus.COMPLETED.value
    db.commit()
    db.refresh(tx)
    db.refresh(wallet)
    return tx


@app.post("/api/auth/driver/upload-photo", tags=["Auth"])
async def upload_driver_photo(
    file: UploadFile = File(...),
    current_user: models.User = Depends(require_role("DRIVER")),
    db: Session = Depends(get_db),
):
    ext = file.filename.split(".")[-1]
    filename = f"driver_{current_user.id}_{uuid.uuid4().hex[:6]}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    current_user.profile_photo_url = f"/uploads/{filename}"
    db.commit()
    return {"url": current_user.profile_photo_url}


# Products

@app.get("/api/products", response_model=List[schemas.ProductOut], tags=["Products"])
def list_products(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Product).options(joinedload(models.Product.vendor)).filter(models.Product.is_available == True)
    if category:
        q = q.filter(models.Product.category == category)
    prods = q.all()
    return [schemas.ProductOut.model_validate(p) for p in prods]


@app.get("/api/products/{product_id}", response_model=schemas.ProductOut, tags=["Products"])
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Product).options(joinedload(models.Product.vendor)).filter(models.Product.id == product_id).first()
    if not p:
        raise HTTPException(404, "Product not found.")
    return schemas.ProductOut.model_validate(p)


@app.post("/api/vendor/products", response_model=schemas.ProductOut, tags=["Vendor"])
def create_product(
    product: schemas.ProductCreate,
    current_user: models.User = Depends(require_role("VENDOR", "ADMIN")),
    db: Session = Depends(get_db),
):
    v_id = current_user.id
    # Note: ProductCreate currently doesn't have vendor_id. 
    # For admins, we might need to add it, but for now we'll default to 1 (Demo Vendor) or require it.
    # To keep it simple for now and fix the 403:
    new_product = models.Product(vendor_id=v_id, **product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    # return serialized ProductOut with vendor preview
    return schemas.ProductOut.model_validate(new_product)


@app.put("/api/vendor/products/{product_id}", response_model=schemas.ProductOut, tags=["Vendor"])
def update_product(
    product_id: int,
    update: schemas.ProductUpdate,
    current_user: models.User = Depends(require_role("VENDOR", "ADMIN")),
    db: Session = Depends(get_db),
):
    p = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not p:
        raise HTTPException(404, "Product not found.")
    
    # Access control: VENDOR can only edit their own products
    if current_user.role == "VENDOR" and p.vendor_id != current_user.id:
        raise HTTPException(403, "You can only edit your own products.")

    for field, value in update.model_dump(exclude_none=True).items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return schemas.ProductOut.model_validate(p)


@app.delete("/api/vendor/products/{product_id}", tags=["Vendor"])
def delete_product(
    product_id: int,
    current_user: models.User = Depends(require_role("VENDOR", "ADMIN")),
    db: Session = Depends(get_db),
):
    p = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not p:
        raise HTTPException(404, "Product not found.")
    
    # Access control: VENDOR can only delete their own products
    if current_user.role == "VENDOR" and p.vendor_id != current_user.id:
        raise HTTPException(403, "You can only delete your own products.")

    db.delete(p)
    db.commit()
    return {"status": "Deleted"}


# Orders

@app.post("/api/orders/wallet-pay", response_model=schemas.OrderOut, tags=["Orders"])
def create_wallet_order(
    order_data: schemas.OrderCreate,
    current_user: models.User = Depends(require_role("CUSTOMER")),
    db: Session = Depends(get_db),
):
    return process_wallet_checkout(db, order_data, current_user)


@app.post("/api/orders", response_model=schemas.OrderOut, tags=["Orders"])
def create_order(
    order_data: schemas.OrderCreate,
    current_user: models.User = Depends(require_role("CUSTOMER")),
    db: Session = Depends(get_db),
):
    # Validate products belong to stated vendor
    total = 0.0
    items_to_create = []
    for item in order_data.items:
        product = db.query(models.Product).filter(
            models.Product.id == item.product_id,
            models.Product.vendor_id == order_data.vendor_id,
            models.Product.is_available == True,
        ).first()
        if not product:
            raise HTTPException(400, f"Product {item.product_id} not found or unavailable.")
        total += product.price * item.quantity
        items_to_create.append((product, item.quantity))

    order_ref = generate_order_ref(db)
    new_order = models.Order(
        order_ref=order_ref,
        customer_id=current_user.id,
        vendor_id=order_data.vendor_id,
        total_amount=total,
        delivery_fee=50.0,
        driver_earnings=40.0,
        platform_fee=10.0,
        delivery_address=order_data.delivery_address,
        delivery_lat=order_data.delivery_lat,
        delivery_lng=order_data.delivery_lng,
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # Add line items
    for product, qty in items_to_create:
        db.add(models.OrderItem(
            order_id=new_order.id,
            product_id=product.id,
            quantity=qty,
            unit_price=product.price,
        ))
    db.commit()

    # Initiate STK Push → escrow
    initiate_stk_push(db, new_order, order_data.phone_number)

    # Generate double-blind handshake keys
    generate_handshake_keys(db, new_order.id)

    db.refresh(new_order)
    return new_order


@app.get("/api/orders", response_model=List[schemas.OrderOut], tags=["Orders"])
def list_orders(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "CUSTOMER":
        return db.query(models.Order).filter(models.Order.customer_id == current_user.id).all()
    elif current_user.role == "VENDOR":
        return db.query(models.Order).filter(models.Order.vendor_id == current_user.id).all()
    elif current_user.role == "DRIVER":
        return db.query(models.Order).filter(models.Order.driver_id == current_user.id).all()
    return []


@app.get("/api/orders/{order_id}", response_model=schemas.OrderOut, tags=["Orders"])
def get_order(
    order_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found.")
    # ── Access control: only the involved parties can read an order ──
    is_owner = (
        (current_user.role == "CUSTOMER" and order.customer_id == current_user.id) or
        (current_user.role == "VENDOR"   and order.vendor_id   == current_user.id) or
        (current_user.role == "DRIVER"   and order.driver_id   == current_user.id)
    )
    if not is_owner:
        raise HTTPException(403, "You do not have access to this order.")
    return order


@app.get("/api/orders/{order_id}/qr", tags=["Orders"])
def get_order_qr(
    order_id: int,
    current_user: models.User = Depends(require_role("CUSTOMER")),
    db: Session = Depends(get_db),
):
    """Returns the customer's QR code (Part B of handshake) ONLY when driver has arrived (OUT_FOR_DELIVERY)."""
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.customer_id == current_user.id,
    ).first()
    if not order:
        raise HTTPException(404, "Order not found.")

    # QR is ONLY available when driver is actively delivering at location
    if order.status != models.OrderStatus.OUT_FOR_DELIVERY:
        raise HTTPException(400, f"QR not available yet. Current status: {order.status}. Driver must be at your location.")

    key = db.query(models.HandshakeKey).filter(
        models.HandshakeKey.order_id == order_id
    ).first()
    if not key or key.mated:
        raise HTTPException(404, "Handshake key not found or already used.")

    qr_image = generate_qr_base64(key.part_b_customer)
    return {
        "order_ref": order.order_ref,
        "qr_code": qr_image,
        "part_b": key.part_b_customer,
    }


@app.post("/api/driver/orders/{order_id}/arrived", tags=["Driver"])
def driver_arrived(
    order_id: int,
    driver_lat: float,
    driver_lng: float,
    current_user: models.User = Depends(require_role("DRIVER")),
    db: Session = Depends(get_db),
):
    """Mark that driver has arrived at delivery location. Customer can now scan QR."""
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.driver_id == current_user.id,
    ).first()
    if not order:
        raise HTTPException(404, "Order not found or not assigned to you.")

    if order.status != models.OrderStatus.ACCEPTED_BY_VENDOR:
        raise HTTPException(400, f"Order must be in ACCEPTED status. Current: {order.status}")

    # Verify driver is at delivery location (within 100m)
    from .services.security import verify_geofence
    if order.delivery_lat and order.delivery_lng:
        if not verify_geofence(driver_lat, driver_lng, order.delivery_lat, order.delivery_lng, max_radius_meters=100.0):
            return {
                "status": "Error",
                "message": "You must be within 100m of the delivery location."
            }

    order.status = models.OrderStatus.OUT_FOR_DELIVERY
    db.commit()
    db.refresh(order)

    return {
        "status": "Success",
        "message": "Driver arrived! Customer should now scan the QR code.",
        "order_ref": order.order_ref,
    }


@app.post("/api/orders/{order_id}/cancel", tags=["Orders"])
def cancel_order(
    order_id: int,
    current_user: models.User = Depends(require_role("CUSTOMER")),
    db: Session = Depends(get_db),
):
    return cancel_order_and_refund(db, order_id, current_user.id)


# Vendor Actions

@app.post("/api/vendor/orders/{order_id}/accept", tags=["Vendor"])
def vendor_accept_order(
    order_id: int,
    current_user: models.User = Depends(require_role("VENDOR")),
    db: Session = Depends(get_db),
):
    """Vendor accepts order → moves to ACCEPTED_BY_VENDOR. Refund window closes."""
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.vendor_id == current_user.id,
    ).first()
    if not order:
        raise HTTPException(404, "Order not found.")
    if order.status != models.OrderStatus.PENDING_VENDOR_APPROVAL:
        raise HTTPException(400, f"Cannot accept order in status: {order.status}")

    order.status = models.OrderStatus.PENDING_ADMIN_APPROVAL
    order.accepted_at = datetime.datetime.utcnow()
    db.commit()

    # Return Part A key to vendor
    key = db.query(models.HandshakeKey).filter(
        models.HandshakeKey.order_id == order_id
    ).first()

    return {
        "status": "Success",
        "message": "Order accepted. Refund window is now closed.",
        "order_ref": order.order_ref,
        "vendor_key_part_a": key.part_a_vendor if key else None,
    }


@app.post("/api/vendor/orders/{order_id}/ready", tags=["Vendor"])
def vendor_mark_ready(
    order_id: int,
    current_user: models.User = Depends(require_role("VENDOR")),
    db: Session = Depends(get_db),
):
    """Vendor marks order as ready → visible to nearby drivers."""
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.vendor_id == current_user.id,
    ).first()
    if not order:
        raise HTTPException(404, "Order not found.")
    if order.status != models.OrderStatus.ACCEPTED_BY_VENDOR:
        raise HTTPException(400, "Order must be accepted before marking ready.")
    order.status = models.OrderStatus.OUT_FOR_DELIVERY
    db.commit()
    return {"status": "Success", "message": "Order is now visible to drivers."}


@app.get("/api/vendor/orders", response_model=List[schemas.OrderOut], tags=["Vendor"])
def vendor_orders(
    current_user: models.User = Depends(require_role("VENDOR")),
    db: Session = Depends(get_db),
):
    return db.query(models.Order).filter(
        models.Order.vendor_id == current_user.id
    ).order_by(models.Order.created_at.desc()).all()


@app.get("/api/vendor/products", response_model=List[schemas.ProductOut], tags=["Vendor"])
def vendor_products(
    current_user: models.User = Depends(require_role("VENDOR", "ADMIN")),
    db: Session = Depends(get_db),
):
    prods = db.query(models.Product).options(joinedload(models.Product.vendor)).filter(
        models.Product.vendor_id == current_user.id
    ).all()
    return [schemas.ProductOut.model_validate(p) for p in prods]


# Driver Routes

@app.get("/api/driver/nearby-jobs", response_model=List[schemas.OrderOut], tags=["Driver"])
def nearby_jobs(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    current_user: models.User = Depends(require_role("DRIVER")),
    db: Session = Depends(get_db),
):
    """Returns unassigned orders ready for pickup."""
    orders = db.query(models.Order).filter(
        models.Order.status == models.OrderStatus.OUT_FOR_DELIVERY,
        models.Order.driver_id == None,
    ).all()
    return orders


@app.post("/api/driver/orders/{order_id}/accept", tags=["Driver"])
def driver_accept_job(
    order_id: int,
    current_user: models.User = Depends(require_role("DRIVER")),
    db: Session = Depends(get_db),
):
    from haversine import haversine, Unit
    # ── Race-condition protection: use with_for_update() to lock the row ──
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.status == models.OrderStatus.OUT_FOR_DELIVERY,
        models.Order.driver_id == None,
    ).with_for_update(skip_locked=True).first()
    if not order:
        raise HTTPException(409, "Job no longer available — another driver may have claimed it.")

    # Prevent a driver from accepting their own vendor's orders (conflict-of-interest)
    if order.vendor_id == current_user.id:
        raise HTTPException(403, "You cannot deliver your own vendor's orders.")

    order.driver_id = current_user.id
    db.commit()

    # ── Smart Batching: Auto-assign nearby orders on the same path ──
    nearby_radius_km = 2.0
    batched_orders = db.query(models.Order).filter(
        models.Order.id != order.id,
        models.Order.status == models.OrderStatus.OUT_FOR_DELIVERY,
        models.Order.driver_id == None,
        models.Order.vendor_id != current_user.id
    ).with_for_update(skip_locked=True).all()

    batched_count = 0
    for b_order in batched_orders:
        if b_order.delivery_lat and b_order.delivery_lng and order.delivery_lat and order.delivery_lng:
            try:
                dist = haversine((order.delivery_lat, order.delivery_lng), (b_order.delivery_lat, b_order.delivery_lng), unit=Unit.KILOMETERS)
                if dist <= nearby_radius_km:
                    b_order.driver_id = current_user.id
                    batched_count += 1
            except:
                pass
                
    if batched_count > 0:
        db.commit()

    msg = "Job accepted." + (f" Auto-batched {batched_count} nearby orders on your route!" if batched_count > 0 else " Navigate to vendor for pickup.")
    return {"status": "Success", "message": msg, "order_ref": order.order_ref}


@app.post("/api/driver/orders/{order_id}/handshake", tags=["Driver"])
def driver_handshake(
    order_id: int,
    handshake: schemas.HandshakeVerify,
    current_user: models.User = Depends(require_role("DRIVER")),
    db: Session = Depends(get_db),
):
    """QR scan + GPS verification to complete delivery and release escrow."""
    # ── Verify this driver is the ASSIGNED driver for this order ──
    order = db.query(models.Order).filter(models.Order.id == handshake.order_id).first()
    if not order:
        raise HTTPException(404, "Order not found.")
    if order.driver_id != current_user.id:
        raise HTTPException(403, "You are not the assigned driver for this order.")

    result = process_double_blind_handshake(
        db,
        handshake.order_id,
        handshake.qr_data,
        handshake.driver_lat,
        handshake.driver_lng,
    )
    if result["status"] == "Success":
        # Refresh order and send delivery notifications
        db.refresh(order)
        from .services.notifications import send_delivery_email, send_delivery_sms
        send_delivery_email(order)
        send_delivery_sms(order)
    return result


ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

@app.post("/api/driver/orders/{order_id}/no-show", tags=["Driver"])
async def driver_no_show(
    order_id: int,
    driver_lat: float,
    driver_lng: float,
    notes: Optional[str] = None,
    file: UploadFile = File(...),
    current_user: models.User = Depends(require_role("DRIVER")),
    db: Session = Depends(get_db),
):
    """No-Show Protection: GPS-verified photo required. Only the assigned driver can file."""
    # ── Verify this driver is the assigned driver ──
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found.")
    if order.driver_id != current_user.id:
        raise HTTPException(403, "You are not the assigned driver for this order.")

    # ── Validate file type (no executable uploads) ──
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(400, f"Invalid file type. Allowed: {ALLOWED_IMAGE_EXTENSIONS}")

    filename = f"noshow_{order_id}_{uuid.uuid4().hex[:8]}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    photo_url = f"/uploads/{filename}"

    return register_no_show(db, order_id, driver_lat, driver_lng, photo_url, notes)


@app.post("/api/driver/location/update", tags=["Driver"])
def update_driver_location(
    location: schemas.DriverLocationUpdate,
    current_user: models.User = Depends(require_role("DRIVER")),
    db: Session = Depends(get_db),
):
    """Update driver's real-time GPS location."""
    existing = db.query(models.DriverLocation).filter(
        models.DriverLocation.driver_id == current_user.id
    ).first()

    if existing:
        existing.lat = location.lat
        existing.lng = location.lng
        existing.updated_at = datetime.datetime.utcnow()
    else:
        new_loc = models.DriverLocation(
            driver_id=current_user.id,
            lat=location.lat,
            lng=location.lng,
        )
        db.add(new_loc)

    db.commit()
    return {"status": "Location updated"}


@app.get("/api/driver/profile/stats", tags=["Driver"])
def driver_stats(
    current_user: models.User = Depends(require_role("DRIVER")),
    db: Session = Depends(get_db),
):
    """Driver community impact & earnings stats."""
    deliveries = current_user.deliveries_completed or 0
    # Calculate estimated earnings (example: 40 KES per delivery)
    estimated_earnings = deliveries * 40
    
    return {
        "deliveries_completed": deliveries,
        "estimated_earnings_khs": estimated_earnings,
        "student_id": current_user.student_id,
        "university": current_user.university,
        "course_major": current_user.course_major,
        "year_of_study": current_user.year_of_study,
        "is_active": current_user.is_active_driver,
    }


# Disputes & Escalations

@app.post("/api/disputes", response_model=schemas.DisputeOut, tags=["Disputes"])
def create_dispute(
    dispute: schemas.DisputeCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Raise a manual dispute (e.g., no-show, quality issue)."""
    order = db.query(models.Order).filter(models.Order.id == dispute.order_id).first()
    if not order:
        raise HTTPException(404, "Order not found.")

    # Only customer, vendor, or driver can dispute
    if not (
        (current_user.role == "CUSTOMER" and order.customer_id == current_user.id) or
        (current_user.role == "VENDOR" and order.vendor_id == current_user.id) or
        (current_user.role == "DRIVER" and order.driver_id == current_user.id)
    ):
        raise HTTPException(403, "Unauthorized to dispute this order.")

    new_dispute = models.Dispute(
        order_id=dispute.order_id,
        raised_by_id=current_user.id,
        reason=dispute.reason,
        evidence_url=dispute.evidence_url,
    )
    db.add(new_dispute)
    db.commit()
    db.refresh(new_dispute)
    return new_dispute


@app.get("/api/disputes/{dispute_id}", response_model=schemas.DisputeOut, tags=["Disputes"])
def get_dispute(
    dispute_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dispute = db.query(models.Dispute).filter(models.Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(404, "Dispute not found.")
    return dispute


# Community Impact (Customer Dashboard)

@app.get("/api/customer/community-impact", tags=["Customer"])
def community_impact(
    current_user: models.User = Depends(require_role("CUSTOMER")),
    db: Session = Depends(get_db),
):
    """Show customer their community support metrics."""
    orders = db.query(models.Order).filter(
        models.Order.customer_id == current_user.id,
        models.Order.status == models.OrderStatus.DELIVERED,
    ).all()

    vendors_supported = len(set(o.vendor_id for o in orders))
    total_spent = sum(o.total_amount for o in orders)

    impact_message = (
        f"🌍 Amazing! You've helped {vendors_supported} local vendors! "
        f"Each purchase directly funds student drivers' education."
    )

    return {
        "deliveries_completed": len(orders),
        "vendors_supported": vendors_supported,
        "total_spent_khs": total_spent,
        "impact_message": impact_message,
    }


# Customer Wallet / Payment History

@app.get("/api/customer/orders/{order_id}/receipt", tags=["Customer"])
def get_receipt(
    order_id: int,
    current_user: models.User = Depends(require_role("CUSTOMER")),
    db: Session = Depends(get_db),
):
    """Return order receipt (detailed breakdown)."""
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.customer_id == current_user.id,
    ).first()
    if not order:
        raise HTTPException(404, "Order not found.")

    return {
        "order_ref": order.order_ref,
        "total_amount": order.total_amount,
        "delivery_fee": order.delivery_fee,
        "driver_earnings": order.driver_earnings,
        "platform_fee": order.platform_fee,
        "total_paid": order.total_amount + order.delivery_fee,
        "vendor_name": order.vendor.name if order.vendor else "N/A",
        "driver_name": order.driver.name if order.driver else "Unassigned",
        "delivery_address": order.delivery_address,
        "created_at": order.created_at,
        "delivered_at": order.delivered_at,
    }


@app.get("/api/customer/orders/{order_id}/driver", tags=["Customer"])
def get_order_driver_profile(
    order_id: int,
    current_user: models.User = Depends(require_role("CUSTOMER")),
    db: Session = Depends(get_db),
):
    """Get safe driver profile for customer (no sensitive data)."""
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.customer_id == current_user.id,
    ).first()
    if not order:
        raise HTTPException(404, "Order not found.")
    
    if not order.driver:
        return {"driver_profile": None, "message": "Driver not yet assigned"}
    
    # Return only safe, public-facing driver info
    return {
        "driver_profile": {
            "id": order.driver.id,
            "name": order.driver.name,
            "profile_photo_url": order.driver.profile_photo_url,
            "deliveries_completed": order.driver.deliveries_completed or 0,
            "university": order.driver.university,  # Social context only
        },
        "order_status": order.status,
    }


# Vendor Dashboard

@app.get("/api/vendor/dashboard", tags=["Vendor"])
def vendor_dashboard(
    current_user: models.User = Depends(require_role("VENDOR")),
    db: Session = Depends(get_db),
):
    """Vendor analytics dashboard."""
    orders = db.query(models.Order).filter(
        models.Order.vendor_id == current_user.id
    ).all()

    delivered = sum(1 for o in orders if o.status == models.OrderStatus.DELIVERED)
    pending = sum(1 for o in orders if o.status == models.OrderStatus.PENDING_VENDOR_APPROVAL)
    in_progress = sum(1 for o in orders if o.status == models.OrderStatus.OUT_FOR_DELIVERY)
    revenue = sum(o.total_amount for o in orders if o.status == models.OrderStatus.DELIVERED)

    return {
        "total_orders": len(orders),
        "delivered": delivered,
        "pending_approval": pending,
        "in_progress": in_progress,
        "total_revenue_khs": revenue,
        "average_order_value": revenue / delivered if delivered > 0 else 0,
    }


# Geofencing & Security

@app.post("/api/security/geofence-check", response_model=schemas.GeofenceCheckResponse, tags=["Security"])
def check_geofence(
    req: schemas.GeofenceCheckRequest,
    db: Session = Depends(get_db),
):
    """Check if driver is within geofence of customer delivery location."""
    from haversine import haversine, Unit
    
    distance = haversine(
        (req.driver_lat, req.driver_lng),
        (req.customer_lat, req.customer_lng),
        unit=Unit.METERS
    )
    
    return {
        "within_radius": distance <= 15,
        "distance_meters": distance,
        "radius_meters": 15,
    }


@app.post("/api/security/qr-generate", response_model=schemas.QRCodeResponse, tags=["Security"])
def generate_qr(
    req: schemas.GenerateQRRequest,
    current_user: models.User = Depends(require_role("CUSTOMER")),
    db: Session = Depends(get_db),
):
    """Generate or retrieve customer's QR code for order delivery."""
    order = db.query(models.Order).filter(
        models.Order.id == req.order_id,
        models.Order.customer_id == current_user.id,
    ).first()
    if not order:
        raise HTTPException(404, "Order not found.")

    key = db.query(models.HandshakeKey).filter(
        models.HandshakeKey.order_id == req.order_id
    ).first()
    if not key:
        raise HTTPException(404, "Handshake not initialized.")

    qr_code = generate_qr_base64(key.part_b_customer)

    return {
        "order_id": order.id,
        "qr_code_base64": qr_code,
        "part_b": key.part_b_customer,
        "handshake_id": key.id,
    }


@app.post("/api/security/handshake/mate", response_model=schemas.MateHandshakeResponse, tags=["Security"])
def mate_handshake(
    req: schemas.MateHandshakeRequest,
    current_user: models.User = Depends(require_role("DRIVER")),
    db: Session = Depends(get_db),
):
    """Execute double-blind handshake: verify driver location + QR match."""
    result = process_double_blind_handshake(
        db,
        req.order_id,
        req.part_b,
        req.driver_lat,
        req.driver_lng,
    )
    
    from haversine import haversine, Unit
    distance = haversine(
        (req.driver_lat, req.driver_lng),
        (req.customer_lat, req.customer_lng),
        unit=Unit.METERS
    )

    success = result.get("status") == "Success"
    if success:
        # Send notifications
        order = db.query(models.Order).filter(models.Order.id == req.order_id).first()
        if order:
            from .services.notifications import send_delivery_email, send_delivery_sms
            send_delivery_email(order)
            send_delivery_sms(order)

    return {
        "success": success,
        "message": result.get("message", ""),
        "distance_meters": distance,
        "mated": success,
    }


# Real-time Driver Tracking (WebSocket)

class DriverConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, driver_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[driver_id] = websocket

    def disconnect(self, driver_id: int):
        self.active_connections.pop(driver_id, None)

    async def broadcast_location(self, driver_id: int, location: dict):
        for conn_id, connection in self.active_connections.items():
            if conn_id != driver_id:
                try:
                    await connection.send_json({
                        "type": "driver_location",
                        "driver_id": driver_id,
                        **location,
                    })
                except:
                    pass


manager = DriverConnectionManager()


@app.websocket("/ws/driver-tracking/{driver_id}")
async def websocket_driver_tracking(
    driver_id: int,
    websocket: WebSocket,
):
    """Real-time GPS tracking broadcast for active deliveries."""
    await manager.connect(driver_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "location_update":
                location = {
                    "lat": data.get("lat"),
                    "lng": data.get("lng"),
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                }
                await manager.broadcast_location(driver_id, location)
    except WebSocketDisconnect:
        manager.disconnect(driver_id)


# Health Check

@app.get("/api/health", tags=["System"])
def health_check():
    """Service health check."""
    return {
        "status": "healthy",
        "service": "SokoYetu Hyperlocal Delivery API",
        "version": "1.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }


# NOTE: /api/driver/location/update at line ~455 is the canonical location update route.
# This duplicate is removed to avoid ambiguous routing.


# WebSocket — Real-time Driver GPS

class WSManager:
    def __init__(self):
        self.connections: Dict[int, WebSocket] = {}

    async def connect(self, ws: WebSocket, driver_id: int):
        await ws.accept()
        self.connections[driver_id] = ws

    def disconnect(self, driver_id: int):
        self.connections.pop(driver_id, None)

    async def broadcast(self, data: dict):
        for ws in list(self.connections.values()):
            try:
                await ws.send_json(data)
            except Exception:
                pass

ws_manager = WSManager()


@app.websocket("/ws/driver/{driver_id}")
async def driver_ws(websocket: WebSocket, driver_id: int, db: Session = Depends(get_db)):
    await ws_manager.connect(websocket, driver_id)
    try:
        while True:
            data = await websocket.receive_json()
            lat, lng = data.get("lat"), data.get("lng")
            if lat and lng:
                existing = db.query(models.DriverLocation).filter(
                    models.DriverLocation.driver_id == driver_id
                ).first()
                if existing:
                    existing.lat = lat
                    existing.lng = lng
                    existing.updated_at = datetime.datetime.utcnow()
                else:
                    db.add(models.DriverLocation(driver_id=driver_id, lat=lat, lng=lng))
                db.commit()
                await ws_manager.broadcast({"driver_id": driver_id, "lat": lat, "lng": lng})
    except WebSocketDisconnect:
        ws_manager.disconnect(driver_id)


# Admin Panel

@app.post("/api/admin/orders/{order_id}/approve", tags=["Admin"])
def admin_approve_order(
    order_id: int,
    approval: schemas.AdminOrderApprovalRequest,
    current_user: models.User = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    """Admin reviews images and approves/rejects order before vendor can upload."""
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found.")

    if approval.approved:
        order.status = models.OrderStatus.ACCEPTED_BY_VENDOR
        order.admin_id = current_user.id
        order.admin_approved_at = datetime.datetime.utcnow()
        order.admin_notes = approval.notes or ""
        
        # Mark images as verified if they exist
        images = db.query(models.ProductImage).filter(models.ProductImage.order_id == order_id).all()
        for image in images:
            image.is_verified = True
            image.admin_notes = approval.notes
    else:
        # Reject: order goes back to vendor for corrections
        order.status = models.OrderStatus.PENDING_VENDOR_APPROVAL
        order.admin_id = current_user.id
        order.admin_notes = approval.notes or "Rejected - please resubmit with better images"

    db.commit()
    return {"status": "Success", "message": f"Order {'approved' if approval.approved else 'rejected'}", "order_id": order_id}


@app.get("/api/admin/orders/pending", response_model=List[schemas.AdminOrderOut], tags=["Admin"])
def admin_pending_orders(
    current_user: models.User = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    """Get all orders pending admin approval."""
    orders = db.query(models.Order).filter(
        models.Order.status == models.OrderStatus.PENDING_ADMIN_APPROVAL
    ).order_by(models.Order.created_at.desc()).all()
    return orders


@app.get("/api/admin/vendors/unverified", response_model=List[schemas.UserOut], tags=["Admin"])
def admin_get_unverified_vendors(
    current_user: models.User = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    vendors = db.query(models.User).filter(
        models.User.role == "VENDOR",
        models.User.is_verified_vendor == False
    ).all()
    return vendors


@app.post("/api/admin/vendors/{vendor_id}/verify", tags=["Admin"])
def admin_verify_vendor(
    vendor_id: int,
    current_user: models.User = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    vendor = db.query(models.User).filter(models.User.id == vendor_id, models.User.role == "VENDOR").first()
    if not vendor:
        raise HTTPException(404, "Vendor not found")
    vendor.is_verified_vendor = True
    db.commit()
    return {"status": "Success", "message": "Vendor verified"}


@app.get("/api/admin/orders/{order_id}", response_model=schemas.AdminOrderOut, tags=["Admin"])
def admin_get_order(
    order_id: int,
    current_user: models.User = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    """Admin view full order details with images for verification."""
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found.")
    
    # Load images
    images = db.query(models.ProductImage).filter(
        models.ProductImage.order_id == order_id
    ).all()
    order.product_images = images
    
    return order


@app.get("/api/admin/products", response_model=List[schemas.ProductOut], tags=["Admin"])
def admin_get_all_products(
    current_user: models.User = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    """Admin can see all products, including hidden/out of stock."""
    prods = db.query(models.Product).options(joinedload(models.Product.vendor)).order_by(models.Product.created_at.desc()).all()
    return [schemas.ProductOut.model_validate(p) for p in prods]


@app.post("/api/vendor/products/{product_id}/images", tags=["Vendor"])
async def vendor_upload_product_image(
    product_id: int,
    order_id: Optional[int] = None,
    side_name: Optional[str] = None,  # e.g., "front", "side", "back"
    file: UploadFile = File(...),
    current_user: models.User = Depends(require_role("VENDOR", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Vendor uploads product images (minimum 2 different sides required)."""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Product not found.")
    
    # Access control
    if current_user.role == "VENDOR" and product.vendor_id != current_user.id:
        raise HTTPException(403, "You can only upload images for your own products.")

    # Validate file type
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(400, f"Invalid file type. Allowed: {ALLOWED_IMAGE_EXTENSIONS}")

    filename = f"product_{product_id}_{uuid.uuid4().hex[:8]}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    image_url = f"/uploads/{filename}"

    # Create ProductImage record
    product_image = models.ProductImage(
        product_id=product_id,
        order_id=order_id,
        image_url=image_url,
        side_name=side_name,
        uploaded_by_id=current_user.id,
    )
    db.add(product_image)
    
    # Update product's main image if first upload
    if not product.image_url:
        product.image_url = image_url
    
    db.commit()
    db.refresh(product_image)
    
    return {
        "success": True,
        "image_id": product_image.id,
        "image_url": image_url,
        "side_name": side_name,
        "message": "Image uploaded successfully"
    }


@app.get("/api/vendor/orders/{order_id}/images", response_model=List[schemas.ProductImageOut], tags=["Vendor"])
def vendor_get_order_images(
    order_id: int,
    current_user: models.User = Depends(require_role("VENDOR")),
    db: Session = Depends(get_db),
):
    """Vendor view all images uploaded for an order."""
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.vendor_id == current_user.id,
    ).first()
    if not order:
        raise HTTPException(404, "Order not found.")
    
    images = db.query(models.ProductImage).filter(
        models.ProductImage.order_id == order_id
    ).all()
    return images


@app.post("/api/delivery/verify-location", response_model=schemas.LocationVerificationResponse, tags=["Delivery"])
def verify_delivery_location(
    order_id: int,
    current_lat: float,
    current_lng: float,
    current_user: models.User = Depends(require_role("DRIVER")),
    db: Session = Depends(get_db),
):
    """Verify driver's current location against stated delivery address. Returns distance."""
    from haversine import haversine, Unit
    
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.driver_id == current_user.id,
    ).first()
    if not order:
        raise HTTPException(404, "Order not found or you're not the assigned driver.")

    # Calculate distance from current location to delivery point
    distance = haversine(
        (current_lat, current_lng),
        (order.delivery_lat, order.delivery_lng),
        unit=Unit.METERS
    )

    radius_meters = 200.0  # 200m radius for successful delivery
    within_radius = distance <= radius_meters

    return {
        "order_id": order_id,
        "delivery_address": order.delivery_address,
        "stated_lat": order.delivery_lat,
        "stated_lng": order.delivery_lng,
        "current_lat": current_lat,
        "current_lng": current_lng,
        "distance_meters": distance,
        "within_radius": within_radius,
        "radius_meters": radius_meters,
    }


@app.get("/api/admin/dashboard", response_model=schemas.AdminDashboardStats, tags=["Admin"])
def admin_dashboard(
    current_user: models.User = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db),
):
    """Admin dashboard overview (pending orders, vendors, drivers stats)."""
    pending_orders = db.query(models.Order).filter(
        models.Order.status == models.OrderStatus.PENDING_ADMIN_APPROVAL
    ).count()
    
    vendors = db.query(models.User).filter(
        models.User.role == models.UserRole.VENDOR
    ).count()
    
    drivers = db.query(models.User).filter(
        models.User.role == models.UserRole.DRIVER
    ).count()
    
    customers = db.query(models.User).filter(
        models.User.role == models.UserRole.CUSTOMER
    ).count()
    
    total_revenue = 0
    delivered_orders = db.query(models.Order).filter(
        models.Order.status == models.OrderStatus.DELIVERED
    ).all()
    for order in delivered_orders:
        total_revenue += order.total_amount

    pending_images = db.query(models.ProductImage).filter(
        models.ProductImage.is_verified == False
    ).count()

    return {
        "total_pending_orders": pending_orders,
        "total_vendors": vendors,
        "total_drivers": drivers,
        "total_customers": customers,
        "total_revenue": total_revenue,
        "pending_images_count": pending_images,
    }


# Health

@app.get("/api/health", tags=["System"])
def health():
    return {"status": "ok", "service": "SokoYetu API", "version": "1.0.0"}


# Main Entry Point

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
