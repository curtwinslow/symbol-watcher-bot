import os
from flask import Blueprint, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from symbol_extractor import extract_symbols
from gpt_summarizer import summarize_mentions

slack_events_bp = Blueprint("slack_events", __name__)
client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

seen_messages = set()
bot_user_id = None

@slack_events_bp.before_app_first_request
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
    data = request.get_json()

    if data.get("type") == "url_verification":
        return jsonify({"challenge": data["challenge"]})

    if data.get("type") == "event_callback":
        event = data.get("event", {})

        if event.get("type") == "message" and "subtype" not in event:
            user = event.get("user")
            text = event.get("text")
            channel = event.get("channel")
            ts = event.get("ts")

            if user == bot_user_id:
                print("Skipping message from bot to prevent loop.")
                return "", 200

            message_key = f"{channel}-{ts}"
            if message_key in seen_messages:
                print(f"Skipping already processed message {message_key}")
                return "", 200

            seen_messages.add(message_key)

            symbols = extract_symbols(text)
            if symbols:
                try:
                    blocks = [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f":information_source: *Symbol(s) detected:* `{', '.join(symbols)}`"
                            }
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "Summarize"},
                                    "value": ",".join(symbols),
                                    "action_id": "summarize_symbols"
                                }
                            ]
                        }
                    ]

                    client.chat_postMessage(
                        channel=channel,
                        thread_ts=ts,
                        text=f"Symbol(s) detected: {', '.join(symbols)}",
                        blocks=blocks
                    )
                except SlackApiError as e:
                    print(f"Error posting message: {e.response['error']}")

    return "", 200

