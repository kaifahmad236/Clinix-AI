"""
Orchestrator Agent (3rd agent), built with LangGraph.

For every incoming chat message it decides, via a small routing node:
  - "report_qa": the user seems to be asking about their uploaded report
                  -> pulls the latest report summary in as context, then
                     hands off to the Chat Agent with that context attached.
  - "general_chat": plain health question -> Chat Agent with no extra context.

This keeps the graph tiny (2 real nodes) but demonstrates the intended
pattern: Orchestrator decides routing, specialist agents do the actual work.
"""

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from app.agents.chat_agent import run_chat_agent

REPORT_KEYWORDS = [
    "report", "my results", "my labs", "my scan", "my test",
    "uploaded", "summary you gave", "the pdf", "my prescription",
]


class OrchestratorState(TypedDict):
    message: str
    history: list
    latest_report_summary: Optional[str]
    route: str
    reply: str
    agent_used: str


def route_node(state: OrchestratorState) -> OrchestratorState:
    text = state["message"].lower()
    if state.get("latest_report_summary") and any(k in text for k in REPORT_KEYWORDS):
        state["route"] = "report_qa"
    else:
        state["route"] = "general_chat"
    return state


def report_qa_node(state: OrchestratorState) -> OrchestratorState:
    reply = run_chat_agent(
        user_message=state["message"],
        history=state["history"],
        report_context=state.get("latest_report_summary"),
    )
    state["reply"] = reply
    state["agent_used"] = "chat_agent+report_context"
    return state


def general_chat_node(state: OrchestratorState) -> OrchestratorState:
    reply = run_chat_agent(
        user_message=state["message"],
        history=state["history"],
        report_context=None,
    )
    state["reply"] = reply
    state["agent_used"] = "chat_agent"
    return state


def _build_graph():
    graph = StateGraph(OrchestratorState)
    graph.add_node("router", route_node)
    graph.add_node("report_qa", report_qa_node)
    graph.add_node("general_chat", general_chat_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        lambda s: s["route"],
        {"report_qa": "report_qa", "general_chat": "general_chat"},
    )
    graph.add_edge("report_qa", END)
    graph.add_edge("general_chat", END)
    return graph.compile()


_compiled_graph = _build_graph()


def run_orchestrator(message: str, history: list, latest_report_summary: Optional[str] = None) -> dict:
    result = _compiled_graph.invoke(
        {
            "message": message,
            "history": history,
            "latest_report_summary": latest_report_summary,
            "route": "",
            "reply": "",
            "agent_used": "",
        }
    )
    return {"reply": result["reply"], "agent_used": result["agent_used"]}
