import logging
import re
import pdfplumber
import camelot

from scraping.utils.Utils import parse_vietnamese_date, clean_number, verify_four_digit_year, normalize_year

# V3 Scraping
def extract_clean_eps_v3(pdf_path, report_date):
    if not report_date:
        return None
    _, _, rep_year = parse_vietnamese_date(report_date)
    rep_year = int(rep_year)

    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            logging.info("Extracting tables from page..., table mode")
            tables = page.extract_tables()
            for table in tables:
                # Normalize table: replace None with ""
                table = [[(c or "").strip() for c in row] for row in table if row]

                # Find a row containing EPS or EPS (VNĐ)
                eps_rows = [row for row in table if any(re.search(r"EPS", c, re.IGNORECASE) for c in row)]
                if not eps_rows:
                    logging.info("No EPS row found in this table.")
                    continue

                for eps_row in eps_rows:
                    # first col is label, rest are EPS values
                    values = [clean_number(c) for c in eps_row[1:] if c]

                    # Find header row (years)
                    header = None
                    for r in table:
                        if any(re.search(r"\d{4}", c) for c in r):
                            header = r
                            break
                    if not header:
                        header = table[0]

                    years = [c for c in header[1:] if c]

                    for year, val in zip(years, values):
                        val = clean_number(val)
                        if val is None or not (500 <= val <= 18000):
                            logging.info(f"No valid EPS value found for {year}.")
                            continue
                        
                        clean_year = normalize_year(year)
                        
                        if not clean_year or not verify_four_digit_year(clean_year):
                            logging.warning(f"Invalid year format: {year} -> {clean_year}")
                            continue
                        
                        is_forecast = False
                        
                        if clean_year.isdigit() and int(clean_year) >= rep_year:
                            is_forecast = True
                        results.append({
                            "year": year,
                            "clean_year": clean_year,
                            "eps": val,
                            "is_forecast": is_forecast,
                            "report_date": report_date,
                        })
        
    
    if not results:  
        logging.info("No EPS data found in tables, trying full text search. text mode")
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

            # Match year rows like: 2015 2016E 2017F 2018F Dec-21 F*22 31/12/2022
            year_line_pattern = re.compile(
                r"(?:\d{4}(?:E|F)?)"             # 2015, 2016E, 2017F
                r"|(?:[A-Za-z]{3}-\d{2})"        # Dec-21
                r"|(?:FY\d{2,4})"                # FY22, FY2022
                r"|(?:F\d{2,4})"                 # F22, F2022
                r"|(?:31/12/\d{4})"              # ONLY 31/12/YYYY
            )

            # Match EPS values row with 4 numbers
            eps_line_pattern = re.compile(
                r"EPS[^\d]*([\d\.,]+)\s+([\d\.,]+)\s+([\d\.,]+)\s+([\d\.,]+)",
                re.IGNORECASE
            )

            years = []
            values = []

            year_match = year_line_pattern.search(text)
            if year_match:
                years = [y for y in year_match.groups() if y]

            eps_match = eps_line_pattern.search(text)
            if eps_match:
                values = [v for v in eps_match.groups() if v]

            for year, val in zip(years, values):
                # Normalize year (remove E/F if exists)
                clean_year = normalize_year(year)
                if not clean_year or not verify_four_digit_year(clean_year):
                    logging.warning(f"Invalid year format in text mode: {year} -> {clean_year}")
                    continue
                val = clean_number(val)
                if val is None and not (500 <= val <= 18000):
                    logging.info(f"No valid EPS value found for {year} in text mode.")
                    continue
                is_forecast = False
                if clean_year.isdigit() and int(clean_year) >= rep_year:
                    is_forecast = True
                results.append({
                            "year": year,
                            "clean_year": clean_year,
                            "eps": val,
                            "is_forecast": is_forecast,
                            "report_date": report_date,
                        })

    return results

