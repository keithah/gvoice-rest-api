from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime

from app.schemas.webhook import (
    CreateWebhookInput, UpdateWebhookInput, WebhookResponse,
    WebhookDeliveryResponse, TestWebhookInput
)
from app.models.webhook import Webhook, WebhookEvent
from app.services.webhook_service import webhook_service
from app.core.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=WebhookResponse)
async def create_webhook(
    input_data: CreateWebhookInput,
    current_user: dict = Depends(get_current_user)
):
    """Create a new webhook endpoint"""
    webhook = Webhook(
        user_id=current_user["id"],
        url=input_data.url,
        events=input_data.events,
        headers=input_data.headers,
        secret=input_data.secret,
        max_retries=input_data.max_retries,
        retry_delay=input_data.retry_delay
    )
    
    await webhook_service.save_webhook(webhook)
    
    return WebhookResponse(
        id=webhook.id,
        url=str(webhook.url),
        events=webhook.events,
        status=webhook.status,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at,
        last_triggered_at=webhook.last_triggered_at,
        failure_count=webhook.failure_count
    )

@router.get("/", response_model=List[WebhookResponse])
async def list_webhooks(current_user: dict = Depends(get_current_user)):
    """List all webhooks for the current user"""
    webhooks = await webhook_service.get_user_webhooks(current_user["id"])
    
    return [
        WebhookResponse(
            id=w.id,
            url=str(w.url),
            events=w.events,
            status=w.status,
            created_at=w.created_at,
            updated_at=w.updated_at,
            last_triggered_at=w.last_triggered_at,
            failure_count=w.failure_count
        )
        for w in webhooks
    ]

@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get webhook details"""
    webhook = await webhook_service.get_webhook(webhook_id)
    
    if not webhook or webhook.user_id != current_user["id"]:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return WebhookResponse(
        id=webhook.id,
        url=str(webhook.url),
        events=webhook.events,
        status=webhook.status,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at,
        last_triggered_at=webhook.last_triggered_at,
        failure_count=webhook.failure_count
    )

@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: str,
    input_data: UpdateWebhookInput,
    current_user: dict = Depends(get_current_user)
):
    """Update webhook configuration"""
    webhook = await webhook_service.get_webhook(webhook_id)
    
    if not webhook or webhook.user_id != current_user["id"]:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Update fields
    if input_data.url is not None:
        webhook.url = input_data.url
    if input_data.events is not None:
        webhook.events = input_data.events
    if input_data.headers is not None:
        webhook.headers = input_data.headers
    if input_data.secret is not None:
        webhook.secret = input_data.secret
    if input_data.status is not None:
        webhook.status = input_data.status
        if webhook.status == WebhookStatus.ACTIVE:
            webhook.failure_count = 0  # Reset failure count when reactivating
    if input_data.max_retries is not None:
        webhook.max_retries = input_data.max_retries
    if input_data.retry_delay is not None:
        webhook.retry_delay = input_data.retry_delay
    
    await webhook_service.save_webhook(webhook)
    
    return WebhookResponse(
        id=webhook.id,
        url=str(webhook.url),
        events=webhook.events,
        status=webhook.status,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at,
        last_triggered_at=webhook.last_triggered_at,
        failure_count=webhook.failure_count
    )

@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a webhook"""
    webhook = await webhook_service.get_webhook(webhook_id)
    
    if not webhook or webhook.user_id != current_user["id"]:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    success = await webhook_service.delete_webhook(webhook_id)
    
    if success:
        return {"message": "Webhook deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete webhook")

@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    input_data: TestWebhookInput,
    current_user: dict = Depends(get_current_user)
):
    """Send a test event to the webhook"""
    webhook = await webhook_service.get_webhook(webhook_id)
    
    if not webhook or webhook.user_id != current_user["id"]:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Trigger test webhook
    await webhook_service.trigger_webhook(
        user_id=current_user["id"],
        event_type=WebhookEvent.MESSAGE_RECEIVED,
        data={
            "test": True,
            "message": input_data.message,
            "sender": "+1234567890",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    return {
        "message": "Test webhook queued for delivery",
        "webhook_id": webhook_id
    }

# Add missing import
from app.models.webhook import WebhookStatus