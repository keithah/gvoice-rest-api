from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime
import uuid

from app.schemas.sms import (
    SendSMSInput, SMSMessage, ThreadResponse, ListThreadsResponse
)
from app.core.auth import get_current_user
from app.core.storage import storage
from app.services.gvoice_client import GVoiceClient
from app.services.browser_waa_service import EnhancedGVoiceClient
from app.services.ui_automation_client import UIAutomationClient
from app.services.webhook_service import webhook_service
from app.models.webhook import WebhookEvent

router = APIRouter()

async def get_gvoice_client(user_id: str) -> GVoiceClient:
    """Get authenticated Google Voice client for user"""
    cookies = await storage.get_gv_session(user_id)
    if not cookies:
        raise HTTPException(
            status_code=400,
            detail="No Google Voice session found. Please login with cookies first."
        )
    return GVoiceClient(cookies)

@router.post("/send")
async def send_sms(
    input_data: SendSMSInput,
    current_user: dict = Depends(get_current_user)
):
    """Send SMS message(s)"""
    client = await get_gvoice_client(current_user["id"])
    
    try:
        results = []
        for recipient in input_data.recipients:
            result = await client.send_sms(recipient, input_data.message)
            results.append({
                "recipient": recipient,
                "success": result.get("success", False),
                "message_id": result.get("message_id"),
                "error": result.get("error")
            })
            
            # Trigger webhook for sent message
            if result.get("success", False):
                await webhook_service.trigger_webhook(
                    user_id=current_user["id"],
                    event_type=WebhookEvent.MESSAGE_SENT,
                    data={
                        "message_id": result.get("message_id"),
                        "recipient": recipient,
                        "message": input_data.message,
                        "timestamp": result.get("timestamp")
                    }
                )
            else:
                await webhook_service.trigger_webhook(
                    user_id=current_user["id"],
                    event_type=WebhookEvent.MESSAGE_FAILED,
                    data={
                        "recipient": recipient,
                        "message": input_data.message,
                        "error": result.get("error")
                    }
                )
        
        # Check if all succeeded
        all_success = all(r["success"] for r in results)
        
        return {
            "success": all_success,
            "results": results,
            "message": "Messages sent successfully" if all_success else "Some messages failed"
        }
    
    finally:
        await client.close()

