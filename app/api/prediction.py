# app/api/prediction.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.config.database import get_db
from app.models.db_models import LoanApplication, User, UserRole
from app.utils.dependencies import get_current_user

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predictions", tags=["predictions"])

# # @router.post("/predict", response_model=PredictionResponse)
# # async def predict_loan_amount(
# #     request: PredictionRequest,
# #     db: Session = Depends(get_db),
# #     current_user: User = Depends(get_current_user)
# # ):
# #     """
# #     Predict loan amount for a farmer application
# #     """
# #     try:
# #         # Check if user has permission to make predictions
# #         if current_user.role not in [UserRole.LOAN_OFFICER, UserRole.SUPERVISOR, UserRole.ADMIN]:
# #             raise HTTPException(
# #                 status_code=403, 
# #                 detail="Insufficient permissions to make predictions"
# #             )
        
# #         # Make prediction
# #         prediction = model_service.predict_loan_amount(request, db)
        
# #         logger.info(f"Prediction made for farmer {request.farmer_id} by user {current_user.id}")
# #         return prediction
        
# #     except HTTPException:
# #         raise
# #     except Exception as e:
# #         logger.error(f"Error in prediction endpoint: {str(e)}")
# #         raise HTTPException(status_code=500, detail="Internal server error")

# # @router.post("/predict-and-update/{application_id}")
# # async def predict_and_update_application(
# #     application_id: str,
# #     db: Session = Depends(get_db),
# #     current_user: User = Depends(get_current_user)
# # ):
# #     """
# #     Make prediction and update loan application with results
# #     """
# #     try:
        
# #         # Get application
# #         application = db.query(LoanApplication).filter(
# #             LoanApplication.id == application_id
# #         ).first()
        
# #         if not application:
# #             raise HTTPException(status_code=404, detail="Application not found")
        
# #         # Create prediction request from application data
# #         prediction_request = PredictionRequest(
# #             farmer_id=str(application.farmer_id),
# #             crop_type_id=str(application.crop_type_id),
# #             farm_size_hectares=float(application.farm_size_hectares),
# #             expected_yield_kg=float(application.expected_yield_kg),
# #             expected_revenue_mwk=float(application.expected_revenue_mwk),
# #             district_id=str(application.district_id)
# #         )
        
# #         # Make prediction
# #         prediction = model_service.predict_loan_amount(prediction_request, db)
        
# #         # Update application
# #         updated_application = model_service.update_loan_application_with_prediction(
# #             application_id, prediction, db
# #         )
        
# #         return {
# #             "message": "Application updated with prediction",
# #             "application_id": application_id,
# #             "prediction": prediction,
# #             "application_status": updated_application.status
# #         }
        
# #     except HTTPException:
# #         raise
# #     except Exception as e:
# #         logger.error(f"Error in predict-and-update endpoint: {str(e)}")
# #         raise HTTPException(status_code=500, detail="Internal server error")

# # @router.post("/batch-predict", response_model=List[PredictionResponse])
# # async def batch_predict(
# #     requests: List[PredictionRequest],
# #     db: Session = Depends(get_db),
# #     current_user: User = Depends(get_current_user)
# # ):
# #     """
# #     Make batch predictions for multiple applications
# #     """
# #     try:
# #         # Limit batch size
# #         if len(requests) > 100:
# #             raise HTTPException(
# #                 status_code=400, 
# #                 detail="Batch size too large. Maximum 100 predictions per request."
# #             )
        
# #         predictions = model_service.batch_predict(requests, db)
        
# #         logger.info(f"Batch prediction completed for {len(requests)} applications by user {current_user.id}")
# #         return predictions
        
#     # except HTTPException:
#     #     raise
#     # except Exception as e:
#     #     logger.error(f"Error in batch prediction endpoint: {str(e)}")
#     #     raise HTTPException(status_code=500, detail="Internal server error")

# @router.get("/pending-applications")
# async def get_pending_applications(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
#     limit: int = 50
# ):
#     """
#     Get applications that need predictions
#     """
#     try:        
#         # Get applications without predictions
#         applications = db.query(LoanApplication).filter(
#             LoanApplication.predicted_amount_mwk.is_(None),
#             LoanApplication.status.in_(["submitted", "under_review"])
#         ).limit(limit).all()
        
