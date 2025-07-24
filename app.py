import os
from flask import Flask, request, jsonify
from summarizer import summarize_messages
from symbol_parser import extract_symbols
from db import log_symbol_mention

def create_app():
    app = Flask(__name__)

    @app.route('/')
    def health_check():
        return 'Symbol Watcher is alive!'

    @app.route('/slack/events', methods=['POST'])
    def slack_events():
        data = request.json

        # Slack URL verification challenge
        if data.get('type') == 'url_verification':
            return jsonify({'challenge': data.get('challenge')})

        # Process event
        event = data.get('event', {})
        if event.get('type') == 'message' and 'text' in event:
            text = event['text']
            user = event.get('user')
            channel = event.get('channel')
            ts = event.get('ts')

            symbols = extract_symbols(text)
            if symbols:
                log_symbol_mention(user, channel, ts, text, symbols)

        return jsonify({'status': 'ok'})

    @app.route('/summarize', methods=['POST'])
    def summarize():
        payload = request.get_json()
        messages = payload.get('messages', [])
        summary = summarize_messages(messages)
        return jsonify({'summary': summary})

    return app
