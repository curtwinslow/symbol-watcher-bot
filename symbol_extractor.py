import re

# Matches: $TSLA, TSLA, TSLA.N, TSLA LN, GOGL/CMBT, etc.
SYMBOL_PATTERN = re.compile(r"""
    (?:\$)?                             # optional leading $
    (?<!\w)                             # negative lookbehind (start of word)
    (
        [A-Z]{1,5}                      # base symbol
        (?:[\s\.\/\-][A-Z]{1,4})?       # optional suffix or pair (e.g. LN, .N, /USD)
    )
    (?!\w)                              # negative lookahead (end of word)
""", re.VERBOSE)


def normalize_symbol(symbol: str) -> str:
    """Standardizes symbol formats."""
    symbol = symbol.strip().upper()

    # Fix spacing: 'INOV LN' → 'INOV.LN'
    if ' ' in symbol:
        parts = symbol.split()
        if len(parts) == 2:
            return f"{parts[0]}.{parts[1]}"
    if '/' in symbol:
        return symbol  # Allow pair trades like GOGL/CMBT
    return symbol


def extract_symbols(text: str):
    """Extract and normalize symbols from a Slack message string."""
    matches = SYMBOL_PATTERN.findall(text)
    symbols = {normalize_symbol(m) for m in matches}
    return list(symbols)
