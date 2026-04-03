import re

def normalize_phone(raw: str) -> str:
    """
    Normalize any Bangladeshi phone format to 01XXXXXXXXX.

    Handles:
    +8801676225090 -> 01676225090
    8801676225090  -> 01676225090
    01676225090    -> 01676225090
    1676225090     -> 01676225090
    016-7622-5090  -> 01676225090
    880 1676225090 -> 01676225090
    """
    # Remove everything except digits
    digits = re.sub(r'\D', '', raw)

    # Remove country code prefix
    if digits.startswith('880') and len(digits) > 10:
        digits = digits[3:]  # Remove '880'
    elif digits.startswith('0') and len(digits) == 11:
        pass  # Already correct
    elif len(digits) == 10:
        digits = '0' + digits  # Add leading zero

    # Ensure exactly 11 digits starting with 0
    if len(digits) == 11 and digits.startswith('0'):
        return digits

    # Fallback: return cleaned digits
    return digits

def normalize_phone_international(raw: str) -> str:
    """
    Normalize phone to international format (+8801XXXXXXXXX)
    """
    local = normalize_phone(raw)
    return '+880' + local.lstrip('0')
