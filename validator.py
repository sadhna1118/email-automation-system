import re
import csv
import io

class EmailValidator:
    """Comprehensive email validation and CSV parsing utility"""
    
    # RFC 5322 compliant regex for robust email syntax validation
    EMAIL_REGEX = re.compile(
        r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
    )
    
    # Common disposable/temporary email provider domains
    DISPOSABLE_DOMAINS = {
        'mailinator.com', 'tempmail.com', '10minutemail.com', 'guerrillamail.com',
        'trashmail.com', 'sharklasers.com', 'yopmail.com', 'dispostable.com',
        'getairmail.com', 'temp-mail.org', 'fakeinbox.com', 'throwawaymail.com'
    }
    
    @classmethod
    def is_valid_syntax(cls, email: str) -> bool:
        """Check if email syntax matches RFC standards"""
        if not email or not isinstance(email, str):
            return False
        email = email.strip()
        if len(email) > 254:
            return False
        return bool(cls.EMAIL_REGEX.match(email))
    
    @classmethod
    def is_disposable(cls, email: str) -> bool:
        """Check if email belongs to known disposable provider"""
        if not email or '@' not in email:
            return False
        domain = email.split('@')[-1].strip().lower()
        return domain in cls.DISPOSABLE_DOMAINS
    
    @classmethod
    def validate_email(cls, email: str) -> dict:
        """
        Validate an email address and return structured report
        """
        email = (email or '').strip()
        if not email:
            return {'valid': False, 'email': email, 'reason': 'Email is empty'}
        
        if not cls.is_valid_syntax(email):
            return {'valid': False, 'email': email, 'reason': 'Invalid email syntax'}
        
        is_disp = cls.is_disposable(email)
        domain = email.split('@')[-1].lower()
        
        return {
            'valid': True,
            'email': email.lower(),
            'domain': domain,
            'is_disposable': is_disp,
            'warning': 'Disposable email address' if is_disp else None
        }

    @classmethod
    def normalize_headers(cls, headers: list) -> dict:
        """Map various common CSV header names to standardized fields"""
        mapping = {}
        for h in headers:
            clean = h.strip().lower().replace(' ', '_').replace('-', '_')
            if any(term in clean for term in ('email', 'mail', 'recipient', 'e_mail')):
                mapping[h] = 'email'
            elif any(term in clean for term in ('company', 'org', 'business', 'corp', 'organization')):
                mapping[h] = 'company'
            elif any(term in clean for term in ('first_name', 'firstname', 'fname')):
                mapping[h] = 'first_name'
            elif any(term in clean for term in ('last_name', 'lastname', 'lname')):
                mapping[h] = 'last_name'
            elif any(term in clean for term in ('full_name', 'person_name', 'contact_name', 'customer_name')) or clean in ('name', 'person', 'contact', 'customer'):
                mapping[h] = 'name'
            elif any(term in clean for term in ('phone', 'mobile', 'cell', 'tel')):
                mapping[h] = 'phone'
            else:
                mapping[h] = clean
        return mapping

    @classmethod
    def parse_csv(cls, file_content_or_path, is_raw_text=False) -> dict:
        """
        Parse CSV data, normalize columns, validate emails, and detect duplicates.
        Returns:
            dict: {
                'valid_rows': list of dicts,
                'invalid_rows': list of dicts with reasons,
                'total_rows': int,
                'columns': list of str,
                'duplicates_removed': int
            }
        """
        if is_raw_text:
            f = io.StringIO(file_content_or_path)
        else:
            f = open(file_content_or_path, 'r', encoding='utf-8-sig', errors='ignore')
        
        try:
            reader = csv.reader(f)
            raw_headers = next(reader, None)
            if not raw_headers:
                return {
                    'valid_rows': [],
                    'invalid_rows': [],
                    'total_rows': 0,
                    'columns': [],
                    'duplicates_removed': 0,
                    'error': 'CSV file is empty'
                }
            
            header_map = cls.normalize_headers(raw_headers)
            has_email_col = 'email' in header_map.values()
            
            if not has_email_col:
                return {
                    'valid_rows': [],
                    'invalid_rows': [],
                    'total_rows': 0,
                    'columns': raw_headers,
                    'duplicates_removed': 0,
                    'error': 'CSV must contain an "email" column (e.g., email, email_address, mail)'
                }
            
            valid_rows = []
            invalid_rows = []
            seen_emails = set()
            duplicates_count = 0
            total_count = 0
            
            for row_num, row in enumerate(reader, start=2):
                if not any(row):  # Skip completely empty rows
                    continue
                total_count += 1
                
                # Build dict for row
                row_dict = {}
                for idx, val in enumerate(row):
                    if idx < len(raw_headers):
                        raw_key = raw_headers[idx]
                        std_key = header_map[raw_key]
                        row_dict[std_key] = val.strip()
                
                # Combine first/last name if name not present
                if 'name' not in row_dict and ('first_name' in row_dict or 'last_name' in row_dict):
                    fn = row_dict.get('first_name', '')
                    ln = row_dict.get('last_name', '')
                    row_dict['name'] = f"{fn} {ln}".strip()
                
                email = row_dict.get('email', '')
                val_result = cls.validate_email(email)
                
                if not val_result['valid']:
                    invalid_rows.append({
                        'row_number': row_num,
                        'email': email,
                        'data': row_dict,
                        'reason': val_result['reason']
                    })
                    continue
                
                normalized_email = val_result['email']
                row_dict['email'] = normalized_email
                
                if normalized_email in seen_emails:
                    duplicates_count += 1
                    continue
                
                seen_emails.add(normalized_email)
                valid_rows.append(row_dict)
                
            return {
                'valid_rows': valid_rows,
                'invalid_rows': invalid_rows,
                'total_rows': total_count,
                'columns': list(header_map.values()),
                'duplicates_removed': duplicates_count
            }
            
        finally:
            if not is_raw_text and hasattr(f, 'close'):
                f.close()
