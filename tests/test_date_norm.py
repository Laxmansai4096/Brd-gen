import re
from datetime import datetime
from typing import Optional, List, Dict, Any

MONTH_MAP = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12
}

def clean_ordinal(text: str) -> str:
    return re.sub(r'(\d+)(st|nd|rd|th)\b', r'\1', text, flags=re.IGNORECASE)

def normalize_date_string(raw: str, default_year: int = 2026) -> Optional[str]:
    raw = raw.strip()
    raw = re.sub(r'^(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)[,\s\-:]+', '', raw, flags=re.IGNORECASE)
    raw = clean_ordinal(raw)
    raw = re.sub(r'[^\w\s\-\/\.]', '', raw).strip()
    
    # 1. ISO YYYY-MM-DD
    m_iso = re.search(r'(\d{4})[-\/\.](\d{1,2})[-\/\.](\d{1,2})', raw)
    if m_iso:
        y, m, d = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
        if 1 <= m <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{m:02d}-{d:02d}"
            
    # 2. Textual Month: e.g. "January 26, 2026", "26 January 2026", "26-Jan-2026", "Jan 26"
    m_text1 = re.search(r'([A-Za-z]+)\s+(\d{1,2})(?:[,\s]+(\d{4}))?', raw)
    if m_text1 and m_text1.group(1).lower() in MONTH_MAP:
        mon_str, day_str, yr_str = m_text1.group(1).lower(), m_text1.group(2), m_text1.group(3)
        m = MONTH_MAP[mon_str]
        d = int(day_str)
        y = int(yr_str) if yr_str else default_year
        if 1 <= d <= 31:
            return f"{y:04d}-{m:02d}-{d:02d}"

    m_text2 = re.search(r'(\d{1,2})[\s\-\/]+([A-Za-z]+)(?:[\s\-\/]+(\d{4}))?', raw)
    if m_text2 and m_text2.group(2).lower() in MONTH_MAP:
        day_str, mon_str, yr_str = m_text2.group(1), m_text2.group(2).lower(), m_text2.group(3)
        m = MONTH_MAP[mon_str]
        d = int(day_str)
        y = int(yr_str) if yr_str else default_year
        if 1 <= d <= 31:
            return f"{y:04d}-{m:02d}-{d:02d}"

    # 3. Numeric DD-MM-YYYY or MM-DD-YYYY or DD/MM/YYYY
    m_num = re.search(r'(\d{1,2})[-\/\.](\d{1,2})(?:[-\/\.](\d{2,4}))?', raw)
    if m_num:
        p1, p2, p3 = int(m_num.group(1)), int(m_num.group(2)), m_num.group(3)
        y = int(p3) if p3 else default_year
        if y < 100:
            y += 2000
        # If p1 > 12, p1 is day, p2 is month
        if 1 <= p2 <= 12 and 1 <= p1 <= 31:
            return f"{y:04d}-{p2:02d}-{p1:02d}"
        elif 1 <= p1 <= 12 and 1 <= p2 <= 31:
            return f"{y:04d}-{p1:02d}-{p2:02d}"
            
    return None

test_cases = [
    "2026-01-01",
    "26/01/2026",
    "Monday, 26th January 2026",
    "15-Aug-2026",
    "December 25, 2026",
    "02.10.2026",
    "Nov 26",
    "1st May",
]
for t in test_cases:
    print(f"{t} -> {normalize_date_string(t)}")
