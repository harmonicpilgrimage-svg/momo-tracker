# ============================================
# MTN MoMo API Integration
# ============================================
import base64
import uuid
import requests
from config import (
    MOMO_BASE_URL, CURRENCY,
    COLLECTION_PRIMARY_KEY, COLLECTION_REF_ID, COLLECTION_API_KEY,
    DISBURSEMENT_PRIMARY_KEY, DISBURSEMENT_REF_ID, DISBURSEMENT_API_KEY,
    MOMO_PHONE_NUMBER,
)


def _get_token(product="collection"):
    """
    Gets a temporary access token from MTN MoMo.
    The token is valid for about 1 hour.
    """
    if product == "collection":
        primary = COLLECTION_PRIMARY_KEY
        ref_id = COLLECTION_REF_ID
        api_key = COLLECTION_API_KEY
    else:
        primary = DISBURSEMENT_PRIMARY_KEY
        ref_id = DISBURSEMENT_REF_ID
        api_key = DISBURSEMENT_API_KEY

    # Basic auth = base64(referenceId:apiKey)
    credentials = base64.b64encode(f"{ref_id}:{api_key}".encode()).decode()

    url = f"{MOMO_BASE_URL}/{product}/token/"
    headers = {
        "Ocp-Apim-Subscription-Key": primary,
        "Authorization": f"Basic {credentials}",
    }

    try:
        resp = requests.post(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("access_token")
        print(f"Token error ({product}): {resp.status_code} - {resp.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Token error ({product}): {e}")
        return None


def send_money(recipient_number, amount, payer_message=""):
    """Send money FROM your account TO someone else."""
    token = _get_token("disbursement")
    if not token:
        return {"success": False, "error": "Could not authenticate with MTN"}

    ref_id = str(uuid.uuid4())
    url = f"{MOMO_BASE_URL}/disbursement/v1_0/transfer"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Reference-Id": ref_id,
        "X-Target-Environment": "sandbox",
        "Ocp-Apim-Subscription-Key": DISBURSEMENT_PRIMARY_KEY,
        "Content-Type": "application/json",
    }
    body = {
        "amount": str(amount),
        "currency": CURRENCY,
        "externalId": ref_id,
        "payee": {"partyIdType": "MSISDN", "partyId": recipient_number},
        "payerMessage": payer_message or "Sent via MoMo Tracker",
        "payeeNote": payer_message or "Money received",
    }
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=30)
        if resp.status_code == 202:
            return {"success": True, "reference_id": ref_id,
                    "message": "Submitted! Check your phone to confirm."}
        return {"success": False, "error": f"MTN rejected (status {resp.status_code}): {resp.text[:200]}"}
    except Exception as e:
        return {"success": False, "error": f"Connection error: {e}"}


def request_payment(payer_number, amount, note=""):
    """Request payment FROM someone TO your account."""
    token = _get_token("collection")
    if not token:
        return {"success": False, "error": "Could not authenticate with MTN"}

    ref_id = str(uuid.uuid4())
    url = f"{MOMO_BASE_URL}/collection/v1_0/requesttopay"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Reference-Id": ref_id,
        "X-Target-Environment": "sandbox",
        "Ocp-Apim-Subscription-Key": COLLECTION_PRIMARY_KEY,
        "Content-Type": "application/json",
    }
    body = {
        "amount": str(amount),
        "currency": CURRENCY,
        "externalId": ref_id,
        "payer": {"partyIdType": "MSISDN", "partyId": payer_number},
        "payerMessage": note or "Payment requested",
        "payeeNote": f"From {MOMO_PHONE_NUMBER}",
    }
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=30)
        if resp.status_code == 202:
            return {"success": True, "reference_id": ref_id,
                    "message": "Request sent! They must confirm on their phone."}
        return {"success": False, "error": f"MTN rejected (status {resp.status_code}): {resp.text[:200]}"}
    except Exception as e:
        return {"success": False, "error": f"Connection error: {e}"}


def check_transaction_status(reference_id, product="collection"):
    """Check if a transaction completed."""
    token = _get_token(product)
    if not token:
        return {"success": False, "error": "Could not authenticate"}
    primary = COLLECTION_PRIMARY_KEY if product == "collection" else DISBURSEMENT_PRIMARY_KEY
    url = f"{MOMO_BASE_URL}/{product}/v1_0/requesttopay/{reference_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Target-Environment": "sandbox",
        "Ocp-Apim-Subscription-Key": primary,
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return {"success": True, "status": data.get("status"), "data": data}
        return {"success": False, "error": f"Status {resp.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"Connection error: {e}"}


def get_balance():
    """Get your MoMo account balance."""
    token = _get_token("collection")
    if not token:
        return {"success": False, "error": "Could not authenticate"}
    url = f"{MOMO_BASE_URL}/collection/v1_0/account/balance"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Target-Environment": "sandbox",
        "Ocp-Apim-Subscription-Key": COLLECTION_PRIMARY_KEY,
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return {"success": True, "balance": data.get("balance"), "currency": data.get("currency")}
        return {"success": False, "error": f"Status {resp.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"Connection error: {e}"}
