"""
Webhook API endpoints for payment provider callbacks
Handles incoming webhooks from MTN MoMo, AirtelTigo, and Vodafone Cash
"""
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from typing import Dict, Any
import structlog

from src.providers.webhooks import webhook_processor

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.post("/webhooks/mtn-momo")
async def mtn_momo_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle MTN MoMo webhook callbacks"""
    try:
        # Get request payload and headers
        payload = await request.json()
        headers = dict(request.headers)
        
        logger.info("Received MTN MoMo webhook", 
                   payload_keys=list(payload.keys()) if payload else None)
        
        # Process webhook in background to return quickly
        background_tasks.add_task(
            webhook_processor.process_mtn_webhook,
            payload,
            headers
        )
        
        # Return success immediately (MTN expects quick response)
        return {"status": "received", "message": "Webhook processed"}
        
    except Exception as e:
        logger.error("Error handling MTN MoMo webhook", exc_info=e)
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

@router.post("/webhooks/airteltigo")
async def airteltigo_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle AirtelTigo Money webhook callbacks"""
    try:
        # Get request payload and headers
        payload = await request.json()
        headers = dict(request.headers)
        
        logger.info("Received AirtelTigo webhook",
                   payload_keys=list(payload.keys()) if payload else None)
        
        # Process webhook in background
        background_tasks.add_task(
            webhook_processor.process_airteltigo_webhook,
            payload,
            headers
        )
        
        return {"status": "received", "message": "Webhook processed"}
        
    except Exception as e:
        logger.error("Error handling AirtelTigo webhook", exc_info=e)
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

@router.post("/webhooks/vodafone")
async def vodafone_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle Vodafone Cash webhook callbacks"""
    try:
        # Get request payload and headers
        payload = await request.json()
        headers = dict(request.headers)
        
        logger.info("Received Vodafone webhook",
                   payload_keys=list(payload.keys()) if payload else None)
        
        # Process webhook in background
        background_tasks.add_task(
            webhook_processor.process_vodafone_webhook,
            payload,
            headers
        )
        
        return {"status": "received", "message": "Webhook processed"}
        
    except Exception as e:
        logger.error("Error handling Vodafone webhook", exc_info=e)
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

@router.get("/webhooks/health")
async def webhooks_health():
    """Health check for webhook endpoints"""
    return {
        "status": "healthy",
        "endpoints": {
            "mtn_momo": "/api/v1/webhooks/mtn-momo",
            "airteltigo": "/api/v1/webhooks/airteltigo", 
            "vodafone": "/api/v1/webhooks/vodafone"
        },
        "message": "All webhook endpoints operational"
    }
