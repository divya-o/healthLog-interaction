from typing import Annotated, Any
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    Central state passed between LangGraph nodes.

    Fields:
        messages:        Full conversation history (user + assistant turns).
                         `add_messages` reducer appends rather than replaces.
        hcp_id:          UUID string of the HCP being discussed.
        rep_id:          Identifier of the field rep driving this session.
        session_id:      Optional session UUID for multi-turn continuity.
        tool_result:     Raw result returned by the last tool invocation.
        final_response:  The formatted string reply sent back to the client.
        action_taken:    Name of the tool the agent chose, for the API envelope.
        interaction_id:  Set after a log/edit operation for downstream reference.
    """
    messages: Annotated[list[BaseMessage], add_messages]
    hcp_id: str
    rep_id: str
    session_id: str | None
    tool_result: Any | None
    final_response: str | None
    action_taken: str | None
    interaction_id: str | None