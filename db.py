import csv
import os
from datetime import datetime

DB_FILE = "symbol_mentions.csv"

def log_symbol_mention(symbol: str, user: str, text: str, timestamp: str):
    file_exists = os.path.isfile(DB_FILE)
    with open(DB_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["timestamp", "symbol", "user", "text", "received_at"])
        writer.writerow([
            timestamp,
            symbol,
            user,
            text,
            datetime.utcnow().isoformat()
        ])
