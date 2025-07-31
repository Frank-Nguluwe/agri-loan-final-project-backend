from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.utils.dependencies import get_current_user
from app.models.db_models import User, FarmerProfile
from app.schemas.user_schemas import UserProfileUpdate
from app.schemas.base_response_schema import BaseResponse

router = APIRouter(prefix="/users", tags=["Users"])

@router.put("/update-profile", status_code=status.HTTP_200_OK, response_model=BaseResponse)
def update_user_profile(
    update_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Update User fields
        if update_data.first_name:
            user.first_name = update_data.first_name
        if update_data.last_name:
            user.last_name = update_data.last_name
        if update_data.phone_number:
            user.phone_number = update_data.phone_number
        if update_data.email:
            user.email = update_data.email

        # Update FarmerProfile if it exists
        if update_data.farmer_profile:
            if not user.farmer_profile:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Farmer profile not found")

            farmer: FarmerProfile = user.farmer_profile
            data = update_data.farmer_profile
            if data.national_id:
                farmer.national_id = data.national_id
            if data.address:
                farmer.address = data.address
            if data.farm_location_gps:
                farmer.farm_location_gps = data.farm_location_gps
            if data.farm_size_hectares is not None:
                farmer.farm_size_hectares = data.farm_size_hectares
            if data.date_of_birth:
                farmer.date_of_birth = data.date_of_birth
            if data.district_id:
                farmer.district_id = data.district_id


        db.commit()
        return BaseResponse(message="Profile updated successfully", status_code=status.HTTP_200_OK)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


