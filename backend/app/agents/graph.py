import json
from datetime import datetime
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from app.agents.state import AgentState
from app.config import settings

# Primary: gemma2-9b-it for tool routing (fast, efficient)
_router_llm = ChatGroq(
    api_key=settings.groq_api_key,
    model=settings.groq_primary_model,
    temperature=0.1,
    max_tokens=1024,
)

# Fallback / complex reasoning: llama-3.3-70b-versatile
_reasoning_llm = ChatGroq(
    api_key=settings.groq_api_key,
    model=settings.groq_fallback_model,
    temperature=0.3,
    max_tokens=1024,
)

_SYSTEM_PROMPT = """You are an AI assistant embedded in a life sciences CRM system,
helping field sales representatives log and manage interactions with Healthcare Professionals (HCPs).

You have access to the following tools:
- log_interaction: Log a new interaction with an HCP (use when the rep describes a meeting or call)
- edit_interaction: Modify an existing logged interaction (use when rep wants to correct/update)
- get_hcp_profile: Retrieve HCP details and history (use to answer questions about the HCP)
- schedule_followup: Create a follow-up task for a future action
- search_interactions: Search past interactions by keyword, date, sentiment, or product

Current context:
- HCP ID: {hcp_id}
- Rep ID: {rep_id}
- Date/Time: {current_datetime}

Guidelines:
1. Always confirm what you understood before calling log_interaction
2. Extract key clinical details: products, objections, commitments, sentiment
3. Suggest follow-up tasks when the rep mentions future actions
4. Be concise and professional — you're a tool, not a conversationalist
5. If the rep's message is ambiguous, ask ONE clarifying question

Respond with a JSON object: {{"tool": "<tool_name>", "args": {{...}}}} to call a tool,
or {{"tool": null, "reply": "<your message>"}} for a direct response.
"""


def _build_system_message(state: AgentState) -> SystemMessage:
    return SystemMessage(
        content=_SYSTEM_PROMPT.format(
            hcp_id=state["hcp_id"],
            rep_id=state["rep_id"],
            current_datetime=datetime.now().isoformat(),
        )
    )


#nodess

async def load_context_node(state: AgentState) -> dict:
    """
    Node: load_context
    Prepends the system prompt to the message list so the LLM always has
    full context, regardless of where in the conversation we are.
    """
    # conversation messages follow
    return {}  # State passed unchanged


async def llm_router_node(state: AgentState) -> dict:
   
    messages = [_build_system_message(state)] + state["messages"]

    response = await _router_llm.ainvoke(messages)
    content = response.content.strip()

   
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        # LLM returned plain text — treat as direct reply
        parsed = {"tool": None, "reply": content}

    return {
        "tool_result": parsed,
        "action_taken": parsed.get("tool"),
    }


def route_after_llm(state: AgentState) -> Literal["execute_tool", "format_response"]:
  
    tool_result = state.get("tool_result") or {}
    if tool_result.get("tool"):
        return "execute_tool"
    return "format_response"


async def execute_tool_node(state: AgentState) -> dict:
    """
    Node: execute_tool
    Dynamically dispatches to the appropriate tool function.
    The db session is injected via state (set by the route handler before
    invoking the graph).
    """
    from app.tools.edit_interaction import edit_interaction
    from app.tools.get_hcp_profile import get_hcp_profile
    from app.tools.log_interaction import log_interaction
    from app.tools.schedule_followup import schedule_followup
    from app.tools.search_interactions import search_interactions

    tool_map = {
        "log_interaction": log_interaction,
        "edit_interaction": edit_interaction,
        "get_hcp_profile": get_hcp_profile,
        "schedule_followup": schedule_followup,
        "search_interactions": search_interactions,
    }

    parsed = state["tool_result"]
    tool_name = parsed["tool"]
    args = parsed.get("args", {})

    tool_fn = tool_map.get(tool_name)
    if not tool_fn:
        return {"tool_result": {"error": f"Unknown tool: {tool_name}"}}

    db = state.get("_db")
    if db:
        args["db"] = db

    if "hcp_id" not in args:
        args.setdefault("hcp_id", state["hcp_id"])
    if "rep_id" not in args:
        args.setdefault("rep_id", state["rep_id"])

    result = await tool_fn(**args)

    updates = {"tool_result": result}
    if "interaction_id" in result:
        updates["interaction_id"] = result["interaction_id"]

    return updates


async def format_response_node(state: AgentState) -> dict:
    """
    Node: format_response
    Takes the tool result (or direct reply) and generates the final
    human-readable response using the LLM.
    """
    tool_result = state.get("tool_result") or {}
    action = state.get("action_taken")

    if action:
        #llm summarize
        summary_prompt = (
            f"The tool '{action}' was called and returned this result:\n"
            f"{json.dumps(tool_result, indent=2)}\n\n"
            "Write a brief, professional confirmation message for the sales rep. "
            "Mention key details (summary, next steps, follow-up) if present. "
            "Keep it under 3 sentences."
        )
        messages = [_build_system_message(state), HumanMessage(content=summary_prompt)]
        response = await _router_llm.ainvoke(messages)
        final_reply = response.content.strip()
    else:
        # Direct reply already generated by the router
        final_reply = tool_result.get("reply", "I'm not sure how to help with that.")

    return {"final_response": final_reply}


# graph assembly

def build_agent_graph() -> StateGraph:
    """
    Assembles and compiles the LangGraph state machine.
    Call once at startup; the compiled graph is thread-safe and reusable.
    """
    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("load_context", load_context_node)
    graph.add_node("llm_router", llm_router_node)
    graph.add_node("execute_tool", execute_tool_node)
    graph.add_node("format_response", format_response_node)

    # Edges
    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "llm_router")
    graph.add_conditional_edges(
        "llm_router",
        route_after_llm,
        {"execute_tool": "execute_tool", "format_response": "format_response"},
    )
    graph.add_edge("execute_tool", "format_response")
    graph.add_edge("format_response", END)

    return graph.compile()

agent_graph = build_agent_graph()