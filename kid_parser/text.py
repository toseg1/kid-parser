"""Text extraction and normalization helpers shared by kid_parser.fields."""

import re

from pypdf import PdfReader

NORMALIZE_MAP = {
    "“": '"', "”": '"', "‘": "'", "’": "'",
    "ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff",
    "–": "-", "—": "-",
}

CURRENCY_NAME_TO_CODE = {
    "us dollar": "USD", "euro": "EUR", "pound sterling": "GBP",
    "british pound": "GBP", "swiss franc": "CHF", "japanese yen": "JPY",
}

SYMBOL_TO_CODE = {"$": "USD", "€": "EUR", "£": "GBP"}

MONEY = r"(?:([$€£])\s?)?(\d[\d,]*(?:\.\d+)?)\s?(EUR|USD|GBP|CHF)?"


def ligature_fix(text):
    for old, new in NORMALIZE_MAP.items():
        text = text.replace(old, new)
    return text


def extract_pdf_text(pdf_path):
    reader = PdfReader(pdf_path)
    return "\n".join(page.extract_text() for page in reader.pages)


def normalize_flat(text):
    text = ligature_fix(text)
    # pypdf sometimes drops the space between sentences across text runs
    # (e.g. "products.The information"); only fix punctuation-glued joins,
    # not general lower-upper transitions, since those also occur inside
    # legitimate camel-cased words/codes (iShares, BlackRock, IE00B4L5Y983).
    # The 2-letter lookbehind also keeps single-letter abbreviations like
    # "S.A." from being split into "S. A.".
    text = re.sub(r"(?<=[a-zA-Z]{2})([.,;:])(?=[A-Z])", r"\1 ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean(text):
    if text is None:
        return None
    text = re.sub(r"\s+", " ", text).strip(" .,\"'")
    return text or None


def parse_money(symbol, amount, code):
    if amount is None:
        return None
    value = float(amount.replace(",", ""))
    currency = code or SYMBOL_TO_CODE.get(symbol)
    return {"value": value, "currency": currency}


def find(pattern, text, flags=re.I, group=1):
    m = re.search(pattern, text, flags)
    return clean(m.group(group)) if m else None
