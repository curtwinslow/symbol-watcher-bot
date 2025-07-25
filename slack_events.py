from flask import Blueprint, request, jsonify
import os
import json
import logging
from symbol_extractor import extract_symbols_from_text as extract_symbols  # ✅ alias to expected name
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier

slack_events_bp = Blueprint("slack_events", __name__)
client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
signature_verifier = SignatureVerifier(os.environ["SLACK_SIGNING_SECRET"])

@slack_events_bp.route("/slack/events", methods=["POST"])
def slack_events():
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return "Invalid request signature", 403

    payload = request.get_json()
    if "challenge" in payload:
        return jsonify({"challenge": payload["challenge"]})

    event = payload.get("event", {})
    if event.get("type") == "message" and "text" in event:
        text = event["text"]
        symbols = extract_symbols(text)
        if symbols:
            thread_ts = event.get("ts")
            channel = event["channel"]
            message = f"👀 Mentioned symbols: {', '.join(symbols)}"
            client.chat_postMessage(channel=channel, text=message, thread_ts=thread_ts)

    return "", 200

