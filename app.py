# app.py

from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
import os
from dotenv import load_dotenv

from symbol_parser import extract_symbols
from summarizer import summarize_messages
from db import store_message, get_messages_by_symbol

# Load environment variables from .env
load_dotenv()

# Initialize Slack app
app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"]
)

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@app.event("message")
def handle_message_events(body, say, logger):
    event = body.get("event", {})
    text = event.get("text", "")
    channel = event.get("channel")
    user = event.get("user")
    ts = event.get("ts")

    symbols = extract_symbols(text)
    if not symbols:
        return

    store_message(text, user, channel, ts, symbols)

    for sym in symbols:
        say(
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Detected *{sym}*"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "See Mentions"},
                        "value": sym,
                        "action_id": "see_mentions"
                    }
                }
            ],
            thread_ts=ts
        )

@app.action("see_mentions")
def handle_mentions_click(ack, body, say):
    ack()
    sym = body["actions"][0]["value"]
    messages = get_messages_by_symbol(sym)
    summary = summarize_messages(sym, messages)
    say(f"*{sym} summary:*\n{summary}")

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

if __name__ == "__main__":
    flask_app.run(port=3000)
