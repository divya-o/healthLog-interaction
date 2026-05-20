# CRUD endpoints for Healthcare Professionals.

# Endpoints:
#   POST   /api/hcps          - create a new HCP
#   GET    /api/hcps          - list HCPs (filter by specialty or territory)
#   GET    /api/hcps/{id}     - get single HCP
#   PATCH  /api/hcps/{id}     - update HCP fields

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.hcp import HCP
from app.schemas.hcp import HCPCreate, HCPOut

router = APIRouter()


# Helper 

async def _get_hcp_or_404(hcp_id: uuid.UUID, db: AsyncSession) -> HCP:
    hcp = await db.get(HCP, hcp_id)
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found.")
    return hcp


# Endpoints 

@router.post("", response_model=HCPOut, status_code=status.HTTP_201_CREATED)
async def create_hcp(
    body: HCPCreate,
    db: AsyncSession = Depends(get_db),) -> HCPOut:
    """Register a new HCP"""
    hcp = HCP(**body.model_dump())
    db.add(hcp)
    await db.flush()
    await db.refresh(hcp)
    return hcp


@router.get("", response_model=list[HCPOut])
async def list_hcps(
    specialty: str | None = Query(None),
    territory: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),) -> list[HCPOut]:
    #lisst HCPs
    stmt = select(HCP)
    if specialty:
        stmt = stmt.where(HCP.specialty.ilike(f"%{specialty}%"))
    if territory:
        stmt = stmt.where(HCP.territory == territory)
    stmt = stmt.order_by(HCP.last_name).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{hcp_id}", response_model=HCPOut)
async def get_hcp(
    hcp_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),) -> HCPOut:
    #Fetch a single HCP by UUID
    return await _get_hcp_or_404(hcp_id, db)


@router.patch("/{hcp_id}", response_model=HCPOut)
async def update_hcp(
    hcp_id: uuid.UUID,
    body: HCPCreate,
    db: AsyncSession = Depends(get_db),
) -> HCPOut:
    #update HCP fields
    hcp = await _get_hcp_or_404(hcp_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(hcp, field, value)
    await db.flush()
    await db.refresh(hcp)
    return hcp
