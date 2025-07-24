from collections import defaultdict
from typing import List, Dict

def summarize_messages(messages: List[Dict[str, str]]) -> str:
    """
    Summarize a list of Slack messages mentioning a symbol.
    For now, this returns a simple concatenation grouped by user.
    """
    grouped = defaultdict(list)
    for msg in messages:
        user = msg.get("user", "unknown")
        text = msg.get("text", "")
        grouped[user].append(text)

    summary = []
    for user, lines in grouped.items():
        summary.append(f"*{user}* said:")
        for line in lines:
            summary.append(f"> {line}")
        summary.append("")

    return "\n".join(summary)
