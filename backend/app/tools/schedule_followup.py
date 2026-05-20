# Tool 4: schedule_followup
# Creates a follow-up task linked to a specific interaction.
# The LLM in the agent graph may call this tool after logging an interaction
# if next_steps imply a date-bound action

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.followUp import FollowUp, FollowUpStatus


async def schedule_followup(
    db: AsyncSession,
    interaction_id: str,
    due_date: str,          
    task_description: str,
    assigned_to: str | None = None,) -> dict:
    
    parsed_date = date.fromisoformat(due_date)

    followUp = FollowUp(
        id=uuid.uuid4(),
        interaction_id=uuid.UUID(interaction_id),
        due_date=parsed_date,
        task_description=task_description,
        assigned_to=assigned_to,
        status=FollowUpStatus.PENDING,
    )
    db.add(followUp)
    await db.flush()

    return {
        "followUp_id": str(followUp.id),
        "interaction_id": interaction_id,
        "due_date": due_date,
        "task_description": task_description,
        "assigned_to": assigned_to,
        "status": followUp.status.value,
    }