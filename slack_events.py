import os
from flask import Blueprint, request, make_response
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from slack_sdk.errors import SlackApiError
from symbol_extractor import extract_symbols
from message_store import add_message, get_recent_messages
from openai import OpenAI

slack_events_bp = Blueprint("slack_events", __name__)
client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
signature_verifier = SignatureVerifier(signing_secret=os.environ["SLACK_SIGNING_SECRET"])
openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def fetch_bot_user_id():
    auth_resp = client.auth_test()
    return auth_resp["user_id"]

@slack_events_bp.route("/slack/events", methods=["POST"])
def slack_events():
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("Invalid request", 403)

    payload = request.get_json()
    if "challenge" in payload:
        return make_response(payload["challenge"], 200, {"content_type": "application/json"})

    if payload.get("type") == "event_callback":
        event = payload.get("event", {})
        subtype = event.get("subtype")
        if subtype in ["bot_message", "message_changed", "message_deleted"]:
            return make_response("Ignored", 200)

        text = event.get("text", "")
        user = event.get("user")
        ts = event.get("ts")
        channel = event.get("channel")

        symbols = extract_symbols(text)
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
        return make_response("Invalid request", 403)

    payload = request.form.get("payload")
    if payload:
        data = json.loads(payload)
        if data.get("type") == "block_actions":
            action = data["actions"][0]
            if action["action_id"] == "summarize_symbol":
                value = action["value"]
                symbol, channel, thread_ts = value.split("|")

                messages = get_recent_messages(symbol)
                if not messages:
                    summary_text = f"No recent messages found for `{symbol}`."
                else:
                    combined_text = "\n".join([msg["text"] for msg in messages])
                    response = openai_client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "Summarize the following discussion related to a stock symbol."},
                            {"role": "user", "content": combined_text}
                        ],
                        max_tokens=300
                    )
                    summary_text = response.choices[0].message.content.strip()

                try:
                    client.chat_postMessage(
                        channel=channel,
                        thread_ts=thread_ts,
                        text=f":bookmark_tabs: Summary for `{symbol}`:\n{summary_text}"
                    )
                except SlackApiError as e:
                    print(f"Error posting summary: {e.response['error']}")

    return make_response("", 200)
