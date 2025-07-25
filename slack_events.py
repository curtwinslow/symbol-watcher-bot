import os
import json
from flask import Blueprint, request, make_response
from symbol_extractor import extract_symbols

slack_events_bp = Blueprint("slack_events", __name__)

@slack_events_bp.route("/slack/events", methods=["POST"])
def slack_events():
    slack_event = request.get_json()

    # URL verification challenge
    if "type" in slack_event and slack_event["type"] == "url_verification":
        return make_response(slack_event["challenge"], 200, {"content_type": "text/plain"})

    # Event callback
    if "event" in slack_event:
        event = slack_event["event"]

        if event.get("type") == "message" and "text" in event:
            text = event["text"]
            symbols = extract_symbols(text)
            if symbols:
                print(f"🔍 Extracted symbols: {symbols}")

    return make_response("OK", 200)
