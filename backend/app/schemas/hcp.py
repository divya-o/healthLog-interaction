import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class HCPCreate(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    specialty: str = Field(..., max_length=150)
    institution: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    territory: str | None = None
    npi_number: str | None = None
    notes: str | None = None


class HCPOut(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    full_name: str
    specialty: str
    institution: str | None
    email: str | None
    phone: str | None
    territory: str | None
    npi_number: str | None
    created_at: datetime

    model_config = {"from_attributes": True}