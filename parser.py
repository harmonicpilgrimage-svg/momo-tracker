"""Transaction message parsing logic."""

import re
from datetime import datetime
from categories import categorize_transaction

# Rwandan phone number regex
PHONE_REGEX = r'(250\d{9}|07[8|2|3]\d{7})'

# Currency detection
CURRENCIES = {
    'RWF': ['RWF', 'FRW', 'rwf', 'frw'],
    'USD': ['USD', '$', 'usd', 'dollar', 'dollars'],
    'EUR': ['EUR', '€', 'eur', 'euro', 'euros'],
    'KES': ['KES', 'ksh', 'kes', 'kenyan'],
    'UGX': ['UGX', 'ugx', 'shilling', 'ugandan'],
}

# Transaction type indicators
INCOME_KEYWORDS = [
    'receive', 'received', 'incoming', 'income', 'cash.?in', 'deposit',
    'credit', 'wishyuwe', 'wakiriye', 'yishyuwe', 'payment into', 'credited',
    'received payment', 'sent to you', 'transfer to you', 'deposit to account',
]

EXPENSE_KEYWORDS = [
    'sent', 'send', 'paid', 'pay', 'bought', 'purchased', 'transferred to',
    'transfer to', 'cash.?out', 'expense', 'debit', 'withdr', 'withdrawal',
    'wishyuye', 'kohereza', 'yishyuye', 'payment to', 'sent to', 'transfer out',
]

# Source detection
SOURCES = {
    'MoMo': ['MoMo', 'mobile money', 'MTN', 'momo', 'mtn'],
    'Bank': ['bank', 'BK', 'I&M', 'KCB', 'Equity', 'BPR', 'COGEBANQUE', 'Artilink'],
    'Airtel Money': ['airtel', 'tigo', 'airtel money'],
    'Manual': [],
}


