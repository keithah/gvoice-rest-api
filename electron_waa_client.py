#!/usr/bin/env python3
"""
Python client for Electron-based WAA service
Communicates with Electron app to get authentic WAA signatures
"""
import asyncio
import json
import subprocess
import time
import httpx
from typing import Dict, Optional, Any
from datetime import datetime


class ElectronWAAClient:
    """Client for communicating with Electron WAA service"""
    
    def __init__(self):
        self.electron_process = None
        self.electron_url = "http://localhost:3001"
        self.http_client = httpx.AsyncClient()
        self._initialized = False
    
    async def start_electron_service(self) -> bool:
        """Start the Electron WAA service"""
        try:
            print("🚀 Starting Electron WAA service...")
            
            # Start Electron app in background
            self.electron_process = subprocess.Popen(
                ["npm", "start"],
                cwd="electron-waa",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for service to be ready
            max_wait = 30  # seconds
            for i in range(max_wait):
                try:
                    response = await self.http_client.get(f"{self.electron_url}/health")
                    if response.status_code == 200:
                        print("✅ Electron service is running")
                        return True
                except:
                    pass
                
                await asyncio.sleep(1)
                print(f"⏳ Waiting for Electron service... ({i+1}/{max_wait})")
            
            print("❌ Electron service failed to start")
            return False
            
        except Exception as e:
            print(f"❌ Failed to start Electron: {e}")
            return False
    
    async def initialize_waa(self, cookies: Dict[str, str]) -> bool:
        """Initialize WAA system in Electron"""
        try:
            print("🔧 Initializing WAA in Electron...")
            
            response = await self.http_client.post(
                f"{self.electron_url}/initialize",
                json={"cookies": cookies}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print("✅ Electron WAA initialized")
                    self._initialized = True
                    return True
                else:
                    print(f"❌ WAA initialization failed: {result.get('error')}")
                    return False
            else:
                print(f"❌ HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ WAA initialization error: {e}")
            return False
    
    async def send_sms_via_electron(self, cookies: Dict[str, str], recipient: str, message: str, thread_id: str = "") -> Dict[str, Any]:
        """Send SMS using Electron-generated WAA signature"""
        try:
            if not self._initialized:
                raise Exception("Electron WAA not initialized")
            
            print(f"📱 Sending SMS via Electron: {recipient}")
            
            response = await self.http_client.post(
                f"{self.electron_url}/send-sms",
                json={
                    "cookies": cookies,
                    "recipient": recipient,
                    "message": message,
                    "threadId": thread_id
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    print("🎉 SMS sent successfully via Electron!")
                else:
                    print(f"❌ SMS failed: {result.get('error')}")
                
                return result
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            print(f"❌ Electron SMS error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def stop_electron_service(self):
        """Stop the Electron service"""
        try:
            if self.electron_process:
                self.electron_process.terminate()
                await asyncio.sleep(2)
                
                if self.electron_process.poll() is None:
                    self.electron_process.kill()
                
                print("🛑 Electron service stopped")
            
            await self.http_client.aclose()
            
        except Exception as e:
            print(f"Warning: Electron cleanup error: {e}")


async def test_electron_waa():
    """Test Electron-based WAA SMS sending"""
    
    # Load fresh cookies
    with open('fresh_cookies.json', 'r') as f:
        cookies = json.load(f)
    
    client = ElectronWAAClient()
    
    try:
        print("="*70)
        print("🚀 TESTING ELECTRON-BASED WAA SMS SYSTEM 🚀")
        print("="*70)
        
        # Start Electron service
        if not await client.start_electron_service():
            print("❌ Failed to start Electron service")
            return False
        
        # Initialize WAA
        if not await client.initialize_waa(cookies):
            print("❌ Failed to initialize WAA")
            return False
        
        # Send test SMS
        result = await client.send_sms_via_electron(
            cookies=cookies,
            recipient="3602415033",  # Replace with your number
            message=f"🔥 Electron WAA Test {datetime.now().strftime('%H:%M:%S')}"
        )
        
        print(f"\n📊 Final Result:")
        print(json.dumps(result, indent=2))
        
        if result.get("success"):
            print("\n🎉🎉🎉 SUCCESS! ELECTRON WAA WORKED! 🎉🎉🎉")
            print("Google Voice SMS sent using authentic Electron-generated WAA signature!")
            return True
        else:
            print(f"\n❌ Electron WAA test failed: {result.get('error')}")
            return False
        
    finally:
        await client.stop_electron_service()
        print("🧹 Cleanup completed")


if __name__ == "__main__":
    success = asyncio.run(test_electron_waa())
    
    if success:
        print("\n✅ Electron WAA implementation successful!")
        print("The system can now send SMS with authentic signatures!")
    else:
        print("\n❌ Electron WAA test failed")
        print("Check logs above for issues")