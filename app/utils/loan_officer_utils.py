# Helper functions
from typing import List, Optional
from app.models.db_models import District, User, UserRole
from sqlalchemy.orm import Session


def check_loan_officer_permissions(current_user: User, district_id: Optional[str] = None) -> bool:
    """Check if user has loan officer permissions and district access"""
    if current_user.role not in [UserRole.LOAN_OFFICER, UserRole.SUPERVISOR, UserRole.ADMIN]:
        return False
    
    # Admins can access all districts
    if current_user.role == UserRole.ADMIN:
        return True
    
    # Loan officers and supervisors are limited to their assigned districts
    if district_id and current_user.district_id and str(current_user.district_id) != district_id:
        return False
    
    return True

def get_accessible_districts(current_user: User, db: Session) -> List[str]:
    """Get list of district IDs the user can access"""
    if current_user.role in [UserRole.LOAN_OFFICER, UserRole.SUPERVISOR, UserRole.ADMIN]:
        # Admins can access all districts
        districts = db.query(District).all()
        return [str(d.id) for d in districts]
    
    elif current_user.role == UserRole.SUPERVISOR:
        # Supervisors can access their district and districts of their loan officers
        accessible_districts = set()
        if current_user.district_id:
            accessible_districts.add(str(current_user.district_id))
        
        # Add districts of managed loan officers
        for loan_officer in current_user.managed_loan_officers:
            if loan_officer.district_id:
                accessible_districts.add(str(loan_officer.district_id))
        
        return list(accessible_districts)
    
    elif current_user.role == UserRole.LOAN_OFFICER:
        # Loan officers can only access their assigned district
        if current_user.district_id:
            return [str(current_user.district_id)]
        return []
    
    return []
