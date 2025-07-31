import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.db_models import LoanApplication

logger = logging.getLogger(__name__)

class ModelMonitor:
    """Monitor model performance and system health"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.prediction_count = 0
        self.error_count = 0
        self.total_prediction_time = 0.0
        self.last_health_check = datetime.now()
    
    def record_prediction(self, prediction_time: float, success: bool = True):
        """Record a prediction attempt"""
        self.prediction_count += 1
        self.total_prediction_time += prediction_time
        
        if not success:
            self.error_count += 1
        
        logger.info(f"Prediction recorded: time={prediction_time:.2f}s, success={success}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        avg_prediction_time = (
            self.total_prediction_time / self.prediction_count 
            if self.prediction_count > 0 else 0
        )
        error_rate = (
            self.error_count / self.prediction_count 
            if self.prediction_count > 0 else 0
        )
        
        return {
            "uptime_seconds": uptime,
            "total_predictions": self.prediction_count,
            "total_errors": self.error_count,
            "error_rate": error_rate,
            "average_prediction_time": avg_prediction_time,
            "predictions_per_minute": self.prediction_count / (uptime / 60) if uptime > 0 else 0
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
    
    def get_model_metrics(self, db: Session) -> Dict[str, Any]:
        """Get model-specific metrics from database"""
        try:
            # Get prediction statistics from last 24 hours
            yesterday = datetime.now() - timedelta(days=1)
            
            recent_predictions = db.query(LoanApplication).filter(
                LoanApplication.prediction_date >= yesterday,
                LoanApplication.predicted_amount_mwk.isnot(None)
            ).all()
            
            if recent_predictions:
                predictions = [float(app.predicted_amount_mwk) for app in recent_predictions]
                confidences = [
                    float(app.prediction_confidence) 
                    for app in recent_predictions 
                    if app.prediction_confidence is not None
                ]
                
                return {
                    "recent_predictions_count": len(recent_predictions),
                    "avg_predicted_amount": sum(predictions) / len(predictions),
                    "min_predicted_amount": min(predictions),
                    "max_predicted_amount": max(predictions),
                    "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
                    "min_confidence": min(confidences) if confidences else 0,
                    "max_confidence": max(confidences) if confidences else 0
                }
            else:
                return {
                    "recent_predictions_count": 0,
                    "avg_predicted_amount": 0,
                    "min_predicted_amount": 0,
                    "max_predicted_amount": 0,
                    "avg_confidence": 0,
                    "min_confidence": 0,
                    "max_confidence": 0
                }
        
        except Exception as e:
            logger.error(f"Error getting model metrics: {str(e)}")
            return {"error": "Failed to retrieve model metrics"}
    
    def check_health(self) -> Dict[str, Any]:
        """Perform health check"""
        self.last_health_check = datetime.now()
        
        health_status = {
            "status": "healthy",
            "timestamp": self.last_health_check,
            "checks": {}
        }
        
        try:
            # Check system resources
            system_metrics = self.get_system_metrics()
            
            # Check CPU usage
            if system_metrics["cpu_percent"] > 90:
                health_status["checks"]["cpu"] = "warning"
                health_status["status"] = "degraded"
            else:
                health_status["checks"]["cpu"] = "healthy"
            
            # Check memory usage
            if system_metrics["memory_percent"] > 85:
                health_status["checks"]["memory"] = "warning"
                health_status["status"] = "degraded"
            else:
                health_status["checks"]["memory"] = "healthy"
            
            # Check disk usage
            if system_metrics["disk_percent"] > 90:
                health_status["checks"]["disk"] = "warning"
                health_status["status"] = "degraded"
            else:
                health_status["checks"]["disk"] = "healthy"
            
            # Check error rate
            performance_metrics = self.get_performance_metrics()
            if performance_metrics["error_rate"] > 0.1:  # 10% error rate
                health_status["checks"]["error_rate"] = "warning"
                health_status["status"] = "degraded"
            else:
                health_status["checks"]["error_rate"] = "healthy"
            
            # Check prediction response time
            if performance_metrics["average_prediction_time"] > 5.0:  # 5 seconds
                health_status["checks"]["response_time"] = "warning"
                health_status["status"] = "degraded"
            else:
                health_status["checks"]["response_time"] = "healthy"
            
        except Exception as e:
            logger.error(f"Error during health check: {str(e)}")
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.prediction_count = 0
        self.error_count = 0
        self.total_prediction_time = 0.0
        self.start_time = datetime.now()
        logger.info("Performance metrics reset")

# Initialize monitor
model_monitor = ModelMonitor()