# V4 Scraping
def extract_clean_eps_v4(pdf_path, report_date):
    if not report_date:
        return None
    _, _, rep_year = parse_vietnamese_date(report_date)
    rep_year = int(rep_year)

    results = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            try:
                tables = page.extract_tables()
            except Exception as e:
                logging.warning(f"extract_tables failed: {e}")
                continue

            for idx, table in enumerate(tables):
                # --- Step 1: structured parsing ---
                table = [[(c or "").strip() for c in row] for row in table if row]

                eps_rows = [
                    row for row in table
                    if any(re.search(r"(EPS|Lãi cơ bản trên cổ phiếu)", c, re.IGNORECASE) for c in row)
                ]
                if eps_rows:
                    # detect header row (years)
                    header = None
                    for r in table:
                        if any(
                            re.search(r"\d{4}", c) or
                            re.search(r"(?:Dec|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov)[- ]?\d{2}", c) or
                            re.search(r"\d{1,2}/\d{1,2}/\d{4}", c) for c in r
                        ):
                            header = r
                            break
                    if not header:
                        header = table[0]

                    years_raw = [c for c in header[1:] if c]

                    for eps_row in eps_rows:
                        values = [clean_number(c) for c in eps_row[1:] if c]
                        for year, val in zip(years_raw, values):
                            if val is None or not (500 <= val <= 18000):  # strict filter
                                continue
                            clean_year = normalize_year(year)
                            if not clean_year or not verify_four_digit_year(clean_year):
                                continue
                            is_forecast = False
                            if clean_year.isdigit() and int(clean_year) >= rep_year:
                                is_forecast = True
                            results.append({
                                "year": year,
                                "clean_year": clean_year,
                                "eps": val,
                                "is_forecast": is_forecast,
                                "report_date": report_date,
                            })

                # --- Step 2: fallback regex on flattened table ---
                if not results:
                    flat_text = "\n".join(" ".join(row) for row in table)

                    year_pattern = re.compile(
                        r"(?:\d{4}(?:E|F)?)|(?:\w{3}-\d{2})|(?:F\*\d{2,4})|(?:\d{1,2}/\d{1,2}/\d{4})"
                    )
                    eps_pattern = re.compile(
                        r"(?:EPS|Lãi cơ bản trên cổ phiếu)[^\d]*(\d[\d\., ]+)+",
                        re.IGNORECASE
                    )

                    years = year_pattern.findall(flat_text)
                    eps_matches = eps_pattern.findall(flat_text)

                    values = []
                    for match in eps_matches:
                        vals = [clean_number(v) for v in re.split(r"\s+", match.strip()) if v]
                        values.extend(vals)

                    for year, val in zip(years, values):
                        clean_year = normalize_year(year)
                        if not clean_year or not verify_four_digit_year(clean_year):
                            continue
                        if val is None or not (500 <= val <= 18000):  # strict filter
                            continue
                        is_forecast = False
                        if clean_year.isdigit() and int(clean_year) >= rep_year:
                            is_forecast = True
                        results.append({
                            "year": year,
                            "clean_year": clean_year,
                            "eps": val,
                            "is_forecast": is_forecast,
                            "report_date": report_date,
                        })

    return results

def validate_sec_code_in_pdf(pdf_path, sec_code):
    """Check if sec_code exists in the first 2 pages of the PDF."""
    sec_code = sec_code.upper()
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages_to_check = min(2, len(pdf.pages))
            text = ""
            for i in range(pages_to_check):
                text += pdf.pages[i].extract_text() or ""
        if re.search(rf"\b{re.escape(sec_code)}\b", text, re.IGNORECASE):
            return True
        else:
            return False
    except Exception as e:
        logging.error(f"Failed to validate sec_code in {pdf_path}: {e}")
        return False


