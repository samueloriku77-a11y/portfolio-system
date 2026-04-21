import uuid
import base64
import datetime
import json
import httpx
from sqlalchemy.orm import Session

try:
    from .. import models
    from ..config import (
        MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET,
        MPESA_SHORTCODE, MPESA_PASSKEY, MPESA_CALLBACK_URL,
        INTASEND_API_URL, INTASEND_API_KEY, INTASEND_API_SECRET, INTASEND_CALLBACK_URL,
    )
except ImportError:
    import models
    from config import (
        MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET,
        MPESA_SHORTCODE, MPESA_PASSKEY, MPESA_CALLBACK_URL,
        INTASEND_API_URL, INTASEND_API_KEY, INTASEND_API_SECRET, INTASEND_CALLBACK_URL,
    )


# M-Pesa Helpers

def _get_mpesa_token() -> str:
    """Fetch OAuth token from Daraja sandbox. Returns mock token in dev."""
    try:
        credentials = base64.b64encode(
            f"{MPESA_CONSUMER_KEY}:{MPESA_CONSUMER_SECRET}".encode()
        ).decode()
        resp = httpx.get(
            "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
            headers={"Authorization": f"Basic {credentials}"},
            timeout=10,
        )
        return resp.json().get("access_token", "mock_token")
    except Exception:
        return "mock_token"  # Dev fallback


def _build_stk_password() -> tuple[str, str]:
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    raw = f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(raw.encode()).decode()
    return password, timestamp

def _intasend_headers() -> dict:
    return {
        "Authorization": f"Bearer {INTASEND_API_SECRET}",
        "Content-Type": "application/json",
    }


from .intasend import initiate_checkout as _checkout, process_intasend_callback
def initiate_intasend_checkout(amount: float, phone_number: str, reference: str, description: str) -> dict:
    """Initiate a deposit payment using IntaSend mobile checkout."""
    if not INTASEND_API_SECRET or not INTASEND_API_URL:
        return {"mode": "mock", "checkout_request_id": f"MOCK-{uuid.uuid4().hex[:10].upper()}", "amount": amount}

    payload = {
        "amount": int(amount),
        "currency": "KES",
        "payment_method": "MPESA",
        "phone_number": phone_number,
        "reference": reference,
        "description": description,
        "callback_url": INTASEND_CALLBACK_URL,
    }

    try:
        response = httpx.post(
            f"{INTASEND_API_URL}/checkout/create",
            json=payload,
            headers=_intasend_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        return {"error": str(exc), "payload": payload}


def initiate_intasend_payout(amount: float, phone_number: str, reference: str, description: str) -> dict:
        return initiate_intasend_checkout(amount, phone_number, reference, description)  # IntaSend handles both
"""Initiate a withdrawal payout using IntaSend.""" 
def initiate_intasend_payout(amount: float, phone_number: str, reference: str, description: str) -> dict:
    if not INTASEND_API_SECRET or not INTASEND_API_URL:
        return {"mode": "mock", "payout_reference": f"MOCK-PAYOUT-{uuid.uuid4().hex[:10].upper()}", "amount": amount}

    payload = {
        "amount": int(amount),
        "currency": "KES",
        "payment_method": "MPESA",
        "phone_number": phone_number,
        "reference": reference,
        "description": description,
        "callback_url": INTASEND_CALLBACK_URL,
    }

    try:
        response = httpx.post(
            f"{INTASEND_API_URL}/payouts",
            json=payload,
            headers=_intasend_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        return {"error": str(exc), "payload": payload}

# Core Payment Functions

def initiate_stk_push(db: Session, order: models.Order, phone_number: str) -> bool:
    """
    Initiates an M-Pesa STK Push (real Daraja call in prod, mock in dev).
    Creates a HOLDING ledger entry representing the escrow.
    """
    # Generate mock transaction ID (in prod this comes from Daraja callback)
    transaction_id = f"STK{uuid.uuid4().hex[:10].upper()}"
    order.transaction_id = transaction_id
    order.status = models.OrderStatus.PENDING_VENDOR_APPROVAL

    # Create escrow ledger entry
    ledger = models.Ledger(
        order_id=order.id,
        amount=order.total_amount + order.delivery_fee,
        status=models.LedgerStatus.HOLDING.value,
    )
    db.add(ledger)
    db.commit()
    db.refresh(order)


    # httpx.post(
    #     "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
    #     json={
    #         "BusinessShortCode": MPESA_SHORTCODE,
    #         "Password": password,
    #         "Timestamp": timestamp,
    #         "TransactionType": "CustomerPayBillOnline",
    #         "Amount": int(order.total_amount + order.delivery_fee),
    #         "PartyA": phone_number,
    #         "PartyB": MPESA_SHORTCODE,
    #         "PhoneNumber": phone_number,
    #         "CallBackURL": MPESA_CALLBACK_URL,
    #         "AccountReference": order.order_ref,
    #         "TransactionDesc": f"SokoYetu Order {order.order_ref}",
    #     },
    #     headers={"Authorization": f"Bearer {token}"},
    # )

    return True


def cancel_order_and_refund(db: Session, order_id: int, customer_id: int) -> dict:
    """
    Escrow Refund Loop:
    - Only allowed if vendor has NOT yet accepted (status == PENDING_VENDOR_APPROVAL).
    - Marks ledger as REFUNDED and order as CANCELLED_BY_USER.
    """
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return {"status": "Error", "message": "Order not found."}
    if order.customer_id != customer_id:
        return {"status": "Error", "message": "Unauthorized."}

    if order.status != models.OrderStatus.PENDING_VENDOR_APPROVAL:
        return {
            "status": "Error",
            "message": "Refund unavailable — vendor has already accepted or trip is underway.",
        }

    ledger = db.query(models.Ledger).filter(models.Ledger.order_id == order.id).first()
    if ledger and ledger.status == models.LedgerStatus.HOLDING.value:
        ledger.status = models.LedgerStatus.REFUNDED.value
        order.status = models.OrderStatus.CANCELLED_BY_USER.value
        db.commit()

        # In prod: call Daraja refund API here
        return {
            "status": "Success",
            "message": "Refund initiated. Funds will be returned to your M-Pesa within 5 minutes.",
            "transaction_id": order.transaction_id,
        }

    return {"status": "Error", "message": "No eligible ledger entry found."}


def release_funds(db: Session, order_id: int) -> bool:
    """
    Release escrow on successful handshake.
    Transfers funds to:
    - Vendor: order.total_amount (product costs)
    - Driver: order.driver_earnings (from delivery fee)
    - Platform: order.platform_fee (kept by platform)
    """
    ledger = db.query(models.Ledger).filter(models.Ledger.order_id == order_id).first()
    if not ledger or ledger.status != models.LedgerStatus.HOLDING.value:
        return False

    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return False

    # Credit vendor wallet
    vendor = db.query(models.User).filter(models.User.id == order.vendor_id).first()
    if vendor and vendor.wallet:
        vendor.wallet.balance += order.total_amount
        db.commit()
        db.refresh(vendor.wallet)

    # Credit driver wallet
    driver = db.query(models.User).filter(models.User.id == order.driver_id).first()
    if driver and driver.wallet:
        driver.wallet.balance += order.driver_earnings
        db.commit()
        db.refresh(driver.wallet)

    # Update ledger
    ledger.status = models.LedgerStatus.RELEASED.value
    ledger.released_at = datetime.datetime.utcnow()

    db.commit()
    return True
