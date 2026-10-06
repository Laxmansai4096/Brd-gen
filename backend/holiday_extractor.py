import os
import re
import csv
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

MONTH_MAP = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12
}

HOLIDAY_TYPES = [
    "statutory", "floating", "gazetted", "restricted", "optional",
    "public", "national", "bank", "corporate", "mandatory"
]

HEADER_TOKENS = {"date", "day", "holiday", "name", "occasion", "description", "type", "category", "remarks", "sl", "no", "sr", "s.no"}

def clean_ordinal(text: str) -> str:
    return re.sub(r'(\d+)(st|nd|rd|th)\b', r'\1', text, flags=re.IGNORECASE)

def normalize_holiday_date(raw: str, default_year: int = 2026) -> Optional[str]:
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()
    # Strip leading day of week
    raw = re.sub(r'^(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)[,\s\-:]+', '', raw, flags=re.IGNORECASE)
    raw = clean_ordinal(raw)
    raw = re.sub(r'[^\w\s\-\/\.]', '', raw).strip()
    
    if not raw:
        return None

    # 1. ISO YYYY-MM-DD / YYYY.MM.DD / YYYY/MM/DD
    m_iso = re.search(r'(\d{4})[-\/\.](\d{1,2})[-\/\.](\d{1,2})', raw)
    if m_iso:
        y, m, d = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
        if 1 <= m <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{m:02d}-{d:02d}"

    # 2. Textual Month: e.g. "January 26, 2026", "26 January 2026", "26-Jan-2026", "Jan 26"
    m_text1 = re.search(r'([A-Za-z]{3,9})\s+(\d{1,2})(?:[,\s\-]+(\d{4}))?', raw)
    if m_text1 and m_text1.group(1).lower() in MONTH_MAP:
        mon_str, day_str, yr_str = m_text1.group(1).lower(), m_text1.group(2), m_text1.group(3)
        m = MONTH_MAP[mon_str]
        d = int(day_str)
        y = int(yr_str) if yr_str else default_year
        if 1 <= d <= 31:
            return f"{y:04d}-{m:02d}-{d:02d}"

    m_text2 = re.search(r'(\d{1,2})[\s\-\/]+([A-Za-z]{3,9})(?:[\s\-\/]+(\d{4}))?', raw)
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

def detect_holiday_type(text: str) -> str:
    lower = text.lower()
    for ht in HOLIDAY_TYPES:
        if ht in lower:
            return ht.capitalize()
    return "Statutory"

def parse_holiday_line(line: str, default_year: int = 2026) -> Optional[Dict[str, str]]:
    line = line.strip()
    if not line or len(line) < 4:
        return None
    
    # Skip obvious headers or code blocks
    tokens = set(re.findall(r'[a-zA-Z]+', line.lower()))
    if tokens and tokens.issubset(HEADER_TOKENS):
        return None

    # Try to find a date match in the line
    # Common separators: |, -, :, ,, \t, —
    parts = re.split(r'[\t|;]|\s+-\s+|\s+—\s+|\s+–\s+', line)
    if len(parts) >= 2:
        date_cand = None
        date_idx = -1
        for idx, part in enumerate(parts):
            nd = normalize_holiday_date(part, default_year)
            if nd:
                date_cand = nd
                date_idx = idx
                break
        
        if date_cand:
            other_parts = [p.strip() for i, p in enumerate(parts) if i != date_idx and p.strip()]
            if other_parts:
                # Find name and type
                name = other_parts[0]
                htype = "Statutory"
                if len(other_parts) > 1:
                    htype = detect_holiday_type(other_parts[1])
                else:
                    htype = detect_holiday_type(line)
                
                name = re.sub(r'^\d+[\.\)]\s*', '', name)
                name = re.sub(r'\((statutory|floating|gazetted|restricted|optional|public|national)\)', '', name, flags=re.IGNORECASE).strip()
                if name and len(name) >= 2:
                    return {"date": date_cand, "name": name, "type": htype}

    # Fallback line regex search
    # Find any date pattern in line
    date_cand = normalize_holiday_date(line, default_year)
    if date_cand:
        # Remove date pattern and common separators from line to get name
        rem = re.sub(r'\b\d{4}[-\/\.]\d{1,2}[-\/\.]\d{1,2}\b', '', line)
        rem = re.sub(r'\b\d{1,2}[-\/\.]\d{1,2}(?:[-\/\.]\d{2,4})?\b', '', rem)
        rem = re.sub(r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)(?:\s+\d{4})?\b', '', rem, flags=re.IGNORECASE)
        rem = re.sub(r'\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?(?:[,\s]+\d{4})?\b', '', rem, flags=re.IGNORECASE)
        rem = re.sub(r'^(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)[,\s\-:]+', '', rem, flags=re.IGNORECASE)
        rem = re.sub(r'^\d+[\.\)]\s*', '', rem)
        rem = re.sub(r'[:|,\-—–]', ' ', rem).strip()
        
        htype = detect_holiday_type(line)
        name = re.sub(r'\b(statutory|floating|gazetted|restricted|optional|public|national|holiday)\b', '', rem, flags=re.IGNORECASE).strip()
        name = re.sub(r'\s+', ' ', name).strip()
        if name and len(name) >= 2:
            return {"date": date_cand, "name": name, "type": htype}

    return None

