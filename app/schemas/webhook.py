from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
from datetime import datetime

from app.models.webhook import WebhookEvent, WebhookStatus

class CreateWebhookInput(BaseModel):
    url: HttpUrl
    events: List[WebhookEvent] = [WebhookEvent.ALL]
    headers: Optional[Dict[str, str]] = {}
    secret: Optional[str] = None
    max_retries: Optional[int] = 3
    retry_delay: Optional[int] = 60

class UpdateWebhookInput(BaseModel):
    url: Optional[HttpUrl] = None
    events: Optional[List[WebhookEvent]] = None
    headers: Optional[Dict[str, str]] = None
    secret: Optional[str] = None
    status: Optional[WebhookStatus] = None
    max_retries: Optional[int] = None
    retry_delay: Optional[int] = None

class WebhookResponse(BaseModel):
    id: str
    url: str
    events: List[WebhookEvent]
    status: WebhookStatus
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime] = None
    failure_count: int = 0

class WebhookDeliveryResponse(BaseModel):
    id: str
    webhook_id: str
    event_type: WebhookEvent
    status_code: Optional[int] = None
    delivered_at: Optional[datetime] = None
    attempt: int
    error: Optional[str] = None

class TestWebhookInput(BaseModel):
    message: Optional[str] = "This is a test webhook delivery"