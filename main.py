from fastapi import FastAPI, APIRouter, status
from fastapi.responses import RedirectResponse
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.users import router as users_router
from app.api.admin import router as admin_router
from app.api.farmers import router as farmer_router
from app.api.supervisor import router as supervisor_router
from app.api.loan_officers import router as loan_officers_router
from app.api.ml_monitoring import router as monitoring_router
from app.api.prediction import router as prediction_router
from app.api.districts import router as districts_router

from app.middleware import add_cors_middleware


app = FastAPI(title="Agri Loan API", description="API for the Agri Loan application", version="1.0.0")
add_cors_middleware(app)
api_router = APIRouter(prefix="/api")
@app.get("/", include_in_schema=False, response_class=RedirectResponse, status_code=status.HTTP_302_FOUND)
def redirect_to_docs():
    return RedirectResponse(url="/docs")

api_router.include_router(auth_router)
api_router.include_router(monitoring_router)
api_router.include_router(prediction_router)
api_router.include_router(districts_router)
api_router.include_router(farmer_router)
api_router.include_router(loan_officers_router)
api_router.include_router(supervisor_router)
api_router.include_router(dashboard_router)
api_router.include_router(users_router)
api_router.include_router(admin_router)

app.include_router(api_router)  




