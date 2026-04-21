from sqlalchemy import (
    Boolean, Column, ForeignKey, Integer, String,
    Float, DateTime, Text, Enum
)
from sqlalchemy.orm import relationship
import datetime
import enum

try:
    from .database import Base
except ImportError:
    from database import Base


class UserRole(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    VENDOR = "VENDOR"
    DRIVER = "DRIVER"
    ADMIN = "ADMIN"


class OrderStatus(str, enum.Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PENDING_VENDOR_APPROVAL = "PENDING_VENDOR_APPROVAL"
    PENDING_ADMIN_APPROVAL = "PENDING_ADMIN_APPROVAL"
    ADMIN_APPROVED = "ADMIN_APPROVED"
    ACCEPTED_BY_VENDOR = "ACCEPTED_BY_VENDOR"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED_BY_USER = "CANCELLED_BY_USER"
    DISPUTE = "DISPUTE"
    FAILED = "FAILED"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class LedgerStatus(str, enum.Enum):
    HOLDING = "HOLDING"
    RELEASED = "RELEASED"
    REFUNDED = "REFUNDED"


class VerificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    DISPUTED = "DISPUTED"


class WalletTransactionType(str, enum.Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


class WalletTransactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)
    role = Column(String, default=UserRole.CUSTOMER.value)
    phone = Column(String, nullable=True)
    # Driver specific
    student_id = Column(String, unique=True, index=True, nullable=True)
    profile_photo_url = Column(String, nullable=True)
    university = Column(String, nullable=True)
    course_major = Column(String, nullable=True)
    year_of_study = Column(String, nullable=True)
    is_active_driver = Column(Boolean, default=True)

    # Community stats
    deliveries_completed = Column(Integer, default=0)
    vendors_supported = Column(Integer, default=0)

    # Vendor specific
    business_name = Column(String, nullable=True)
    location_address = Column(Text, nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    is_verified_vendor = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    products = relationship("Product", back_populates="vendor", foreign_keys="Product.vendor_id")
    wallet = relationship("Wallet", back_populates="user", uselist=False)
    wallet_transactions = relationship("WalletTransaction", back_populates="user", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float)
    category = Column(String)  # "LOCAL_MARKET", "RESTAURANT"
    image_url = Column(String, nullable=True)  # Main thumbnail
    stock_qty = Column(Integer, default=0)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    vendor = relationship("User", back_populates="products", foreign_keys=[vendor_id])
    order_items = relationship("OrderItem", back_populates="product")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)  # Link to specific order
    image_url = Column(String, nullable=False)
    side_name = Column(String, nullable=True)  # e.g. "front", "side", "back"
    uploaded_by_id = Column(Integer, ForeignKey("users.id"))  # Vendor who uploaded
    is_verified = Column(Boolean, default=False)  # Admin verification
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    product = relationship("Product", back_populates="images")
    order = relationship("Order", back_populates="product_images")
    uploaded_by = relationship("User")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_ref = Column(String, unique=True, index=True)  # Human-readable e.g. SKY-2024-00001
    customer_id = Column(Integer, ForeignKey("users.id"))
    vendor_id = Column(Integer, ForeignKey("users.id"))
    driver_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    total_amount = Column(Float)
    delivery_fee = Column(Float, default=50.0)
    driver_earnings = Column(Float, default=40.0)   # Part of delivery fee
    platform_fee = Column(Float, default=10.0)      # Platform cut

    status = Column(String, default=OrderStatus.PENDING_PAYMENT)
    transaction_id = Column(String, nullable=True)

    # Admin verification
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    admin_approved_at = Column(DateTime, nullable=True)
    admin_notes = Column(Text, nullable=True)

    # Delivery address
    delivery_address = Column(Text, nullable=True)
    delivery_lat = Column(Float, nullable=True)
    delivery_lng = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    customer = relationship("User", foreign_keys=[customer_id])
    vendor = relationship("User", foreign_keys=[vendor_id])
    driver = relationship("User", foreign_keys=[driver_id])
    admin = relationship("User", foreign_keys=[admin_id])
    items = relationship("OrderItem", back_populates="order")
    ledger = relationship("Ledger", back_populates="order", uselist=False)
    handshake = relationship("HandshakeKey", back_populates="order", uselist=False)
    delivery_verifications = relationship("DeliveryVerification", back_populates="order")
    product_images = relationship("ProductImage", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)
    unit_price = Column(Float)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Ledger(Base):
    __tablename__ = "ledgers"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True)
    amount = Column(Float)
    status = Column(String, default=LedgerStatus.HOLDING)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    released_at = Column(DateTime, nullable=True)

    order = relationship("Order", back_populates="ledger")


class HandshakeKey(Base):
    __tablename__ = "handshake_keys"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True)
    part_a_vendor = Column(String)       # Sent to vendor on order placed
    part_b_customer = Column(String)     # Encoded in QR code for customer
    mated = Column(Boolean, default=False)
    mated_at = Column(DateTime, nullable=True)
    mated_lat = Column(Float, nullable=True)
    mated_lng = Column(Float, nullable=True)

    order = relationship("Order", back_populates="handshake")


class DeliveryVerification(Base):
    __tablename__ = "delivery_verifications"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    driver_photo_url = Column(String)
    gps_lat = Column(Float)
    gps_lng = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    is_no_show = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    order = relationship("Order", back_populates="delivery_verifications")


class DriverLocation(Base):
    __tablename__ = "driver_locations"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("users.id"), unique=True)
    lat = Column(Float)
    lng = Column(Float)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    driver = relationship("User")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    status = Column(String, default=PaymentStatus.PENDING)
    transaction_id = Column(String, unique=True, index=True)
    phone_number = Column(String)
    mpesa_receipt = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    order = relationship("Order")
    user = relationship("User")


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="wallet")


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    transaction_type = Column(String, default=WalletTransactionType.DEPOSIT.value)
    status = Column(String, default=WalletTransactionStatus.PENDING.value)
    phone_number = Column(String, nullable=True)
    reference = Column(String, unique=True, index=True)
    transaction_metadata = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="wallet_transactions")


class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    raised_by_id = Column(Integer, ForeignKey("users.id"))
    reason = Column(Text)
    status = Column(String, default=VerificationStatus.PENDING)
    evidence_url = Column(String, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    order = relationship("Order")
    raised_by = relationship("User")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    notification_type = Column(String)  # email, sms, whatsapp
    message = Column(Text)
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User")
    order = relationship("Order")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    body = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    author = relationship("User")
    is_hidden = Column(Boolean, default=False)


class PostComment(Base):
    __tablename__ = "post_comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    post = relationship("Post")
    user = relationship("User")


class PostLike(Base):
    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    post = relationship("Post")
    user = relationship("User")
