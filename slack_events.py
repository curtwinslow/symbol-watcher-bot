from flask import Blueprint, request, make_response
from slack_sdk.signature import SignatureVerifier
import os
from symbol_extractor import extract_symbols_from_text as extract_symbols

slack_events_bp = Blueprint("slack_events", __name__)
signature_verifier = SignatureVerifier(os.environ["SLACK_SIGNING_SECRET"])

@slack_events_bp.route("/slack/events", methods=["POST"])
def slack_events():
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("Invalid request signature", 403)

    event_data = request.json

    # Respond to Slack URL verification challenge
    if "challenge" in event_data:
        return make_response(event_data["challenge"], 200, {"content_type": "application/json"})

    # Process message events
    if "event" in event_data:
        event = event_data["event"]
        if event.get("type") == "message" and "subtype" not in event:
            text = event.get("text", "")
            user = event.get("user")
            channel = event.get("channel")

            symbols = extract_symbols(text)
            print(f"User {user} in channel {channel} mentioned symbols: {symbols}")

    return make_response("", 200)
