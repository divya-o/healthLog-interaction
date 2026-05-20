# Tool 1: log_interaction-Captures raw interaction notes from the rep, then uses the Groq LLM to:
#    Generate a concise clinical summary
#    Extract product names mentioned
#    Detect sentiment (positive / neutral / negative)
#    Identify key topics discussed
#    Suggest next steps if not provided

import json
import uuid
from datetime import datetime

from langchain_core.tools import tool
from langchain_groq import ChatGroq
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.interaction import Interaction, InteractionType


#LLM client
_llm = ChatGroq(
    api_key=settings.groq_api_key,
    model=settings.groq_primary_model,  # gemma2-9b-it
    temperature=0.2,
    max_tokens=512,
)

_EXTRACTION_PROMPT = """
You are a life sciences CRM assistant. Analyze the following sales rep notes from a
Healthcare Professional (HCP) interaction and return ONLY a valid JSON object with
these exact keys:

{{
  "summary": "<2-3 sentence clinical summary of the interaction>",
  "products_discussed": ["<product name>", ...],
  "sentiment": "<positive|neutral|negative>",
  "key_topics": ["<topic>", ...],
  "suggested_next_steps": "<actionable follow-up for the rep or null>"
}}

Rep Notes:
{raw_notes}

HCP Specialty: {specialty}
Interaction Type: {interaction_type}
"""


async def _enrich_with_llm(
    raw_notes: str,
    specialty: str,
    interaction_type: str,) -> dict:

    #Call the Groq LLM to extract structured insights from raw notes
    prompt = _EXTRACTION_PROMPT.format(
        raw_notes=raw_notes,
        specialty=specialty,
        interaction_type=interaction_type,
    )
    response = await _llm.ainvoke(prompt)
    text = response.content.strip()

    #strip
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    
    return json.loads(text)


async def log_interaction(
    db: AsyncSession,
    hcp_id: str,
    rep_id: str,
    interaction_type: str,
    occurred_at: datetime,
    raw_notes: str,
    hcp_specialty: str,
    location: str | None = None,
    duration_minutes: int | None = None,
    products_discussed: list[str] | None = None,
    next_steps: str | None = None,) -> dict:
    
    #1-LLM enrichment
    enriched: dict = {}
    if raw_notes:
        try:
            enriched = await _enrich_with_llm(raw_notes, hcp_specialty, interaction_type)
        except (json.JSONDecodeError, Exception):
            #  degradation
            enriched = {}

    # 2-Merge data 
    final_products = products_discussed or enriched.get("products_discussed") or []
    final_next_steps = next_steps or enriched.get("suggested_next_steps")

    # 3- Persist to database
    interaction = Interaction(
        id=uuid.uuid4(),
        hcp_id=uuid.UUID(hcp_id),
        rep_id=rep_id,
        interaction_type=InteractionType(interaction_type),
        occurred_at=occurred_at,
        location=location,
        duration_minutes=duration_minutes,
        raw_notes=raw_notes,
        ai_summary=enriched.get("summary"),
        products_discussed=final_products if final_products else None,
        sentiment=enriched.get("sentiment"),
        key_topics=enriched.get("key_topics"),
        next_steps=final_next_steps,
    )
    db.add(interaction)
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
    }