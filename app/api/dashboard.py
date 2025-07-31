from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.config.database import get_db
from app.models.db_models import CropType, FarmerProfile, User, YieldHistory
from app.utils.dependencies import get_current_user
from app.schemas.dashboard_schemas import CropTypeOut, DashboardUserInfo, YieldInfo, FarmerProfileInfo

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/crop-types", response_model=List[CropTypeOut])
def get_crop_types(db: Session = Depends(get_db)):
    return db.query(CropType).order_by(CropType.name).all()

@router.get("/me", response_model=DashboardUserInfo)
def get_dashboard_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Eager load related data
    user = db.query(User)\
        .options(
            joinedload(User.district_rel),
            joinedload(User.farmer_profile).joinedload(FarmerProfile.yield_history).joinedload(YieldHistory.crop_type_rel)
        ).filter(User.id == current_user.id).first()

    # Prepare yield history data
    yield_data = []
    if user.farmer_profile:
        for y in user.farmer_profile.yield_history:
            yield_data.append(YieldInfo(
                year=y.year,
                crop_type=y.crop_type_rel.name if y.crop_type_rel else "",
                yield_amount_kg=float(y.yield_amount_kg),
                revenue_mwk=float(y.revenue_mwk)
            ))

    # Compose response
    return DashboardUserInfo(
        id=user.id,
        email=user.email.lower(),
        first_name=user.first_name.title(),
        last_name=user.last_name.title(),
        role=user.role,
        district=user.district_rel.name if user.district_rel else None,
        farmer_profile=FarmerProfileInfo(
            national_id=user.farmer_profile.national_id,
            address=user.farmer_profile.address,
            farm_location_gps=user.farmer_profile.farm_location_gps,
            farm_size_hectares=float(user.farmer_profile.farm_size_hectares or 0),
            yield_history=yield_data
        ) if user.farmer_profile else None
    )
