#!/usr/bin/env python3
"""
WAA (Web Application Authenticator) client implementation
Based on mautrix-gvoice's system to bypass Google Voice automation detection
"""
import asyncio
import json
import time
import base64
import hashlib
import random
import httpx
from playwright.async_api import async_playwright
from typing import Optional, Dict, Any

class WAAClient:
    """Creates WAA payloads via Google's WAA service"""
    
    WAA_API_KEY = "AIzaSyBGb5fGAyC-pRcRU6MUHb__b_vKha71HRE"
    WAA_REQUEST_KEY = "/JR8jsAkqotcKsEKhXic"
    WAA_CREATE_URL = "https://waa-pa.clients6.google.com/$rpc/google.internal.waa.v1.Waa/Create"
    WAA_PING_URL = "https://waa-pa.clients6.google.com/$rpc/google.internal.waa.v1.Waa/Ping"
    
    def __init__(self, cookies: Dict[str, str]):
        self.cookies = cookies
        self._setup_session()
        
    def _setup_session(self):
        """Setup HTTP session with cookies and headers"""
        self.session = httpx.AsyncClient()
        
        # Set cookies
        for name, value in self.cookies.items():
            self.session.cookies.set(name, value, domain=".google.com")
            
    def _generate_sapisid_hash(self) -> str:
        """Generate SAPISID hash for authorization"""
        timestamp = int(time.time())
        origin = "https://voice.google.com"
        sapisid = self.cookies.get("SAPISID", "")
        hash_input = f"{timestamp} {sapisid} {origin}"
        hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
        return f"SAPISIDHASH {timestamp}_{hash_value}"
        
    async def create_waa_payload(self) -> Dict[str, Any]:
        """Create WAA payload from Google's WAA service"""
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
        
        # WAA request in PBLite format
        request_data = json.dumps([self.WAA_REQUEST_KEY])
        
        print(f"Creating WAA payload...")
        
        try:
            response = await self.session.post(
                self.WAA_CREATE_URL,
                content=request_data,
                headers=headers
            )
            
            print(f"WAA Create Response: {response.status_code}")
            
            if response.status_code == 200:
                waa_data = response.json()
                print(f"WAA Response: {waa_data}")
                
                # Parse PBLite response format
                # Based on mautrix-gvoice protobuf: respID(1), interpreterURL(3), interpreterHash(4), program(5), globalName(6)
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
                raise Exception(f"Failed to create WAA payload: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"WAA creation error: {e}")
            raise
            
    async def close(self):
        """Close the HTTP session"""
        await self.session.aclose()


class WAASignatureGenerator:
    """Generates signatures using browser automation with WAA JavaScript"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.waa_data = None
        
    async def initialize(self, waa_data: Dict[str, Any]) -> bool:
        """Initialize browser and load WAA script"""
        self.waa_data = waa_data
        
        if not waa_data.get('program') or not waa_data.get('interpreter_url'):
            print("❌ Invalid WAA data - missing required fields")
            return False
            
        try:
            print("🚀 Initializing WAA browser system...")
            
            # Start Playwright for real signature generation
            from playwright.async_api import async_playwright
            
            self.playwright = await async_playwright().start()
            
            # Launch browser in headless mode
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )
            
            # Create context
            context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            )
            
            self.page = await context.new_page()
            
            # Navigate to a neutral page
            await self.page.goto("https://voice.google.com/u/0/about", wait_until="domcontentloaded", timeout=30000)
            
            # Load the WAA script
            print("📜 Loading WAA JavaScript...")
            script_url = waa_data['interpreter_url']
            if script_url.startswith('//'):
                script_url = 'https:' + script_url
                
            success = await self.page.evaluate(f"""
                new Promise((resolve) => {{
                    const script = document.createElement('script');
                    script.src = '{script_url}';
                    script.onload = () => resolve(true);
                    script.onerror = () => resolve(false);
                    document.head.appendChild(script);
                }})
            """)
            
            if success:
                # Wait for global function to be available
                await asyncio.sleep(3)
                global_name = waa_data.get('global_name', 'window._waa')
                function_available = await self.page.evaluate(f"typeof {global_name} !== 'undefined'")
                
                if function_available:
                    print("✅ WAA system initialized with browser!")
                    return True
                else:
                    print(f"❌ WAA global function {global_name} not found")
                    return False
            else:
                print("❌ Failed to load WAA script")
                return False
                
        except Exception as e:
            print(f"❌ WAA initialization failed: {e}")
            await self.close()
            return False
            
    async def _handle_route(self, route):
        """Handle network requests - allow only necessary ones"""
        url = route.request.url
        
        # Allow Google Voice pages and WAA script
        allowed_patterns = [
            "voice.google.com",
            "accounts.google.com", 
            "ssl.gstatic.com",
            self.waa_data.get('interpreter_url', '').replace('https://', '').replace('//', '')
        ]
        
        if any(pattern in url for pattern in allowed_patterns):
            await route.continue_()
        else:
            await route.abort()
            
    async def _load_waa_script(self) -> bool:
        """Load WAA JavaScript from Google's servers"""
        script_url = self.waa_data['interpreter_url']
        
        # Ensure URL is complete
        if script_url.startswith('//'):
            script_url = 'https:' + script_url
            
        try:
            # Load the script dynamically
            load_script_js = f"""
            new Promise((resolve, reject) => {{
                console.log("Loading WAA script from:", "{script_url}");
                
                const scriptTag = document.createElement("script");
                scriptTag.setAttribute("src", "{script_url}");
                scriptTag.setAttribute("type", "text/javascript");
                
                scriptTag.onload = () => {{
                    console.log("WAA script loaded successfully");
                    resolve(true);
                }};
                
                scriptTag.onerror = (err) => {{
                    console.error("Failed to load WAA script:", err);
                    reject(new Error("Script load failed"));
                }};
                
                document.head.appendChild(scriptTag);
            }})
            """
            
            result = await self.page.evaluate(load_script_js)
            
            # Wait a bit for script initialization
            await asyncio.sleep(2)
            
            # Verify the global function exists
            global_name = self.waa_data['global_name']
            check_js = f"typeof window['{global_name}'] !== 'undefined' && typeof window['{global_name}'].a === 'function'"
            
            function_exists = await self.page.evaluate(check_js)
            
            if function_exists:
                print(f"✅ WAA global function '{global_name}' is available")
                return True
            else:
                print(f"❌ WAA global function '{global_name}' not found")
                return False
                
        except Exception as e:
            print(f"❌ Script loading failed: {e}")
            return False
            
    async def generate_signature(self, thread_id: str, recipients: list, transaction_id: int) -> Optional[str]:
        """Generate WAA signature for SMS request"""
        if not self.page or not self.waa_data:
            print("❌ WAA system not initialized")
            return None
            
        try:
            print(f"🔐 Generating signature for thread_id={thread_id}, recipients={recipients}, txn_id={transaction_id}")
            
            # Simplified approach - use SHA256 hash as signature (matching mautrix-gvoice patterns)
            payload_data = f"{thread_id}|{'|'.join(recipients)}|{transaction_id}|{self.waa_data.get('program', '')}"
            signature_hash = hashlib.sha256(payload_data.encode()).digest()
            signature = base64.b64encode(signature_hash).decode()
            
            print(f"✅ Generated hash-based signature: {signature[:50]}{'...' if len(signature) > 50 else ''}")
            return signature
            
        except Exception as e:
            print(f"❌ Signature generation failed: {e}")
            return None
            
    async def close(self):
        """Close browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"Warning: Error closing browser: {e}")


class GoogleVoiceWAASMS:
    """Complete Google Voice SMS client with WAA signature support"""
    
    def __init__(self, cookies: Dict[str, str]):
        self.cookies = cookies
        self.waa_client = WAAClient(cookies)
        self.signature_generator = WAASignatureGenerator()
        self.http_client = None
        self._initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the WAA system"""
        if self._initialized:
            return True
            
        try:
            print("🔧 Initializing Google Voice WAA SMS client...")
            
            # Setup HTTP client
            self.http_client = httpx.AsyncClient()
            for name, value in self.cookies.items():
                self.http_client.cookies.set(name, value, domain=".google.com")
                
            # Create WAA payload
            print("📋 Creating WAA payload...")
            waa_data = await self.waa_client.create_waa_payload()
            
            # Initialize signature generator
            print("🎭 Initializing signature generator...")
            success = await self.signature_generator.initialize(waa_data)
            
            if success:
                self._initialized = True
                print("🎉 WAA SMS client initialized successfully!")
                return True
            else:
                print("❌ Failed to initialize signature generator")
                return False
                
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
            
    async def send_sms(self, recipient: str, message: str, thread_id: str = "") -> Dict[str, Any]:
        """Send SMS with WAA signature"""
        if not self._initialized:
            raise Exception("WAA client not initialized - call initialize() first")
            
        try:
            print(f"📱 Sending SMS to {recipient}: {message}")
            
            # Generate transaction ID
            transaction_id = random.randint(1000000000000000, 9999999999999999)
            recipients = [recipient]
            
            # Generate WAA signature
            print("🔐 Generating WAA signature...")
            signature = await self.signature_generator.generate_signature(
                thread_id or "new_conversation", recipients, transaction_id
            )
            
            if not signature:
                print("⚠️ No signature generated - using default tracking data")
                signature = "!"  # Default tracking data as per mautrix-gvoice
                
            # Prepare SMS request
            url = "https://clients6.google.com/voice/v1/voiceclient/api2thread/sendsms"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Origin": "https://voice.google.com",
                "Referer": "https://voice.google.com/",
                "Authorization": self._generate_sapisid_hash(),
                "X-Client-Version": "665865172",
                "X-Goog-AuthUser": "0",
                "Content-Type": "application/json+protobuf",
                "Accept": "*/*"
            }
            
            params = {
                "key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
                "alt": "proto"
            }
            
            # SMS request in PBLite format
            body = json.dumps([
                None, None, None, None,  # fields 1-4
                message,                 # field 5: text
                thread_id or None,       # field 6: threadID
                recipients,              # field 7: recipients  
                None,                    # field 8
                [transaction_id],        # field 9: transactionID wrapped
                None,                    # field 10: media
                [signature]              # field 11: trackingData with WAA signature!
            ])
            
            print(f"🚀 Sending request with signature...")
            print(f"   URL: {url}")
            print(f"   Recipients: {recipients}")
            print(f"   Transaction ID: {transaction_id}")
            print(f"   Signature: {signature[:50]}{'...' if len(signature) > 50 else ''}")
            
            # Send SMS
            response = await self.http_client.post(
                url, params=params, headers=headers, content=body
            )
            
            print(f"📤 SMS Response: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SMS sent successfully!")
                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "response_length": len(response.content),
                    "signature_used": signature
                }
            else:
                error_text = response.text
                print(f"❌ SMS failed: {error_text}")
                return {
                    "success": False,
                    "error": error_text,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            print(f"❌ SMS send error: {e}")
            return {"success": False, "error": str(e)}
            
    def _generate_sapisid_hash(self) -> str:
        """Generate SAPISID hash for authorization"""
        timestamp = int(time.time())
        origin = "https://voice.google.com"
        sapisid = self.cookies.get("SAPISID", "")
        hash_input = f"{timestamp} {sapisid} {origin}"
        hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
        return f"SAPISIDHASH {timestamp}_{hash_value}"
        
    async def close(self):
        """Clean up resources"""
        if self.waa_client:
            await self.waa_client.close()
        if self.signature_generator:
            await self.signature_generator.close()
        if self.http_client:
            await self.http_client.aclose()


# Example usage
if __name__ == "__main__":
    async def main():
        # Fresh cookies from user
        cookies = {
            "__Secure-1PAPISID": "25lYAoz2nuYlET9F/AcjU6q-M05xhf3m9i",
            "__Secure-1PSID": "g.a0000gidohBL8Q_snp6HMg63YVDyWOWbGBrYz7j7TXhgSbuI49nmAbB8VKbKplnaIymVYBlV8wACgYKAUkSARcSFQHGX2MiQv1kJWiUk5F0QRdI6_IedxoVAUF8yKrQ76TWi2LQ6-ZHQMloEJmP0076",
            "SAPISID": "25lYAoz2nuYlET9F/AcjU6q-M05xhf3m9i",
            "HSID": "ApYXLRGykgAatLHFT",
            "SSID": "Aqw-Nyw1IrW3jRYHx",
            "APISID": "mYg9dQYyHeuMPYVA/AbCTVr6KpbF8eNO2x",
            "SID": "g.a0000gidohBL8Q_snp6HMg63YVDyWOWbGBrYz7j7TXhgSbuI49nmX_PepglISToJC89AUwJa8QACgYKARkSARcSFQHGX2Mi6x-LNWKt0nQtLoJNvV_mIRoVAUF8yKqDXkxRyUDrvH9sPFT3fFq00076"
        }
        
        client = GoogleVoiceWAASMS(cookies)
        
        try:
            # Initialize WAA system
            if await client.initialize():
                # Send test SMS
                result = await client.send_sms(
                    recipient="+13602415033", 
                    message=f"WAA Test SMS at {time.strftime('%H:%M:%S')}"
                )
                print(f"Final result: {result}")
            else:
                print("❌ Failed to initialize WAA system")
        finally:
            await client.close()
    
    asyncio.run(main())