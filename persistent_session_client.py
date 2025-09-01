#!/usr/bin/env python3
"""
Persistent Google Voice session client that maintains long-lived sessions
by automatically updating cookies from API responses like mautrix-gvoice
"""
import asyncio
import json
import time
import base64
import hashlib
import random
import httpx
from playwright.async_api import async_playwright
from typing import Optional, Dict, Any, Set
from datetime import datetime
import threading
import pickle
from pathlib import Path

class PersistentGoogleVoiceSession:
    """Maintains long-lived Google Voice sessions with automatic cookie management"""
    
    WAA_API_KEY = "AIzaSyBGb5fGAyC-pRcRU6MUHb__b_vKha71HRE"
    WAA_REQUEST_KEY = "/JR8jsAkqotcKsEKhXic"
    WAA_CREATE_URL = "https://waa-pa.clients6.google.com/$rpc/google.internal.waa.v1.Waa/Create"
    WAA_EXPIRY_HOURS = 1
    
    # Cookies to ignore for change detection (like mautrix-gvoice)
    IGNORED_COOKIES = {"__Secure-1PSIDCC", "__Secure-3PSIDCC", "SIDCC"}
    
    def __init__(self, initial_cookies: Dict[str, str], storage_path: str = "session_data.pkl"):
        self.cookies = initial_cookies.copy()
        self.storage_path = Path(storage_path)
        self.http_client = None
        self.playwright = None
        self.browser = None
        self.page = None
        self.waa_data = None
        self.initialized_at = None
        self.cookies_changed = False
        self.session_lock = threading.Lock()
        
        # Load saved session if exists
        self._load_session()
        
    def _load_session(self):
        """Load saved session data"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'rb') as f:
                    saved_data = pickle.load(f)
                    self.cookies.update(saved_data.get('cookies', {}))
                    print(f"📁 Loaded saved session with {len(self.cookies)} cookies")
        except Exception as e:
            print(f"⚠️ Could not load saved session: {e}")
            
    def _save_session(self):
        """Save session data for persistence"""
        try:
            session_data = {
                'cookies': self.cookies,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.storage_path, 'wb') as f:
                pickle.dump(session_data, f)
            print(f"💾 Session saved with {len(self.cookies)} cookies")
        except Exception as e:
            print(f"⚠️ Could not save session: {e}")
            
    def _update_cookies_from_response(self, response: httpx.Response) -> bool:
        """Update cookies from HTTP response like mautrix-gvoice does"""
        if not hasattr(response, 'cookies') or not response.cookies:
            return False
            
        with self.session_lock:
            cookies_changed = False
            
            for cookie_name, cookie_value in response.cookies.items():
                # Skip expired cookies
                cookie_obj = response.cookies.get(cookie_name)
                if hasattr(cookie_obj, 'expires') and cookie_obj.expires:
                    if cookie_obj.expires < time.time():
                        if cookie_name in self.cookies:
                            del self.cookies[cookie_name]
                            cookies_changed = True
                        continue
                
                # Update if changed
                if self.cookies.get(cookie_name) != cookie_value:
                    self.cookies[cookie_name] = cookie_value
                    # Only mark as changed for important cookies (ignore noise)
                    if cookie_name not in self.IGNORED_COOKIES:
                        cookies_changed = True
                        print(f"🔄 Cookie updated: {cookie_name}")
            
            if cookies_changed:
                self.cookies_changed = True
                self._save_session()
                
            return cookies_changed
            
    async def _setup_http_client(self):
        """Setup HTTP client with current cookies"""
        if self.http_client:
            await self.http_client.aclose()
            
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Set all current cookies
        for name, value in self.cookies.items():
            self.http_client.cookies.set(name, value, domain=".google.com")
            
    async def _make_authenticated_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make authenticated request and automatically update cookies"""
        if not self.http_client:
            await self._setup_http_client()
            
        response = await self.http_client.request(method, url, **kwargs)
        
        # Automatically update cookies from response
        self._update_cookies_from_response(response)
        
        return response
        
    async def initialize_session(self) -> bool:
        """Initialize persistent session with automatic cookie management"""
        try:
            print("🔧 Initializing persistent Google Voice session...")
            
            await self._setup_http_client()
            
            # Test authentication with account endpoint
            print("🔍 Testing authentication...")
            account_result = await self._test_authentication()
            
            if not account_result:
                print("❌ Authentication failed with current cookies")
                return False
                
            print("✅ Authentication successful")
            
            # Initialize WAA system
            print("📋 Initializing WAA system...")
            waa_result = await self._initialize_waa()
            
            if waa_result:
                print("✅ Persistent session initialized successfully!")
                return True
            else:
                print("⚠️ WAA initialization failed, but basic auth works")
                return True  # Can still work without WAA
                
        except Exception as e:
            print(f"❌ Session initialization failed: {e}")
            return False
            
    async def _test_authentication(self) -> bool:
        """Test authentication and update cookies"""
        try:
            url = "https://clients6.google.com/voice/v1/voiceclient/account/get"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Authorization": self._generate_sapisid_hash(),
                "X-Client-Version": "665865172",
                "X-Goog-AuthUser": "0",
                "Content-Type": "application/json+protobuf",
                "Origin": "https://voice.google.com",
                "Referer": "https://voice.google.com/",
                "Accept": "*/*"
            }
            
            params = {
                "key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
                "alt": "proto"
            }
            
            body = json.dumps([None, 1])
            
            response = await self._make_authenticated_request(
                "POST", url, params=params, headers=headers, content=body
            )
            
            print(f"Auth test result: {response.status_code}")
            return response.status_code == 200
            
        except Exception as e:
            print(f"❌ Auth test failed: {e}")
            return False
            
    async def _initialize_waa(self) -> bool:
        """Initialize WAA system"""
        try:
            # Create WAA payload
            self.waa_data = await self._create_waa_payload()
            if not self.waa_data:
                return False
                
            # Setup browser for WAA
            if await self._setup_waa_browser():
                self.initialized_at = datetime.now()
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ WAA initialization error: {e}")
            return False
            
    async def _create_waa_payload(self) -> Optional[Dict[str, Any]]:
        """Create WAA payload and update cookies"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Authorization": self._generate_sapisid_hash(),
                "X-Goog-Api-Key": self.WAA_API_KEY,
                "X-User-Agent": "grpc-web-javascript/0.1",
                "Content-Type": "application/json+protobuf",
                "Origin": "https://voice.google.com",
                "Referer": "https://voice.google.com/",
                "Accept": "*/*"
            }
            
            request_data = json.dumps([self.WAA_REQUEST_KEY])
            
            response = await self._make_authenticated_request(
                "POST", self.WAA_CREATE_URL, content=request_data, headers=headers
            )
            
            if response.status_code == 200:
                waa_data = response.json()
                
                if len(waa_data) > 1 and len(waa_data[1]) > 6:
                    interpreter_url = waa_data[1][3][4] if len(waa_data[1][3]) > 4 else None
                    
                    return {
                        'resp_id': waa_data[1][1] if len(waa_data[1]) > 1 else None,
                        'interpreter_url': interpreter_url,
                        'interpreter_hash': waa_data[1][4] if len(waa_data[1]) > 4 else None,
                        'program': waa_data[1][5] if len(waa_data[1]) > 5 else None,
                        'global_name': waa_data[1][6] if len(waa_data[1]) > 6 else None
                    }
                else:
                    raise Exception(f"Unexpected WAA response format: {waa_data}")
            else:
                print(f"⚠️ WAA creation failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ WAA creation error: {e}")
            return None
            
    async def _setup_waa_browser(self) -> bool:
        """Setup browser for WAA signature generation"""
        try:
            if not self.waa_data or not self.waa_data.get('interpreter_url'):
                return False
                
            # Start Playwright
            self.playwright = await async_playwright().start()
            
            # Launch browser
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )
            
            # Create context with cookies
            context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            )
            
            # Set cookies
            cookie_objects = []
            for name, value in self.cookies.items():
                cookie_objects.append({
                    "name": name,
                    "value": value,
                    "domain": ".google.com",
                    "path": "/"
                })
            await context.add_cookies(cookie_objects)
            
            self.page = await context.new_page()
            
            # Navigate to Google Voice
            await self.page.goto("https://voice.google.com/u/0/about", 
                                wait_until="domcontentloaded", 
                                timeout=30000)
            
            # Load WAA script
            script_url = self.waa_data['interpreter_url']
            if script_url.startswith('//'):
                script_url = 'https:' + script_url
                
            success = await self.page.evaluate(f"""
                new Promise((resolve, reject) => {{
                    const script = document.createElement('script');
                    script.src = '{script_url}';
                    script.onload = () => resolve(true);
                    script.onerror = () => resolve(false);
                    document.head.appendChild(script);
                }})
            """)
            
            if success:
                await asyncio.sleep(2)
                global_name = self.waa_data.get('global_name', '')
                function_available = await self.page.evaluate(f"typeof window['{global_name}'] !== 'undefined'")
                
                if function_available:
                    print("✅ WAA browser system ready")
                    return True
                    
            return False
            
        except Exception as e:
            print(f"❌ WAA browser setup failed: {e}")
            return False
            
    async def send_sms_with_persistent_session(self, recipient: str, message: str, thread_id: str = "") -> Dict[str, Any]:
        """Send SMS with automatic session management"""
        try:
            print(f"📱 Sending SMS to {recipient}: {message}")
            
            # Check if WAA needs refresh
            if self.waa_data and self.initialized_at:
                elapsed_hours = (datetime.now() - self.initialized_at).total_seconds() / 3600
                if elapsed_hours > self.WAA_EXPIRY_HOURS:
                    print("⏰ WAA expired, refreshing...")
                    await self._initialize_waa()
            
            # Generate transaction ID
            transaction_id = random.randint(1, 99999999999999)
            recipients = [recipient]
            
            # Generate signature (real if WAA available, fallback otherwise)
            signature = await self._generate_signature(thread_id or "new_conversation", recipients, transaction_id)
            
            # Send SMS
            url = "https://clients6.google.com/voice/v1/voiceclient/api2thread/sendsms"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Authorization": self._generate_sapisid_hash(),
                "X-Client-Version": "665865172",
                "X-Goog-AuthUser": "0",
                "Content-Type": "application/json+protobuf",
                "Origin": "https://voice.google.com",
                "Referer": "https://voice.google.com/",
                "Accept": "*/*"
            }
            
            params = {
                "key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
                "alt": "proto"
            }
            
            body = json.dumps([
                None, None, None, None,  # fields 1-4
                message,                 # field 5: text
                thread_id or None,       # field 6: threadID
                recipients,              # field 7: recipients  
                None,                    # field 8
                [transaction_id],        # field 9: transactionID
                None,                    # field 10: media
                [signature]              # field 11: trackingData
            ])
            
            print(f"🚀 Sending SMS with persistent session...")
            
            response = await self._make_authenticated_request(
                "POST", url, params=params, headers=headers, content=body
            )
            
            print(f"📤 SMS Response: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SMS sent successfully with persistent session!")
                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "response_length": len(response.content),
                    "cookies_updated": self.cookies_changed,
                    "signature_type": "WAA" if self.waa_data else "fallback"
                }
            else:
                error_text = response.text
                print(f"❌ SMS failed: {error_text}")
                return {
                    "success": False,
                    "error": error_text,
                    "status_code": response.status_code,
                    "cookies_updated": self.cookies_changed
                }
                
        except Exception as e:
            print(f"❌ SMS send error: {e}")
            return {"success": False, "error": str(e)}
            
    async def _generate_signature(self, thread_id: str, recipients: list, transaction_id: int) -> str:
        """Generate signature (WAA if available, fallback otherwise)"""
        if self.page and self.waa_data:
            try:
                # Try real WAA signature
                thread_id_hash = hashlib.sha256(thread_id.encode()).digest()
                recipients_hash = hashlib.sha256("|".join(recipients).encode()).digest()
                message_id_hash = hashlib.sha256(str(transaction_id).encode()).digest()
                
                payload = {
                    "thread_id": base64.b64encode(thread_id_hash).decode(),
                    "destinations": base64.b64encode(recipients_hash).decode(),
                    "message_ids": base64.b64encode(message_id_hash).decode()
                }
                
                program = self.waa_data['program']
                global_name = self.waa_data['global_name']
                
                signature = await self.page.evaluate(f"""
                    new Promise((resolve, reject) => {{
                        try {{
                            const payload = {json.dumps(payload)};
                            const program = {json.dumps(program)};
                            
                            new Promise(resolve => {{
                                window['{global_name}'].a(program, (fn1, fn2, fn3, fn4) => {{
                                    resolve({{fn1, fn2, fn3, fn4}});
                                }}, true, undefined, () => {{}});
                            }}).then(fns => {{
                                fns.fn1(result => {{
                                    resolve(result);
                                }}, [payload, undefined, undefined, undefined]);
                            }}).catch(reject);
                        }} catch (error) {{
                            reject(error);
                        }}
                    }})
                """)
                
                if signature:
                    print("✅ Generated real WAA signature")
                    return str(signature)
                    
            except Exception as e:
                print(f"⚠️ WAA signature failed, using fallback: {e}")
        
        # Fallback signature
        return "!"
        
    def _generate_sapisid_hash(self) -> str:
        """Generate SAPISID hash"""
        timestamp = int(time.time())
        origin = "https://voice.google.com"
        sapisid = self.cookies.get("SAPISID", "")
        hash_input = f"{timestamp} {sapisid} {origin}"
        hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
        return f"SAPISIDHASH {timestamp}_{hash_value}"
        
    async def start_background_maintenance(self):
        """Start background session maintenance like mautrix-gvoice"""
        async def maintenance_loop():
            while True:
                try:
                    # Test authentication every 15 minutes
                    await asyncio.sleep(15 * 60)  # 15 minutes
                    
                    print("🔄 Running background session maintenance...")
                    auth_ok = await self._test_authentication()
                    
                    if not auth_ok:
                        print("⚠️ Authentication failed during maintenance")
                    else:
                        print("✅ Session maintenance successful")
                        
                except Exception as e:
                    print(f"❌ Background maintenance error: {e}")
                    
        # Start maintenance task
        asyncio.create_task(maintenance_loop())
        print("🔄 Background session maintenance started")
        
    async def close(self):
        """Clean up resources"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            if self.http_client:
                await self.http_client.aclose()
        except Exception as e:
            print(f"Warning: Error closing session: {e}")


