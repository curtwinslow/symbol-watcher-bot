# db.py
import sqlite3
import os

DB_FILE = "symbol_watcher.db"

# Set up database on first run
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            text TEXT,
            user TEXT,
            channel TEXT,
            ts TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def store_message(text, user, channel, ts, symbols):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for symbol in symbols:
        c.execute('INSERT INTO messages (symbol, text, user, channel, ts) VALUES (?, ?, ?, ?, ?)',
                  (symbol, text, user, channel, ts))
    conn.commit()
    conn.close()

def get_messages_by_symbol(symbol):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT text FROM messages WHERE symbol = ? ORDER BY id DESC LIMIT 10', (symbol,))
    rows = c.fetchall()
    conn.close()
    return [{"text": row[0]} for row in rows]
