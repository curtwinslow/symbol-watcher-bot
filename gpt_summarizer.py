import os
import openai

openai.api_key = os.environ["OPENAI_API_KEY"]

def summarize_mentions(messages, symbols):
    if not messages:
        return "No recent messages found for those symbols."

    sample = "\n".join(f"- <@{m['user']}>: {m['text']}" for m in sorted(messages, key=lambda x: x["ts"]))

    prompt = f"""You're a financial analyst bot. Summarize recent Slack conversations about the following symbols: {', '.join(symbols)}.

Messages:
{sample}

Summary:"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"Error generating summary: {e}"
