import asyncio
from datetime import datetime
import logging
import os
from pathlib import Path
import time
from app.config.ml_deployment import ModelDeploymentConfig
import schedule
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.services.ml_model import ModelService
from app.utils.model_monitor import model_monitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = ModelDeploymentConfig()
model_service = ModelService()
class ModelDeploymentManager:
    """Manage model deployment lifecycle"""
    
    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        self.config = config
    
    def start_monitoring(self):
        """Start background monitoring tasks"""
        if not self.is_running:
            self.is_running = True
            
            # Schedule health checks
            schedule.every(config.HEALTH_CHECK_INTERVAL).seconds.do(
                self._scheduled_health_check
            )
            
            # Schedule model performance cleanup
            schedule.every().day.at("02:00").do(
                self._cleanup_old_predictions
            )
            
            # Start scheduler thread
            self.scheduler_thread = threading.Thread(target=self._run_scheduler)
            self.scheduler_thread.daemon = True
            self.scheduler_thread.start()
            
            logger.info("Model monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring tasks"""
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        logger.info("Model monitoring stopped")
    
    def _run_scheduler(self):
        """Run the scheduler in a separate thread"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(1)
    
    def _scheduled_health_check(self):
        """Scheduled health check task"""
        try:
            health_status = model_monitor.check_health()
            if health_status["status"] != "healthy":
                logger.warning(f"Health check warning: {health_status}")
        except Exception as e:
            logger.error(f"Error in scheduled health check: {str(e)}")
    
    def _cleanup_old_predictions(self):
        """Clean up old prediction records"""
        try:
            # This would connect to database and clean up old records
            # Implementation depends on your data retention policy
            logger.info("Prediction cleanup task executed")
        except Exception as e:
            logger.error(f"Error in prediction cleanup: {str(e)}")
    
    def deploy_new_model(self, model_path: str):
        """Deploy a new model version"""
        try:
            # Backup current model
            backup_path = f"{config.MODEL_BACKUP_PATH}/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
            
            # Create backup directory if it doesn't exist
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Copy current model to backup
            if os.path.exists(config.MODEL_PATH):
                import shutil
                shutil.copy2(config.MODEL_PATH, backup_path)
                logger.info(f"Current model backed up to {backup_path}")
      
            # Load new model
            model_service.reload_model(model_path)
            
            # Reset metrics for new model
            model_monitor.reset_metrics()
            
            logger.info(f"New model deployed successfully from {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deploying new model: {str(e)}")
            return False
    
    def rollback_model(self):
        """Rollback to previous model version"""
        try:
            backup_dir = Path(config.MODEL_BACKUP_PATH)
            if backup_dir.exists():
                # Get most recent backup
                backups = sorted(backup_dir.glob("backup_*.pkl"), key=lambda x: x.stat().st_mtime, reverse=True)
                
                if backups:
                    latest_backup = backups[0]
                    model_service.reload_model(str(latest_backup))
                    logger.info(f"Model rolled back to {latest_backup}")
                    return True
                else:
                    logger.error("No backup models found for rollback")
                    return False
            else:
                logger.error("Backup directory not found")
                return False
                
        except Exception as e:
            logger.error(f"Error rolling back model: {str(e)}")
            return False

# Initialize deployment manager
deployment_manager = ModelDeploymentManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    logger.info("Starting model deployment service...")
    deployment_manager.start_monitoring()
    
    yield
    
    # Shutdown
    logger.info("Shutting down model deployment service...")
    deployment_manager.stop_monitoring()