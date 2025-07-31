from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.db_models import CropType 
import uuid

def seed_crop_types(session: Session):
    crops = [
        ("Maize", "MAZ"),
        ("Soya", "SOY"),
        ("Groundnuts", "GRN"),
        ("Tobacco", "TOB"),
        ("Beans", "BNS"),
        ("Sweet Potato", "SWP"),
        ("Irish", "IRS"),
        ("Onion", "ONN")
    ]

    for name, code in crops:
        existing = session.query(CropType).filter_by(name=name).first()
        if not existing:
            crop = CropType(
                id=uuid.uuid4(),
                name=name,
                code=code,
                description=f"{name} crop"
            )
            session.add(crop)
    
    session.commit()
    print("Crop types seeded successfully.")
    
seed_crop_types(session=next(get_db()))
