import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class InteractionType(str, enum.Enum):
    IN_PERSON = "in_person"
    PHONE = "phone"
    EMAIL = "email"
    VIRTUAL = "virtual"
    CONFERENCE = "conference"


class InteractionStatus(str, enum.Enum):
    DRAFT = "draft"
    COMPLETED = "completed"
    FLAGGED = "flagged"


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    hcp_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hcps.id", ondelete="CASCADE"), nullable=False)

    rep_id: Mapped[str] = mapped_column(String(100), nullable=False, comment="Sales rep identifier")

    # interaction fields
    interaction_type: Mapped[InteractionType] = mapped_column(
        Enum(InteractionType), nullable=False
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[str | None] = mapped_column(String(300))
    duration_minutes: Mapped[int | None] = mapped_column()

    # raw notes + AI-generated summary
    raw_notes: Mapped[str | None] = mapped_column(Text, comment="Rep's unstructured notes")
    ai_summary: Mapped[str | None] = mapped_column(Text, comment="LLM-generated concise summary")

    products_discussed: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), comment="Product names extracted by LLM")

    sentiment: Mapped[str | None] = mapped_column(String(20), comment="positive|neutral|negative")
    key_topics: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    next_steps: Mapped[str | None] = mapped_column(Text)

    status: Mapped[InteractionStatus] = mapped_column(
        Enum(InteractionStatus), default=InteractionStatus.COMPLETED)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    #relations
    hcp: Mapped["HCP"] = relationship(back_populates="interactions")  
    followUps: Mapped[list["FollowUp"]] = relationship( back_populates="interaction", cascade="all, delete-orphan", lazy="selectin")