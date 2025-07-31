from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
import uuid

from app.config.database import get_db
from app.models.db_models import District
from app.schemas.districts_schemas import DistrictResponse

router = APIRouter(prefix="/districts", tags=["Districts"])

@router.get("/", response_model=List[DistrictResponse])
def get_all_districts(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search by name or code")
):

    # Base query
    query = db.query(District)

    # Apply search
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                District.name.ilike(search_pattern),
                District.code.ilike(search_pattern)
            )
        )

    items = query.all()

    return items

@router.get("/{district_id}", response_model=DistrictResponse)
def get_district_by_id(district_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a single district by ID"""
    district = db.query(District).get(district_id)
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    return district