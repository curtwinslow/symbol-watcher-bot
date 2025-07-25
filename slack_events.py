import os
import json
from flask import Blueprint, request, make_response
from slack_sdk import WebClient
from slack_sdk.web import SlackResponse
from slack_sdk.signature import SignatureVerifier
from openai import OpenAI
from symbol_extractor import extract_symbols
from message_store import add_message, get_recent_messages_for_symbol
from summarize import summarize_symbol_messages

slack_events_bp = Blueprint("slack_events", __name__)

slack_token = os.environ["SLACK_BOT_TOKEN"]
signing_secret = os.environ["SLACK_SIGNING_SECRET"]
client = WebClient(token=slack_token)
verifier = SignatureVerifier(signing_secret=signing_secret)
openai_client = OpenAI()  # Fixed: removed api_key argument

BOT_USER_ID = None


@slack_events_bp.before_app_first_request
def fetch_bot_user_id():
    global BOT_USER_ID
    auth_response: SlackResponse = client.auth_test()
    BOT_USER_ID = auth_response["user_id"]
    print(f"Bot user ID: {BOT_USER_ID}")


@slack_events_bp.route("/slack/events", methods=["POST"])
def slack_events():
    if not verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("Invalid signature", 403)

    data = request.json
    if data.get("type") == "url_verification":
        return make_response(data.get("challenge"), 200, {"content_type": "text/plain"})

    if data.get("type") == "event_callback":
        event = data["event"]

        if event.get("type") == "message" and not event.get("bot_id"):
            text = event.get("text", "")
            user = event.get("user")
            ts = event.get("ts")
            channel = event.get("channel")

            symbols = extract_symbols(text)
            if symbols:
                print(f"User {user} in channel {channel} mentioned symbols: {symbols}")
                for symbol in symbols:
                    add_message(symbol, text, user, ts, channel)

                for symbol in symbols:
                    client.chat_postMessage(
                        channel=channel,
                        thread_ts=ts,
                        text=f":mag: Click below to summarize recent discussions about *{symbol.upper()}*.",
                        blocks=[
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f":mag: Click below to summarize recent discussions about *{symbol.upper()}*."
                                }
                            },
                            {
                                "type": "actions",
                                "elements": [
                                    {
                                        "type": "button",
                                        "text": {
                                            "type": "plain_text",
                                            "text": f"Summarize {symbol.upper()}",
                                        },
                                        "action_id": "summarize_symbol",
                                        "value": json.dumps({
                                            "symbol": symbol,
                                            "channel": channel,
                                            "thread_ts": ts
                                        }),
                                    }
                                ]
                            }
                        ]
                    )

    return make_response("", 200)


@slack_events_bp.route("/slack/interactions", methods=["POST"])
def slack_interactions():
    if not verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("Invalid signature", 403)

    payload = json.loads(request.form["payload"])
    if payload["type"] == "block_actions":
        action = payload["actions"][0]
        if action["action_id"] == "summarize_symbol":
            data = json.loads(action["value"])
            symbol = data["symbol"]
            channel = data["channel"]
            thread_ts = data["thread_ts"]

            messages = get_recent_messages_for_symbol(symbol)
            summary = summarize_symbol_messages(symbol, messages, openai_client)

            client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=f":memo: Summary for *{symbol.upper()}*:\n\n{summary}",
            )

    return make_response("", 200)

