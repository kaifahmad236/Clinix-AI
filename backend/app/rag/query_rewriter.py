"""
Multi-turn conversational query condenser for ClinixAI.
Reformulates elliptical follow-up questions (e.g., 'What about my platelets?', 'Is that normal?')
into standalone search queries incorporating prior conversation context.
"""

from typing import List, Dict
import re


def condense_query_heuristically(query: str, history: List[Dict[str, str]]) -> str:
    """
    Fast rule-based query contextualizer for follow-up turns.
    Avoids latency and extra token costs on simple follow-ups.
    """
    q_lower = query.lower().strip()

    # If history is empty or query is already long and detailed, keep as is
    if not history or len(query.split()) > 8:
        return query

    # Pronouns and elliptical patterns that require conversational context
    follow_up_triggers = [
        "what about", "how about", "and my", "is that", "are those",
        "why is it", "what does that mean", "was it", "did it", "is this",
        "which doctor", "when was that", "can you explain that"
    ]

    is_follow_up = any(trigger in q_lower for trigger in follow_up_triggers)

    if not is_follow_up:
        return query

    # Find the most recent user or assistant message with medical context
    last_context = ""
    for msg in reversed(history[-4:]):
        content = msg.get("content", "")
        # Look for substantive words in prior turns
        words = [w for w in content.split() if len(w) > 3][:10]
        if words:
            last_context = " ".join(words)
            break

    if last_context:
        return f"{query} (context: {last_context})"

    return query

