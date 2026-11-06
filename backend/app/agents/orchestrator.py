"""
Orchestrator Agent (3rd agent), built with LangGraph.

Routes incoming chat messages using Dual-Layer RAG:
  - Condenses multi-turn conversational follow-up queries.
  - Retrieves personal patient record excerpts (ChromaDB user collection).
  - Retrieves verified clinical reference guidelines (ChromaDB knowledge collection).
  - Routes to:
    * "report_rag": When personal records match the query.
    * "knowledge_chat": When general clinical questions match standard lab references.
    * "general_chat": When plain health conversational advice is needed.
"""

from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, END

from app.agents.chat_agent import run_chat_agent
from app.rag.vector_store import retrieve_relevant_chunks, format_rag_context
from app.rag.knowledge_base import retrieve_medical_knowledge
from app.rag.query_rewriter import condense_query_heuristically

REPORT_KEYWORDS = [
    "report", "my results", "my labs", "my scan", "my test",
    "uploaded", "summary you gave", "the pdf", "my prescription",
    "cholesterol", "platelet", "hba1c", "thyroid", "creatinine",
    "glucose", "blood count", "rbc", "wbc", "hemoglobin", "vitamin d",
    "lipid", "mri", "xray", "ultrasound", "biopsy", "ecg", "doctor noted",
]


class OrchestratorState(TypedDict):
    user_id: int
    message: str
    search_query: str
    history: list
    latest_report_summary: Optional[str]
    retrieved_chunks: List[Dict[str, Any]]
    clinical_guidelines: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    route: str
    reply: str
    agent_used: str


def route_node(state: OrchestratorState) -> OrchestratorState:
    user_id = state.get("user_id", 0)
    query = state.get("message", "")
    history = state.get("history", [])

    # 1. Condense conversational follow-up query if applicable
    search_query = condense_query_heuristically(query, history)
    state["search_query"] = search_query

    # 2. Retrieve from patient's private uploaded records
    patient_chunks: List[Dict[str, Any]] = []
    if user_id:
        try:
            patient_chunks = retrieve_relevant_chunks(user_id=user_id, query=search_query, top_k=4)
        except Exception:
            patient_chunks = []

    # 3. Retrieve from standard medical knowledge base
    kb_chunks: List[Dict[str, Any]] = []
    try:
        kb_chunks = retrieve_medical_knowledge(query=search_query, top_k=1)
    except Exception:
        kb_chunks = []

    state["clinical_guidelines"] = kb_chunks

    query_lower = query.lower()
    has_keyword = any(k in query_lower for k in REPORT_KEYWORDS)

    if patient_chunks:
        state["retrieved_chunks"] = patient_chunks
        citations = [
            {
                "filename": c.get("filename", "Report"),
                "page": c.get("page", 1),
                "citation": c.get("citation", ""),
                "score": c.get("score"),
            }
            for c in patient_chunks
        ]
        # Include clinical guidelines in citations if available
        for kb in kb_chunks:
            citations.append({
                "filename": "Clinical Guidelines",
                "page": None,
                "citation": kb.get("citation", "Clinical Guidelines"),
                "score": None,
            })
        state["citations"] = citations
        state["route"] = "report_rag"
    elif state.get("latest_report_summary") and has_keyword:
        state["retrieved_chunks"] = []
        state["citations"] = []
        state["route"] = "report_summary_qa"
    elif kb_chunks and has_keyword:
        state["retrieved_chunks"] = []
        state["citations"] = [
            {
                "filename": "Clinical Reference",
                "page": None,
                "citation": kb.get("citation", "Clinical Reference"),
                "score": None,
            }
            for kb in kb_chunks
        ]
        state["route"] = "knowledge_chat"
    else:
        state["retrieved_chunks"] = []
        state["citations"] = []
        state["route"] = "general_chat"

    return state


def report_rag_node(state: OrchestratorState) -> OrchestratorState:
    chunks = state.get("retrieved_chunks", [])
    rag_context = format_rag_context(chunks)

    # Attach verified clinical guidelines if retrieved
    kb_chunks = state.get("clinical_guidelines", [])
    if kb_chunks:
        kb_text = "\n\n".join(f"[{kb['citation']}]: {kb['text']}" for kb in kb_chunks)
        rag_context = f"{rag_context}\n\n--- Standard Clinical Reference Ranges ---\n{kb_text}"

    # If available, append latest summary overview
    if state.get("latest_report_summary"):
        rag_context = f"{rag_context}\n\n--- Latest Report High-Level Summary ---\n{state['latest_report_summary']}"

    reply = run_chat_agent(
        user_message=state["message"],
        history=state["history"],
        report_context=rag_context,
        citations=state.get("citations", []),
    )
    state["reply"] = reply
    state["agent_used"] = "chat_agent+rag"
    return state


def knowledge_chat_node(state: OrchestratorState) -> OrchestratorState:
    kb_chunks = state.get("clinical_guidelines", [])
    kb_text = "\n\n".join(f"[{kb['citation']}]: {kb['text']}" for kb in kb_chunks)
    context = f"Verified Medical Reference Guidelines:\n{kb_text}"

    reply = run_chat_agent(
        user_message=state["message"],
        history=state["history"],
        report_context=context,
        citations=state.get("citations", []),
    )
    state["reply"] = reply
    state["agent_used"] = "chat_agent+clinical_kb"
    return state


def report_summary_qa_node(state: OrchestratorState) -> OrchestratorState:
    reply = run_chat_agent(
        user_message=state["message"],
        history=state["history"],
        report_context=state.get("latest_report_summary"),
        citations=[],
    )
    state["reply"] = reply
    state["agent_used"] = "chat_agent+report_summary"
    return state


def general_chat_node(state: OrchestratorState) -> OrchestratorState:
    reply = run_chat_agent(
        user_message=state["message"],
        history=state["history"],
        report_context=None,
        citations=[],
    )
    state["reply"] = reply
    state["agent_used"] = "chat_agent"
    return state


def _build_graph():
    graph = StateGraph(OrchestratorState)
    graph.add_node("router", route_node)
    graph.add_node("report_rag", report_rag_node)
    graph.add_node("knowledge_chat", knowledge_chat_node)
    graph.add_node("report_summary_qa", report_summary_qa_node)
    graph.add_node("general_chat", general_chat_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        lambda s: s["route"],
        {
            "report_rag": "report_rag",
            "knowledge_chat": "knowledge_chat",
            "report_summary_qa": "report_summary_qa",
            "general_chat": "general_chat",
        },
    )
    graph.add_edge("report_rag", END)
    graph.add_edge("knowledge_chat", END)
    graph.add_edge("report_summary_qa", END)
    graph.add_edge("general_chat", END)
    return graph.compile()


_compiled_graph = _build_graph()


def run_orchestrator(
    message: str,
    history: list,
    user_id: int = 0,
    latest_report_summary: Optional[str] = None,
) -> dict:
    result = _compiled_graph.invoke(
        {
            "user_id": user_id,
            "message": message,
            "search_query": message,
            "history": history,
            "latest_report_summary": latest_report_summary,
            "retrieved_chunks": [],
            "clinical_guidelines": [],
            "citations": [],
            "route": "",
            "reply": "",
            "agent_used": "",
        }
    )
    return {
        "reply": result["reply"],
        "agent_used": result["agent_used"],
        "citations": result.get("citations", []),
    }
