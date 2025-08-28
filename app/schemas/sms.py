from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SendSMSInput(BaseModel):
    recipients: List[str]  # Phone numbers
    message: str

class SMSMessage(BaseModel):
    id: str
    thread_id: Optional[str] = None
    sender: Optional[str] = None
    recipients: Optional[List[str]] = None
    message: str
    timestamp: datetime
    direction: str  # "sent" or "received"
    status: Optional[str] = None  # "sent", "delivered", "failed"

class ThreadResponse(BaseModel):
    thread_id: str
    participants: List[str]
    messages: List[SMSMessage]
    last_message_time: Optional[datetime] = None

class ListThreadsResponse(BaseModel):
    threads: List[ThreadResponse]
    next_page_token: Optional[str] = None