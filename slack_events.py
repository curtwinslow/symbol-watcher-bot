import os
import re
from flask import Blueprint, request, make_response
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier
from symbol_extractor import extract_symbols
from gpt_summarizer import summarize_mentions
from message_store import add_message, get_recent_messages

slack_events_bp = Blueprint("slack_events", __name__)
client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
signature_verifier = SignatureVerifier(signing_secret=os.environ["SLACK_SIGNING_SECRET"])

bot_user_id = None  # Will be set at startup

def fetch_bot_user_id():
    global bot_user_id
    try:
        auth_test = client.auth_test()
        bot_user_id = auth_test["user_id"]
        print(f"Bot user ID: {bot_user_id}")
    except SlackApiError as e:
        print(f"Failed to fetch bot user ID: {e}")

@slack_events_bp.route("/slack/events", methods=["POST"])
def slack_events():
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("Invalid signature", 403)

    payload = request.json
    if "challenge" in payload:
        return make_response(payload["challenge"], 200, {"content_type": "application/json"})

    event = payload.get("event", {})
    if event.get("type") == "message" and not event.get("bot_id"):
        user = event.get("user")
        text = event.get("text", "")
        channel = event.get("channel")
        ts = event.get("ts")

        symbols = extract_symbols(text)
        if symbols:
            print(f"User {user} in channel {channel} mentioned symbols: {symbols}")
            add_message(symbols, text, user, ts, channel)

            try:
                for symbol in symbols:
                    client.chat_postMessage(
                        channel=channel,
                        thread_ts=ts,
                        text=f":mag: Click to summarize recent mentions of `{symbol}`",
                        blocks=[
                            {
                                "type": "section",
                                "text": {"type": "mrkdwn", "text": f":mag: Click to summarize recent mentions of `{symbol}`"},
                                "accessory": {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "Summarize"},
                                    "action_id": "summarize_symbol",
                                    "value": f"{symbol}|{channel}|{ts}"
                                }
                            }
                        ]
                    )
            except SlackApiError as e:
                print(f"Error posting message: {e.response['error']}")

    return make_response("", 200)

@slack_events_bp.route("/slack/interactions", methods=["POST"])
def slack_interactions():
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("Invalid signature", 403)

    from urllib.parse import parse_qs
    import json

    payload = json.loads(parse_qs(request.get_data(as_text=True))["payload"][0])
    action = payload["actions"][0]
    if action["action_id"] == "summarize_symbol":
        symbol, channel, message_ts = action["value"].split("|")
        messages = get_recent_messages(symbol)
        summary = summarize_mentions(symbol, messages)
        try:
            client.chat_postMessage(
                channel=channel,
                thread_ts=message_ts,
                text=f"Summary for `{symbol}`:\n{summary}"
            )
        except SlackApiError as e:
            print(f"Error posting summary: {e.response['error']}")

    return make_response("", 200)

