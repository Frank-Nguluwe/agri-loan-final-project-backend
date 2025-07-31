from pydantic import BaseModel, UUID4
from typing import List, Optional

class DistrictBase(BaseModel):
    name: str
    code: str
    region: str

class DistrictCreate(DistrictBase):
    pass

class DistrictResponse(DistrictBase):
    id: UUID4

    class Config:
        from_attributes = True

class PaginatedDistrictResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: List[DistrictResponse]