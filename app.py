from flask import Flask, request
from symbol_parser import extract_symbols
from summarizer import summarize_mentions
from db import store_mention

def create_app():
    app = Flask(__name__)

    @app.route("/")
    def index():
        return "Symbol Watcher bot is alive!"

    @app.route("/slack/events", methods=["POST"])
    def handle_event():
        data = request.json

        # Basic verification
        if data.get("type") == "url_verification":
            return data.get("challenge")

        # Handle Slack event callback
        if "event" in data:
            event = data["event"]
            text = event.get("text", "")
            user = event.get("user", "")
            ts = event.get("ts", "")
            channel = event.get("channel", "")

            # Extract symbols
            symbols = extract_symbols(text)
            if symbols:
                summary = summarize_mentions(text, symbols)
                store_mention(symbols, text, user, ts, channel, summary)

        return "", 200

    return app
