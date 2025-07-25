import os
import json
import time
from collections import defaultdict, deque
from flask import Blueprint, request, make_response
from slack_sdk.web import WebClient
from slack_sdk.signature import SignatureVerifier
from slack_sdk.models.blocks import SectionBlock, ActionsBlock, ButtonElement
from symbol_extractor import extract_symbols
from gpt_summarizer import summarize_mentions

slack_events_bp = Blueprint("slack_events", __name__)
slack_token = os.environ["SLACK_BOT_TOKEN"]
client = WebClient(token=slack_token)
verifier = SignatureVerifier(signing_secret=os.environ["SLACK_SIGNING_SECRET"])

# Store recent messages per symbol (max 25 each)
symbol_messages = defaultdict(lambda: deque(maxlen=25))

@slack_events_bp.route("/slack/events", methods=["POST"])
def slack_events():
    if not verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("Invalid signature", 403)

    data = request.json

    # Respond to Slack URL verification challenge
    if data.get("type") == "url_verification":
        return make_response(data.get("challenge"), 200, {"content_type": "application/json"})

    # Handle message events
    if data.get("type") == "event_callback":
        event = data.get("event", {})
        if event.get("type") == "message" and "subtype" not in event:
            handle_message_event(event)

    return make_response("", 200)

def handle_message_event(event):
    text = event.get("text", "")
    channel = event.get("channel")
    user = event.get("user")
    ts = event.get("ts")

    symbols = extract_symbols(text)
    if not symbols:
        return

    for symbol in symbols:
        symbol_messages[symbol].append({
            "user": user,
            "text": text,
            "ts": ts,
            "channel": channel,
        })

    # Post a message with a button to summarize
    try:
        blocks = [
            SectionBlock(text=f":information_source: Symbol(s) detected: {', '.join(symbols)}").to_dict(),
            ActionsBlock(elements=[
                ButtonElement(text="Summarize", action_id="summarize_mentions", value=",".join(symbols)).to_dict()
            ]).to_dict()
        ]
        client.chat_postMessage(channel=channel, thread_ts=ts, blocks=blocks)
    except Exception as e:
        print(f"Error posting summary button: {e}")

@slack_events_bp.route("/slack/interactions", methods=["POST"])
def slack_interactions():
    if not verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("Invalid signature", 403)

    payload = json.loads(request.form["payload"])
    if payload["type"] == "block_actions":
        action = payload["actions"][0]
        if action["action_id"] == "summarize_mentions":
            symbols = action["value"].split(",")
            channel = payload["channel"]["id"]
            thread_ts = payload["message"]["thread_ts"] or payload["message"]["ts"]

            all_messages = []
            for sym in symbols:
                all_messages.extend(symbol_messages[sym])

            # Deduplicate messages by ts
            all_messages = {m["ts"]: m for m in all_messages}.values()

            summary = summarize_mentions(all_messages, symbols)

            try:
                client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=f":memo: *Summary for {', '.join(symbols)}:*\n{summary}")
            except Exception as e:
                print(f"Error posting summary: {e}")

    return make_response("", 200)
