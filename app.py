import os
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
from dotenv import load_dotenv
from symbol_parser import extract_symbols
from summarizer import summarize_messages
from db import store_message, get_messages_by_symbol

# Load environment variables from .env
load_dotenv()

# Initialize Slack app with bot token and signing secret
app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"]
)

handler = SlackRequestHandler(app)
flask_app = Flask(__name__)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

@app.event("app_mention")
def handle_mentions(body, say):
    event = body.get("event", {})
    user = event.get("user")
    text = event.get("text")
    channel = event.get("channel")
    ts = event.get("ts")

    symbols = extract_symbols(text)
    if symbols:
        store_message(user, text, symbols, ts, channel)
        say(f"Saved message with symbols: {', '.join(symbols)}")
    else:
        say("No valid symbols detected in your message.")

@app.command("/summary")
def handle_summary(ack, respond, command):
    ack()
    text = command.get("text", "").strip().upper()
    if not text:
        respond("Please provide a symbol. Example: `/summary AAPL`")
        return
    messages = get_messages_by_symbol(text)
    if not messages:
        respond(f"No messages found for {text}.")
        return
    summary = summarize_messages(messages)
    respond(f"*Summary for {text}:*\n{summary}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    flask_app.run(host="0.0.0.0", port=port)