# V5 Scraping - cross validate
def extract_clean_eps_w_sc_v5(pdf_path, report_date, sec_code):
    if not validate_sec_code_in_pdf(pdf_path, sec_code):
        logging.warning(f"SEC_CODE '{sec_code}' not found in {pdf_path}")
        return None

    if not report_date:
        return None
    _, _, rep_year = parse_vietnamese_date(report_date)
    rep_year = int(rep_year)

    final_results = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            try:
                tables = page.extract_tables()
            except Exception as e:
                logging.warning(f"extract_tables failed: {e}")
                continue

            for idx, table in enumerate(tables):
                # Normalize table
                table = [[(c or "").strip() for c in row] for row in table if row]

                # --- Step 1: structured table parsing ---
                structured_results = []
                eps_rows = [
                    row for row in table
                    if any(re.search(r"(\bEPS\b)", c, re.IGNORECASE) for c in row)
                ]
                if eps_rows:
                    # find header row
                    header = None
                    for r in table:
                        if any(
                            re.search(r"\d{4}", c) or
                            re.search(r"(?:Dec|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov)[- ]?\d{2}", c) or
                            re.search(r"\d{1,2}/\d{1,2}/\d{4}", c) for c in r
                        ):
                            header = r
                            break
                    if not header:
                        header = table[0]

                    years_raw = [c for c in header[1:] if c]

                    for eps_row in eps_rows:
                        values = [clean_number(c) for c in eps_row[1:] if c]
                        for year, val in zip(years_raw, values):
                            if val is None or not (500 <= val <= 18000):
                                continue
                            clean_year = normalize_year(year)
                            if not clean_year or not verify_four_digit_year(clean_year):
                                continue
                            is_forecast = False
                            if clean_year.isdigit() and int(clean_year) >= rep_year:
                                is_forecast = True
                            structured_results.append({
                                "year": year,
                                "clean_year": clean_year,
                                "eps": val,
                                "is_forecast": is_forecast,
                                "report_date": report_date,
                            })

                # --- Step 2: regex on flattened table text ---
                flat_text = "\n".join(" ".join(row) for row in table)
                year_pattern = re.compile(
                    r"(?:\d{4}(?:E|F)?)|(?:\w{3}-\d{2})|(?:F\*\d{2,4})|(?:31/12/\d{4})"
                )
                eps_pattern = re.compile(
                    r"(?:EPS|Lãi cơ bản trên cổ phiếu)[^\d]*(\d[\d\., ]+)+",
                    re.IGNORECASE
                )

                years = year_pattern.findall(flat_text)
                eps_matches = eps_pattern.findall(flat_text)

                regex_results = []
                values = []
                for match in eps_matches:
                    vals = [clean_number(v) for v in re.split(r"\s+", match.strip()) if v]
                    values.extend(vals)

                for year, val in zip(years, values):
                    clean_year = normalize_year(year)
                    if not clean_year or not verify_four_digit_year(clean_year):
                        continue
                    if val is None or not (500 <= val <= 18000):
                        continue
                    is_forecast = False
                    if clean_year.isdigit() and int(clean_year) >= rep_year:
                        is_forecast = True
                    regex_results.append({
                        "year": year,
                        "clean_year": clean_year,
                        "eps": val,
                        "is_forecast": is_forecast,
                        "report_date": report_date,
                    })

                # --- Step 3: cross-validate results ---
                if structured_results and regex_results:
                    validated = []
                    for s in structured_results:
                        for r in regex_results:
                            if (
                                s["clean_year"] == r["clean_year"] and
                                s["eps"] == r["eps"]
                            ):
                                validated.append(s)
                    final_results.extend(validated)
                else:
                    # if only one mode found, keep it
                    final_results.extend(structured_results or regex_results)

    return final_results

