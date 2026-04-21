import uuid
import qrcode
import io
import base64
from haversine import haversine, Unit
from sqlalchemy.orm import Session
import datetime

try:
    from .. import models
except ImportError:
    import models


def generate_order_ref(db: Session) -> str:
    """Generate a human-readable, unique order reference like SKY-2024-00042"""
    count = db.query(models.Order).count() + 1
    year = datetime.datetime.utcnow().year
    return f"SKY-{year}-{count:05d}"


def generate_handshake_keys(db: Session, order_id: int) -> models.HandshakeKey:
    part_a = uuid.uuid4().hex[:8].upper()       # Vendor token
    part_b = uuid.uuid4().hex[:16].upper()      # Customer QR payload

    key = models.HandshakeKey(
        order_id=order_id,
        part_a_vendor=part_a,
        part_b_customer=part_b,
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    return key


def generate_qr_base64(data: str) -> str:
    """Generate a QR code PNG as a base64-encoded data URI."""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def verify_geofence(
    lat1: float, lng1: float,
    lat2: float, lng2: float,
    max_radius_meters: float = 15.0
) -> bool:
    """Return True if two GPS points are within max_radius_meters of each other."""
    dist = haversine((lat1, lng1), (lat2, lng2), unit=Unit.METERS)
    return dist <= max_radius_meters


def process_double_blind_handshake(
    db: Session,
    order_id: int,
    scanned_qr: str,
    driver_lat: float,
    driver_lng: float,
) -> dict:
    """
    The core security handshake:
    1. Verify driver is geofenced to the customer's delivery location.
    2. Match scanned QR (Part B) against the stored key.
    3. Release escrow funds on success.
    """
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return {"status": "Error", "message": "Order not found."}

    if order.status != models.OrderStatus.OUT_FOR_DELIVERY:
        return {"status": "Error", "message": "Order is not in delivery state."}

    # 1. Geofence check against delivery coordinates
    if order.delivery_lat and order.delivery_lng:
        if not verify_geofence(driver_lat, driver_lng, order.delivery_lat, order.delivery_lng):
            return {
                "status": "Error",
                "message": "Geofence failed. You must be within 15m of the delivery address to complete handshake."
            }

    # 2. Key matching
    key = db.query(models.HandshakeKey).filter(
        models.HandshakeKey.order_id == order_id
    ).first()
    if not key:
        return {"status": "Error", "message": "Handshake key not found."}

    if key.mated:
        return {"status": "Error", "message": "Handshake already completed."}

    if key.part_b_customer != scanned_qr:
        return {"status": "Error", "message": "Invalid QR code. Handshake failed."}

    # 3. Mate the keys
    now = datetime.datetime.utcnow()
    key.mated = True
    key.mated_at = now
    key.mated_lat = driver_lat
    key.mated_lng = driver_lng

    order.status = models.OrderStatus.DELIVERED
    order.delivered_at = now

    db.commit()

    # Release escrow
    from .payment import release_funds
    release_funds(db, order_id)

    # Update driver stats
    driver = db.query(models.User).filter(models.User.id == order.driver_id).first()
    if driver:
        driver.deliveries_completed = (driver.deliveries_completed or 0) + 1
        db.commit()

    # Update customer community stats
    customer = db.query(models.User).filter(models.User.id == order.customer_id).first()
    if customer:
        customer.vendors_supported = (customer.vendors_supported or 0) + 1
        db.commit()

    return {
        "status": "Success",
        "message": "✅ Handshake successful! Funds released. Delivery confirmed.",
        "order_ref": order.order_ref,
    }


def register_no_show(
    db: Session,
    order_id: int,
    driver_lat: float,
    driver_lng: float,
    photo_url: str,
    notes: str = None,
) -> dict:
    """No-Show Protection gate: require GPS-verified photo before opening dispute."""
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return {"status": "Error", "message": "Order not found."}

    # Verify driver is at delivery location
    if order.delivery_lat and order.delivery_lng:
        if not verify_geofence(driver_lat, driver_lng, order.delivery_lat, order.delivery_lng, max_radius_meters=50.0):
            return {
                "status": "Error",
                "message": "You must be within 50m of the delivery address to file a no-show report."
            }

    verification = models.DeliveryVerification(
        order_id=order_id,
        driver_photo_url=photo_url,
        gps_lat=driver_lat,
        gps_lng=driver_lng,
        is_no_show=True,
        notes=notes,
    )
    db.add(verification)

    order.status = models.OrderStatus.DISPUTE
    db.commit()

    return {
        "status": "Success",
        "message": "No-show recorded with GPS evidence. Dispute submitted for admin review.",
        "verification_id": verification.id,
    }
