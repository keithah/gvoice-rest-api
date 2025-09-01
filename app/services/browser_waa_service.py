"""
Browser-based WAA service for Google Voice API
Integrates Playwright-based WAA signature generation with the main API
"""
import asyncio
import json
import time
import hashlib
import random
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
import httpx

from app.core.constants import (
    USER_AGENT, API_KEY, WAA_API_KEY, ORIGIN, API_DOMAIN,
    CLIENT_VERSION, JAVASCRIPT_USER_AGENT, CLIENT_DETAILS, ENDPOINTS
)


class BrowserWAAService:
    """Browser-based WAA signature service"""
    
    WAA_REQUEST_KEY = "/JR8jsAkqotcKsEKhXic"
    WAA_CREATE_URL = "https://waa-pa.clients6.google.com/$rpc/google.internal.waa.v1.Waa/Create"
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.waa_data = None
        self.waa_expiry = None
        self._initialized = False
    
    async def initialize(self, cookies: Dict[str, str]) -> bool:
        """Initialize browser environment for WAA"""
        try:
            if self._initialized:
                return True
                
            print("🚀 Initializing Browser WAA Service...")
            
            # Start Playwright
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-gpu',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            # Create context with Google Voice settings
            self.context = await self.browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1920, "height": 1080}
            )
            
            # Set cookies
            cookie_objects = []
            for name, value in cookies.items():
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
            
            # Create page and navigate to Google Voice
            self.page = await self.context.new_page()
            await self.page.goto("https://voice.google.com/u/0/", wait_until="domcontentloaded")
            await asyncio.sleep(2)  # Allow page to load
            
            self._initialized = True
            print("✅ Browser WAA Service initialized")
            return True
            
        except Exception as e:
            print(f"❌ Browser WAA initialization failed: {e}")
            await self.close()
            return False
    
    async def get_waa_data(self, cookies: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Get fresh WAA data from Google"""
        try:
            async with httpx.AsyncClient() as client:
                # Set cookies
                for name, value in cookies.items():
                    client.cookies.set(name, value, domain=".google.com")
                
                headers = {
                    "Authorization": self._generate_sapisid_hash(cookies.get("SAPISID", "")),
                    "X-Goog-Api-Key": WAA_API_KEY,
                    "X-User-Agent": "grpc-web-javascript/0.1",
                    "Content-Type": "application/json+protobuf",
                    "Origin": ORIGIN,
                    "Referer": f"{ORIGIN}/"
                }
                
                response = await client.post(
                    self.WAA_CREATE_URL,
                    content=json.dumps([self.WAA_REQUEST_KEY]),
                    headers=headers
                )
                
                if response.status_code == 200:
                    waa_response = response.json()
                    if waa_response and len(waa_response) > 0:
                        resp_data = waa_response[0]
                        return {
                            'interpreter_url': resp_data[3][3] if len(resp_data) > 3 and len(resp_data[3]) > 3 else None,
                            'program': resp_data[5] if len(resp_data) > 5 else None,
                            'global_name': resp_data[6] if len(resp_data) > 6 else None
                        }
                return None
                
        except Exception as e:
            print(f"❌ WAA data request failed: {e}")
            return None
    
    async def generate_signature(self, cookies: Dict[str, str], thread_id: str, recipients: list, transaction_id: int) -> Optional[str]:
        """Generate WAA signature using browser execution"""
        try:
            # Ensure browser is initialized
            if not self._initialized:
                if not await self.initialize(cookies):
                    return None
            
            # Get fresh WAA data if needed
            if not self.waa_data or (self.waa_expiry and datetime.now() > self.waa_expiry):
                self.waa_data = await self.get_waa_data(cookies)
                if not self.waa_data:
                    return None
                
                # Load WAA script
                if not await self._load_waa_script():
                    return None
                
                self.waa_expiry = datetime.now() + timedelta(hours=1)
            
            # Create signature payload
            payload_data = {
                "thread_id": thread_id,
                "recipients": recipients,
                "transaction_id": transaction_id,
                "timestamp": int(time.time())
            }
            
            # Execute WAA in browser
            signature = await self.page.evaluate(f"""
                new Promise((resolve, reject) => {{
                    try {{
                        const payload = {json.dumps(payload_data)};
                        const program = {json.dumps(self.waa_data['program'])};
                        const globalName = '{self.waa_data['global_name']}';
                        
                        if (typeof window[globalName] === 'undefined') {{
                            reject(new Error('WAA function not available'));
                            return;
                        }}
                        
                        window[globalName].a(program, (fn1, fn2, fn3, fn4) => {{
                            fn1(result => {{
                                resolve(result);
                            }}, [payload]);
                        }}, true, undefined, () => {{}});
                        
                    }} catch (error) {{
                        reject(error);
                    }}
                }})
            """)
            
            return str(signature) if signature else None
            
        except Exception as e:
            print(f"❌ Browser WAA signature generation failed: {e}")
            return None
    
    async def _load_waa_script(self) -> bool:
        """Load Google's WAA script in browser"""
        try:
            if not self.waa_data or not self.page:
                return False
                
            interpreter_url = self.waa_data['interpreter_url']
            if interpreter_url.startswith('//'):
                interpreter_url = 'https:' + interpreter_url
            
            # Load script
            loaded = await self.page.evaluate(f"""
                new Promise((resolve, reject) => {{
                    const script = document.createElement('script');
                    script.src = '{interpreter_url}';
                    script.onload = () => resolve(true);
                    script.onerror = () => reject(new Error('Script load failed'));
                    document.head.appendChild(script);
                }})
            """)
            
            if loaded:
                await asyncio.sleep(2)  # Allow script initialization
                
                # Verify function is available
                global_name = self.waa_data['global_name']
                available = await self.page.evaluate(f"""
                    typeof window['{global_name}'] !== 'undefined'
                """)
                
                return available
            return False
            
        except Exception as e:
            print(f"❌ WAA script loading failed: {e}")
            return False
    
    def _generate_sapisid_hash(self, sapisid: str) -> str:
        """Generate SAPISID hash for authorization"""
        timestamp = int(time.time())
        hash_input = f"{timestamp} {sapisid} {ORIGIN}"
        hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
        return f"SAPISIDHASH {timestamp}_{hash_value}"
    
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
            print(f"Warning: Browser cleanup error: {e}")
        finally:
            self._initialized = False


class EnhancedGVoiceClient:
    """Google Voice client with browser-based WAA support"""
    
    def __init__(self, cookies: Dict[str, str]):
        self.cookies = cookies
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.waa_service = BrowserWAAService()
        
        # Set cookies in HTTP client
        for name, value in cookies.items():
            self.http_client.cookies.set(name, value, domain=".google.com")
    
    async def initialize(self) -> bool:
        """Initialize the enhanced client with browser WAA"""
        return await self.waa_service.initialize(self.cookies)
    
    async def send_sms(self, recipient: str, message: str, thread_id: str = "") -> Dict[str, Any]:
        """Send SMS with browser-generated WAA signature"""
        try:
            transaction_id = random.randint(1, 99999999999999)
            recipients = [recipient]
            
            # Generate authentic WAA signature
            signature = await self.waa_service.generate_signature(
                self.cookies, thread_id or "new_conversation", recipients, transaction_id
            )
            
            if not signature:
                print("⚠️ Using fallback signature")
                signature = "!"
            
            # Prepare SMS request
            headers = {
                "Authorization": self._generate_sapisid_hash(),
                "X-Goog-Api-Key": API_KEY,
                "X-Client-Version": CLIENT_VERSION,
                "Content-Type": "application/json+protobuf",
                "Origin": ORIGIN,
                "Referer": f"{ORIGIN}/"
            }
            
            params = {"key": API_KEY, "alt": "proto"}
            
            # SMS body in PBLite format
            body = json.dumps([
                None, None, None, None,
                message,
                thread_id or None,
                recipients,
                None,
                [transaction_id],
                None,
                [signature]
            ])
            
            response = await self.http_client.post(
                ENDPOINTS["send_sms"],
                params=params,
                headers=headers,
                content=body
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "signature_type": "BROWSER" if signature != "!" else "FALLBACK"
                }
            else:
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_sapisid_hash(self) -> str:
        """Generate SAPISID hash"""
        timestamp = int(time.time())
        sapisid = self.cookies.get("SAPISID", "")
        hash_input = f"{timestamp} {sapisid} {ORIGIN}"
        hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
        return f"SAPISIDHASH {timestamp}_{hash_value}"
    
    async def close(self):
        """Clean up resources"""
        await self.waa_service.close()
        await self.http_client.aclose()