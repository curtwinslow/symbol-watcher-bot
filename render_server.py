from flask import Flask
from slack_events import slack_events_bp, fetch_bot_user_id

# Initialize the Flask app
app = Flask(__name__)

# Register the Slack events blueprint
app.register_blueprint(slack_events_bp)

# Fetch bot user ID at startup
fetch_bot_user_id()

@app.route("/")
def index():
    return "Symbol Watcher is running"
