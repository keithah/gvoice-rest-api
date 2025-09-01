#!/usr/bin/env python3
"""
Browser-based WAA Implementation
Mimics mautrix-gvoice's Electron approach using Playwright to execute Google's actual JavaScript
"""
import asyncio
import json
import time
import base64
import hashlib
import random
import httpx
from playwright.async_api import async_playwright
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

# Constants
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
ORIGIN = "https://voice.google.com"
CLIENT_VERSION = "665865172"


class BrowserWAAClient:
    """Authentic WAA signature generation using browser automation"""
    
    WAA_API_KEY = "AIzaSyBGb5fGAyC-pRcRU6MUHb__b_vKha71HRE"
    WAA_REQUEST_KEY = "/JR8jsAkqotcKsEKhXic"
    WAA_CREATE_URL = "https://waa-pa.clients6.google.com/$rpc/google.internal.waa.v1.Waa/Create"
    SMS_ENDPOINT = "https://clients6.google.com/voice/v1/voiceclient/api2thread/sendsms"
    
    def __init__(self, cookies: Dict[str, str]):
        self.cookies = cookies
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.http_client = None
        self.waa_data = None
        self.waa_expiry = None
        
    async def initialize(self) -> bool:
        """Initialize browser environment and WAA system"""
        try:
            print("🚀 Initializing Browser WAA Client...")
            
            # Setup HTTP client with cookies
            self.http_client = httpx.AsyncClient(timeout=30.0)
            for name, value in self.cookies.items():
                self.http_client.cookies.set(name, value, domain=".google.com")
            
            # Start browser
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,  # Headless mode for server environment
                args=[
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-gpu'
                ]
            )
            
            # Create context with proper user agent and viewport
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                java_script_enabled=True
            )
            
            # Set cookies in browser
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
            
            # Create page and navigate to Google Voice
            self.page = await self.context.new_page()
            print("🌐 Navigating to Google Voice...")
            await self.page.goto("https://voice.google.com/u/0/", wait_until="domcontentloaded")
            await asyncio.sleep(3)  # Allow page to fully load
            
            print("✅ Browser environment ready")
            return True
            
        except Exception as e:
            print(f"❌ Browser initialization failed: {e}")
            await self.close()
            return False
    
    async def _get_fresh_waa_data(self) -> Optional[Dict[str, Any]]:
        """Get fresh WAA data from Google's service"""
        try:
            print("📋 Requesting fresh WAA data from Google...")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Authorization": self._generate_sapisid_hash(),
                "X-Goog-Api-Key": self.WAA_API_KEY,
                "X-User-Agent": "grpc-web-javascript/0.1",
                "Content-Type": "application/json+protobuf",
                "Origin": "https://voice.google.com",
                "Referer": "https://voice.google.com/"
            }
            
            request_data = json.dumps([self.WAA_REQUEST_KEY])
            
            response = await self.http_client.post(
                self.WAA_CREATE_URL,
                content=request_data,
                headers=headers
            )
            
            if response.status_code == 200:
                waa_response = response.json()
                print(f"✅ WAA data received: {len(str(waa_response))} chars")
                
                # Parse Google's PBLite response format
                if waa_response and len(waa_response) > 0:
                    resp_data = waa_response[0]
                    print(f"🔍 WAA response structure: {[type(x).__name__ if x is not None else 'None' for x in resp_data[:10]]}")
                    
                    # Handle nested array structure - find interpreter URL
                    interpreter_url = None
                    if len(resp_data) > 2 and isinstance(resp_data[2], list) and len(resp_data[2]) > 0:
                        # WAA response format: [id, None, [..., ..., ..., interpreter_url], hash, program, global_name, ...]
                        nested_data = resp_data[2]
                        if len(nested_data) > 3 and isinstance(nested_data[3], str):
                            interpreter_url = nested_data[3]
                        else:
                            # Search for URL pattern
                            for item in nested_data:
                                if isinstance(item, str) and ("/js/bg/" in item or item.startswith("//")):
                                    interpreter_url = item
                                    break
                    
                    # Extract other fields
                    interpreter_hash = resp_data[3] if len(resp_data) > 3 and isinstance(resp_data[3], str) else None
                    program = resp_data[4] if len(resp_data) > 4 else None
                    global_name = resp_data[5] if len(resp_data) > 5 else None
                    
                    print(f"📦 Extracted WAA data:")
                    print(f"   URL: {interpreter_url}")
                    print(f"   Global: {global_name}")
                    print(f"   Hash: {interpreter_hash[:20]}..." if interpreter_hash else "   Hash: None")
                    
                    return {
                        'interpreter_url': interpreter_url,
                        'interpreter_hash': interpreter_hash,
                        'program': program,
                        'global_name': global_name,
                        'extra_data': resp_data[7] if len(resp_data) > 7 else None
                    }
                else:
                    raise Exception("Invalid WAA response format")
            else:
                raise Exception(f"WAA request failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ WAA data request failed: {e}")
            return None
    
    async def _load_waa_interpreter(self, waa_data: Dict[str, Any]) -> bool:
        """Load Google's WAA interpreter script in browser"""
        try:
            interpreter_url = waa_data['interpreter_url']
            if interpreter_url.startswith('//'):
                interpreter_url = 'https:' + interpreter_url
            
            print(f"📜 Loading WAA interpreter from: {interpreter_url}")
            
            # Load the interpreter script
            script_loaded = await self.page.evaluate(f"""
                new Promise((resolve, reject) => {{
                    const script = document.createElement('script');
                    script.src = '{interpreter_url}';
                    script.type = 'text/javascript';
                    script.crossOrigin = 'anonymous';
                    
                    script.onload = () => {{
                        console.log('WAA interpreter loaded');
                        resolve(true);
                    }};
                    
                    script.onerror = (err) => {{
                        console.error('Failed to load WAA script:', err);
                        reject(new Error('Script load failed'));
                    }};
                    
                    document.head.appendChild(script);
                }})
            """)
            
            if script_loaded:
                await asyncio.sleep(2)  # Allow script to initialize
                
                # Verify the global WAA function is available
                global_name = waa_data['global_name']
                function_exists = await self.page.evaluate(f"""
                    typeof window['{global_name}'] !== 'undefined' && 
                    typeof window['{global_name}'].a === 'function'
                """)
                
                if function_exists:
                    print(f"✅ WAA function '{global_name}' ready")
                    return True
                else:
                    print(f"❌ WAA function '{global_name}' not found after load")
                    return False
            else:
                print("❌ Failed to load WAA interpreter")
                return False
                
        except Exception as e:
            print(f"❌ WAA interpreter loading failed: {e}")
            return False
    
    async def generate_signature(self, message_data: Dict[str, Any]) -> Optional[str]:
        """Generate authentic WAA signature for SMS sending"""
        try:
            # Check if we need fresh WAA data
            if not self.waa_data or (self.waa_expiry and datetime.now() > self.waa_expiry):
                print("🔄 Getting fresh WAA data...")
                self.waa_data = await self._get_fresh_waa_data()
                if not self.waa_data:
                    return None
                
                # Load fresh interpreter
                if not await self._load_waa_interpreter(self.waa_data):
                    return None
                
                self.waa_expiry = datetime.now() + timedelta(hours=1)
            
            # Prepare signature payload based on mautrix-gvoice format
            thread_id = message_data.get('thread_id', 'new_conversation')
            recipients = message_data.get('recipients', [])
            transaction_id = message_data.get('transaction_id', random.randint(1, 99999999999999))
            
            # Create payload hash similar to mautrix-gvoice
            payload_string = f"{thread_id}|{','.join(recipients)}|{transaction_id}"
            payload_hash = hashlib.sha256(payload_string.encode()).hexdigest()
            
            signature_payload = {
                "thread_context": thread_id,
                "destinations": recipients,
                "transaction_id": transaction_id,
                "payload_hash": payload_hash,
                "timestamp": int(time.time())
            }
            
            print(f"🔐 Generating signature for: {payload_string}")
            
            # Execute Google's WAA program in browser context
            program = self.waa_data['program']
            global_name = self.waa_data['global_name']
            
            signature = await self.page.evaluate(f"""
                new Promise((resolve, reject) => {{
                    try {{
                        const payload = {json.dumps(signature_payload)};
                        const program = {json.dumps(program)};
                        
                        console.log('Executing WAA program with payload:', payload);
                        
                        // Execute WAA exactly like mautrix-gvoice
                        window['{global_name}'].a(program, (fn1, fn2, fn3, fn4) => {{
                            console.log('WAA functions received');
                            
                            // Call signature generation function
                            fn1(result => {{
                                console.log('WAA signature result:', result);
                                resolve(result);
                            }}, [payload]);
                            
                        }}, true, undefined, () => {{}});
                        
                    }} catch (error) {{
                        console.error('WAA execution error:', error);
                        reject(error);
                    }}
                }})
            """)
            
            if signature:
                print(f"✅ Generated authentic WAA signature")
                return str(signature)
            else:
                print("❌ No signature returned from WAA")
                return None
                
        except Exception as e:
            print(f"❌ Signature generation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def send_sms_with_real_waa(self, recipient: str, message: str, thread_id: str = "") -> Dict[str, Any]:
        """Send SMS using authentic browser-generated WAA signature"""
        try:
            print(f"📱 Sending SMS to {recipient}: {message[:50]}...")
            
            transaction_id = random.randint(1, 99999999999999)
            recipients = [recipient]
            
            # Generate authentic WAA signature
            message_data = {
                'thread_id': thread_id or 'new_conversation',
                'recipients': recipients,
                'transaction_id': transaction_id
            }
            
            signature = await self.generate_signature(message_data)
            if not signature:
                print("⚠️ Failed to generate signature - SMS will likely fail")
                signature = "!"  # Fallback
            
            # Send SMS with generated signature
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Authorization": self._generate_sapisid_hash(),
                "X-Goog-Api-Key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
                "X-Client-Version": "665865172",
                "Content-Type": "application/json+protobuf",
                "Origin": "https://voice.google.com",
                "Referer": "https://voice.google.com/",
                "X-Requested-With": "XMLHttpRequest"
            }
            
            params = {"key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg", "alt": "proto"}
            
            # Build SMS request body
            body = json.dumps([
                None, None, None, None,     # fields 1-4
                message,                    # field 5: message text
                thread_id or None,          # field 6: thread ID
                recipients,                 # field 7: recipients
                None,                       # field 8
                [transaction_id],           # field 9: transaction ID
                None,                       # field 10: media
                [signature]                 # field 11: WAA signature
            ])
            
            print(f"🚀 Sending SMS with signature type: {'AUTHENTIC' if signature != '!' else 'FALLBACK'}")
            
            response = await self.http_client.post(
                self.SMS_ENDPOINT,
                params=params,
                headers=headers,
                content=body
            )
            
            print(f"📤 SMS Response: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SMS sent successfully!")
                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "signature_type": "AUTHENTIC" if signature != "!" else "FALLBACK",
                    "response_code": response.status_code
                }
            else:
                error_text = response.text
                print(f"❌ SMS failed: {error_text}")
                return {
                    "success": False,
                    "error": error_text,
                    "status_code": response.status_code,
                    "signature_type": "AUTHENTIC" if signature != "!" else "FALLBACK"
                }
                
        except Exception as e:
            print(f"❌ SMS send error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_conversations(self) -> Dict[str, Any]:
        """Get conversation threads"""
        try:
            # Use POST request for list endpoint as per mautrix-gvoice
            url = "https://clients6.google.com/voice/v1/voiceclient/api2thread/list"
            headers = {
                "User-Agent": USER_AGENT,
                "Authorization": self._generate_sapisid_hash(),
                "X-Goog-Api-Key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
                "X-Client-Version": CLIENT_VERSION,
                "X-ClientDetails": "appVersion=5.0%20%28X11%29&platform=Linux%20x86_64&userAgent=Mozilla%2F5.0%20%28X11%3B%20Linux%20x86_64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F128.0.0.0%20Safari%2F537.36",
                "X-JavaScript-User-Agent": "google-api-javascript-client/1.1.0",
                "X-Requested-With": "XMLHttpRequest",
                "X-Goog-Encode-Response-If-Executable": "base64",
                "Content-Type": "application/json+protobuf",
                "Origin": ORIGIN,
                "Referer": f"{ORIGIN}/",
                "X-Goog-AuthUser": "0"
            }
            params = {"key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg", "alt": "proto"}
            
            # Send empty body for list request
            body = json.dumps([1, 20, 15, "", {"unknownInt2": 1, "unknownInt3": 1}])
            
            response = await self.http_client.post(url, params=params, headers=headers, content=body)
            
            if response.status_code == 200:
                return {"success": True, "conversations": response.json()}
            else:
                return {"success": False, "error": response.text, "status_code": response.status_code}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def update_cookies_from_browser(self) -> Dict[str, str]:
        """Extract updated cookies from browser session"""
        try:
            if not self.context:
                return self.cookies
                
            # Get all cookies from browser
            browser_cookies = await self.context.cookies()
            updated_cookies = {}
            
            for cookie in browser_cookies:
                if cookie['domain'] in ['.google.com', 'google.com', 'voice.google.com']:
                    updated_cookies[cookie['name']] = cookie['value']
            
            print(f"🍪 Updated {len(updated_cookies)} cookies from browser")
            return updated_cookies
            
        except Exception as e:
            print(f"❌ Cookie extraction failed: {e}")
            return self.cookies
    
    def _generate_sapisid_hash(self) -> str:
        """Generate SAPISID hash for Google authentication"""
        timestamp = int(time.time())
        origin = "https://voice.google.com"
        sapisid = self.cookies.get("SAPISID", "")
        hash_input = f"{timestamp} {sapisid} {origin}"
        hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
        return f"SAPISIDHASH {timestamp}_{hash_value}"
    
    async def close(self):
        """Clean up all resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            if self.http_client:
                await self.http_client.aclose()
        except Exception as e:
            print(f"Warning: Cleanup error: {e}")


# Test implementation
if __name__ == "__main__":
    async def test_browser_waa():
        # Fresh cookies from browser session
        cookies = {
            "__Secure-1PAPISID": "25lYAoz2nuYlET9F/AcjU6q-M05xhf3m9i",
            "__Secure-1PSID": "g.a0000gidohBL8Q_snp6HMg63YVDyWOWbGBrYz7j7TXhgSbuI49nmAbB8VKbKplnaIymVYBlV8wACgYKAUkSARcSFQHGX2MiQv1kJWiUk5F0QRdI6_IedxoVAUF8yKrQ76TWi2LQ6-ZHQMloEJmP0076",
            "__Secure-1PSIDCC": "AKEyXzWsQ8cabGhRaoeIDVpyb9dxSWX6bj-ZwlgfWA4fIE6CsyDOjTCAMX_Prruzk1QSKT6a0Q",
            "SAPISID": "25lYAoz2nuYlET9F/AcjU6q-M05xhf3m9i",
            "SID": "g.a0000gidohBL8Q_snp6HMg63YVDyWOWbGBrYz7j7TXhgSbuI49nmX_PepglISToJC89AUwJa8QACgYKARkSARcSFQHGX2Mi6x-LNWKt0nQtLoJNvV_mIRoVAUF8yKqDXkxRyUDrvH9sPFT3fFq00076"
        }
        
        client = BrowserWAAClient(cookies)
        
        try:
            print("=" * 70)
            print("🚀 TESTING BROWSER-BASED WAA SMS SYSTEM 🚀")
            print("=" * 70)
            
            # Initialize browser WAA system
            if await client.initialize():
                print("\n📞 Testing conversation retrieval...")
                conversations = await client.get_conversations()
                if conversations.get("success"):
                    print("✅ Conversations retrieved successfully")
                else:
                    print(f"❌ Conversations failed: {conversations.get('error')}")
                
                print("\n📱 Testing SMS with browser WAA...")
                result = await client.send_sms_with_real_waa(
                    recipient="3602415033",
                    message=f"🔥 Browser WAA test at {datetime.now().strftime('%H:%M:%S')}"
                )
                
                print(f"\n📊 Final SMS Result:")
                print(json.dumps(result, indent=2))
                
                if result.get("success"):
                    print("\n🎉🎉🎉 SUCCESS! BROWSER WAA WORKED! 🎉🎉🎉")
                else:
                    print(f"\n❌ SMS failed: {result.get('error')}")
                
                # Get updated cookies
                print("\n🍪 Extracting updated cookies...")
                updated_cookies = await client.update_cookies_from_browser()
                print(f"Updated {len(updated_cookies)} cookies")
                
            else:
                print("❌ Failed to initialize browser WAA system")
                
        finally:
            await client.close()
            print("🧹 Cleanup completed")
    
    asyncio.run(test_browser_waa())