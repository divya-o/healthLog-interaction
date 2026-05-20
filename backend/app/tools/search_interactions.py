#Tool 5 - Search Interactions-Builds a dynamic query with optional filters, executes give a list of matching interaction summaries
from datetime import date

from sqlalchemy import and_, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interaction import Interaction, InteractionStatus, InteractionType


async def search_interactions(
    db: AsyncSession,
    hcp_id: str | None = None,
    rep_id: str | None = None,
    query_text: str | None = None,     
    sentiment: str | None = None,      
    interaction_type: str | None = None,
    from_date: str | None = None,      
    to_date: str | None = None,        
    limit: int = 10,) -> dict:
     dict with "results" list and "total" count
   
    limit = min(limit, 50)  # Safety cap
    conditions = []

    if hcp_id:
        import uuid
        conditions.append(Interaction.hcp_id == uuid.UUID(hcp_id))
    if rep_id:
        conditions.append(Interaction.rep_id == rep_id)
    if sentiment:
        conditions.append(Interaction.sentiment == sentiment)
    if interaction_type:
        conditions.append(Interaction.interaction_type == InteractionType(interaction_type))
    if from_date:
        conditions.append(Interaction.occurred_at >= date.fromisoformat(from_date))
    if to_date:
        conditions.append(Interaction.occurred_at <= date.fromisoformat(to_date))

    
    if query_text:
        
        fts_condition = text(
            "to_tsvector('english', COALESCE(raw_notes, '') || ' ' || COALESCE(ai_summary, '')) "
            "@@ plainto_tsquery('english', :query)"
        ).bindparams(query=query_text)
        conditions.append(fts_condition)

    stmt = (
        select(Interaction)
        .where(and_(*conditions) if conditions else text("true"))
        .order_by(Interaction.occurred_at.desc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    interactions = result.scalars().all()

    return {
        "total": len(interactions),
        "results": [
            {
                "interaction_id": str(i.id),
                "hcp_id": str(i.hcp_id),
                "interaction_type": i.interaction_type.value,
                "occurred_at": i.occurred_at.isoformat(),
                "ai_summary": i.ai_summary,
                "sentiment": i.sentiment,
                "products_discussed": i.products_discussed,
                "status": i.status.value,
            }
            for i in interactions
        ],
    }