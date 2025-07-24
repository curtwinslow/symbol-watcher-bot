# summarizer.py

def summarize_messages(symbol, messages):
    if not messages:
        return f"No recent messages for {symbol}."
    
    joined = "\\n".join(msg["text"] for msg in messages[:5])
    
    # In production, you’d send this to OpenAI GPT-4 or Claude
    return f"Recent chatter about *{symbol}*:\\n\\n{joined}"
