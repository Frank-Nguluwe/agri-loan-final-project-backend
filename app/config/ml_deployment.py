import os
from pathlib import Path
from typing import Dict, Any
from pydantic_settings import BaseSettings

class ModelDeploymentConfig(BaseSettings):
    """Configuration for model deployment"""
    
    # Model settings
    MODEL_PATH: str = "models/loan_predictor1.pkl"
    MODEL_BACKUP_PATH: str = "models/backup/"
    MODEL_VERSION: str = "1.0.0"
    
    # Performance settings
    MAX_BATCH_SIZE: int = 100
    PREDICTION_TIMEOUT: int = 30  # seconds
    MODEL_CACHE_SIZE: int = 1  # Number of models to keep in memory
    
    # Monitoring settings
    ENABLE_MONITORING: bool = True
    METRICS_ENDPOINT: str = "/metrics"
    HEALTH_CHECK_INTERVAL: int = 300  # seconds
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/model_predictions.log"
    
    # Database settings
    PREDICTION_HISTORY_RETENTION_DAYS: int = 365
        
ml_config = ModelDeploymentConfig()