@router.post("/send-enhanced")
async def send_sms_enhanced(
    input_data: SendSMSInput,
    current_user: dict = Depends(get_current_user)
):
    """Send SMS using enhanced browser-based WAA signatures"""
    cookies = await storage.get_gv_session(current_user["id"])
    if not cookies:
        raise HTTPException(
            status_code=400,
            detail="No Google Voice session found. Please login with cookies first."
        )
    
    client = EnhancedGVoiceClient(cookies)
    
    try:
        # Initialize browser WAA
        if not await client.initialize():
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize browser WAA system"
            )
        
        results = []
        for recipient in input_data.recipients:
            result = await client.send_sms(recipient, input_data.message)
            results.append({
                "recipient": recipient,
                "success": result.get("success", False),
                "message_id": result.get("transaction_id"),
                "signature_type": result.get("signature_type", "unknown"),
                "error": result.get("error")
            })
            
            # Trigger webhooks
            if result.get("success", False):
                await webhook_service.trigger_webhook(
                    user_id=current_user["id"],
                    event_type=WebhookEvent.MESSAGE_SENT,
                    data={
                        "message_id": result.get("transaction_id"),
                        "recipient": recipient,
                        "message": input_data.message,
                        "signature_type": result.get("signature_type"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            else:
                await webhook_service.trigger_webhook(
                    user_id=current_user["id"],
                    event_type=WebhookEvent.MESSAGE_FAILED,
                    data={
                        "recipient": recipient,
                        "message": input_data.message,
                        "error": result.get("error"),
                        "signature_type": result.get("signature_type")
                    }
                )
        
        all_success = all(r["success"] for r in results)
        
        return {
            "success": all_success,
            "results": results,
            "message": "Enhanced SMS sent successfully" if all_success else "Some enhanced SMS failed",
            "method": "browser_waa"
        }
    
    finally:
        await client.close()

@router.post("/send-ui")
async def send_sms_ui_automation(
    input_data: SendSMSInput,
    current_user: dict = Depends(get_current_user)
):
    """Send SMS using working UI automation method"""
    cookies = await storage.get_gv_session(current_user["id"])
    if not cookies:
        raise HTTPException(
            status_code=400,
            detail="No Google Voice session found. Please login with cookies first."
        )
    
    client = UIAutomationClient(cookies)
    
    try:
        # Initialize browser
        if not await client.initialize():
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize UI automation service"
            )
        
        results = []
        for recipient in input_data.recipients:
            result = await client.send_sms(recipient, input_data.message)
            results.append({
                "recipient": recipient,
                "success": result.get("success", False),
                "message_id": result.get("message_id"),
                "method": "ui_automation",
                "error": result.get("error")
            })
            
            # Trigger webhooks
            if result.get("success", False):
                await webhook_service.trigger_webhook(
                    user_id=current_user["id"],
                    event_type=WebhookEvent.MESSAGE_SENT,
                    data={
                        "message_id": result.get("message_id"),
                        "recipient": recipient,
                        "message": input_data.message,
                        "method": "ui_automation",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            else:
                await webhook_service.trigger_webhook(
                    user_id=current_user["id"],
                    event_type=WebhookEvent.MESSAGE_FAILED,
                    data={
                        "recipient": recipient,
                        "message": input_data.message,
                        "error": result.get("error"),
                        "method": "ui_automation"
                    }
                )
        
        all_success = all(r["success"] for r in results)
        
        return {
            "success": all_success,
            "results": results,
            "message": "UI automation SMS sent successfully" if all_success else "Some UI automation SMS failed",
            "method": "ui_automation"
        }
    
    finally:
        await client.close()

@router.get("/threads")
async def list_threads(
    folder: str = Query("all", regex="^(all|inbox|spam|trash)$"),
    page_token: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
) -> ListThreadsResponse:
    """List conversation threads"""
    client = await get_gvoice_client(current_user["id"])
    
    try:
        result = await client.list_threads(folder, page_token)
        
        # Convert to our schema format
        threads = []
        for thread_data in result.get("threads", []):
            # This would need proper parsing from protobuf in real implementation
            threads.append(ThreadResponse(
                thread_id=thread_data.get("id", ""),
                participants=thread_data.get("participants", []),
                messages=[],
                last_message_time=None
            ))
        
        return ListThreadsResponse(
            threads=threads,
            next_page_token=result.get("version_token")
        )
    
    finally:
        await client.close()

@router.get("/threads/{thread_id}")
async def get_thread(
    thread_id: str,
    message_count: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
) -> ThreadResponse:
    """Get messages in a specific thread"""
    client = await get_gvoice_client(current_user["id"])
    
    try:
        result = await client.get_thread(thread_id, message_count)
        
        # Convert to our schema format
        messages = []
        for msg_data in result.get("messages", []):
            # This would need proper parsing from protobuf in real implementation
            messages.append(SMSMessage(
                id=msg_data.get("id", str(uuid.uuid4())),
                thread_id=thread_id,
                sender=msg_data.get("sender"),
                recipients=msg_data.get("recipients", []),
                message=msg_data.get("text", ""),
                timestamp=datetime.utcnow(),
                direction=msg_data.get("direction", "received"),
                status=msg_data.get("status")
            ))
        
        return ThreadResponse(
            thread_id=thread_id,
            participants=[],  # Would be extracted from thread data
            messages=messages,
            last_message_time=messages[0].timestamp if messages else None
        )
    
    finally:
        await client.close()

@router.delete("/threads/{thread_id}")
async def delete_thread(
    thread_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a conversation thread"""
    client = await get_gvoice_client(current_user["id"])
    
    try:
        success = await client.delete_thread(thread_id)
        
        if success:
            return {"message": "Thread deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to delete thread")
    
    finally:
        await client.close()

@router.post("/mark-all-read")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    """Mark all messages as read"""
    client = await get_gvoice_client(current_user["id"])
    
    try:
        success = await client.mark_all_read()
        
        if success:
            return {"message": "All messages marked as read"}
        else:
            raise HTTPException(status_code=400, detail="Failed to mark messages as read")
    
    finally:
        await client.close()

@router.get("/account")
async def get_account_info(current_user: dict = Depends(get_current_user)):
    """Get Google Voice account information"""
    client = await get_gvoice_client(current_user["id"])
    
    try:
        account_info = await client.get_account()
        return {
            "account": account_info,
            "user_id": current_user["id"]
        }
    
    finally:
        await client.close()