def parse_message(raw_message, default_currency='RWF'):
    """
    Parse an SMS or message into a transaction.
    
    Supports:
    - Various SMS formats (MoMo, Bank, Airtel Money)
    - Multiple currencies (RWF, USD, EUR, etc.)
    - Date parsing (DD/MM/YYYY, MM-DD-YYYY, etc.)
    - Phone number extraction
    - Automatic categorization
    
    Args:
        raw_message: Raw SMS text or message
        default_currency: Default currency if not detected (default: RWF)
    
    Returns:
        dict: Parsed transaction with keys:
            - type: 'income' or 'expense'
            - amount: Numeric amount
            - currency: Currency code
            - category: Auto-detected category
            - description: Extracted description
            - source: Source system
            - receiver: Phone number if found
            - date: Datetime object
            - parse_error: Error message if parsing failed, None otherwise
            - raw_message: Original message
    """
    
    if not raw_message or not raw_message.strip():
        return {
            'type': 'expense',
            'amount': None,
            'currency': default_currency,
            'category': 'Other',
            'description': None,
            'source': 'Manual',
            'receiver': None,
            'sender': None,
            'date': datetime.utcnow(),
            'parse_error': 'No message provided',
            'raw_message': raw_message,
        }
    
    text = raw_message.strip()
    result = {
        'type': 'expense',
        'amount': None,
        'currency': default_currency,
        'category': 'Other',
        'description': None,
        'source': 'Manual',
        'receiver': None,
        'sender': None,
        'date': datetime.utcnow(),
        'parse_error': None,
        'raw_message': text,
    }
    
    # Step 1: Extract amount
    # Try various patterns
    amount_patterns = [
        r'(\d[\d,]*)\s*(RWF|FRW|USD|\$|EUR|€)',  # Number then currency
        r'(RWF|FRW|USD|EUR)\s*(\d[\d,]*)',        # Currency then number
        r'([A-Z]{3})\s*(\d[\d,]*)',               # 3-letter code then number
        r'(\d[\d,]+)',                             # Just numbers
    ]
    
    amount_match = None
    for pattern in amount_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_match = match
            break
    
    if amount_match:
        # Extract the number part
        groups = amount_match.groups()
        amount_str = None
        currency_str = None
        
        if len(groups) == 2:
            # Check which is number and which is currency
            if re.match(r'\d', groups[0]):
                amount_str, currency_str = groups
            else:
                currency_str, amount_str = groups
        else:
            amount_str = groups[0] if groups else None
        
        if amount_str:
            try:
                result['amount'] = int(amount_str.replace(',', ''))
            except (ValueError, AttributeError):
                result['parse_error'] = 'Could not parse amount'
                return result
        
        # Step 2: Detect currency
        if currency_str:
            currency_str = currency_str.upper()
            for curr, variants in CURRENCIES.items():
                if currency_str in variants or any(v.upper() == currency_str for v in variants):
                    result['currency'] = curr
                    break
    
    if result['amount'] is None:
        result['parse_error'] = 'No amount found'
        return result
    
    # Step 3: Detect transaction type (income/expense)
    text_lower = text.lower()
    
    is_income = any(re.search(kw, text_lower, re.IGNORECASE) for kw in INCOME_KEYWORDS)
    is_expense = any(re.search(kw, text_lower, re.IGNORECASE) for kw in EXPENSE_KEYWORDS)
    
    if is_income and not is_expense:
        result['type'] = 'income'
    elif is_expense:
        result['type'] = 'expense'
    # If both or neither, default to expense
    
    # Step 4: Extract phone number (Rwandan format)
    phone_match = re.search(PHONE_REGEX, text)
    if phone_match:
        phone = phone_match.group(0)
        # Normalize to 250 format if it's 07x
        if phone.startswith('07'):
            phone = '25' + phone
        result['receiver'] = phone
    
    # Step 5: Detect source
    for source, keywords in SOURCES.items():
        for kw in keywords:
            if re.search(kw, text, re.IGNORECASE):
                result['source'] = source
                break
        if result['source'] != 'Manual':
            break
    
    # Step 6: Parse date
    date_patterns = [
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', 'dmy'),  # DD/MM/YYYY or DD-MM-YYYY
        (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', 'ymd'),    # YYYY/MM/DD
    ]
    
    for pattern, fmt in date_patterns:
        date_match = re.search(pattern, text)
        if date_match:
            try:
                parts = date_match.groups()
                if fmt == 'dmy':
                    day, month, year = parts
                    if len(year) == 2:
                        year = '20' + year
                    result['date'] = datetime(int(year), int(month), int(day))
                elif fmt == 'ymd':
                    year, month, day = parts
                    result['date'] = datetime(int(year), int(month), int(day))
                break
            except (ValueError, IndexError):
                pass
    
    # Step 7: Extract description
    # Try to find "for:", "description:", "reason:" patterns
    desc_match = re.search(r'(?:for|description|reason|purpose)[:\s]+(.+?)(?:\.|,|\n|$)', text, re.IGNORECASE)
    if desc_match:
        result['description'] = desc_match.group(1).strip()
    else:
        # Use first line or a relevant part
        lines = text.split('\n')
        if len(lines) > 1:
            # Try second line
            result['description'] = lines[1].strip()[:100]
        elif 'sent' in text_lower or 'received' in text_lower:
            # Extract the purpose from context
            context_match = re.search(r'(?:sent|received|transfer).*?(?:to|from)?\s+(.+?)(?:on|at|\.|,|$)', text, re.IGNORECASE)
            if context_match:
                result['description'] = context_match.group(1).strip()[:100]
    
    # Step 8: Auto-categorize
    result['category'] = categorize_transaction(
        result['description'] or '',
        '',
        text
    )
    
    return result


def parse_multiple_messages(messages):
    """
    Parse multiple messages.
    
    Args:
        messages: List of message strings
    
    Returns:
        list: List of parsed transactions
    """
    return [parse_message(msg) for msg in messages if msg and msg.strip()]


def validate_transaction(txn):
    """
    Validate a transaction dict.
    
    Args:
        txn: Transaction dictionary
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not txn:
        return False, "Transaction is empty"
    
    if txn.get('parse_error'):
        return False, f"Parse error: {txn['parse_error']}"
    
    if not txn.get('amount') or txn['amount'] <= 0:
        return False, "Invalid amount"
    
    if txn.get('type') not in ('income', 'expense'):
        return False, "Invalid transaction type"
    
    return True, None
