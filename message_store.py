import time
from collections import defaultdict, deque

# Store recent messages per symbol
MAX_MESSAGES_PER_SYMBOL = 20
MESSAGE_TTL_SECONDS = 86400  # 24 hours

symbol_messages = defaultdict(lambda: deque(maxlen=MAX_MESSAGES_PER_SYMBOL))

def _current_time():
    return int(time.time())

def add_message(symbol: str, message_text: str, user: str, ts: str, channel: str):
    """Store a message mentioning a symbol."""
    symbol = symbol.upper().strip()
    symbol_messages[symbol].append({
        "text": message_text,
        "user": user,
        "ts": ts,
        "channel": channel,
        "timestamp": _current_time()
    })

def get_recent_messages(symbol: str):
    """Retrieve recent, unexpired messages for a symbol."""
    symbol = symbol.upper().strip()
    now = _current_time()
    recent = [
        msg for msg in symbol_messages[symbol]
        if now - msg["timestamp"] <= MESSAGE_TTL_SECONDS
    ]
    return recent
