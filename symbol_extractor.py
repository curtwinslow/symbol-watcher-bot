import re

def extract_symbols_from_text(text):
    symbols = set()

    # Match $SYMBOL (e.g. $TSLA)
    dollar_tickers = re.findall(r'\$(\b[A-Z]{1,6}\b)', text)
    symbols.update(dollar_tickers)

    # Match pair trades like GOOG/CMBT
    pair_tickers = re.findall(r'\b([A-Z]{2,6})/([A-Z]{2,6})\b', text)
    for left, right in pair_tickers:
        symbols.add(left)
        symbols.add(right)

    # Match bare UPPERCASE tickers (2–6 letters), excluding stopwords
    common_stopwords = {
        "THE", "AND", "FOR", "WITH", "FROM", "THIS", "HAVE", "THAT", "HERE",
        "LOOKS", "COULD", "SHOULD", "BREAK", "THEN", "WERE", "ANY"
    }
    bare_tickers = re.findall(r'\b([A-Z]{2,6})\b', text)
    for ticker in bare_tickers:
        if ticker not in common_stopwords and not ticker.startswith("HTTP"):
            symbols.add(ticker)

    # Match symbols with suffixes (e.g. INOV LN)
    suffix_tickers = re.findall(r'\b([A-Z]{2,6} [A-Z]{2,4})\b', text)
    symbols.update(suffix_tickers)

    return list(symbols)
