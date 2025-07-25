import os
from flask import Blueprint, request, make_response
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier
from message_store import add_message, get_recent_messages
from symbol_extractor import extract_symbols
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

slack_events_bp = Blueprint("slack_events", __name__)
client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
signature_verifier = SignatureVerifier(signing_secret=os.environ["SLACK_SIGNING_SECRET"])
openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Used during app startup
bot_user_id = None
def fetch_bot_user_id():
    global bot_user_id
    auth_response = client.auth_test()
    bot_user_id = auth_response["user_id"]
    print(f"Bot user ID: {bot_user_id}")

@slack_events_bp.route("/slack/events", methods=["POST"])
def slack_events():
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("Invalid signature", 403)

    payload = request.json
    if "type" in payload:
        if payload["type"] == "url_verification":
            return make_response(payload["challenge"], 200)

    if "event" in payload:
        event = payload["event"]
        if (
            event.get("type") == "message"
            and "subtype" not in event
            and event.get("user") != bot_user_id
        ):
            text = event.get("text", "")
            user = event.get("user")
            ts = event.get("ts")
            channel = event.get("channel")

            symbols = extract_symbols(text)
            print(f"User {user} in channel {channel} mentioned symbols: {symbols}")

            for symbol in symbols:
                add_message(symbol, text, user, ts, channel)

                try:
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
    if payload["type"] == "block_actions":
        action = payload["actions"][0]
        if action["action_id"] == "summarize_symbol":
            symbol, channel, thread_ts = action["value"].split("|")

            messages = get_recent_messages(symbol)
            summary = summarize_messages(messages)

            try:
                client.chat_postMessage(
                    channel=channel,
                    thread_ts=thread_ts,
                    text=f"*Summary for `{symbol}`:*\n{summary}"
                )
            except SlackApiError as e:
                print(f"Error posting summary: {e.response['error']}")

    return make_response("", 200)

def summarize_messages(messages):
    if not messages:
        return "No recent messages found."

    prompt = "Summarize the following messages mentioning a stock symbol:\n\n"
    for msg in messages:
        prompt += f"- {msg['user']} said: {msg['text']}\n"

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error during summarization: {e}")
        return "Error generating summary."

