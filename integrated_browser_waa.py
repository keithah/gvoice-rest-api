#!/usr/bin/env python3
"""
Integrated Browser WAA Client
Works within Google Voice page context to avoid cross-origin issues
"""
import asyncio
import json
import time
import hashlib
import random
import httpx
from playwright.async_api import async_playwright
from typing import Dict, Optional, Any
from datetime import datetime


class IntegratedBrowserWAA:
    """Execute WAA within Google Voice page context"""
    
    def __init__(self, cookies: Dict[str, str]):
        self.cookies = cookies
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize browser in Google Voice context"""
        try:
            print("🚀 Initializing Integrated Browser WAA...")
            
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-gpu',
                    '--disable-dev-shm-usage'
                ]
            )
            
            # Create context with cookies
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            
            # Add cookies
            cookie_objects = []
            for name, value in self.cookies.items():
                cookie_objects.append({
                    "name": name,
                    "value": value,
                    "domain": ".google.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": False,
                    "sameSite": "None"
                })
            await self.context.add_cookies(cookie_objects)
            
            # Navigate to Google Voice
            self.page = await self.context.new_page()
            await self.page.goto("https://voice.google.com/u/0/messages", wait_until="domcontentloaded")
            await asyncio.sleep(3)  # Let page fully load
            
            # Check if we're logged in
            logged_in = await self.page.evaluate("""
                document.querySelector('gv-web-inbox') !== null || 
                document.querySelector('[role="main"]') !== null
            """)
            
            if logged_in:
                print("✅ Logged into Google Voice successfully")
                self._initialized = True
                return True
            else:
                print("❌ Not logged in - check cookies")
                return False
                
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
    
    async def send_sms_via_ui(self, recipient: str, message: str) -> Dict[str, Any]:
        """Send SMS using Google Voice UI automation"""
        try:
            if not self._initialized:
                raise Exception("Browser not initialized")
            
            print(f"📱 Sending SMS to {recipient} via UI automation...")
            
            # Click new message button
            new_msg_selector = 'div[aria-label="Send a message"]'
            await self.page.wait_for_selector(new_msg_selector, timeout=5000)
            await self.page.click(new_msg_selector)
            await asyncio.sleep(1)
            
            # Enter recipient
            recipient_input = 'input[placeholder="Type a name or phone number"]'
            await self.page.wait_for_selector(recipient_input, timeout=5000)
            await self.page.fill(recipient_input, recipient)
            await asyncio.sleep(1)
            await self.page.keyboard.press('Enter')
            await asyncio.sleep(1)
            
            # Enter message
            message_input = 'div[aria-label="Type a message"]'
            await self.page.wait_for_selector(message_input, timeout=5000)
            await self.page.fill(message_input, message)
            await asyncio.sleep(1)
            
            # Send message
            send_button = 'button[aria-label="Send message"]'
            await self.page.wait_for_selector(send_button, timeout=5000)
            await self.page.click(send_button)
            
            print("✅ SMS sent via UI!")
            
            return {
                "success": True,
                "method": "ui_automation",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ UI automation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "ui_automation"
            }
    
    async def intercept_waa_calls(self) -> Optional[str]:
        """Intercept WAA signatures from actual Google Voice calls"""
        try:
            print("🔍 Setting up WAA interception...")
            
            # Intercept network requests
            intercepted_waa = None
            
            async def handle_route(route, request):
                nonlocal intercepted_waa
                url = request.url
                
                # Check if this is a WAA-related request
                if "waa" in url.lower() or "sendsms" in url:
                    headers = await request.all_headers()
                    post_data = request.post_data
                    
                    # Try to extract WAA signature from request
                    if post_data:
                        try:
                            data = json.loads(post_data)
                            # Look for signature in typical locations
                            if isinstance(data, list) and len(data) > 10:
                                potential_waa = data[10]  # WAA is often at index 10
                                if potential_waa and potential_waa != "!":
                                    intercepted_waa = potential_waa
                                    print(f"🎯 Intercepted WAA signature: {str(potential_waa)[:50]}...")
                        except:
                            pass
                
                # Continue request normally
                await route.continue_()
            
            # Setup interception
            await self.page.route("**/*", handle_route)
            
            # Trigger a real Google Voice action to capture WAA
            print("📞 Triggering Google Voice action...")
            
            # Try to interact with the page to generate WAA
            await self.page.evaluate("""
                // Try to access Google Voice's internal functions
                if (window.goog && window.goog.require) {
                    console.log('Google internal functions available');
                }
            """)
            
            await asyncio.sleep(2)
            
            # Remove interception
            await self.page.unroute("**/*")
            
            return intercepted_waa
            
        except Exception as e:
            print(f"❌ WAA interception failed: {e}")
            return None
    
    async def close(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"Warning: Cleanup error: {e}")


async def test_integrated_approach():
    """Test the integrated browser approach"""
    
    # Load cookies
    with open('fresh_cookies.json', 'r') as f:
        cookies = json.load(f)
    
    client = IntegratedBrowserWAA(cookies)
    
    try:
        print("="*60)
        print("🚀 TESTING INTEGRATED BROWSER WAA")
        print("="*60)
        
        if await client.initialize():
            # Try interception first
            waa_signature = await client.intercept_waa_calls()
            if waa_signature:
                print(f"✅ Got WAA signature: {waa_signature}")
            
            # Try UI automation as fallback
            print("\n📱 Testing UI automation approach...")
            result = await client.send_sms_via_ui(
                recipient="3602415033",
                message=f"Integrated test {datetime.now().strftime('%H:%M:%S')}"
            )
            
            print(f"\n📊 Result: {json.dumps(result, indent=2)}")
            
            if result.get("success"):
                print("\n🎉 SUCCESS! SMS SENT VIA INTEGRATED APPROACH!")
            
    finally:
        await client.close()
        print("🧹 Cleanup complete")


if __name__ == "__main__":
    asyncio.run(test_integrated_approach())