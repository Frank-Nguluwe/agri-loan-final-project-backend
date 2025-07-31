# from fastapi import HTTPException, status
# from datetime import datetime
# from typing import Optional
# from uuid import UUID
# from pytz import timezone

# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession

# from app.models.db_models import User
# from app.schemas.user_schemas import UserCreate, UserUpdate, UserResponse, UserList
# from app.utils.password_utils import password_utils


# class UserUtils:
        
#     @staticmethod
#     async def get_user_by_email(email: str, db: AsyncSession):
#         query = select(User).filter(User.email == email)
#         result = await db.execute(query)
#         return result.scalar_one_or_none()
    
    
#     @staticmethod
#     async def get_user_by_phone_number(phone_number: str, db: AsyncSession):
#         query = select(User).filter(User.phone_number == phone_number)
#         result = await db.execute(query)
#         return result.scalar_one_or_none()
    
#     @staticmethod
#     async def get_user_by_id(user_id: str, db: AsyncSession):
#         query = select(User).filter(User.id == user_id)
#         result = await db.execute(query)
#         return result.scalar_one_or_none()
    
#     @staticmethod
#     async def get_user_by_email_or_phone_number(db: AsyncSession, email: Optional[str] = None, phone_number: Optional[str] = None):
#         if not email and not phone_number:
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either email or phone number must be provided")
#         if email and phone_number:
#             query = select(User).filter((User.email == email) | (User.phone_number == phone_number))
#         elif email:
#             query = select(User).filter(User.email == email)
#         else:
#             query = select(User).filter(User.phone_number == phone_number)
#         result = await db.execute(query)
#         return result.scalar_one_or_none()
        
#     @staticmethod
#     async def create_user(user: UserCreate, db: AsyncSession):
#         user_dict = user.model_dump()
#         user_dict["hashed_password"] = await password_utils.hash_password(user_dict["password"])
#         del user_dict["password"]
#         new_user = User(**user_dict)
#         db.add(new_user)
#         await db.commit()
#         return new_user
    
#     @staticmethod
#     async def get_all_users(db: AsyncSession):
#         query = select(User)    
#         result = await db.execute(query)
#         users = result.scalars().all()
#         return UserList(users=[UserResponse.model_validate(user) for user in users])
    
#     @staticmethod
#     async def get_user_by_id(user_id: UUID, db: AsyncSession):
#         query = select(User).filter(User.id == user_id)
#         result = await db.execute(query)
#         return result.scalar_one_or_none()
    
#     @staticmethod
#     async def update_user(user_id: UUID, user: UserUpdate, db: AsyncSession):
#         user_dict = user.model_dump()
#         user_dict["hashed_password"] = await password_utils.hash_password(user_dict["password"])
#         del user_dict["password"]
#         user_dict["id"] = user_id
#         user_dict["updated_at"] = datetime.now(timezone("Africa/Blantyre"))
#         query = select(User).filter(User.id == user_id)
#         result = await db.execute(query)
#         user = result.scalar_one_or_none()
#         if not user:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
#         for key, value in user_dict.items():
#             setattr(user, key, value)
#         await db.commit()
#         return user
    
#     @staticmethod
#     async def delete_user(user_id: UUID, db: AsyncSession):
#         query = select(User).filter(User.id == user_id)
#         result = await db.execute(query)
#         user = result.scalar_one_or_none()
#         if not user:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
#         await db.delete(user)
#         await db.commit()
#         return {"message": "User deleted successfully"}
    
# user_utils = UserUtils()