def extract_clean_eps_v5(pdf_path, report_date, valid_codes=None, blacklist_codes=None):
    if not report_date:
        return None
    _, _, rep_year = parse_vietnamese_date(report_date)
    rep_year = int(rep_year)

    final_results = []
    
    # --- Step 0: detect sec_code in the PDF ---
    sec_code = None
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages_to_check = min(3, len(pdf.pages))
            text = ""
            for i in range(pages_to_check):
                text += pdf.pages[i].extract_text() or ""

        # Only match exactly 3 uppercase letters, standalone
        matches = re.findall(r"(?<![A-Z])([A-Z]{3})(?![A-Z])", text)

        blacklist = blacklist_codes or {"MBS", "PDF", "EPS", "CP", "QTR", "BCT"}
        tickers = [m for m in matches if m not in blacklist]

        # Cross-check with valid_codes list if provided
        if valid_codes:
            tickers = [m for m in tickers if m in valid_codes]

        if tickers:
            sec_code = max(set(tickers), key=tickers.count)  # most frequent
        else:
            logging.warning(f"No valid sec_code found in {pdf_path}")
            return []  # skip EPS extraction if no ticker detected
    except Exception as e:
        logging.error(f"Failed sec_code detection in {pdf_path}: {e}")
        return []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            try:
                tables = page.extract_tables()
            except Exception as e:
                logging.warning(f"extract_tables failed: {e}")
                continue

            for idx, table in enumerate(tables):
                # Normalize table
                table = [[(c or "").strip() for c in row] for row in table if row]

                # --- Step 1: structured table parsing ---
                structured_results = []
                eps_rows = [
                    row for row in table
                    if any(re.search(r"(\bEPS\b)", c, re.IGNORECASE) for c in row)
                ]
                if eps_rows:
                    # find header row
                    header = None
                    for r in table:
                        if any(
                            re.search(r"\d{4}(?:E|F)", c)                     # only 2022E, 2022F
                            or re.search(r"(?:Dec)[- ]?\d{2}", c)             # Dec-12
                            or re.search(r"31/12/\d{2,4}", c)                 # 31/12/22 or 31/12/2022
                            or re.search(r"FY\d{2,4}[EF]?", c)                # FY22, FY22F, FY2022, FY2022F
                            for c in r
                        ):
                            header = r
                            break
                    if not header:
                        header = table[0]

                    years_raw = [c for c in header[1:] if c]

                    for eps_row in eps_rows:
                        values = [clean_number(c) for c in eps_row[1:] if c]
                        for year, val in zip(years_raw, values):
                            if val is None or not (500 <= val <= 18000):
                                continue
                            clean_year = normalize_year(year)
                            if not clean_year or not verify_four_digit_year(clean_year):
                                continue
                            is_forecast = False
                            if clean_year.isdigit() and int(clean_year) >= rep_year:
                                is_forecast = True
                            structured_results.append({
                                "year": year,
                                "clean_year": clean_year,
                                "eps": val,
                                "is_forecast": is_forecast,
                                "report_date": report_date,
                                "sec_code": sec_code,
                            })

                # --- Step 2: regex on flattened table text ---
                flat_text = "\n".join(" ".join(row) for row in table)
                year_pattern = re.compile(
                    r"(?:\d{4}(?:E|F)?)|(?:\w{3}-\d{2})|(?:F\*\d{2,4})|(?:31/12/\d{4})"
                )
                eps_pattern = re.compile(
                    r"(?:EPS|Lãi cơ bản trên cổ phiếu)[^\d]*(\d[\d\., ]+)+",
                    re.IGNORECASE
                )

                years = year_pattern.findall(flat_text)
                eps_matches = eps_pattern.findall(flat_text)

                regex_results = []
                values = []
                for match in eps_matches:
                    vals = [clean_number(v) for v in re.split(r"\s+", match.strip()) if v]
                    values.extend(vals)

                for year, val in zip(years, values):
                    clean_year = normalize_year(year)
                    if not clean_year or not verify_four_digit_year(clean_year):
                        continue
                    if val is None or not (500 <= val <= 18000):
                        continue
                    is_forecast = False
                    if clean_year.isdigit() and int(clean_year) >= rep_year:
                        is_forecast = True
                    regex_results.append({
                        "year": year,
                        "clean_year": clean_year,
                        "eps": val,
                        "is_forecast": is_forecast,
                        "report_date": report_date,
                        "sec_code": sec_code,
                    })

                # --- Step 3: cross-validate results ---
                if structured_results and regex_results:
                    validated = []
                    for s in structured_results:
                        for r in regex_results:
                            if (
                                s["clean_year"] == r["clean_year"] and
                                s["eps"] == r["eps"]
                            ):
                                validated.append(s)
                    final_results.extend(validated)
                else:
                    # if only one mode found, keep it
                    final_results.extend(structured_results or regex_results)

    return final_results

