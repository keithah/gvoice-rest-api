"""Real-time message receiving implementation based on mautrix-gvoice"""

import asyncio
import json
import random
import time
from typing import Dict, Optional, Callable, Any
import httpx
from urllib.parse import urlencode
import logging
from datetime import datetime

from app.core.constants import (
    REALTIME_ENDPOINTS, CONTENT_TYPE_PBLITE,
    USER_AGENT, CH_USER_AGENT, CH_PLATFORM, ORIGIN
)
from app.services.webhook_service import webhook_service
from app.models.webhook import WebhookEvent

logger = logging.getLogger(__name__)

class RealtimeClient:
    """Real-time message receiving client for Google Voice"""
    
    def __init__(self, cookies: Dict[str, str], auth_user: str = "0"):
        self.cookies = cookies
        self.auth_user = auth_user
        self.client = httpx.AsyncClient(timeout=None)
        self.is_running = False
        self.event_handlers: Dict[str, Callable] = {}
        
    def on_event(self, event_type: str, handler: Callable):
        """Register event handler"""
        self.event_handlers[event_type] = handler
    
    def _prepare_headers(self, url: str, extra_headers: Optional[Dict] = None) -> Dict[str, str]:
        """Prepare headers for realtime requests"""
        headers = {
            "Sec-Ch-Ua": CH_USER_AGENT,
            "Sec-Ch-Ua-Platform": CH_PLATFORM,
            "Sec-Ch-Ua-Mobile": "?0",
            "User-Agent": USER_AGENT,
            "X-Goog-AuthUser": self.auth_user,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Origin": ORIGIN,
            "Referer": f"{ORIGIN}/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }
        
        # Add cookies
        if self.cookies:
            headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        
        # Add authorization if we have SAPISID cookie
        if "SAPISID" in self.cookies:
            headers["Authorization"] = self._generate_sapisid_hash(self.cookies["SAPISID"])
        
        # Add extra headers
        if extra_headers:
            headers.update(extra_headers)
            
        return headers
    
    def _generate_sapisid_hash(self, sapisid: str) -> str:
        """Generate SAPISID hash for authorization"""
        import hashlib
        timestamp = int(time.time())
        hash_input = f"{timestamp} {sapisid} {ORIGIN}"
        hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
        return f"SAPISIDHASH {timestamp}_{hash_value}"
    
    async def _choose_server(self) -> str:
        """Choose realtime server and get session ID"""
        # PBLite format request for choosing server
        req_data = '[[null,null,null,[7,5],null,[null,[null,1],[[["3"]]]]]]'
        
        headers = self._prepare_headers(
            REALTIME_ENDPOINTS["choose_server"],
            {"Content-Type": CONTENT_TYPE_PBLITE}
        )
        
        response = await self.client.post(
            REALTIME_ENDPOINTS["choose_server"],
            headers=headers,
            content=req_data
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to choose server: {response.status_code}")
        
        # Parse response to get GSessionID
        # In a real implementation, you'd parse the protobuf response
        # For now, generate a mock session ID
        gsession_id = f"session_{random.randint(10000000, 99999999)}"
        
        logger.info(f"Chose realtime server with session: {gsession_id}")
        return gsession_id
    
    async def _create_channel(self, gsession_id: str) -> Dict[str, str]:
        """Create realtime channel"""
        query_params = {
            "VER": "8",
            "gsessionid": gsession_id,
            "RID": str(random.randint(10000, 99999)),
            "CVER": "22",
            "t": "1",
        }
        
        # Channel subscription requests
        body_data = {
            "count": "7",
            "ofs": "0",
            "req0___data__": '[[["1",[null,null,null,[7,5],null,[null,[null,1],[[["2"]]]],null,1,2],null,3]]]',
            "req1___data__": '[[["2",[null,null,null,[7,5],null,[null,[null,1],[[["3"]]]],null,1,2],null,3]]]',
            "req2___data__": '[[["3",[null,null,null,[7,5],null,[null,[null,1],[[["3"]]]],null,1,2],null,3]]]',
            "req3___data__": '[[["4",[null,null,null,[7,5],null,[null,[null,1],[[["1"]]]],null,1,2],null,3]]]',
            "req4___data__": '[[["5",[null,null,null,[7,5],null,[null,[null,1],[[["1"]]]],null,1,2],null,3]]]',
            "req5___data__": '[[["6",[null,null,null,[7,5],null,[null,[null,1],[[["1"]]]],null,1,2],null,3]]]',
            "req6___data__": '[[["9",[null,null,null,[7,5],null,[null,[null,1],[[["1"]]]],null,1,2],null,3]]]',
        }
        
        headers = self._prepare_headers(
            REALTIME_ENDPOINTS["channel"],
            {
                "X-WebChannel-Content-Type": CONTENT_TYPE_PBLITE,
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        
        url = f"{REALTIME_ENDPOINTS['channel']}?{urlencode(query_params)}"
        
        response = await self.client.post(
            url,
            headers=headers,
            data=urlencode(body_data)
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to create channel: {response.status_code}")
        
        # In a real implementation, parse the response to get channel details
        # For now, generate mock channel info
        channel_info = {
            "session_id": f"channel_{random.randint(10000000, 99999999)}",
            "gsession_id": gsession_id
        }
        
        logger.info(f"Created realtime channel: {channel_info}")
        return channel_info
    
    async def _poll_messages(self, gsession_id: str, session_id: str):
        """Long poll for real-time messages"""
        ack_id = 0
        failed_requests = 0
        
        while self.is_running:
            try:
                query_params = {
                    "VER": "8",
                    "gsessionid": gsession_id,
                    "RID": "rpc",
                    "SID": session_id,
                    "AID": str(ack_id),
                    "CI": "0",
                    "TYPE": "xmlhttp",
                    "t": "1",
                }
                
                headers = self._prepare_headers(REALTIME_ENDPOINTS["channel"])
                url = f"{REALTIME_ENDPOINTS['channel']}?{urlencode(query_params)}"
                
                logger.debug(f"Long polling for messages with AID={ack_id}")
                
                # Long poll request
                async with self.client.stream("GET", url, headers=headers) as response:
                    if response.status_code != 200:
                        failed_requests += 1
                        if failed_requests > 10:
                            raise Exception("Too many failed requests")
                        
                        logger.warning(f"Poll request failed: {response.status_code}")
                        await asyncio.sleep(min(failed_requests * 2, 30))
                        continue
                    
                    failed_requests = 0
                    
                    # Read streaming response
                    buffer = ""
                    async for chunk in response.aiter_bytes():
                        if not self.is_running:
                            break
                            
                        buffer += chunk.decode('utf-8', errors='ignore')
                        
                        # Process complete JSON messages
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            if line.strip():
                                await self._process_message(line.strip())
                                ack_id += 1
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in message polling: {e}")
                failed_requests += 1
                await asyncio.sleep(min(failed_requests * 2, 30))
    
    async def _process_message(self, message_data: str):
        """Process received real-time message"""
        try:
            # Try to parse as JSON
            data = json.loads(message_data)
            
            # Check if it's a noop message
            if isinstance(data, list) and len(data) > 1 and data[1] == "noop":
                return
            
            # Emit realtime event
            if "message" in self.event_handlers:
                await self.event_handlers["message"](data)
            
            logger.debug(f"Processed realtime message: {data}")
            
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse realtime message: {message_data}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def start(self):
        """Start real-time message receiving"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting real-time message client...")
        
        try:
            # Step 1: Choose server
            gsession_id = await self._choose_server()
            
            # Step 2: Create channel
            channel_info = await self._create_channel(gsession_id)
            
            # Step 3: Start polling for messages
            await self._poll_messages(
                channel_info["gsession_id"], 
                channel_info["session_id"]
            )
            
        except Exception as e:
            logger.error(f"Error in realtime client: {e}")
            self.is_running = False
            raise
    
    async def stop(self):
        """Stop real-time message receiving"""
        self.is_running = False
        await self.client.aclose()
        logger.info("Stopped real-time message client")


class RealtimeManager:
    """Manages real-time clients for multiple users"""
    
    def __init__(self):
        self.clients: Dict[str, RealtimeClient] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
    
    async def start_client(self, user_id: str, cookies: Dict[str, str], event_handlers: Dict[str, Callable]):
        """Start real-time client for a user"""
        if user_id in self.clients:
            await self.stop_client(user_id)
        
        client = RealtimeClient(cookies)
        
        # Add webhook handler wrapper
        original_message_handler = event_handlers.get("message")
        
        async def message_handler_with_webhook(message_data):
            # Call original handler
            if original_message_handler:
                await original_message_handler(message_data)
            
            # Trigger webhook for received message
            try:
                # Parse message data to extract relevant info
                if isinstance(message_data, dict):
                    await webhook_service.trigger_webhook(
                        user_id=user_id,
                        event_type=WebhookEvent.MESSAGE_RECEIVED,
                        data={
                            "raw_data": message_data,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
            except Exception as e:
                logger.error(f"Error triggering webhook: {e}")
        
        # Register event handlers
        for event_type, handler in event_handlers.items():
            if event_type == "message":
                client.on_event(event_type, message_handler_with_webhook)
            else:
                client.on_event(event_type, handler)
        
        self.clients[user_id] = client
        self.tasks[user_id] = asyncio.create_task(client.start())
        
        logger.info(f"Started realtime client for user: {user_id}")
    
    async def stop_client(self, user_id: str):
        """Stop real-time client for a user"""
        if user_id in self.clients:
            await self.clients[user_id].stop()
            del self.clients[user_id]
        
        if user_id in self.tasks:
            self.tasks[user_id].cancel()
            try:
                await self.tasks[user_id]
            except asyncio.CancelledError:
                pass
            del self.tasks[user_id]
        
        logger.info(f"Stopped realtime client for user: {user_id}")
    
    async def stop_all(self):
        """Stop all real-time clients"""
        for user_id in list(self.clients.keys()):
            await self.stop_client(user_id)

# Global realtime manager
realtime_manager = RealtimeManager()