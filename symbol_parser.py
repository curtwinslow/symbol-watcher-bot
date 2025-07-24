import re

# Basic set of tickers for now — you’ll replace this later with live data
TICKER_WHITELIST = {
    "TSLA", "HOOK", "GOGL", "CMBT", "BPMC", "SRPT", "FL", "DKS", "VERV", "ABVX", "ZIMV", "PCHM"
}

# Stopwords to avoid false positives
STOPWORDS = {"AND", "CEO", "USD", "THE", "FOR", "YOU", "ARE", "WITH"}

def extract_symbols(text):
    symbols = set()

    # Match $TSLA style symbols
    for match in re.findall(r"\\$[A-Z]{1,6}", text):
        symbols.add(match[1:])

    # Match pair trades like GOGL/CMBT
    for match in re.findall(r"\\b([A-Z]{1,5})/([A-Z]{1,5})\\b", text):
        symbols.update(match)

    # Match all-caps potential symbols
    for match in re.findall(r"\\b[A-Z]{2,5}\\b", text):
        if match in TICKER_WHITELIST and match not in STOPWORDS:
            symbols.add(match)

    return list(symbols)
