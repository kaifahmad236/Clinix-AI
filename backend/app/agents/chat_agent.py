from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.llm_config import get_llm

SYSTEM_PROMPT = """You are ClinixAI's Health Chat Assistant.

Rules:
- Answer general health questions clearly and simply.
- You are NOT a doctor. Never give a definitive diagnosis or prescribe medication/dosages.
- For anything serious, urgent, or ambiguous, advise the user to consult a licensed
  medical professional, and encourage emergency care for red-flag symptoms
  (e.g. chest pain, difficulty breathing, severe bleeding, stroke symptoms).
- Keep answers concise, empathetic, and easy to understand for a non-medical person.
- If the user references a previously uploaded report, use the provided context.
"""


def run_chat_agent(user_message: str, history: list[dict], report_context: str | None = None) -> str:
    """
    history: list of {"role": "user"|"assistant", "content": str}, oldest first.
    """
    llm = get_llm()

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    if report_context:
        messages.append(
            SystemMessage(
                content=f"Relevant context from the user's uploaded medical report:\n{report_context}"
            )
        )

    for turn in history[-10:]:  # keep last 10 turns for a lean context window
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))

    messages.append(HumanMessage(content=user_message))

    response = llm.invoke(messages)
    return response.content