#         # Format response
#         pending_apps = []
#         for app in applications:
#             pending_apps.append({
#                 "application_id": str(app.id),
#                 "farmer_id": str(app.farmer_id),
#                 "crop_type_id": str(app.crop_type_id),
#                 "district_id": str(app.district_id),
#                 "farm_size_hectares": float(app.farm_size_hectares),
#                 "expected_yield_kg": float(app.expected_yield_kg),
#                 "expected_revenue_mwk": float(app.expected_revenue_mwk),
#                 "application_date": app.application_date,
#                 "status": app.status
#             })
        
#         return {
#             "total_pending": len(pending_apps),
#             "applications": pending_apps
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error getting pending applications: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.post("/process-pending-batch")
# async def process_pending_applications_batch(
#     background_tasks: BackgroundTasks,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
#     limit: int = 20
# ):
#     """
#     Process pending applications in batch (background task)
#     """
#     try:
        
#         # Add background task
#         background_tasks.add_task(
#             process_pending_applications_task, 
#             db, 
#             current_user.id, 
#             limit
#         )
        
#         return {
#             "message": f"Started processing up to {limit} pending applications in background",
#             "initiated_by": current_user.id
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error starting batch processing: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# async def process_pending_applications_task(db: Session, user_id: str, limit: int):
#     """
#     Background task to process pending applications
#     """
#     try:
#         # Get pending applications
#         applications = db.query(LoanApplication).filter(
#             LoanApplication.predicted_amount_mwk.is_(None),
#             LoanApplication.status.in_(["submitted", "under_review"])
#         ).limit(limit).all()
        
#         processed = 0
#         failed = 0
        
#         for app in applications:
#             try:
#                 # Create prediction request
#                 prediction_request = PredictionRequest(
#                     farmer_id=str(app.farmer_id),
#                     crop_type_id=str(app.crop_type_id),
#                     farm_size_hectares=float(app.farm_size_hectares),
#                     expected_yield_kg=float(app.expected_yield_kg),
#                     expected_revenue_mwk=float(app.expected_revenue_mwk),
#                     district_id=str(app.district_id)
#                 )
                
#                 # Make prediction
#                 prediction = model_service.predict_loan_amount(prediction_request, db)
                
#                 # Update application
#                 model_service.update_loan_application_with_prediction(
#                     str(app.id), prediction, db
#                 )
                
#                 processed += 1
                
#             except Exception as e:
#                 logger.error(f"Error processing application {app.id}: {str(e)}")
#                 failed += 1
#                 continue
        
#         logger.info(f"Batch processing completed. Processed: {processed}, Failed: {failed}")
        
#     except Exception as e:
#         logger.error(f"Error in background task: {str(e)}")

# @router.get("/model-info")
# async def get_model_info(
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Get information about the loaded model
#     """
#     try:
        
#         return model_service.get_model_info()
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error getting model info: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.post("/reload-model")
# async def reload_model(
#     model_path: str = None,
#     current_user: User = Depends(get_current_user)
# ):
#     try:
#         model_service.reload_model(model_path)
        
#         logger.info(f"Model reloaded by admin user {current_user.id}")
#         return {
#             "message": "Model reloaded successfully",
#             "model_info": model_service.get_model_info()
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error reloading model: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @router.get("/prediction-history/{farmer_id}")
# async def get_farmer_prediction_history(
#     farmer_id: str,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Get prediction history for a specific farmer
#     """
#     try:
        
#         # Get farmer's applications with predictions
#         applications = db.query(LoanApplication).filter(
#             LoanApplication.farmer_id == farmer_id,
#             LoanApplication.predicted_amount_mwk.isnot(None)
#         ).order_by(LoanApplication.prediction_date.desc()).all()
        
#         history = []
#         for app in applications:
#             history.append({
#                 "application_id": str(app.id),
#                 "predicted_amount_mwk": float(app.predicted_amount_mwk),
#                 "prediction_confidence": float(app.prediction_confidence) if app.prediction_confidence else None,
#                 "prediction_date": app.prediction_date,
#                 "approved_amount_mwk": float(app.approved_amount_mwk) if app.approved_amount_mwk else None,
#                 "status": app.status,
#                 "crop_type_id": str(app.crop_type_id)
#             })
        
#         return {
#             "farmer_id": farmer_id,
#             "total_predictions": len(history),
#             "history": history
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error getting prediction history: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")