import os
from typing import Tuple, Dict, Any
from dotenv import load_dotenv
import requests

# Load environment variables (prefer cricverse.env)
if os.path.exists('cricverse.env'):
    load_dotenv('cricverse.env')
else:
    load_dotenv()

PAYPAL_ENV = os.getenv('PAYPAL_ENV', 'sandbox').lower()
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')

if PAYPAL_ENV == 'live':
    PAYPAL_BASE = 'https://api-m.paypal.com'
else:
    PAYPAL_BASE = 'https://api-m.sandbox.paypal.com'


def _get_access_token() -> str:
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise RuntimeError('PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET are required')
    resp = requests.post(
        f'{PAYPAL_BASE}/v1/oauth2/token',
        auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
        data={'grant_type': 'client_credentials'},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()['access_token']


def paypal_create_order(amount: str, currency: str = 'USD') -> Tuple[str, Dict[str, Any]]:
    token = _get_access_token()
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    body = {
        'intent': 'CAPTURE',
        'purchase_units': [
            {
                'amount': {
                    'currency_code': currency,
                    'value': amount
                }
            }
        ]
    }
    resp = requests.post(f'{PAYPAL_BASE}/v2/checkout/orders', json=body, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return data['id'], data


def paypal_capture_order(order_id: str) -> Dict[str, Any]:
    token = _get_access_token()
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    resp = requests.post(f'{PAYPAL_BASE}/v2/checkout/orders/{order_id}/capture', headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.json()
