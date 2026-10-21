"""
Assembles the full NyayaMitra graph.

    START
      │
      ▼ (entry_router: resuming a follow-up, or a fresh query?)
      │
      ├── awaiting_user_reply=True ──► merge_followup_answer ──┐
      │                                                         │
      └── fresh query ──► scope_gate                            │
                              │                                  │
                    ┌── in scope ──┐   out of scope               │
                    │              ▼                              │
                    │           rejected ──► END                  │
                    ▼                                              │
              intent_agent  ◄─────────────────────────────────────┘
                    │
        ┌── needs follow-up (and < 2 rounds) ──► followup_agent ──► END
        │
        └── enough info ──► retrieval_agent ──► reasoning_agent ──► response_agent ──► END

We do NOT use LangGraph's built-in checkpointer — state persistence between
turns is handled explicitly in backend/db/models.py + api/routes/query.py.
See the note in graph/state.py for why.
"""
from langgraph.graph import StateGraph, START, END

from backend.graph.state import NyayaMitraState
from backend.agents.scope_gate import run_scope_gate, route_after_scope_gate
from backend.agents.intent_agent import run_intent_agent, route_after_intent
from backend.agents.followup_agent import run_followup_agent, run_merge_followup_answer
from backend.agents.followup_validator import run_followup_validator
from backend.agents.retrieval_agent import run_retrieval_agent
from backend.agents.reasoning_agent import run_reasoning_agent
from backend.agents.response_agent import run_response_agent


def _entry_router(state: NyayaMitraState) -> str:
    return "resume_followup" if state.get("awaiting_user_reply") else "fresh_query"


def _rejected_node(state: NyayaMitraState) -> NyayaMitraState:
    state["final_response"] = state.get("rejection_reason", "I can't help with that.")
    return state

def _reset_followup_node(state: NyayaMitraState) -> NyayaMitraState:
    """
    The user did NOT answer our previous follow-up question.
    Treat the latest message as a completely new legal query.
    """

    state["awaiting_user_reply"] = False
    state["followup_round"] = 0
    state["last_followup_question"] = ""
    state["collected_context"] = {}

    state["legal_domain"] = None
    state["user_intent"] = None
    state["jurisdiction"] = None

    state["needs_followup"] = False
    state["missing_info"] = []
    state["continue_followup"] = True

    return state

def _route_after_followup_validator(state: NyayaMitraState) -> str:
    if state.get("continue_followup"):
        return "merge"

    return "reset"

def build_graph():
    builder = StateGraph(NyayaMitraState)

    builder.add_node("merge_followup_answer", run_merge_followup_answer)
    builder.add_node("followup_validator", run_followup_validator)
    builder.add_node("reset_followup", _reset_followup_node)
    builder.add_node("scope_gate", run_scope_gate)
    builder.add_node("rejected", _rejected_node)
    builder.add_node("intent_agent", run_intent_agent)
    builder.add_node("followup_agent", run_followup_agent)
    builder.add_node("retrieval_agent", run_retrieval_agent)
    builder.add_node("reasoning_agent", run_reasoning_agent)
    builder.add_node("response_agent", run_response_agent)

    builder.add_conditional_edges(
        START,
        _entry_router,
        {
            "resume_followup": "followup_validator",
            "fresh_query": "scope_gate",
        },
    )

    # Validate whether the latest user message is actually answering our
    # previous follow-up question before deciding how to continue.
    builder.add_conditional_edges(
        "followup_validator",
        _route_after_followup_validator,
        {
            "merge": "merge_followup_answer",
            "reset": "reset_followup",
        },
    )

    builder.add_edge(
    "merge_followup_answer",
    "intent_agent",
)

    builder.add_edge(
        "reset_followup",
        "scope_gate",
    )

    builder.add_conditional_edges(
        "scope_gate",
        route_after_scope_gate,
        {"intent_agent": "intent_agent", "rejected": "rejected"},
    )
    builder.add_edge("rejected", END)

    builder.add_conditional_edges(
        "intent_agent",
        route_after_intent,
        {"followup_agent": "followup_agent", "retrieval_agent": "retrieval_agent"},
    )
    builder.add_edge("followup_agent", END)

    builder.add_edge("retrieval_agent", "reasoning_agent")
    builder.add_edge("reasoning_agent", "response_agent")
    builder.add_edge("response_agent", END)

    return builder.compile()


# Built once at import time and reused across requests.
graph = build_graph()
