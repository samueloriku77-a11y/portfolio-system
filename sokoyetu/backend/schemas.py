from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


#  USER & AUTH SCHEMAS

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None
    role: str = "CUSTOMER"  # CUSTOMER | VENDOR | DRIVER
    student_id: Optional[str] = None
    university: Optional[str] = None
    course_major: Optional[str] = None
    year_of_study: Optional[str] = None
    profile_photo_url: Optional[str] = None
    # Vendor specific
    business_name: Optional[str] = None
    location_address: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    phone: Optional[str] = None
    wallet: Optional['WalletOut'] = None
    student_id: Optional[str] = None
    profile_photo_url: Optional[str] = None
    university: Optional[str] = None
    course_major: Optional[str] = None
    year_of_study: Optional[str] = None
    deliveries_completed: int = 0
    vendors_supported: int = 0
    is_active_driver: bool = True
    
    # Vendor specific
    business_name: Optional[str] = None
    location_address: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    is_verified_vendor: bool = False
    
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


class LoginRequest(BaseModel):
    email: str
    password: str


class WalletTransactionCreate(BaseModel):
    amount: float
    transaction_type: str  # DEPOSIT | WITHDRAWAL
    phone_number: Optional[str] = None


class WalletTransactionOut(BaseModel):
    id: int
    user_id: int
    amount: float
    transaction_type: str
    status: str
    phone_number: Optional[str] = None
    reference: str
    transaction_metadata: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WalletOut(BaseModel):
    id: int
    user_id: int
    balance: float
    created_at: datetime

    class Config:
        from_attributes = True


class WalletSummaryOut(BaseModel):
    wallet_balance: float
    transactions: List[WalletTransactionOut]


class DriverProfileUpdate(BaseModel):
    course_major: Optional[str] = None
    year_of_study: Optional[str] = None
    profile_photo_url: Optional[str] = None
    is_active_driver: Optional[bool] = None


#  PRODUCT SCHEMAS

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: str  # LOCAL_MARKET | RESTAURANT
    stock_qty: int = 0
    is_available: bool = True


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    stock_qty: Optional[int] = None
    is_available: Optional[bool] = None


class ProductOut(BaseModel):
    id: int
    vendor_id: int
    name: str
    description: Optional[str] = None
    price: float
    category: str
    image_url: Optional[str] = None
    stock_qty: int
    is_available: bool
    vendor: Optional['VendorProfilePreview'] = None
    created_at: datetime

    class Config:
        from_attributes = True


#  ORDER SCHEMAS

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = 1


class OrderCreate(BaseModel):
    vendor_id: int
    items: List[OrderItemCreate]
    delivery_address: str
    delivery_lat: float
    delivery_lng: float
    phone_number: str  # for STK Push


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    product: Optional[ProductOut] = None

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    order_ref: str
    customer_id: int
    vendor_id: int
    driver_id: Optional[int] = None
    total_amount: float
    delivery_fee: float
    driver_earnings: float
    platform_fee: float
    status: str
    transaction_id: Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_lat: Optional[float] = None
    delivery_lng: Optional[float] = None
    created_at: datetime
    accepted_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    items: List[OrderItemOut] = []
    driver_profile: Optional['DriverProfilePreview'] = None  # Safe driver info for customers
    vendor: Optional['VendorProfilePreview'] = None # Safe vendor info for drivers

    class Config:
        from_attributes = True


class OrderAcceptRequest(BaseModel):
    order_id: int


class OrderStatusUpdate(BaseModel):
    status: str


#  PAYMENT & ESCROW SCHEMAS

class STKPushRequest(BaseModel):
    order_id: int
    phone_number: str  # e.g., "254712345678"
    amount: float


class STKPushResponse(BaseModel):
    checkout_request_id: str
    response_code: str
    response_description: str
    customer_message: str
    order_id: int


class PaymentOut(BaseModel):
    id: int
    order_id: int
    user_id: int
    amount: float
    status: str
    transaction_id: str
    mpesa_receipt: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RefundRequest(BaseModel):
    order_id: int


class LedgerOut(BaseModel):
    id: int
    order_id: int
    amount: float
    status: str
    created_at: datetime
    released_at: Optional[datetime] = None

    class Config:
        from_attributes = True


#  SECURITY & HANDSHAKE SCHEMAS

class GenerateQRRequest(BaseModel):
    order_id: int


class QRCodeResponse(BaseModel):
    order_id: int
    qr_code_base64: str
    part_b: str
    handshake_id: int


class HandshakeKeyOut(BaseModel):
    id: int
    order_id: int
    part_a_vendor: str
    part_b_customer: str
    mated: bool
    mated_at: Optional[datetime] = None
    mated_lat: Optional[float] = None
    mated_lng: Optional[float] = None

    class Config:
        from_attributes = True


class MateHandshakeRequest(BaseModel):
    order_id: int
    part_a: str
    part_b: str
    driver_lat: float
    driver_lng: float
    customer_lat: float
    customer_lng: float


