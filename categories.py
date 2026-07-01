"""Category auto-detection patterns."""

# Regex patterns for category detection
# Organized by category with comprehensive patterns for RWF/East African context

CATEGORY_PATTERNS = {
    'Food': {
        'patterns': [
            r'restaurant', r'food', r'eat', r'lunch', r'dinner', r'breakfast',
            r'grocer', r'market', r'canteen', r'cafe', r'coffee', r'rice',
            r'meal', r'pizza', r'burger', r'drink', r'juice', r'kitchen',
            r'bakery', r'pastry', r'chicken', r'meat', r'fish', r'vegetable',
            r'dairy', r'fruit', r'soup', r'salad', r'restaurant', r'kiosk',
            r'hotel', r'bar food', r'fast food', r'diner', r'bistro',
        ],
        'exclude': [r'restaurant supplies', r'kitchen equipment'],
    },
    
    'Transport': {
        'patterns': [
            r'transport', r'taxi', r'moto', r'bus', r'fuel', r'gas',
            r'park', r'fare', r'ride', r'move', r'car', r'bike', r'garage',
            r'uber', r'uber eats', r'logistics', r'delivery', r'courier',
            r'train', r'flight', r'plane', r'airline', r'petrol', r'diesel',
            r'maintenance', r'repair', r'toll', r'toll gate', r'parking',
            r'vehicle', r'insurance', r'registration', r'driving',
        ],
        'exclude': [r'car rental business'],
    },
    
    'Bills': {
        'patterns': [
            r'rent', r'bill', r'electric', r'water', r'internet', r'wifi',
            r'airtime', r'data', r'bundle', r'top.?up', r'canal', r'dstv',
            r'subscription', r'insurance', r'phone bill', r'utility',
            r'waste', r'tax', r'government', r'fee', r'charge', r'monthly',
            r'annual', r'annual fee', r'subscription fee', r'mtn', r'airtel',
            r'vodacom', r'orange', r'electricity', r'sewage', r'gas bill',
        ],
        'exclude': [],
    },
    
    'Shopping': {
        'patterns': [
            r'shop', r'buy', r'cloth', r'shoe', r'watch', r'phone',
            r'amazon', r'jumia', r'mall', r'store', r'purchase', r'order',
            r'item', r'market', r'retail', r'sale', r'discount', r'deal',
            r'clothing', r'apparel', r'fashion', r'accessories', r'luggage',
            r'bag', r'backpack', r'shoes', r'boots', r'sneaker', r'sandal',
            r'glasses', r'sunglasses', r'jewelry', r'necklace', r'bracelet',
            r'electronics', r'gadget', r'tablet', r'laptop', r'computer',
            r'printer', r'scanner', r'keyboard', r'mouse', r'headphone',
        ],
        'exclude': [r'shopping cart', r'shopping bag'],
    },
    
    'Entertainment': {
        'patterns': [
            r'movie', r'game', r'netflix', r'spotify', r'show', r'concert',
            r'party', r'bar', r'club', r'beer', r'music', r'fun', r'ticket',
            r'cinema', r'theater', r'theatre', r'play', r'comedy', r'event',
            r'nightlife', r'disco', r'karaoke', r'gaming', r'video game',
            r'streaming', r'hulu', r'disney', r'youtube', r'prime video',
            r'playstation', r'xbox', r'nintendo', r'twitch', r'podcast',
            r'book', r'ebook', r'audiobook', r'magazine', r'subscription',
        ],
        'exclude': [r'entertainment industry'],
    },
    
    'Health': {
        'patterns': [
            r'doctor', r'hospital', r'medic', r'pharma', r'clinic', r'health',
            r'dental', r'dentist', r'check.?up', r'prescrip', r'drug',
            r'medicine', r'pharmacy', r'vaccine', r'immuniz', r'surgery',
            r'therapy', r'physio', r'psychology', r'mental', r'counseling',
            r'eye care', r'optician', r'glasses', r'contact lens', r'fitness',
            r'gym', r'yoga', r'wellness', r'supplement', r'vitamin', r'protein',
            r'lab test', r'blood test', r'ultrasound', r'xray', r'ct scan',
        ],
        'exclude': [r'health insurance company'],
    },
    
    'Transfer': {
        'patterns': [
            r'transfer', r'send', r'sent', r'received', r'receive', r'momo',
            r'mtn', r'bank', r'mobile money', r'cash.?in', r'cash.?out',
            r'withdr', r'deposit', r'payment', r'remit', r'p2p', r'peer',
            r'friend', r'family', r'relative', r'wallet', r'account',
            r'tigo', r'airtel money', r'equitel', r'kopo kopo', r'pesapal',
            r'mpesa', r'ukash', r'moneygram', r'western union', r'swift',
        ],
        'exclude': [],
    },
    
    'Other': {
        'patterns': [],
        'exclude': [],
    },
}


def categorize_transaction(description, notes='', raw_message=''):
    """
    Auto-categorize a transaction based on description, notes, and raw message.
    
    Args:
        description: Transaction description
        notes: Additional notes
        raw_message: Raw SMS/message
    
    Returns:
        str: Category name
    """
    import re
    
    # Combine all text fields for search
    text = ' '.join([
        description or '',
        notes or '',
        raw_message or ''
    ]).lower()
    
    # Skip empty text
    if not text.strip():
        return 'Other'
    
    # Check each category (in priority order)
    category_priority = ['Food', 'Transport', 'Bills', 'Shopping', 'Entertainment', 'Health', 'Transfer', 'Other']
    
    for category in category_priority:
        if category == 'Other':
            continue
        
        patterns = CATEGORY_PATTERNS.get(category, {}).get('patterns', [])
        exclude = CATEGORY_PATTERNS.get(category, {}).get('exclude', [])
        
        # Check if any pattern matches
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # Check if excluded
                excluded = False
                for exclude_pattern in exclude:
                    if re.search(exclude_pattern, text, re.IGNORECASE):
                        excluded = True
                        break
                
                if not excluded:
                    return category
    
    return 'Other'


# Alias for backward compatibility
def autoCat(description, notes='', raw_message=''):
    """Backward compatible alias for categorize_transaction."""
    return categorize_transaction(description, notes, raw_message)
