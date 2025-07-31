from datetime import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException
from app.config.database import get_db
from app.config.ml_deployment import ml_config as config
from app.models.db_models import User, UserRole
from app.services.ml_model import ModelService
from app.utils.dependencies import get_current_user
from app.utils.model_monitor import model_monitor
from sqlalchemy.orm import Session
from app.services.model_deployment import deployment_manager

model_service = ModelService()


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        health_status = model_monitor.check_health()
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")

@router.get("/metrics")
async def get_metrics(
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Get comprehensive metrics"""
    try:
        
        performance_metrics = model_monitor.get_performance_metrics()
        system_metrics = model_monitor.get_system_metrics()
        model_metrics = model_monitor.get_model_metrics(db)
        
        return {
            "timestamp": datetime.now(),
            "performance": performance_metrics,
            "system": system_metrics,
            "model": model_metrics,
            "config": {
                "model_version": config.MODEL_VERSION,
                "max_batch_size": config.MAX_BATCH_SIZE,
                "prediction_timeout": config.PREDICTION_TIMEOUT
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/deploy")
async def deploy_model(
    model_path: str,
    current_user: User = Depends(get_current_user)
):
    """Deploy new model version"""
    try:
        # Check permissions
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=403, 
                detail="Admin access required"
            )
        
        success = deployment_manager.deploy_new_model(model_path)
        
        if success:
            return {
                "message": "Model deployed successfully",
                "model_path": model_path,
                "deployed_by": current_user.id,
                "deployed_at": datetime.now()
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail="Failed to deploy model"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deploying model: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/rollback")
async def rollback_model(
    current_user: User = Depends(get_current_user)
):
    """Rollback to previous model version"""
    try:
        # Check permissions
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=403, 
                detail="Admin access required"
            )
        
        success = deployment_manager.rollback_model()
        
        if success:
            return {
                "message": "Model rolled back successfully",
                "rolled_back_by": current_user.id,
                "rolled_back_at": datetime.now()
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail="Failed to rollback model"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rolling back model: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/status")
async def get_deployment_status():
    """Get deployment status"""
    try:
        model_info = model_service.get_model_info()
        health_status = model_monitor.check_health()
        
        return {
            "deployment_status": "active" if model_info["model_loaded"] else "inactive",
            "model_info": model_info,
            "health_status": health_status["status"],
            "monitoring_active": deployment_manager.is_running
        }
        
    except Exception as e:
        logger.error(f"Error getting deployment status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")