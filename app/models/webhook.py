"""Webhook models and storage"""

from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
import uuid

class WebhookEvent(str, Enum):
    """Supported webhook event types"""
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_SENT = "message.sent"
    MESSAGE_FAILED = "message.failed"
    THREAD_CREATED = "thread.created"
    THREAD_DELETED = "thread.deleted"
    ALL = "*"

class WebhookStatus(str, Enum):
    """Webhook status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"

class Webhook(BaseModel):
    """Webhook configuration"""
    id: str = None
    user_id: str
    url: HttpUrl
    events: List[WebhookEvent] = [WebhookEvent.ALL]
    headers: Optional[Dict[str, str]] = {}
    secret: Optional[str] = None  # For HMAC signature validation
    status: WebhookStatus = WebhookStatus.ACTIVE
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    created_at: datetime = None
    updated_at: datetime = None
    last_triggered_at: Optional[datetime] = None
    failure_count: int = 0
    
    def __init__(self, **data):
        if 'id' not in data or data['id'] is None:
            data['id'] = str(uuid.uuid4())
        if 'created_at' not in data or data['created_at'] is None:
            data['created_at'] = datetime.utcnow()
        if 'updated_at' not in data or data['updated_at'] is None:
            data['updated_at'] = datetime.utcnow()
        super().__init__(**data)

class WebhookDelivery(BaseModel):
    """Record of webhook delivery attempt"""
    id: str
    webhook_id: str
    event_type: WebhookEvent
    payload: Dict
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None
    attempt: int = 1
    delivered_at: Optional[datetime] = None
    created_at: datetime = None
    
    def __init__(self, **data):
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        if 'created_at' not in data:
            data['created_at'] = datetime.utcnow()
        super().__init__(**data)