"""
app/modules/finance/pdf/text_utils.py
─────────────────────────────────────
Text utilities for PDF generation.

Note: Arabic text processing functions have been deprecated.
These may be re-enabled in a future version with proper font support.
"""
import re
from typing import Optional


def is_arabic(text: Optional[str]) -> bool:
    """
    Check if text contains Arabic characters.
    
    DEPRECATED: Arabic support temporarily disabled.
    Returns False for all inputs to skip Arabic processing.
    """
    # Temporarily disabled - always returns False
    return False


def prepare_arabic_text(text: str) -> str:
    """
    Reshape Arabic text and apply bidirectional algorithm for proper display.
    
    DEPRECATED: Arabic support temporarily disabled.
    Returns text unchanged.
    """
    # Temporarily disabled - returns text as-is
    return text


def prepare_mixed_text(text: str) -> str:
    """
    Prepare text that may contain both Arabic and Latin characters.
    
    DEPRECATED: Arabic support temporarily disabled.
    Returns text unchanged.
    """
    # Temporarily disabled - returns text as-is
    return text


def format_bilingual_label(english: str, arabic: str, separator: str = " / ") -> str:
    """
    Format a bilingual label with English and Arabic.
    
    DEPRECATED: Arabic support temporarily disabled.
    Returns English text only.
    """
    # Temporarily disabled - returns English only
    return english


def format_currency(amount: float, currency: str = "EGP") -> str:
    """Format amount with currency."""
    # Format number with thousands separator and 2 decimal places
    formatted_amount = f"{amount:,.2f}"
    return f"{formatted_amount} {currency}"


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
