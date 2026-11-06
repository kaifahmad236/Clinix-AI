from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.llm_config import get_llm

SYSTEM_PROMPT = """You are ClinixAI's Expert Health Assistant.

Role & Core Principles:
- Provide clear, empathetic, and medically informed explanations in accessible language.
- You are NOT a doctor: never give a definitive medical diagnosis, and never prescribe medications or specific drug dosages.
- Emergency Red Flags: If the user reports red-flag symptoms (severe chest pain, shortness of breath, sudden numbness, uncontrolled bleeding), immediately advise emergency medical attention.

Response Quality & Formatting:
- Use rich, clean Markdown formatting:
  * Bold key terms, test names, and numeric values with units (e.g., **Total Cholesterol: 240 mg/dL**, **High**).
  * Use organized bullet points or short comparisons when reviewing multiple test values.
  * When appropriate, structure responses into clear sections (e.g. **Summary**, **Clinical Context**, **Questions for Your Doctor**).
- Explain "the why": Translate complex medical jargon into plain English so patients understand what their lab values actually mean for their health.
- Empower the patient: Provide sensible lifestyle/dietary context and suggest relevant questions to discuss with their physician.

Grounding & Anti-Hallucination:
- When excerpts from the user's uploaded medical records/reports are provided in context, you MUST strictly ground your answers on that data.
- Cite the specific report name and page number when quoting test values or doctor notes (e.g. "[Report: blood_test.pdf, Page 1]").
- Do NOT invent, assume, or fabricate any numbers, reference ranges, findings, or dates that are not present in the provided excerpts.
- If the user asks about a test, condition, or result that is NOT mentioned in the provided excerpts, clearly inform them that their uploaded records do not contain that information.
"""


def run_chat_agent(
    user_message: str,
    history: list[dict],
    report_context: str | None = None,
    citations: list[dict] | None = None,
) -> str:
    """
    history: list of {"role": "user"|"assistant", "content": str}, oldest first.
    report_context: RAG-retrieved document excerpts or report summaries.
    citations: list of chunk citation dicts.
    """
    llm = get_llm()

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    if report_context:
        messages.append(
            SystemMessage(
                content=(
                    "The following verified excerpts were retrieved from the user's uploaded medical records. "
                    "Use them to answer the user's question accurately without hallucinating unmentioned values:\n\n"
                    f"{report_context}"
                )
            )
        )

    for turn in history[-10:]:  # keep last 10 turns for a lean context window
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))

    messages.append(HumanMessage(content=user_message))

    response = llm.invoke(messages)
    reply_text = response.content

    # If RAG citations exist and aren't explicitly listed in the reply, append a clean footer
    if citations and "Sources Cited" not in reply_text and "References" not in reply_text:
        unique_sources = []
        seen = set()
        for c in citations:
            cit_str = c.get("citation") or f"{c.get('filename')} (Page {c.get('page', 1)})"
            if cit_str not in seen:
                seen.add(cit_str)
                unique_sources.append(cit_str)

        if unique_sources:
            sources_footer = "\n\n---\n**Sources Cited:**\n" + "\n".join(
                f"- 📄 `{s}`" for s in unique_sources
            )
            reply_text += sources_footer

    return reply_text