def extract_holidays_from_table(rows: List[List[str]], default_year: int = 2026) -> List[Dict[str, str]]:
    holidays = []
    if not rows:
        return holidays

    date_col = -1
    name_col = -1
    type_col = -1

    # Inspect first few rows for header detection
    for r_idx, row in enumerate(rows[:3]):
        cleaned = [str(c).strip().lower() for c in row if c is not None]
        for c_idx, cell in enumerate(cleaned):
            if "date" in cell or "day" in cell:
                date_col = c_idx
            elif "holiday" in cell or "name" in cell or "occasion" in cell or "description" in cell or "festival" in cell:
                name_col = c_idx
            elif "type" in cell or "category" in cell or "remarks" in cell:
                type_col = c_idx

    for row in rows:
        row_str = [str(c).strip() for c in row if c is not None and str(c).strip()]
        if not row_str or len(row_str) < 2:
            continue
        
        # Check if this row is header
        cell_tokens = set(" ".join(row_str).lower().split())
        if cell_tokens.issubset(HEADER_TOKENS):
            continue

        date_val = None
        name_val = None
        type_val = "Statutory"

        # If columns were identified
        if date_col >= 0 and date_col < len(row):
            date_val = normalize_holiday_date(str(row[date_col]), default_year)
        if name_col >= 0 and name_col < len(row):
            name_val = str(row[name_col]).strip()
        if type_col >= 0 and type_col < len(row):
            type_val = detect_holiday_type(str(row[type_col]))

        # Positional search if column identification was incomplete
        if not date_val or not name_val:
            for idx, cell in enumerate(row_str):
                nd = normalize_holiday_date(cell, default_year)
                if nd and not date_val:
                    date_val = nd
                elif len(cell) > 2 and not name_val:
                    name_val = cell
                elif detect_holiday_type(cell) != "Statutory":
                    type_val = detect_holiday_type(cell)

        if date_val and name_val:
            name_clean = re.sub(r'^\d+[\.\)]\s*', '', name_val)
            name_clean = re.sub(r'\((statutory|floating|gazetted|restricted|optional|public|national)\)', '', name_clean, flags=re.IGNORECASE).strip()
            if name_clean and name_clean.lower() not in ["date", "holiday", "name"]:
                holidays.append({
                    "date": date_val,
                    "name": name_clean,
                    "type": type_val
                })

    return holidays

