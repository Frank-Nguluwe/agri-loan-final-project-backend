from pydantic import BaseModel
from typing import Optional

class BaseResponse(BaseModel):
    message: str
    status_code: int
    data: Optional[dict] = None
    
class SuccessResponse(BaseResponse):
    success: bool = True
    
class ErrorResponse(BaseResponse):
    success: bool = False
    
class DataResponse(BaseResponse):
    data: dict
    