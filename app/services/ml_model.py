# app/services/model_service.py
import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List
from fastapi import HTTPException
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)
model_path = "app/ml_model/loan_predictor1.pkl"

class PredictionInput(BaseModel):
    loan_farm_size: float
    loan_crop: str
    past_yield_kgs: float
    past_yield_mk: float
    expected_yield_kgs: float
    expected_yield_mk: float

class ModelService:
    def __init__(self, model_path: str = model_path):
        self.model_path = model_path
        self.model = None
        self.model_version = None
        self.load_model()
    
    def load_model(self):
        """Load the trained model from disk"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.model_version = datetime.now().strftime("%Y%m%d_%H%M%S")
                logger.info(f"Model loaded successfully from {self.model_path}")
            else:
                raise FileNotFoundError(f"Model file not found: {self.model_path}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load prediction model: {str(e)}"
            )
    
    def reload_model(self, new_model_path: str = None):
        """Reload model with new version"""
        if new_model_path:
            self.model_path = new_model_path
        self.load_model()
        logger.info(f"Model reloaded with version: {self.model_version}")
        return self.get_model_info()
    
    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction using only the 6 required features"""
        try:
            if not self.model:
                raise HTTPException(status_code=503, detail="Model not loaded")
            
            # Validate input contains all required features
            required_fields = [
                'loan_farm_size', 'loan_crop', 'past_yield_kgs',
                'past_yield_mk', 'expected_yield_kgs', 'expected_yield_mk'
            ]
            missing_fields = [f for f in required_fields if f not in input_data]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")

            # Prepare features DataFrame
            features = pd.DataFrame([{
                'loan_farm_size': input_data['loan_farm_size'],
                'loan_crop': input_data['loan_crop'],
                'past_yield_kgs': input_data['past_yield_kgs'],
                'past_yield_mk': input_data['past_yield_mk'],
                'expected_yield_kgs': input_data['expected_yield_kgs'],
                'expected_yield_mk': input_data['expected_yield_mk']
            }])
            
            # Make prediction
            prediction = float(self.model.predict(features)[0])
            prediction = max(0, prediction)  # Ensure non-negative
            
            # Calculate confidence score
            confidence = self._calculate_confidence(input_data, prediction)
            
            return {
                "predicted_amount_mwk": prediction,
                "prediction_confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Prediction error: {str(e)}"
            )
    
    def _calculate_confidence(self, input_data: Dict[str, Any], prediction: float) -> float:
        """Calculate confidence score based on input data"""
        confidence = 0.7  # Base confidence
        
        # Higher confidence if historical data exists
        if input_data.get('past_yield_kgs', 0) > 0 and input_data.get('past_yield_mk', 0) > 0:
            confidence = min(0.9, confidence + 0.2)
        
        # Lower confidence for very large loans
        if prediction > 1000000:  # 1 million MWK
            confidence = max(0.5, confidence - 0.1)
        
        return round(confidence, 2)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "model_path": self.model_path,
            "model_version": self.model_version,
            "model_loaded": self.model is not None,
            "features_used": [
                'loan_farm_size',
                'loan_crop',
                'past_yield_kgs',
                'past_yield_mk',
                'expected_yield_kgs',
                'expected_yield_mk'
            ],
            "last_loaded": datetime.now().isoformat()
        }

# Initialize model service
model_service = ModelService()