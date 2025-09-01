"""
UI Automation client for Google Voice SMS sending
Uses Node.js/Puppeteer service for browser automation
"""
import httpx
import json
import asyncio
from typing import Dict, Any, Optional


class UIAutomationClient:
    """Client for UI automation SMS service"""
    
    def __init__(self, cookies: Dict[str, str], service_url: str = "http://localhost:3005"):
        self.cookies = cookies
        self.service_url = service_url
        self.initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the browser automation service"""
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    f"{self.service_url}/initialize",
                    json={"cookies": self.cookies}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.initialized = result.get("success", False)
                    return self.initialized
                else:
                    print(f"❌ UI service init failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ UI service connection error: {e}")
            return False
    
    async def send_sms(self, recipient: str, message: str) -> Dict[str, Any]:
        """Send SMS using UI automation"""
        if not self.initialized:
            await self.initialize()
            
        if not self.initialized:
            return {
                "success": False,
                "error": "UI automation service not initialized"
            }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.service_url}/send-sms",
                    json={
                        "recipient": recipient,
                        "message": message
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": result.get("success", False),
                        "message_id": f"ui_auto_{recipient}_{int(asyncio.get_event_loop().time())}",
                        "method": "ui_automation",
                        "error": result.get("error")
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"UI automation error: {str(e)}"
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if the UI automation service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.service_url}/health")
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"status": "error", "code": response.status_code}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        """Close any resources (placeholder for interface compatibility)"""
        pass