# Test script
if __name__ == "__main__":
    async def main():
        # Initial cookies from user (these will be automatically updated)
        initial_cookies = {
            "__Secure-1PAPISID": "25lYAoz2nuYlET9F/AcjU6q-M05xhf3m9i",
            "__Secure-1PSID": "g.a0000gidohBL8Q_snp6HMg63YVDyWOWbGBrYz7j7TXhgSbuI49nmAbB8VKbKplnaIymVYBlV8wACgYKAUkSARcSFQHGX2MiQv1kJWiUk5F0QRdI6_IedxoVAUF8yKrQ76TWi2LQ6-ZHQMloEJmP0076",
            "__Secure-1PSIDCC": "AKEyXzVQZUb5Pun3fT4ZwFZ7Dy_WBBy2HuwT8f5_vt8oB6nRsZp6Dg6CzikM1dVt8-TTijmF",
            "__Secure-1PSIDTS": "sidts-CjIB5H03P3p5ycVr5ZtEkBoVXv7IVxjjXkHn9FGyi7jm7tE-_jndAn8iAF95wZh5Xw7V9hAA",
            "__Secure-3PAPISID": "25lYAoz2nuYlET9F/AcjU6q-M05xhf3m9i",
            "__Secure-3PSID": "g.a0000gidohBL8Q_snp6HMg63YVDyWOWbGBrYz7j7TXhgSbuI49nmptstfVG3sOuBex1won4fOAACgYKASQSARcSFQHGX2MitGTAfMcy05dsGQLPlBAr3RoVAUF8yKqbYCBU-BT9ONjIWNiQri-h0076",
            "__Secure-3PSIDCC": "AKEyXzUIjhXhqdjuoDQcP-Cj2o0EpPlfDJoUMjqZ51m6gVmIua_B-zb0yGO3daqq_qSBMfRA",
            "__Secure-3PSIDTS": "sidts-CjIB5H03P3p5ycVr5ZtEkBoVXv7IVxjjXkHn9FGyi7jm7tE-_jndAn8iAF95wZh5Xw7V9hAA",
            "__Secure-OSID": "g.a0000gidomf-Km8BaxbLZKsQno7wq4K3q3N0WabexlpDZxQ-737PlapNUkl3VcjwpXckZfrTigACgYKAbsSARcSFQHGX2MiBXLJQb4seMM4YY2dCEzn8BoVAUF8yKr2qyjdOzEybx8Kv8ZUb20w0076",
            "APISID": "mYg9dQYyHeuMPYVA/AbCTVr6KpbF8eNO2x",
            "COMPASS": "voice-web-frontend=CgAQ5JPCxQYaXgAJa4lXDPiI5XaP-nYDPAkZMqqZ94lMW8GB9vCUYYH7783Byrombw9404lBqdqnAPMLeOa6sgk0QkesAR38RSnvBylpC00zm2xIvr4P6a3Uy5A3wv8hAcBA5-nMngkwAQ",
            "HSID": "ApYXLRGykgAatLHFT",
            "OSID": "g.a0000gidomf-Km8BaxbLZKsQno7wq4K3q3N0WabexlpDZxQ-737P_NLRTpnlu9TbOdkWVIwQ9gACgYKAbwSARcSFQHGX2Mi2-8454Xc5-S2UMGkfrsaJxoVAUF8yKq0yUUJMWsNycV4MBJONjER0076",
            "S": "billing-ui-v3=c8vqT6pMKIM10h3hUSnnakj9Uc7Ievsp:billing-ui-v3-efe=c8vqT6pMKIM10h3hUSnnakj9Uc7Ievsp",
            "SAPISID": "25lYAoz2nuYlET9F/AcjU6q-M05xhf3m9i",
            "SID": "g.a0000gidohBL8Q_snp6HMg63YVDyWOWbGBrYz7j7TXhgSbuI49nmX_PepglISToJC89AUwJa8QACgYKARkSARcSFQHGX2Mi6x-LNWKt0nQtLoJNvV_mIRoVAUF8yKqDXkxRyUDrvH9sPFT3fFq00076",
            "SIDCC": "AKEyXzX5pSyjNTGRWoAB7kWjHYwUdGrBk9O_W8PqiYz400RZEI56yGvGyL7gs18ak9HsfhIfsA",
            "SSID": "Aqw-Nyw1IrW3jRYHx"
        }
        
        client = PersistentGoogleVoiceSession(initial_cookies)
        
        try:
            print("=" * 70)
            print("🚀 TESTING PERSISTENT SESSION SYSTEM 🚀")
            print("=" * 70)
            
            # Initialize persistent session
            if await client.initialize_session():
                
                # Start background maintenance
                await client.start_background_maintenance()
                
                # Send test SMS
                result = await client.send_sms_with_persistent_session(
                    recipient="3602415033", 
                    message=f"🎉 Persistent Session SMS Test at {datetime.now().strftime('%H:%M:%S')}"
                )
                print(f"\n📊 Final Result: {json.dumps(result, indent=2)}")
                
                if result.get("success"):
                    print("\n🎉🎉🎉 SUCCESS! SMS SENT WITH PERSISTENT SESSION! 🎉🎉🎉")
                    print("✅ Session will be maintained automatically")
                else:
                    print(f"\n❌ SMS failed: {result.get('error')}")
                    
            else:
                print("❌ Failed to initialize persistent session")
                
        finally:
            await client.close()
    
    asyncio.run(main())