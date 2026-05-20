#Tool 3: get_hcp_profile-Retrieves full HCP context for the agent ,  conversation with HCP-specific history and metadata.
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hcp import HCP
from app.models.interaction import Interaction


async def get_hcp_profile(db: AsyncSession, hcp_id: str) -> dict:

    hcp_uuid = uuid.UUID(hcp_id)

    #fetch HCP
    hcp_result = await db.execute(select(HCP).where(HCP.id == hcp_uuid))
    hcp = hcp_result.scalar_one_or_none()

    if hcp is None:
        return {"error": f"HCP {hcp_id} not found."}

    # aggregate interaction stats
    stats_result = await db.execute(
        select(
            func.count(Interaction.id).label("total_interactions"),
            func.max(Interaction.occurred_at).label("last_interaction_date"),
        ).where(Interaction.hcp_id == hcp_uuid)
    )
    stats = stats_result.one()

    return {
        "hcp_id": str(hcp.id),
        "full_name": hcp.full_name,
        "specialty": hcp.specialty,
        "institution": hcp.institution,
        "territory": hcp.territory,
        "npi_number": hcp.npi_number,
        "total_interactions": stats.total_interactions or 0,
        "last_interaction_date": (
            stats.last_interaction_date.isoformat() if stats.last_interaction_date else None
        ),
        "notes": hcp.notes,
    }