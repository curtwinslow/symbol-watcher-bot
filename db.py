import csv
from datetime import datetime
import os

CSV_FILE = "symbol_mentions.csv"

def normalize(symbol):
    return symbol.upper().replace(" ", "_").strip()

def log_symbol_mention(symbol, channel, user, message):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    normalized = normalize(symbol)

    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["timestamp", "raw_symbol", "normalized_symbol", "channel", "user", "message"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "timestamp": timestamp,
            "raw_symbol": symbol,
            "normalized_symbol": normalized,
            "channel": channel,
            "user": user,
            "message": message
        })
