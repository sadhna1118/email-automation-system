"""
Validation Utilities for Email Automation System
Wraps and extends core validation logic for email addresses, CSV schemas, and templates.
"""

from typing import Dict, Any, List
from validator import EmailValidator

def validate_single_email(email_str: str) -> Dict[str, Any]:
    """
    Validate a single email address.
    Returns:
        dict: {'valid': bool, 'email': str, 'domain': str, 'is_disposable': bool, 'reason': str or None}
    """
    return EmailValidator.validate_email(email_str)

def validate_csv_content(csv_raw_text: str) -> Dict[str, Any]:
    """
    Validate and parse raw CSV text uploaded by user.
    Returns:
        dict with valid_rows, invalid_rows, total_rows, columns, duplicates_removed, and optional error.
    """
    return EmailValidator.parse_csv(csv_raw_text, is_raw_text=True)

def validate_csv_file(file_path: str) -> Dict[str, Any]:
    """
    Validate and parse CSV from a file path.
    """
    return EmailValidator.parse_csv(file_path, is_raw_text=False)

def extract_template_variables(template_str: str) -> List[str]:
    """
    Extract placeholder variable names from template string ({name} or {{ name }}).
    """
    import re
    # Match both {var} and {{ var }}
    single_brackets = re.findall(r"\{([a-zA-Z0-9_]+)\}", template_str)
    double_brackets = re.findall(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", template_str)
    all_vars = list(dict.fromkeys(single_brackets + double_brackets))
    return all_vars
