import re
import logging
from datetime import datetime

def parse_vietnamese_date(date_string):
    """
    Parse Vietnamese date format (DD/MM/YYYY) and return day, month, year as integers
    
    Args:
        date_string (str): Date string in format "01/12/2016" or similar
        
    Returns:
        tuple: (day, month, year) as integers, or (None, None, None) if parsing fails
    """
    try:
        # Remove any extra whitespace
        date_string = date_string.strip()
        
        # Pattern to match DD/MM/YYYY format
        date_pattern = r'(\d{1,2})/(\d{1,2})/(\d{4})'
        match = re.search(date_pattern, date_string)
        
        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            year = int(match.group(3))
            
            # Validate the date
            try:
                datetime(year, month, day)  # This will raise ValueError if invalid
                return day, month, year
            except ValueError:
                logging.warning(f"Invalid date values: {day}/{month}/{year}")
                return None, None, None
        else:
            # Try alternative formats or patterns
            # Pattern for YYYY-MM-DD format
            iso_pattern = r'(\d{4})-(\d{1,2})-(\d{1,2})'
            iso_match = re.search(iso_pattern, date_string)
            
            if iso_match:
                year = int(iso_match.group(1))
                month = int(iso_match.group(2))
                day = int(iso_match.group(3))
                
                try:
                    datetime(year, month, day)
                    return day, month, year
                except ValueError:
                    logging.warning(f"Invalid date values: {day}/{month}/{year}")
                    return None, None, None
            
            logging.warning(f"Could not parse date string: {date_string}")
            return None, None, None
            
    except Exception as e:
        logging.error(f"Error parsing date '{date_string}': {e}")
        return None, None, None

def clean_number(val):
    if not val:
        return None
    val = str(val).strip().replace(".", "").replace(",", "")
    if not val:
        return None
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except:
            return None

year_patterns = [
    r"\d{4}(?:E|F)", 
    r"(?:Dec)[- ]?\d{2}",
    r"31/12/\d{2,4}",
    r"FY\d{2,4}[EF]?",
    r"F\*\d{2,4}"
]
        
def normalize_year(raw):
    """
    Convert strings like '2018F', '2017E', 'Dec-21', '31/12/2022', 'F*22', 'F*2022'
    into a clean 4-digit year string.
    """
    if not raw:
        return None
    raw = raw.strip()
    
    # Handle using year_patterns
    for pattern in year_patterns:
        if re.search(pattern, raw):
            break
    else:
        return raw  # no pattern matched, return as is
    
    # Handle explicit 4-digit year + suffix (2018F, 2017E)
    m = re.match(r"(\d{4})(?:[EF])?", raw)
    if m:
        return m.group(1)

    # Handle DD/MM/YYYY or similar
    m = re.search(r"\d{4}", raw)
    if m:
        return m.group(0)
    
    # Handle 31/12/2022, 31/12/22 etc.
    m = re.match(r"31/12/(\d{2,4})", raw)
    if m:
        yy = int(m.group(1))
        year = 2000 + yy if yy < 50 else 1900 + yy
        return str(year)
    
    # Handle FY22, FY2022, FY2022E etc.
    m = re.match(r"FY(\d{2,4})(?:[EF])?", raw, re.IGNORECASE)
    if m:
        yy = int(m.group(1))
        year = 2000 + yy if yy < 50 else 1900 + yy
        return str(year)
    

    # Handle Dec-21, Mar-20 etc.
    m = re.match(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[- ]?(\d{2})", raw, re.IGNORECASE)
    if m:
        yy = int(m.group(1))
        # assume 2000s if yy < 50 else 1900s
        year = 2000 + yy if yy < 50 else 1900 + yy
        return str(year)

    # Handle F*22, F22F etc.
    m = re.match(r"F\*?(\d{2})", raw)
    if m:
        yy = int(m.group(1))
        year = 2000 + yy if yy < 50 else 1900 + yy
        return str(year)

    # Handle F*2022, F*22 etc.
    m = re.match(r"F\*?(\d{2,4})", raw)
    if m:
        yy = int(m.group(1))
        year = 2000 + yy if yy < 50 else 1900 + yy
        return str(year)

    return raw  # fallback

def verify_four_digit_year(year_str):
    """Verify if the given string is a valid 4-digit year."""
    if re.match(r"^\d{4}$", year_str):
        year_int = int(year_str)
        if 1900 <= year_int <= 2100:  # reasonable range for years
            return True
    return False

def extract_report_date(text: str) -> str:
    """
    Extracts a date in format DD/MM/YYYY from given text.
    Returns a datetime.date object, or None if not found.
    """
    match = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", text)
    if match:
        try:
            return match.group(1)
        except ValueError:
            return None
    return None