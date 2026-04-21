import httpx
from config import INTASEND_API_URL, INTASEND_API_KEY, INTASEND_API_SECRET, INTASEND_CALLBACK_URL

def initiate_checkout(amount, phone, reference, description):
    payload = {
        'amount': amount,
        'currency': 'KES',
        'payment_method': 'MPESA',
        'phone_number': phone,
        'reference': reference,
        'description': description,
        'callback_url': INTASEND_CALLBACK_URL,
    }
    
    headers = {
        'Authorization': f'Bearer {INTASEND_API_SECRET}',
        'Content-Type': 'application/json',
    }
    
    response = httpx.post(f'{INTASEND_API_URL}/checkout/create', json=payload, headers=headers)
    return response.json() if response.is_success else {'error': response.text}

def process_intasend_callback(data):
    # Handle IntaSend webhook callback
    transaction_id = data.get('reference')
    status = data.get('status')
    
    # Update wallet transaction status based on IntaSend response
    return {'status': 'processed', 'transaction_id': transaction_id}
