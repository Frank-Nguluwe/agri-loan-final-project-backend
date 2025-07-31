from pydantic import BaseModel, Field


class LoanPredictionInput(BaseModel):
    """Input features matching exactly what the model expects"""
    loan_farm_size: float = Field(..., gt=0, description="Farm size in hectares")
    loan_crop: str = Field(..., description="Crop type name")
    past_yield_kgs: float = Field(..., description="Historical yield in kg")
    past_yield_mk: float = Field(..., description="Historical revenue in MWK")
    expected_yield_kgs: float = Field(..., gt=0, description="Expected yield in kg")
    expected_yield_mk: float = Field(..., gt=0, description="Expected revenue in MWK")