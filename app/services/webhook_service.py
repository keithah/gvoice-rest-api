"""Webhook delivery service"""

import httpx
import asyncio
import json
import hmac
import hashlib
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import logging

from app.models.webhook import Webhook, WebhookDelivery, WebhookEvent, WebhookStatus
from app.core.storage import storage

logger = logging.getLogger(__name__)

class WebhookService:
    """Service for managing and delivering webhooks"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.delivery_queue: asyncio.Queue = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start webhook delivery worker"""
        if not self.worker_task:
            self.worker_task = asyncio.create_task(self._delivery_worker())
            logger.info("Started webhook delivery worker")
    
    async def stop(self):
        """Stop webhook delivery worker"""
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
            self.worker_task = None
        await self.client.aclose()
        logger.info("Stopped webhook delivery worker")
    
    async def _delivery_worker(self):
        """Background worker for delivering webhooks"""
        while True:
            try:
                delivery = await self.delivery_queue.get()
                await self._deliver_webhook(delivery)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in webhook delivery worker: {e}")
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook payload"""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    async def _deliver_webhook(self, delivery: WebhookDelivery):
        """Deliver a single webhook"""
        webhook = await self.get_webhook(delivery.webhook_id)
        if not webhook or webhook.status != WebhookStatus.ACTIVE:
            return
        
        try:
            # Prepare headers
            headers = webhook.headers.copy() if webhook.headers else {}
            headers["Content-Type"] = "application/json"
            headers["X-Webhook-Event"] = delivery.event_type
            headers["X-Webhook-Delivery"] = delivery.id
            
            # Add signature if secret is configured
            payload_json = json.dumps(delivery.payload)
            if webhook.secret:
                signature = self._generate_signature(payload_json, webhook.secret)
                headers["X-Webhook-Signature"] = f"sha256={signature}"
            
            # Send webhook
            logger.info(f"Delivering webhook {delivery.id} to {webhook.url}")
            
            response = await self.client.post(
                str(webhook.url),
                content=payload_json,
                headers=headers
            )
            
            # Update delivery record
            delivery.status_code = response.status_code
            delivery.response_body = response.text[:1000]  # Store first 1KB
            delivery.delivered_at = datetime.utcnow()
            
            # Update webhook status
            webhook.last_triggered_at = datetime.utcnow()
            
            if response.status_code >= 200 and response.status_code < 300:
                webhook.failure_count = 0
                logger.info(f"Webhook {delivery.id} delivered successfully")
            else:
                webhook.failure_count += 1
                logger.warning(f"Webhook {delivery.id} failed with status {response.status_code}")
                
                # Retry if needed
                if delivery.attempt < webhook.max_retries:
                    await self._schedule_retry(delivery, webhook.retry_delay)
                elif webhook.failure_count >= 5:
                    # Disable webhook after too many failures
                    webhook.status = WebhookStatus.FAILED
                    logger.error(f"Webhook {webhook.id} disabled after repeated failures")
            
            # Save updates
            await self.save_webhook(webhook)
            await self._save_delivery(delivery)
            
        except Exception as e:
            logger.error(f"Error delivering webhook {delivery.id}: {e}")
            delivery.error = str(e)
            await self._save_delivery(delivery)
            
            webhook.failure_count += 1
            if delivery.attempt < webhook.max_retries:
                await self._schedule_retry(delivery, webhook.retry_delay)
            
            await self.save_webhook(webhook)
    
    async def _schedule_retry(self, delivery: WebhookDelivery, delay_seconds: int):
        """Schedule webhook retry"""
        delivery.attempt += 1
        logger.info(f"Scheduling webhook {delivery.id} retry #{delivery.attempt} in {delay_seconds}s")
        
        async def retry():
            await asyncio.sleep(delay_seconds)
            await self.delivery_queue.put(delivery)
        
        asyncio.create_task(retry())
    
    async def trigger_webhook(self, user_id: str, event_type: WebhookEvent, data: Dict):
        """Trigger webhooks for a user and event"""
        webhooks = await self.get_user_webhooks(user_id)
        
        for webhook in webhooks:
            # Check if webhook is subscribed to this event
            if webhook.status != WebhookStatus.ACTIVE:
                continue
            
            if WebhookEvent.ALL not in webhook.events and event_type not in webhook.events:
                continue
            
            # Create delivery record
            delivery = WebhookDelivery(
                webhook_id=webhook.id,
                event_type=event_type,
                payload={
                    "event": event_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": data
                }
            )
            
            # Queue for delivery
            await self.delivery_queue.put(delivery)
    
    # Storage methods
    async def save_webhook(self, webhook: Webhook):
        """Save webhook to storage"""
        webhook.updated_at = datetime.utcnow()
        
        # Get user's webhooks
        user_webhooks_file = storage.base_dir / "webhooks" / f"{webhook.user_id}.json"
        user_webhooks_file.parent.mkdir(exist_ok=True)
        
        existing = await storage.load_json_file(user_webhooks_file) or {"webhooks": []}
        
        # Update or add webhook
        webhook_dict = webhook.dict()
        webhook_found = False
        for i, w in enumerate(existing["webhooks"]):
            if w["id"] == webhook.id:
                existing["webhooks"][i] = webhook_dict
                webhook_found = True
                break
        
        if not webhook_found:
            existing["webhooks"].append(webhook_dict)
        
        await storage.save_json_file(user_webhooks_file, existing)
    
    async def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """Get webhook by ID"""
        # Search all user webhook files
        webhooks_dir = storage.base_dir / "webhooks"
        if not webhooks_dir.exists():
            return None
        
        for user_file in webhooks_dir.glob("*.json"):
            user_data = await storage.load_json_file(user_file)
            if user_data:
                for webhook_data in user_data.get("webhooks", []):
                    if webhook_data["id"] == webhook_id:
                        return Webhook(**webhook_data)
        
        return None
    
    async def get_user_webhooks(self, user_id: str) -> List[Webhook]:
        """Get all webhooks for a user"""
        user_webhooks_file = storage.base_dir / "webhooks" / f"{user_id}.json"
        user_data = await storage.load_json_file(user_webhooks_file)
        
        if not user_data:
            return []
        
        return [Webhook(**w) for w in user_data.get("webhooks", [])]
    
    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook"""
        webhook = await self.get_webhook(webhook_id)
        if not webhook:
            return False
        
        user_webhooks_file = storage.base_dir / "webhooks" / f"{webhook.user_id}.json"
        user_data = await storage.load_json_file(user_webhooks_file) or {"webhooks": []}
        
        user_data["webhooks"] = [
            w for w in user_data["webhooks"] if w["id"] != webhook_id
        ]
        
        await storage.save_json_file(user_webhooks_file, user_data)
        return True
    
    async def _save_delivery(self, delivery: WebhookDelivery):
        """Save delivery record"""
        deliveries_dir = storage.base_dir / "webhook_deliveries"
        deliveries_dir.mkdir(exist_ok=True)
        
        # Save by date for easier cleanup
        date_str = delivery.created_at.strftime("%Y-%m-%d")
        delivery_file = deliveries_dir / f"{date_str}.json"
        
        existing = await storage.load_json_file(delivery_file) or {"deliveries": []}
        existing["deliveries"].append(delivery.dict())
        
        # Keep only last 1000 deliveries per day
        if len(existing["deliveries"]) > 1000:
            existing["deliveries"] = existing["deliveries"][-1000:]
        
        await storage.save_json_file(delivery_file, existing)

# Global webhook service instance
webhook_service = WebhookService()