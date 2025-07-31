from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.db_models import Base, District
import uuid
from app.config.database import engine


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# District data
districts_data = [
    {"name": "Chitipa", "code": "CP", "region": "3"},
    {"name": "Karonga", "code": "KA", "region": "3"},
    {"name": "Rumphi", "code": "RU", "region": "3"},
    {"name": "Nkhatabay", "code": "NB", "region": "3"},
    {"name": "Likoma", "code": "LA", "region": "3"},
    {"name": "Mzimba", "code": "MZ", "region": "3"},
    {"name": "Kasungu", "code": "KU", "region": "2"},
    {"name": "Nkhotakota", "code": "KK", "region": "2"},
    {"name": "Ntchisi", "code": "NS", "region": "2"},
    {"name": "Dowa", "code": "DA", "region": "2"},
    {"name": "Salima", "code": "SA", "region": "2"},
    {"name": "Mchinji", "code": "MC", "region": "2"},
    {"name": "Lilongwe", "code": "LL", "region": "2"},
    {"name": "Dedza", "code": "DZ", "region": "2"},
    {"name": "Ntcheu", "code": "NU", "region": "2"},
    {"name": "Mangochi", "code": "MH", "region": "4"},
    {"name": "Balaka", "code": "BLK", "region": "4"},
    {"name": "Machinga", "code": "MHG", "region": "4"},
    {"name": "Zomba", "code": "ZA", "region": "1"},
    {"name": "Chiradzulu", "code": "CZ", "region": "1"},
    {"name": "Blantyre", "code": "BT", "region": "1"},
    {"name": "Mwanza", "code": "MN", "region": "1"},
    {"name": "Neno", "code": "NN", "region": "1"},
    {"name": "Thyolo", "code": "TO", "region": "1"},
    {"name": "Phalombe", "code": "PE", "region": "1"},
    {"name": "Mulanje", "code": "MJ", "region": "1"},
    {"name": "Chikwawa", "code": "CK", "region": "1"},
    {"name": "Nsanje", "code": "NE", "region": "1"},
]

# Region data (to map region numbers to names)
regions_data = {
    "1": {"name": "Southern", "code": "S"},
    "2": {"name": "Central", "code": "C"},
    "3": {"name": "Northern", "code": "N"},
    "4": {"name": "Eastern", "code": "E"},
    "5": {"name": "Western", "code": "W"},
}

def insert_districts():
    db = SessionLocal()
    try:
        # First, check if districts already exist to avoid duplicates
        existing_districts = db.query(District).count()
        if existing_districts > 0:
            print("Districts already exist in the database. Skipping insertion.")
            return
        
        # Insert districts
        for district_info in districts_data:
            # Map region number to region name
            region_number = district_info["region"]
            region_name = regions_data.get(region_number, {}).get("name", "Unknown")
            
            district = District(
                id=uuid.uuid4(),
                name=district_info["name"],
                code=district_info["code"],
                region=region_name
            )
            db.add(district)
        
        db.commit()
        print("Successfully inserted all districts.")
    except Exception as e:
        db.rollback()
        print(f"Error inserting districts: {e}")
    finally:
        db.close()

if __name__ == "__main__":
   
    # Insert the data
    insert_districts()