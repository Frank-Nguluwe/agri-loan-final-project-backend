
# Helper functions
from typing import List

from sqlalchemy import and_
from app.models.db_models import District, User, UserRole
from sqlalchemy.orm import Session


def check_supervisor_permissions(current_user: User) -> bool:
    """Check if user has supervisor permissions"""
    return current_user.role in [UserRole.SUPERVISOR, UserRole.ADMIN]

def get_supervisor_districts(current_user: User, db: Session) -> List[str]:
    """Get districts accessible by supervisor"""
    if current_user.role == UserRole.ADMIN:
        # Admins can access all districts
        districts = db.query(District).all()
        return [str(d.id) for d in districts]
    
    elif current_user.role == UserRole.SUPERVISOR:
        accessible_districts = set()
        
        # Add supervisor's own district
        if current_user.district_id:
            accessible_districts.add(str(current_user.district_id))
        
        # Add districts of managed loan officers
        for loan_officer in current_user.managed_loan_officers:
            if loan_officer.district_id:
                accessible_districts.add(str(loan_officer.district_id))
        
        return list(accessible_districts)
    
    return []

def get_managed_loan_officers(current_user: User, db: Session) -> List[User]:
    """Get loan officers managed by supervisor"""
    if current_user.role == UserRole.ADMIN:
        # Admins can see all loan officers
        return db.query(User).filter(User.role == UserRole.LOAN_OFFICER).all()
    
    elif current_user.role == UserRole.SUPERVISOR:
        # Get directly managed loan officers
        managed_officers = list(current_user.managed_loan_officers)
        
        # Also include loan officers in supervisor's district
        if current_user.district_id:
            district_officers = db.query(User).filter(
                and_(
                    User.role == UserRole.LOAN_OFFICER,
                    User.district_id == current_user.district_id,
                    User.id.notin_([officer.id for officer in managed_officers])
                )
            ).all()
            managed_officers.extend(district_officers)
        
        return managed_officers
    
    return []