from flask import Flask
from slack_events import slack_events_bp  # 🔹 import the blueprint

app = Flask(__name__)
app.register_blueprint(slack_events_bp)  # 🔹 register the /slack/events route

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