def extract_clean_eps_v6(pdf_path, report_date, valid_codes=None, blacklist_codes=None, url=None, firm=None, already_detected_sc=None):
    if not report_date:
        return None
    _, _, rep_year = parse_vietnamese_date(report_date)
    rep_year = int(rep_year)
    year_patterns = [
        r"\d{4}(?:E|F)", 
        r"(?:Dec)[- ]?\d{2}",
        r"31/12/\d{2,4}",
        r"FY\d{2,4}[EF]?",
        r"F\*\d{2,4}"
    ]
    year_patterns_v2 = [
        r"\d{4}(?:E|F)?(?:\s*(?:cũ|mới|old|new))?",     # 2021, 2021E, 2021F, 2021 cũ, 2021 mới
        r"(?:Dec)[- ]?\d{2}(?:\s*(?:cũ|mới|old|new))?", # Dec-21, Dec-21 mới
        r"31/12/\d{2,4}(?:\s*(?:cũ|mới|old|new))?",     # 31/12/2021, 31/12/2021 cũ
        r"FY\d{2,4}[EF]?(?:\s*(?:cũ|mới|old|new))?",    # FY22, FY2022F, FY22 mới
        r"F\*?\d{2,4}(?:\s*(?:cũ|mới|old|new))?"        # F22, F*22, F2022 cũ
    ]
    
    global_year_pattern = re.compile(
        "|".join(year_patterns),
        re.IGNORECASE
        )
    eps_patterns = [
        r"^\s*EPS\b"
    ]
    global_eps_pattern = re.compile("|".join(eps_patterns), re.IGNORECASE)
    final_results = []
    
    # --- Step 0: detect sec_code in the PDF ---
    
    sec_code = None
    try:
        if already_detected_sc:
            sec_code = already_detected_sc
        else:
            with pdfplumber.open(pdf_path) as pdf:
                pages_to_check = min(3, len(pdf.pages))
                text = ""
                for i in range(pages_to_check):
                    text += pdf.pages[i].extract_text() or ""

            # Only match exactly 3 uppercase letters, or with 2 uppercase letters with 1 number, standalone
            matches = re.findall(r"(?<![A-Z])([A-Z]{3})(?![A-Z])", text)
            matches += re.findall(r"(?<![A-Z])([A-Z]{2}\d)(?![A-Z])", text)

            blacklist = blacklist_codes or {"MBS", "PDF", "EPS", "KKN", "CP", "QTR", "BCT", "KCN", "HNX", "HSX", "HOSE", "VNI", "VN30", "UPCOM", "USD", "VND", "VIX", "VNINDEX", "FY2", "FY1"}
            tickers = [m for m in matches if m not in blacklist]

            # Cross-check with valid_codes list if provided
            if valid_codes:
                tickers = [m for m in tickers if m in valid_codes]

            if tickers:
                sec_code = max(set(tickers), key=tickers.count)  # most frequent
                logging.info(f"Detected sec_code '{sec_code}' in {pdf_path}")
            else:
                logging.warning(f"No valid sec_code found in {pdf_path}")
                return []  # skip EPS extraction if no ticker detected

        tables = camelot.read_pdf(pdf_path, pages='1-end', flavor='stream')
        results = []

        for table in tables:
            df = table.df
            # logging.info(f"Extracted table {table} with \n{df}")
            # Remove all columns with out EPS or year patterns
            cols_to_keep = []
            for col in df.columns:
                if df[col].apply(lambda x: bool(global_eps_pattern.search(x)) or bool(global_year_pattern.search(x))).any():
                    cols_to_keep.append(col)
            if not cols_to_keep:
                continue
            df = df[cols_to_keep]
            logging.info(f"After filtering, table has columns: {df.columns.tolist()}")
            # Find EPS column and delete columns before it
            eps_col = None
            for col in df.columns:
                if df[col].apply(lambda x: bool(global_eps_pattern.search(x))).any():
                    eps_col = col
                    break
            if eps_col is None:
                continue
            df = df.loc[:, df.columns[df.columns.get_loc(eps_col):]]
            logging.info(f"After EPS filtering, table has columns: {df.columns.tolist()}")
            # Filtering row with EPS and year patterns
            df = df[df.apply(lambda row: row.astype(str).str.contains(global_eps_pattern).any() or row.astype(str).str.contains(global_year_pattern).any(), axis=1)]
            if df.empty:
                logging.warning(f"No rows with EPS or year patterns found in table from {pdf_path}")
                continue
            # Reset index and columns
            df.columns = df.iloc[0]
            df = df[1:]
            df = df.reset_index(drop=True)
            logging.info(f"Filtered table:\n{df}")
            # Expected format:
            # 1 Chỉ số tài chính 31/12/2024 31/12/2025 31/12/2026 31/12/2027
            # 0              EPS      3,679      3,993      4,726      5,493
            header = df.columns.tolist()
            for idx, row in df.iterrows():
                logging.info(f"Processing row {idx}: {row.tolist()}")
                # Check if EPS in the first column
                if not any(re.search(r"\bEPS\b", str(c), re.IGNORECASE) for c in row):
                    continue
                # Extract EPS values
                eps_values = row[1:].tolist()
                for year, eps in zip(header[1:], eps_values):
                    logging.info(f"Year: {year}, EPS: {eps}")
                
                    clean_year = normalize_year(year)
                    if not verify_four_digit_year(clean_year):
                        logging.warning(f"Invalid year format for year '{year}' in row {idx}")
                        continue
                    
                    final_results.append({
                        "year": year,
                        "clean_year": clean_year,
                        "eps": clean_number(eps),
                        "is_forecast": clean_year and int(clean_year) >= rep_year,
                        "report_date": report_date,
                        "sec_code": sec_code,
                        "firm": firm,
                        "url": url + "  " # Space to avoid URL truncation in some DB viewers
                    })
        return final_results
    except Exception as e:
        logging.error(f"Failed sec_code detection in {pdf_path}: {e}")
        return []
    

