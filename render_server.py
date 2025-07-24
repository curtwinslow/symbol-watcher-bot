from app import app  # This assumes your Flask app object is named `app` in app.py

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)  # Port can match Render’s default or be overridden
