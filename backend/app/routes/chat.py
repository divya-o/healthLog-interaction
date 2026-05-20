# Conversational interface endpoint - routes messages through the LangGraph agent
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from langchain_core.messages import HumanMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import agent_graph
from app.database import get_db
from app.models.interaction import Interaction
from app.rate_limit import check_llm_rate_limit 
from app.schemas.interaction import AgentResponse, ChatMessage, InteractionOut

router = APIRouter()


@router.post("/message", response_model=AgentResponse)
async def chat_message(
    body: ChatMessage,
    db: AsyncSession = Depends(get_db),) -> AgentResponse:
    
    check_llm_rate_limit(body.rep_id, "chat_message")
    # initial state for the LangGraph graph
    initial_state = {
        "messages": [HumanMessage(content=body.message)],
        "hcp_id": str(body.hcp_id),
        "rep_id": body.rep_id,
        "session_id": body.session_id or str(uuid.uuid4()),
        "tool_result": None,
        "final_response": None,
        "action_taken": None,
        "interaction_id": None,
        "_db": db,   
    }

    try:
        final_state = await agent_graph.ainvoke(initial_state)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Agent error: {str(exc)}",
        )

    #fetch the full record
    interaction_out = None
    if final_state.get("interaction_id"):
        result = await db.execute(
            select(Interaction).where(
                Interaction.id == uuid.UUID(final_state["interaction_id"])
            )
        )
        row = result.scalar_one_or_none()
        if row:
            interaction_out = InteractionOut.model_validate(row)

    return AgentResponse(
        reply=final_state.get("final_response") or "Done.",
        interaction=interaction_out,
        action_taken=final_state.get("action_taken"),
    )