def extract_clean_eps_w_sc_v6(pdf_path, report_date, sec_code, url=None, firm=None, pages='1-end'):
    """
    (parameter) pages: str
    pages : str, optional (default: '1')
    Comma-separated page numbers. Example: '1,3,4' or '1,4-end' or 'all'.
    """
    if not report_date:
        return None
    _, _, rep_year = parse_vietnamese_date(report_date)
    rep_year = int(rep_year)
    year_patterns = [
        r"\d{4}(?:E|F)", 
        r"(?:Dec)[- ]?\d{2}",
        r"31/12/\d{2,4}",
        r"FY\d{2,4}[EF]?",
        r"F\*\d{2,4}"
    ]
    global_year_pattern = re.compile(
        "|".join(year_patterns),
        re.IGNORECASE
        )
    eps_patterns = [
        r"^\s*EPS\b",
    ]
    global_eps_pattern = re.compile("|".join(eps_patterns), re.IGNORECASE)
    final_results = []
    
    try:
        tables = camelot.read_pdf(pdf_path, pages='1-end', flavor='stream')

        for table in tables:
            df = table.df
            # logging.info(f"Extracted table {table} with \n{df}")
            # Remove all columns with out EPS or year patterns
            cols_to_keep = []
            for col in df.columns:
                if df[col].apply(lambda x: bool(global_eps_pattern.search(x)) or bool(global_year_pattern.search(x))).any():
                    cols_to_keep.append(col)
            if not cols_to_keep:
                continue
            df = df[cols_to_keep]
            logging.info(f"After filtering, table has columns: {df.columns.tolist()}")
            # Find EPS column and delete columns before it
            eps_col = None
            for col in df.columns:
                if df[col].apply(lambda x: bool(global_eps_pattern.search(x))).any():
                    eps_col = col
                    break
            if eps_col is None:
                continue
            df = df.loc[:, df.columns[df.columns.get_loc(eps_col):]]
            logging.info(f"After EPS filtering, table has columns: {df.columns.tolist()}")
            # Filtering row with EPS and year patterns
            df = df[df.apply(lambda row: row.astype(str).str.contains(global_eps_pattern).any() or row.astype(str).str.contains(global_year_pattern).any(), axis=1)]
            if df.empty:
                logging.warning(f"No rows with EPS or year patterns found in table from {pdf_path}")
                continue
            # Reset index and columns
            df.columns = df.iloc[0]
            df = df[1:]
            df = df.reset_index(drop=True)
            logging.info(f"Filtered table:\n{df}")
            # Expected format:
            # 1 Chỉ số tài chính 31/12/2024 31/12/2025 31/12/2026 31/12/2027
            # 0              EPS      3,679      3,993      4,726      5,493
            header = df.columns.tolist()
            for idx, row in df.iterrows():
                logging.info(f"Processing row {idx}: {row.tolist()}")
                # Check if EPS in the first column
                if not any(re.search(r"\bEPS\b", str(c), re.IGNORECASE) for c in row):
                    continue
                # Extract EPS values
                eps_values = row[1:].tolist()
                for year, eps in zip(header[1:], eps_values):
                    logging.info(f"Year: {year}, EPS: {eps}")
                
                    clean_year = normalize_year(year)
                    final_results.append({
                        "year": year,
                        "clean_year": clean_year,
                        "eps": clean_number(eps),
                        "is_forecast": clean_year.isdigit() and int(clean_year) >= rep_year,
                        "report_date": report_date,
                        "sec_code": sec_code,
                        "firm": firm,
                        "url": url
                    })
        return final_results
    except Exception as e:
        logging.error(f"Failed sec_code detection in {pdf_path}: {e}")
        return []