#endpoints:
#   POST   /api/interactions           - log a new interaction
#   GET    /api/interactions          - list interactions 
#   GET    /api/interactions/{id}      - fetch single interaction
#   PATCH  /api/interactions/{id}      - partial update 
#   GET    /api/interactions/{id}/followups - list follow-ups for an interaction

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.hcp import HCP
from app.models.interaction import Interaction, InteractionStatus
from app.schemas.interaction import InteractionCreate, InteractionOut, InteractionUpdate
from app.tools.log_interaction import log_interaction
from app.tools.edit_interaction import edit_interaction

router = APIRouter()


#helpers 

async def _get_interaction_or_404(interaction_id: uuid.UUID, db: AsyncSession) -> Interaction:
    row = await db.get(Interaction, interaction_id)
    if not row:
        raise HTTPException(status_code=404, detail="Interaction not found.")
    return row


async def _get_hcp_specialty(hcp_id: uuid.UUID, db: AsyncSession) -> str:
    hcp = await db.get(HCP, hcp_id)
    return hcp.specialty if hcp else "Unknown"


#endpoints 

@router.post("", response_model=InteractionOut, status_code=status.HTTP_201_CREATED)
async def create_interaction(
    body: InteractionCreate,
    db: AsyncSession = Depends(get_db),) -> InteractionOut:
    
    specialty = await _get_hcp_specialty(body.hcp_id, db)

    result = await log_interaction(
        db=db,
        hcp_id=str(body.hcp_id),
        rep_id=body.rep_id,
        interaction_type=body.interaction_type.value,
        occurred_at=body.occurred_at,
        raw_notes=body.raw_notes or "",
        hcp_specialty=specialty,
        location=body.location,
        duration_minutes=body.duration_minutes,
        products_discussed=body.products_discussed,
        next_steps=body.next_steps,
    )

    return await _get_interaction_or_404(uuid.UUID(result["interaction_id"]), db)


@router.get("", response_model=list[InteractionOut])
async def list_interactions(
    rep_id: str | None = Query(None),
    hcp_id: uuid.UUID | None = Query(None),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[InteractionOut]:
    # List interactions with optional filters
    stmt = select(Interaction)

    if rep_id:
        stmt = stmt.where(Interaction.rep_id == rep_id)
    if hcp_id:
        stmt = stmt.where(Interaction.hcp_id == hcp_id)
    if from_date:
        stmt = stmt.where(Interaction.occurred_at >= from_date)
    if to_date:
        stmt = stmt.where(Interaction.occurred_at <= to_date)

    stmt = stmt.order_by(Interaction.occurred_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{interaction_id}", response_model=InteractionOut)
async def get_interaction(
    interaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),) -> InteractionOut:
    
    return await _get_interaction_or_404(interaction_id, db)


@router.patch("/{interaction_id}", response_model=InteractionOut)
async def update_interaction(
    interaction_id: uuid.UUID,
    body: InteractionUpdate,
    db: AsyncSession = Depends(get_db),) -> InteractionOut:
  
    #calls the edit_interaction tool - if raw_notes changed, the LLM
   
    existing = await _get_interaction_or_404(interaction_id, db)
    specialty = await _get_hcp_specialty(existing.hcp_id, db)

    #serialise enum/datetime values for the tool
    update_data = {
        k: (v.isoformat() if isinstance(v, datetime) else (v.value if hasattr(v, "value") else v))
        for k, v in body.model_dump(exclude_unset=True).items()
    }

    result = await edit_interaction(
        db=db,
        interaction_id=str(interaction_id),
        hcp_specialty=specialty,
        **update_data,
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return await _get_interaction_or_404(interaction_id, db)


@router.get("/{interaction_id}/followups")
async def get_followups(
    interaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),) -> list[dict]:
   
    interaction = await _get_interaction_or_404(interaction_id, db)
    return [
        {
            "id": str(fu.id),
            "due_date": fu.due_date.isoformat(),
            "task_description": fu.task_description,
            "assigned_to": fu.assigned_to,
            "status": fu.status.value,
        }
        for fu in interaction.followUps
    ]
