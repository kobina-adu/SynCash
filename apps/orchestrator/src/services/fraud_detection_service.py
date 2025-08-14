"""
Enhanced Fraud Detection Service for SyncCash
Integrates ML model with comprehensive risk assessment and UI response generation
"""

import structlog
import joblib
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import os
import asyncio
from pathlib import Path

from src.models.transaction import Transaction, TransactionStatus
from src.config.settings import get_settings
from src.core.metrics import get_metrics_collector

logger = structlog.get_logger(__name__)

class FraudDetectionResult:
    """Result of fraud detection analysis"""
    
    def __init__(self, is_fraud: bool, risk_score: float, risk_level: str, 
                 confidence: float, ui_response: Dict[str, Any], reasons: List[str] = None):
        self.is_fraud = is_fraud
        self.risk_score = risk_score
        self.risk_level = risk_level
        self.confidence = confidence
        self.ui_response = ui_response
        self.reasons = reasons or []

class EnhancedFraudDetectionService:
    """
    Simple fraud detection service using the existing trained ML model
    Based on detector.py approach
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.metrics = get_metrics_collector()
        self.model = None
        self._load_ml_model()
        
    def _load_ml_model(self):
        """Load the trained fraud detection ML model - same as detector.py"""
        try:
            # Use the same path as detector.py
            model_path = Path(__file__).parent.parent.parent.parent / "apps" / "fraud-detector" / "anti_fraud_model_pipeline.pkl"
            if model_path.exists():
                self.model = joblib.load(str(model_path))
                logger.info("Fraud detection ML model loaded successfully", model_path=str(model_path))
            else:
                logger.warning("ML model not found", model_path=str(model_path))
        except Exception as e:
            logger.error("Failed to load ML model", error=str(e))
            self.model = None
    
    async def validate_transaction(self, transaction: Transaction) -> FraudDetectionResult:
        """
        Simple fraud validation using existing ML model - same approach as detector.py
        """
        logger.info(
            "Starting fraud detection validation",
            transaction_id=str(transaction.id),
            amount=transaction.amount,
            user_id=transaction.user_id
        )
        
        try:
            if not self.model:
                # Fallback if model not loaded
                return self._create_error_result("ML model not available")
            
            # Use the exact same data structure as detector.py
            data = pd.DataFrame([{
                'type': 'PAYMENT',  # Same as detector.py
                'amount': transaction.amount,
                'oldbalanceOrg': getattr(transaction, 'sender_old_balance', 0),
                'newbalanceOrig': getattr(transaction, 'sender_new_balance', 0), 
                'oldbalanceDest': getattr(transaction, 'receiver_old_balance', 0),
                'newbalanceDest': getattr(transaction, 'receiver_new_balance', 0)
            }])
            
            # Making prediction - same as detector.py
            prediction = self.model.predict(data)[0]
            
            # Get prediction probability for confidence
            confidence = 0.8  # Default confidence
            if hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(data)[0]
                confidence = max(proba)
            
            # Convert ML prediction to our risk system
            is_fraud = bool(prediction)  # 1 = fraud, 0 = not fraud
            risk_score = float(prediction)  # Use prediction as risk score
            
            # Determine risk level based on ML model output
            if is_fraud:
                risk_level = "HIGH"  # ML model says it's fraud
            else:
                risk_level = "LOW"   # ML model says it's safe
            
            # Generate UI response based on ML model result
            ui_response = self._generate_ui_response(is_fraud, risk_level, risk_score)
            
            # Log result
            logger.info(
                "ML fraud detection completed",
                transaction_id=str(transaction.id),
                ml_prediction=prediction,
                is_fraud=is_fraud,
                risk_level=risk_level,
                confidence=confidence
            )
            
            return FraudDetectionResult(
                is_fraud=is_fraud,
                risk_score=risk_score,
                risk_level=risk_level,
                confidence=confidence,
                ui_response=ui_response,
                reasons=["ML model prediction"] if is_fraud else ["ML model verified as safe"]
            )
            
        except Exception as e:
            logger.error("Fraud detection failed", error=str(e), transaction_id=str(transaction.id))
            return self._create_error_result(f"Fraud detection error: {str(e)}")
    
    def _generate_ui_response(self, is_fraud: bool, risk_level: str, risk_score: float) -> Dict[str, Any]:
        """Generate UI response based on ML model result"""
        
        if not is_fraud and risk_level == "LOW":
            # ML model says transaction is safe - Green popup
            return {
                "type": "safe",
                "title": "✅ Transaction Verified",
                "message": "Your ML model has verified this transaction as safe.",
                "color": "green",
                "show_popup": True,
                "require_confirmation": True
            }
        else:
            # ML model detected fraud - Red/Orange popup with OTP
            return {
                "type": "high_risk", 
                "title": "⚠️ CAUTION MODE",
                "message": "Your ML model has detected potential fraud. Additional verification required.",
                "warning_text": "DANGER: ML model flagged this transaction",
                "color": "orange",
                "show_popup": True,
                "require_confirmation": True
            }
    
    def _create_error_result(self, error_message: str) -> FraudDetectionResult:
        """Create error result when ML model fails"""
        return FraudDetectionResult(
            is_fraud=True,  # Fail safe - treat as fraud if error
            risk_score=0.9,
            risk_level="HIGH",
            confidence=0.0,
            ui_response={
                "type": "system_error",
                "title": "⚠️ SECURITY CHECK REQUIRED", 
                "message": f"Unable to verify transaction security: {error_message}",
                "warning_text": "CAUTION: Security verification failed",
                "color": "orange",
                "show_popup": True,
                "require_confirmation": True
            },
            reasons=[error_message]
        )
