import re

def extract_symbols(text: str):
    if not text:
        return []

    # Capture $SYMBOL or standalone WORD (e.g., GOOGL or GOOGL/CMBT)
    pattern = re.compile(r'\$?[A-Z]{2,6}(?:/[A-Z]{2,6})?')
    candidates = pattern.findall(text.upper())

    # Optional: add filtering of stopwords or false positives here
    return candidates
