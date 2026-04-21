import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    from ..config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
    from .. import models
except ImportError:
    from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
    import models


# Styled HTML Receipt Template

def _build_receipt_html(order: models.Order) -> str:
    driver = order.driver
    vendor = order.vendor
    customer = order.customer

    driver_name = driver.name if driver else "N/A"
    driver_major = driver.course_major or "Student"
    driver_year = driver.year_of_study or ""
    vendor_name = vendor.name if vendor else "N/A"

    items_html = "".join(
        f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;">{item.product.name if item.product else 'Item'}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:center;">{item.quantity}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:right;">KES {item.unit_price * item.quantity:,.2f}</td>
        </tr>
        """
        for item in (order.items or [])
    )

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
    <body style="margin:0;padding:0;background:#f5f5f5;font-family:'Segoe UI',Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:40px 0;">
        <tr><td align="center">
          <table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.08);">

            <!-- Header -->
            <tr><td style="background:linear-gradient(135deg,#16213e 0%,#0f3460 60%,#e94560 100%);padding:40px 40px 32px;text-align:center;">
              <h1 style="color:#fff;margin:0;font-size:28px;letter-spacing:2px;">🛒 SOKOYETU</h1>
              <p style="color:rgba(255,255,255,.75);margin:8px 0 0;font-size:14px;">Hyperlocal • Community • Delivery</p>
            </td></tr>

            <!-- Thank You Banner -->
            <tr><td style="background:#e8f5e9;padding:20px 40px;text-align:center;">
              <p style="margin:0;color:#2e7d32;font-size:16px;font-weight:600;">✅ Order Delivered Successfully!</p>
              <p style="margin:6px 0 0;color:#388e3c;font-size:13px;">Thank you for supporting your local community, {customer.name}!</p>
            </td></tr>

            <!-- Order Ref -->
            <tr><td style="padding:24px 40px 0;">
              <p style="margin:0;color:#999;font-size:12px;text-transform:uppercase;letter-spacing:1px;">Order Reference</p>
              <p style="margin:4px 0 0;font-size:22px;font-weight:700;color:#16213e;">{order.order_ref}</p>
            </td></tr>

            <!-- Items -->
            <tr><td style="padding:20px 40px;">
              <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #f0f0f0;border-radius:8px;overflow:hidden;">
                <thead>
                  <tr style="background:#f8f9fa;">
                    <th style="padding:10px 12px;text-align:left;font-size:12px;color:#666;font-weight:600;">ITEM</th>
                    <th style="padding:10px 12px;text-align:center;font-size:12px;color:#666;font-weight:600;">QTY</th>
                    <th style="padding:10px 12px;text-align:right;font-size:12px;color:#666;font-weight:600;">AMOUNT</th>
                  </tr>
                </thead>
                <tbody>
                  {items_html}
                  <tr style="background:#fafafa;">
                    <td colspan="2" style="padding:10px 12px;font-weight:600;color:#333;">Subtotal</td>
                    <td style="padding:10px 12px;text-align:right;font-weight:600;">KES {order.total_amount:,.2f}</td>
                  </tr>
                  <tr>
                    <td colspan="2" style="padding:8px 12px;color:#555;">Delivery Fee</td>
                    <td style="padding:8px 12px;text-align:right;">KES {order.delivery_fee:,.2f}</td>
                  </tr>
                  <tr style="background:#16213e;">
                    <td colspan="2" style="padding:12px;color:#fff;font-weight:700;font-size:16px;border-radius:0 0 0 8px;">TOTAL PAID</td>
                    <td style="padding:12px;text-align:right;color:#e94560;font-weight:700;font-size:18px;">KES {order.total_amount + order.delivery_fee:,.2f}</td>
                  </tr>
                </tbody>
              </table>
            </td></tr>

            <!-- Fee Breakdown -->
            <tr><td style="padding:0 40px 20px;">
              <p style="font-size:12px;color:#999;text-transform:uppercase;letter-spacing:1px;margin:0 0 10px;">Delivery Fee Breakdown</p>
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="font-size:13px;color:#555;padding:4px 0;">🎓 Student Driver ({driver_name} · {driver_major} {driver_year})</td>
                  <td style="text-align:right;font-size:13px;color:#2e7d32;font-weight:600;">KES {order.driver_earnings:,.2f}</td>
                </tr>
                <tr>
                  <td style="font-size:13px;color:#555;padding:4px 0;">🏪 Platform Fee</td>
                  <td style="text-align:right;font-size:13px;color:#555;">KES {order.platform_fee:,.2f}</td>
                </tr>
              </table>
            </td></tr>

            <!-- Participants -->
            <tr><td style="padding:0 40px 20px;">
              <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8f9fa;border-radius:10px;padding:16px;">
                <tr>
                  <td width="50%" style="padding:8px;">
                    <p style="margin:0;font-size:11px;color:#999;text-transform:uppercase;">Vendor</p>
                    <p style="margin:4px 0 0;font-weight:600;color:#333;">{vendor_name}</p>
                  </td>
                  <td width="50%" style="padding:8px;border-left:2px solid #e0e0e0;">
                    <p style="margin:0;font-size:11px;color:#999;text-transform:uppercase;">Your Driver</p>
                    <p style="margin:4px 0 0;font-weight:600;color:#333;">{driver_name}</p>
                    <p style="margin:2px 0 0;font-size:12px;color:#666;">{driver_major} {driver_year}</p>
                  </td>
                </tr>
              </table>
            </td></tr>

            <!-- Community Impact -->
            <tr><td style="padding:0 40px 32px;text-align:center;">
              <p style="color:#555;font-size:13px;margin:0;">
                🌍 Your purchase supports <strong>local vendors</strong> and funds a <strong>student's education</strong>.<br>
                Thank you for being part of the SokoYetu community!
              </p>
            </td></tr>

            <!-- Footer -->
            <tr><td style="background:#16213e;padding:20px 40px;text-align:center;">
              <p style="margin:0;color:rgba(255,255,255,.5);font-size:12px;">SokoYetu · Hyperlocal Delivery · support@sokoyetu.co.ke</p>
            </td></tr>

          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """


def send_delivery_email(order: models.Order) -> bool:
    """Send styled HTML receipt email to the customer after delivery."""
    if not order.customer or not order.customer.email:
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"✅ Delivered! Your SokoYetu order {order.order_ref}"
        msg["From"] = f"SokoYetu <{SMTP_USER}>"
        msg["To"] = order.customer.email

        html_content = _build_receipt_html(order)
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, order.customer.email, msg.as_string())

        return True
    except Exception as e:
        print(f"[Email] Failed to send to {order.customer.email}: {e}")
        return False


def send_delivery_sms(order: models.Order) -> bool:
    """
    Send SMS via Africa's Talking. Falls back gracefully in sandbox.
    In production set real AFRICASTALKING_API_KEY and USERNAME.
    """
    if not order.customer or not order.customer.phone:
        return False

    message = (
        f"Hi {order.customer.name}! Your SokoYetu order {order.order_ref} has been delivered. "
        f"Thank you for supporting your local community! 🛒"
    )

    try:
        import africastalking  # optional dep — graceful skip if not installed
        from ..config import AFRICASTALKING_USERNAME, AFRICASTALKING_API_KEY
        africastalking.initialize(AFRICASTALKING_USERNAME, AFRICASTALKING_API_KEY)
        sms = africastalking.SMS
        sms.send(message, [order.customer.phone])
        return True
    except Exception as e:
        print(f"[SMS] Skipped (sandbox/missing dep): {e}")
        return False
