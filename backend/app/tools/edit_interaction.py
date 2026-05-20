#Tool 2: edit_interaction: Allows a sales rep to modify a previously logged interaction
import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interaction import Interaction, InteractionStatus, InteractionType
from app.tools.log_interaction import _enrich_with_llm  # reuse LLM helper
from app.rate_limit import check_llm_rate_limit 

async def edit_interaction(
    db: AsyncSession,
    interaction_id: str,
    hcp_specialty: str,
    rep_id: str,
    interaction_type: str | None = None,
    occurred_at: str | None = None,
    location: str | None = None,
    duration_minutes: int | None = None,
    raw_notes: str | None = None,
    products_discussed: list[str] | None = None,
    next_steps: str | None = None,
    status: str | None = None,) -> dict:
    
    #fetch  record
    result = await db.execute(
        select(Interaction).where(Interaction.id == uuid.UUID(interaction_id))
    )
    interaction = result.scalar_one_or_none()

    if interaction is None:
        return {"error": f"Interaction {interaction_id} not found."}

    #track whether notes changed 
    notes_changed = raw_notes is not None and raw_notes != interaction.raw_notes

    #only partial updates
    if interaction_type is not None:
        interaction.interaction_type = InteractionType(interaction_type)
    if occurred_at is not None:
        from datetime import datetime
        interaction.occurred_at = datetime.fromisoformat(occurred_at)
    if location is not None:
        interaction.location = location
    if duration_minutes is not None:
        interaction.duration_minutes = duration_minutes
    if raw_notes is not None:
        interaction.raw_notes = raw_notes
    if products_discussed is not None:
        interaction.products_discussed = products_discussed
    if next_steps is not None:
        interaction.next_steps = next_steps
    if status is not None:
        interaction.status = InteractionStatus(status)

    #re-enrich if notes changed
    if notes_changed and interaction.raw_notes:
        check_llm_rate_limit(rep_id, "edit_interaction")
        try:
            enriched = await _enrich_with_llm(
                interaction.raw_notes,
                hcp_specialty,
                interaction.interaction_type.value,
            )
            interaction.ai_summary = enriched.get("summary", interaction.ai_summary)
            interaction.sentiment = enriched.get("sentiment", interaction.sentiment)
            interaction.key_topics = enriched.get("key_topics", interaction.key_topics)

            # preserve rep-provided products if they exist
            if not interaction.products_discussed:
                interaction.products_discussed = enriched.get("products_discussed")
            if not interaction.next_steps:
                interaction.next_steps = enriched.get("suggested_next_steps")
        except (json.JSONDecodeError, Exception):
            pass  # Keep existing AI fields on failure

    await db.flush()
    await db.refresh(interaction)

    return {
        "interaction_id": str(interaction.id),
        "ai_summary": interaction.ai_summary,
        "products_discussed": interaction.products_discussed,
        "sentiment": interaction.sentiment,
        "key_topics": interaction.key_topics,
        "next_steps": interaction.next_steps,
        "status": interaction.status.value,
        "re_enriched": notes_changed,
    }