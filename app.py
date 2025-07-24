from flask import Flask, request, jsonify
from summarizer import summarize_messages
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

slack_token = os.environ.get("SLACK_BOT_TOKEN")
client = WebClient(token=slack_token)

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health_check():
    return "Symbol Watcher is live."

@app.route("/summarize", methods=["POST"])
def summarize():
    data = request.get_json()
    if not data or "channel_id" not in data:
        return jsonify({"error": "Missing channel_id"}), 400

    channel_id = data["channel_id"]

    try:
        messages = []
        response = client.conversations_history(channel=channel_id, limit=100)
        messages.extend(response["messages"])
        summary = summarize_messages(messages)
        return jsonify({"summary": summary})
    except SlackApiError as e:
        return jsonify({"error": str(e)}), 500
