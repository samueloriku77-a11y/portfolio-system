from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List
import models
import schemas

def process_wallet_checkout(db: Session, order_data: schemas.OrderCreate, current_user: models.User):
    """Process order payment using wallet balance."""
    # Get or create customer wallet
    wallet = db.query(models.Wallet).filter(models.Wallet.user_id == current_user.id).first()
    if not wallet:
        raise HTTPException(404, "Customer wallet not found. Fund your wallet first.")
    
    # Calculate total (products + delivery)
    total_amount = 0.0
    valid_items = []
    for item in order_data.items:
        product = db.query(models.Product).filter(
            models.Product.id == item.product_id,
            models.Product.vendor_id == order_data.vendor_id,
            models.Product.is_available == True
        ).first()
        if not product:
            raise HTTPException(400, f"Invalid product {item.product_id}")
        total_amount += product.price * item.quantity
        valid_items.append((product, item.quantity))
    
    total_payable = total_amount + 50.0  # + delivery_fee
    
    if wallet.balance < total_payable:
        raise HTTPException(400, f"Insufficient wallet balance. Required: {total_payable:.2f} KES, Available: {wallet.balance:.2f} KES")
    
    # Deduct from wallet
    wallet.balance -= total_payable
    db.commit()
    db.refresh(wallet)
    
    # Create order (same logic as regular checkout, no STK)
    import datetime
    import uuid
    order_ref = "WAL-" + str(int(datetime.datetime.now().timestamp()))
    new_order = models.Order(
        order_ref=order_ref,
        customer_id=current_user.id,
        vendor_id=order_data.vendor_id,
        total_amount=total_amount,
        delivery_fee=50.0,
        driver_earnings=40.0,
        platform_fee=10.0,
        delivery_address=order_data.delivery_address,
        delivery_lat=order_data.delivery_lat,
        delivery_lng=order_data.delivery_lng,
        status=models.OrderStatus.PENDING_VENDOR_APPROVAL,  # Skip payment step
        transaction_id=f"WALLET-{uuid.uuid4().hex[:8].upper()}"
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    # Add items
    for product, qty in valid_items:
        db.add(models.OrderItem(
            order_id=new_order.id,
            product_id=product.id,
            quantity=qty,
            unit_price=product.price
        ))
    
    # Create ledger (escrow)
    ledger = models.Ledger(
        order_id=new_order.id,
        amount=total_payable,
        status=models.LedgerStatus.HOLDING.value
    )
    db.add(ledger)
    
    # Generate handshake
    from services.security import generate_handshake_keys
    generate_handshake_keys(db, new_order.id)
    
    db.commit()
    
    return new_order
