# ============================================
# MTN MoMo SMS Parser for Rwanda
# ============================================
import re
from datetime import datetime


def parse_momo_sms(sms_text):
    """
    Parse an MTN Rwanda MoMo SMS and extract transaction details.

    Handles these common MTN MoMo SMS formats:
    1. "You have sent XXX RWF to [NAME] 250XXXXXXXXX on DD/MM/YYYY at HH:MM"
    2. "You have received XXX RWF from [NAME] 250XXXXXXXXX on DD/MM/YYYY at HH:MM"
    3. "Payment of XXX RWF to [NAME] 250XXXXXXXXX..."
    4. "A payment of XXX RWF from [NAME] 250XXXXXXXXX..."
    5. "You have paid XXX RWF to [MERCHANT]..."
    6. "You have bought airtime..."
    7. "Yakorewe igikorwa cyo kohereza XXX RWF kuri 250XXXXXXXXX..."
    """

    text = sms_text.strip()

    # Amount pattern: digits followed by RWF or FRW
    amount_match = re.search(r'(\d[\d,]*)\s*(RWF|FRW)', text, re.IGNORECASE)
    amount = None
    if amount_match:
        amount = int(amount_match.group(1).replace(',', ''))

    # Phone number pattern: 250XXXXXXXXX or 078XXXXXXXX
    phone_match = re.search(r'(250\d{9}|07[8|2|3]\d{7})', text)
    phone = None
    if phone_match:
        phone = phone_match.group(0)
        if phone.startswith('0'):
            phone = '25' + phone

    # Determine transaction type
    # SEND indicators
    send_keywords = [
        'sent', 'you have sent', 'you sent', 'paid', 'you have paid',
        'payment of', 'payment to', 'you have transferred',
        'kohereza', 'kohereje', 'wishyuye', 'yishyuye',
        'transfer', 'transferred', 'buy', 'bought', 'purchased',
    ]
    # RECEIVE indicators
    receive_keywords = [
        'received', 'you have received', 'you received',
        'payment from', 'from', 'sent you',
        'wakiriye', 'yakohereje', 'wakorewe',
        'deposit', 'credited',
    ]

    text_lower = text.lower()
    is_send = any(kw in text_lower for kw in send_keywords)
    is_receive = any(kw in text_lower for kw in receive_keywords)

    # If both or neither, try to determine by context
    if is_send and is_receive:
        # Check which keyword appears first
        send_pos = min((text_lower.find(kw) for kw in send_keywords if kw in text_lower), default=999)
        receive_pos = min((text_lower.find(kw) for kw in receive_keywords if kw in text_lower), default=999)
        txn_type = "SEND" if send_pos < receive_pos else "RECEIVE"
    elif is_send:
        txn_type = "SEND"
    elif is_receive:
        txn_type = "RECEIVE"
    else:
        # Try to detect from context
        if 'paid' in text_lower or 'pay' in text_lower or 'buy' in text_lower:
            txn_type = "SEND"
        else:
            txn_type = "UNKNOWN"

    # Extract name if present
    name_match = re.search(r'(?:to|from)\s+([A-Za-z\s]+?)(?:\s+250|\s+07|\s+on\s+\d|\s*$)', text, re.IGNORECASE)
    name = name_match.group(1).strip() if name_match else None

    # Extract date
    date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)
    date_str = date_match.group(1) if date_match else None

    # Extract time
    time_match = re.search(r'(\d{1,2}:\d{2})', text)
    time_str = time_match.group(1) if time_match else None

    # Fee
    fee_match = re.search(r'(?:fee|transaction fee|fees)[:\s]*(\d[\d,]*)\s*(RWF|FRW)?', text, re.IGNORECASE)
    fee = int(fee_match.group(1).replace(',', '')) if fee_match else None

    # New balance
    balance_match = re.search(r'(?:balance|new balance|your new balance)[:\s]*(\d[\d,]*)\s*(RWF|FRW)?', text, re.IGNORECASE)
    new_balance = int(balance_match.group(1).replace(',', '')) if balance_match else None

    return {
        "amount": amount,
        "phone": phone,
        "type": txn_type,
        "name": name,
        "date": date_str,
        "time": time_str,
        "fee": fee,
        "new_balance": new_balance,
        "raw_text": text,
    }


def is_momo_sms(sms_text):
    """Check if an SMS is from MTN MoMo."""
    momo_indicators = [
        'MoMo', 'MTN', 'Mobile Money', 'MOMO',
        'RWF', 'FRW', "Y'ello",
        'MoKash', 'mokash',
        '250',  # Rwanda country code
    ]
    text_upper = sms_text.upper()
    # Must have both an MTN indicator AND a money amount
    has_momo = any(ind.upper() in text_upper for ind in momo_indicators)
    has_amount = bool(re.search(r'(\d[\d,]*)\s*(RWF|FRW)', text_upper))
    return has_momo and has_amount