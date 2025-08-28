"""Google Voice client implementation based on mautrix-gvoice"""

import httpx
import hashlib
import time
import random
import json
import base64
from typing import Dict, Optional, List, Any
from datetime import datetime
from urllib.parse import urlencode, quote

from app.core.constants import (
    USER_AGENT, CH_USER_AGENT, CH_PLATFORM, CLIENT_VERSION,
    JAVASCRIPT_USER_AGENT, WAA_X_USER_AGENT, API_KEY, WAA_API_KEY,
    ORIGIN, API_DOMAIN, CONTACTS_DOMAIN, WAA_DOMAIN, UPLOAD_DOMAIN,
    ENDPOINTS, CLIENT_DETAILS, CONTENT_TYPE_PBLITE, CONTENT_TYPE_PROTOBUF
)


class GVoiceClient:
    """Google Voice client for making API calls"""
    
    def __init__(self, cookies: Optional[Dict[str, str]] = None):
        self.cookies = cookies or {}
        self.auth_user = "0"
        self.client = httpx.AsyncClient(timeout=120.0)
    
    def _generate_sapisid_hash(self, sapisid: str) -> str:
        """Generate SAPISID hash for authorization"""
        timestamp = int(time.time())
        hash_input = f"{timestamp} {sapisid} {ORIGIN}"
        hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
        return f"SAPISIDHASH {timestamp}_{hash_value}"
    
    def _prepare_headers(self, url: str, content_type: Optional[str] = None) -> Dict[str, str]:
        """Prepare headers for request based on mautrix-gvoice logic"""
        headers = {
            "Sec-Ch-Ua": CH_USER_AGENT,
            "Sec-Ch-Ua-Platform": CH_PLATFORM,
            "Sec-Ch-Ua-Mobile": "?0",
            "User-Agent": USER_AGENT,
            "X-Goog-AuthUser": self.auth_user,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        # Set origin and referer
        if UPLOAD_DOMAIN in url:
            headers["Origin"] = f"https://{UPLOAD_DOMAIN}"
            headers["Referer"] = f"https://{UPLOAD_DOMAIN}/"
        else:
            headers["Origin"] = ORIGIN
            headers["Referer"] = f"{ORIGIN}/"
        
        # API domain specific headers
        if API_DOMAIN in url:
            headers["X-Client-Version"] = CLIENT_VERSION
            headers["X-ClientDetails"] = urlencode(CLIENT_DETAILS)
            headers["X-JavaScript-User-Agent"] = JAVASCRIPT_USER_AGENT
            headers["X-Requested-With"] = "XMLHttpRequest"
            headers["X-Goog-Encode-Response-If-Executable"] = "base64"
        
        # Contacts domain specific headers
        if CONTACTS_DOMAIN in url:
            headers["X-Goog-Api-Key"] = API_KEY
            headers["X-Goog-Encode-Response-If-Executable"] = "base64"
        
        # WAA domain specific headers
        if WAA_DOMAIN in url:
            headers["X-Goog-Api-Key"] = WAA_API_KEY
            headers["X-User-Agent"] = WAA_X_USER_AGENT
        
        # Set sec-fetch-site
        if API_DOMAIN in url and url.startswith("https://"):
            headers["Sec-Fetch-Site"] = "same-site"
        else:
            headers["Sec-Fetch-Site"] = "same-origin"
        
        # Set content type if provided
        if content_type:
            headers["Content-Type"] = content_type
        
        # Add authorization if we have SAPISID cookie
        if "SAPISID" in self.cookies:
            headers["Authorization"] = self._generate_sapisid_hash(self.cookies["SAPISID"])
        
        # Convert cookies dict to Cookie header
        if self.cookies:
            headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        
        return headers
    
    def _generate_transaction_id(self) -> int:
        """Generate random transaction ID"""
        return random.randint(1, 99999999999999)
    
    async def _make_request(
        self, 
        method: str, 
        url: str, 
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> httpx.Response:
        """Make HTTP request to Google Voice API"""
        # Add API key to params for certain endpoints
        if params is None:
            params = {}
        
        if API_DOMAIN in url and WAA_DOMAIN not in url:
            params["key"] = API_KEY
            if API_DOMAIN in url or CONTACTS_DOMAIN in url:
                params["alt"] = "proto"
        
        # For now, we'll use JSON format instead of protobuf
        content_type = CONTENT_TYPE_PBLITE
        headers = self._prepare_headers(url, content_type)
        
        # Convert data to JSON string for PBLite format
        data = None
        if json_data:
            data = json.dumps(json_data)
        
        response = await self.client.request(
            method=method,
            url=url,
            headers=headers,
            content=data,
            params=params
        )
        
        # Update cookies from response
        for cookie in response.cookies:
            self.cookies[cookie.name] = cookie.value
        
        return response
    
    async def get_account(self) -> Dict:
        """Get account information"""
        # Simplified version - would need protobuf in real implementation
        response = await self._make_request(
            "POST",
            ENDPOINTS["get_account"],
            json_data={"unknown_int2": 1}
        )
        return response.json() if response.status_code == 200 else {}
    
    async def send_sms(self, phone_number: str, message: str) -> Dict:
        """Send SMS message"""
        request_data = {
            "conversationId": phone_number,
            "message": {
                "text": message
            },
            "sendWithoutConversation": True,
            "transactionId": self._generate_transaction_id(),
            "trackingData": {"data": "!"}
        }
        
        response = await self._make_request(
            "POST",
            ENDPOINTS["send_sms"],
            json_data=request_data
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message_id": str(self._generate_transaction_id()),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "success": False,
                "error": f"Failed to send SMS: {response.status_code}"
            }
    
    async def list_threads(self, folder: str = "all", version_token: Optional[str] = None) -> Dict:
        """List conversation threads"""
        # Folder types: all, inbox, spam, trash
        folder_map = {
            "all": 1,
            "inbox": 2,
            "spam": 7,
            "trash": 8
        }
        
        request_data = {
            "folder": folder_map.get(folder, 1),
            "unknownInt2": 20 if not version_token else 10,
            "unknownInt3": 15,
            "versionToken": version_token or "",
            "unknownWrapper": {
                "unknownInt2": 1,
                "unknownInt3": 1
            }
        }
        
        response = await self._make_request(
            "POST",
            ENDPOINTS["list_threads"],
            json_data=request_data
        )
        
        if response.status_code == 200:
            # Parse response - in real implementation would parse protobuf
            return {"threads": [], "version_token": ""}
        return {"threads": [], "error": f"Failed: {response.status_code}"}
    
    async def get_thread(self, thread_id: str, message_count: int = 20) -> Dict:
        """Get messages in a thread"""
        request_data = {
            "threadId": thread_id,
            "maybeMessageCount": message_count,
            "paginationToken": "",
            "unknownWrapper": {
                "unknownInt2": 1,
                "unknownInt3": 1
            }
        }
        
        response = await self._make_request(
            "POST",
            ENDPOINTS["get_thread"],
            json_data=request_data
        )
        
        if response.status_code == 200:
            # Parse response - in real implementation would parse protobuf
            return {"messages": [], "thread_id": thread_id}
        return {"messages": [], "error": f"Failed: {response.status_code}"}
    
    async def delete_thread(self, thread_id: str) -> bool:
        """Delete a conversation thread"""
        response = await self._make_request(
            "POST",
            ENDPOINTS["delete_thread"],
            json_data={"threadId": thread_id}
        )
        return response.status_code == 200
    
    async def mark_all_read(self) -> bool:
        """Mark all messages as read"""
        response = await self._make_request(
            "POST",
            ENDPOINTS["mark_all_read"],
            json_data={}
        )
        return response.status_code == 200
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()