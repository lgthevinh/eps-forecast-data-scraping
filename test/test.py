import pdfplumber
import re
from typing import Dict, List, Optional

def find_header_row(table: List[List[str]]) -> Optional[List[str]]:
    """Scans a table to find the row that looks like a year-based header."""
    year_pattern = re.compile(r'\b(20\d{2}|19\d{2})[EF]?\b') # Matches 2023, 2024F, 2025E etc.
    for row in table:
        # A good header has at least 2 years in it
        if sum(1 for cell in row if cell and year_pattern.search(cell)) >= 2:
            return row
    return None

def find_eps_row(table: List[List[str]]) -> Optional[List[str]]:
    """Scans a table to find the row that contains EPS data."""
    eps_pattern = re.compile(r'\bEPS\b', re.IGNORECASE) # Matches 'EPS', 'EPS (VND)' etc.
    for row in table:
        if row and row[0] and eps_pattern.search(row[0]):
            return row
    return None

def parse_eps_from_pdf(pdf_path: str) -> Dict[str, float]:
    """
    Extracts EPS data from a PDF using the "Header-First" strategy.

    Args:
        pdf_path: The file path to the PDF report.

    Returns:
        A dictionary mapping year (e.g., "2023F") to its EPS value.
    """
    all_eps_data = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # extract_tables() is robust and handles complex layouts
            tables = page.extract_tables()
            for table in tables:
                header = find_header_row(table)
                eps_row = find_eps_row(table)

                if not header or not eps_row:
                    continue # Move to the next table if we can't find both

                # Map EPS values to years using header indices
                for i, year in enumerate(header):
                    if not year:
                        continue # Skip empty header cells

                    try:
                        eps_value_str = eps_row[i]
                        if eps_value_str:
                            # Clean the value: remove commas, handle parentheses for negatives
                            cleaned_str = eps_value_str.replace(',', '').strip()
                            if cleaned_str.startswith('(') and cleaned_str.endswith(')'):
                                value = -float(cleaned_str[1:-1])
                            else:
                                value = float(cleaned_str)
                            all_eps_data[year.strip()] = value
                    except (IndexError, ValueError):
                        # This happens if the EPS row is shorter than the header or value is not a number
                        continue
    
    return all_eps_data

if __name__ == '__main__':
    # Replace with the actual path to your PDF file
    # pdf_file = r"E:\University\hust\data-collect\downloads\INN.pdf"
    # This example will use a dummy file path
    root = r"E:\University\hust\data-collect"
    pdf_files = [
        "downloads/AGG_search_1.pdf",
        "downloads/AGG_search_3.pdf",
        "downloads/ANV_BCN_20250825.pdf",
        "downloads/ANV_search_1.pdf",
        "downloads/BCM_search_1.pdf",
        "downloads/BCM_search_3.pdf",
        "downloads/BCM_search_5.pdf",
        "downloads/BCM_search_7.pdf",
    ]
    for pdf_file in pdf_files:
        try:
            eps_data = parse_eps_from_pdf(pdf_file)
            if eps_data:
                print("Successfully extracted EPS data:")
                print(eps_data)
            else:
                print("Could not find a valid EPS table in the document.")
        except FileNotFoundError:
            print(f"Error: The file was not found at {pdf_file}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
