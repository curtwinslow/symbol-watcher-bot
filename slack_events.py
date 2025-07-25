import os
from flask import Blueprint, request, make_response
from slack_sdk.web import WebClient
from slack_sdk.signature import SignatureVerifier

from symbol_extractor import extract_symbols
from db import log_symbol_mention

slack_events_bp = Blueprint("slack_events", __name__)
slack_token = os.environ["SLACK_BOT_TOKEN"]
signing_secret = os.environ["SLACK_SIGNING_SECRET"]
client = WebClient(token=slack_token)
verifier = SignatureVerifier(signing_secret)

@slack_events_bp.route("/slack/events", methods=["POST"])
def slack_events():
    if not verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("Invalid signature", 403)

    data = request.json

    # Slack URL verification challenge
    if "type" in data and data["type"] == "url_verification":
        return make_response(data["challenge"], 200)

    # Handle message events
    if "event" in data:
        event = data["event"]
        if event.get("type") == "message" and not event.get("bot_id"):
            text = event.get("text", "")
            user = event.get("user", "")
            ts = event.get("ts", "")

            symbols = extract_symbols(text)
            for symbol in symbols:
                log_symbol_mention(symbol, user, text, ts)

    return make_response("OK", 200)