class MateHandshakeResponse(BaseModel):
    success: bool
    message: str
    distance_meters: float
    mated: bool


class GeofenceCheckRequest(BaseModel):
    order_id: int
    driver_lat: float
    driver_lng: float
    customer_lat: float
    customer_lng: float


class GeofenceCheckResponse(BaseModel):
    within_radius: bool
    distance_meters: float
    radius_meters: float


class HandshakeVerify(BaseModel):
    order_id: int
    qr_data: str
    driver_lat: float
    driver_lng: float


#  DELIVERY VERIFICATION SCHEMAS

class DeliveryVerificationCreate(BaseModel):
    order_id: int
    gps_lat: float
    gps_lng: float
    is_no_show: bool = False
    notes: Optional[str] = None


class DeliveryVerificationOut(BaseModel):
    id: int
    order_id: int
    driver_photo_url: str
    gps_lat: float
    gps_lng: float
    timestamp: datetime
    is_no_show: bool
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class NoShowReport(BaseModel):
    order_id: int
    driver_lat: float
    driver_lng: float
    photo_url: str
    notes: Optional[str] = None


#  DISPUTE SCHEMAS

class DisputeCreate(BaseModel):
    order_id: int
    reason: str
    evidence_url: Optional[str] = None


class DisputeOut(BaseModel):
    id: int
    order_id: int
    raised_by_id: int
    reason: str


#  DRIVER PROFILE SCHEMAS (SAFE FOR CUSTOMER VIEW)

class VendorProfilePreview(BaseModel):
    """Safe vendor profile shown to drivers during pickup"""
    id: int
    name: str 
    business_name: Optional[str] = None
    location_address: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    is_verified_vendor: bool = False

    class Config:
        from_attributes = True


class DriverProfilePreview(BaseModel):
    """Safe driver profile shown to customers - NO sensitive data"""
    id: int
    name: str
    profile_photo_url: Optional[str] = None
    deliveries_completed: int = 0
    university: Optional[str] = None  # Social context only
    
    class Config:
        from_attributes = True


#  DRIVER SCHEMAS

class DriverLocationUpdate(BaseModel):
    driver_id: int
    lat: float
    lng: float


class NearbyJobsResponse(BaseModel):
    id: int
    order_ref: str
    customer_name: str
    delivery_address: str
    delivery_lat: float
    delivery_lng: float
    driver_lat: float
    driver_lng: float
    distance_meters: float
    total_amount: float
    delivery_fee: float
    items_count: int


class AcceptOrderRequest(BaseModel):
    driver_id: int


#  PRODUCT IMAGE SCHEMAS (for multi-image vendor verification)

class ProductImageOut(BaseModel):
    id: int
    product_id: int
    order_id: Optional[int] = None
    image_url: str
    side_name: Optional[str] = None  # e.g. "front", "side", "back"
    is_verified: bool = False
    admin_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProductImageCreate(BaseModel):
    product_id: int
    order_id: Optional[int] = None
    image_url: str
    side_name: Optional[str] = None


#  Blog / Social Schemas

class PostCreate(BaseModel):
    title: str
    body: Optional[str] = None
    image_url: Optional[str] = None


class CommentCreate(BaseModel):
    body: str


class CommentOut(BaseModel):
    id: int
    post_id: int
    user_id: int
    body: str
    created_at: datetime
    user: Optional[UserOut] = None

    class Config:
        from_attributes = True


class PostOut(BaseModel):
    id: int
    author_id: int
    title: str
    body: Optional[str] = None
    image_url: Optional[str] = None
    likes_count: int = 0
    comments_count: int = 0
    author: Optional['VendorProfilePreview'] = None
    is_hidden: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class PostsListOut(BaseModel):
    items: List[PostOut]
    total: int
    offset: int
    limit: int

    class Config:
        from_attributes = True


#  ADMIN SCHEMAS

class AdminOrderApprovalRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None


class AdminOrderOut(OrderOut):
    admin_id: Optional[int] = None
    admin_approved_at: Optional[datetime] = None
    admin_notes: Optional[str] = None
    product_images: List[ProductImageOut] = []

    class Config:
        from_attributes = True


class AdminDashboardStats(BaseModel):
    total_pending_orders: int
    total_vendors: int
    total_drivers: int
    total_customers: int
    total_revenue: float
    pending_images_count: int


class LocationVerificationResponse(BaseModel):
    order_id: int
    delivery_address: str
    stated_lat: float
    stated_lng: float
    current_lat: float
    current_lng: float
    distance_meters: float
    within_radius: bool
    radius_meters: float = 200.0  # 200m radius for delivery


OrderOut.model_rebuild()
WalletOut.model_rebuild()
UserOut.model_rebuild()
PostOut.model_rebuild()
ProductOut.model_rebuild()
PostsListOut.model_rebuild()

# Rebuild all forward refs
VendorProfilePreview.model_rebuild()
DriverProfilePreview.model_rebuild()
CommentOut.model_rebuild()

#  Rebuild forward references for Pydantic v2

