from flask import Flask, request, redirect, jsonify
import os
import requests

app = Flask(__name__)

SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")

@app.route("/slack/oauth/callback")
def oauth_callback():
    code = request.args.get("code")
    if not code:
        return "Missing code", 400

    token_url = "https://slack.com/api/oauth.v2.access"
    data = {
        "client_id": SLACK_CLIENT_ID,
        "client_secret": SLACK_CLIENT_SECRET,
        "code": code,
        "redirect_uri": "https://symbol-watcher.onrender.com/slack/oauth/callback"
    }

    response = requests.post(token_url, data=data)
    token_data = response.json()

    if not token_data.get("ok"):
        return jsonify(token_data), 400

    return "Slack app successfully authorized! ✅ You can now invite the bot to a channel."