def extract_holidays_from_file(file_path: str, default_year: int = 2026) -> List[Dict[str, str]]:
    ext = os.path.splitext(file_path)[1].lower()
    holidays: List[Dict[str, str]] = []

    try:
        # 1. DOCX / DOC
        if ext in [".docx", ".doc"]:
            import docx
            doc = docx.Document(file_path)
            # Tables first
            for table in doc.tables:
                table_rows = []
                for row in table.rows:
                    cells = [c.text.strip() for c in row.cells]
                    if any(cells):
                        table_rows.append(cells)
                holidays.extend(extract_holidays_from_table(table_rows, default_year))
            
            # Paragraphs
            for p in doc.paragraphs:
                txt = p.text.strip()
                if txt:
                    item = parse_holiday_line(txt, default_year)
                    if item:
                        holidays.append(item)

        # 2. PDF
        elif ext == ".pdf":
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                for page in doc:
                    # Check for tables if PyMuPDF table finder is supported
                    try:
                        tabs = page.find_tables()
                        if tabs and tabs.tables:
                            for tab in tabs.tables:
                                extracted_tab = tab.extract()
                                holidays.extend(extract_holidays_from_table(extracted_tab, default_year))
                    except Exception:
                        pass
                    
                    # Extract text lines
                    page_text = page.get_text("text")
                    for line in page_text.splitlines():
                        item = parse_holiday_line(line, default_year)
                        if item:
                            holidays.append(item)
            except Exception:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                for page in reader.pages:
                    txt = page.extract_text() or ""
                    for line in txt.splitlines():
                        item = parse_holiday_line(line, default_year)
                        if item:
                            holidays.append(item)

        # 3. XLSX / XLS
        elif ext in [".xlsx", ".xls"]:
            import openpyxl
            wb = openpyxl.load_workbook(file_path, data_only=True)
            for sheet in wb.worksheets:
                sheet_rows = []
                for row in sheet.iter_rows(values_only=True):
                    row_cells = [str(c) if c is not None else "" for c in row]
                    if any(row_cells):
                        sheet_rows.append(row_cells)
                holidays.extend(extract_holidays_from_table(sheet_rows, default_year))

        # 4. CSV / TSV
        elif ext in [".csv", ".tsv"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                sample = f.read(2048)
                delimiter = "\t" if "\t" in sample and ext == ".tsv" else (";" if ";" in sample and "," not in sample else ",")
                f.seek(0)
                reader = csv.reader(f, delimiter=delimiter)
                csv_rows = list(reader)
                holidays.extend(extract_holidays_from_table(csv_rows, default_year))

        # 5. JSON / TXT
        elif ext in [".json", ".txt"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                try:
                    data = json.loads(content)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                d_val = item.get("date") or item.get("day")
                                n_val = item.get("name") or item.get("title") or item.get("holiday") or item.get("occasion")
                                t_val = item.get("type") or item.get("category") or "Statutory"
                                if d_val and n_val:
                                    nd = normalize_holiday_date(str(d_val), default_year)
                                    if nd:
                                        holidays.append({
                                            "date": nd,
                                            "name": str(n_val).strip(),
                                            "type": detect_holiday_type(str(t_val))
                                        })
                    elif isinstance(data, dict):
                        for k, v in data.items():
                            if isinstance(v, list):
                                for sub in v:
                                    if isinstance(sub, dict) and "date" in sub:
                                        nd = normalize_holiday_date(str(sub["date"]), default_year)
                                        if nd:
                                            holidays.append({
                                                "date": nd,
                                                "name": str(sub.get("name", "Holiday")).strip(),
                                                "type": detect_holiday_type(str(sub.get("type", "Statutory")))
                                            })
                except Exception:
                    for line in content.splitlines():
                        item = parse_holiday_line(line, default_year)
                        if item:
                            holidays.append(item)

    except Exception as e:
        print(f"Error parsing holiday file {file_path}: {e}")

    # Deduplicate and sort
    seen = set()
    unique_holidays = []
    for h in holidays:
        key = (h["date"], h["name"].lower())
        if key not in seen:
            seen.add(key)
            unique_holidays.append(h)

    unique_holidays.sort(key=lambda x: x["date"])
    return unique_holidays
