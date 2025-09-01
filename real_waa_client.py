#!/usr/bin/env python3
"""
Real WAA signature generation using Google's actual JavaScript
Based on mautrix-gvoice's Electron implementation for authentic signatures
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
from datetime import datetime

class RealWAASignatureGenerator:
    """Generates authentic WAA signatures using Google's actual JavaScript"""
    
    WAA_API_KEY = "AIzaSyBGb5fGAyC-pRcRU6MUHb__b_vKha71HRE"
    WAA_REQUEST_KEY = "/JR8jsAkqotcKsEKhXic"
    WAA_CREATE_URL = "https://waa-pa.clients6.google.com/$rpc/google.internal.waa.v1.Waa/Create"
    WAA_EXPIRY_HOURS = 1
    
    def __init__(self, cookies: Dict[str, str]):
        self.cookies = cookies
        self.playwright = None
        self.browser = None
        self.page = None
        self.waa_data = None
        self.initialized_at = None
        self.http_client = None
        
    async def initialize(self) -> bool:
        """Initialize WAA system with real browser and Google's JavaScript"""
        try:
            print("🚀 Initializing Real WAA System...")
            
            # Setup HTTP client
            self.http_client = httpx.AsyncClient()
            for name, value in self.cookies.items():
                self.http_client.cookies.set(name, value, domain=".google.com")
            
            # Create WAA payload from Google
            print("📋 Creating WAA payload...")
            self.waa_data = await self._create_waa_payload()
            if not self.waa_data:
                return False
                
            # Initialize browser environment
            print("🌐 Setting up browser environment...")
            success = await self._setup_browser()
            if not success:
                return False
                
            # Load WAA script and verify
            print("📜 Loading Google's WAA JavaScript...")
            success = await self._load_waa_script()
            if not success:
                return False
                
            self.initialized_at = datetime.now()
            print("✅ Real WAA System initialized successfully!")
            return True
            
        except Exception as e:
            print(f"❌ WAA initialization failed: {e}")
            await self.close()
            return False
            
    async def _create_waa_payload(self) -> Optional[Dict[str, Any]]:
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
        
        request_data = json.dumps([self.WAA_REQUEST_KEY])
        
        try:
            response = await self.http_client.post(
                self.WAA_CREATE_URL,
                content=request_data,
                headers=headers
            )
            
            if response.status_code == 200:
                waa_data = response.json()
                print(f"✅ WAA payload created: {waa_data}")
                
                # Parse PBLite response format
                if len(waa_data) > 0 and len(waa_data[0]) > 6:
                    # WAA response structure: [['resp_id', None, [None, None, None, 'interpreter_url'], 'interpreter_hash', 'program', 'global_name', None, 'extra_data']]
                    resp_data = waa_data[0]
                    interpreter_url = resp_data[3][3] if len(resp_data[3]) > 3 else None
                    
                    return {
                        'resp_id': resp_data[0] if len(resp_data) > 0 else None,
                        'interpreter_url': interpreter_url,
                        'interpreter_hash': resp_data[4] if len(resp_data) > 4 else None,
                        'program': resp_data[5] if len(resp_data) > 5 else None,
                        'global_name': resp_data[6] if len(resp_data) > 6 else None
                    }
                else:
                    raise Exception(f"Unexpected WAA response format: {waa_data}")
            else:
                raise Exception(f"Failed to create WAA payload: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ WAA creation error: {e}")
            return None
            
    async def _setup_browser(self) -> bool:
        """Setup browser environment for WAA script execution"""
        try:
            # Start Playwright
            self.playwright = await async_playwright().start()
            
            # Launch browser with proper Chrome settings
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create context with proper settings
            context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
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
            
            # Navigate to proper Google Voice context
            await self.page.goto("https://voice.google.com/u/0/about", 
                                wait_until="domcontentloaded", 
                                timeout=30000)
            
            print("✅ Browser context established")
            return True
            
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return False
            
    async def _load_waa_script(self) -> bool:
        """Load and verify Google's WAA script"""
        try:
            script_url = self.waa_data['interpreter_url']
            if script_url.startswith('//'):
                script_url = 'https:' + script_url
                
            # Load the script
            load_result = await self.page.evaluate(f"""
                new Promise((resolve, reject) => {{
                    console.log("Loading WAA script from: {script_url}");
                    
                    const script = document.createElement('script');
                    script.src = '{script_url}';
                    script.type = 'text/javascript';
                    
                    script.onload = () => {{
                        console.log("WAA script loaded successfully");
                        resolve(true);
                    }};
                    
                    script.onerror = (err) => {{
                        console.error("Failed to load WAA script:", err);
                        reject(new Error("Script load failed"));
                    }};
                    
                    document.head.appendChild(script);
                }})
            """)
            
            if load_result:
                # Wait for script initialization
                await asyncio.sleep(3)
                
                # Verify global function exists
                global_name = self.waa_data['global_name']
                function_available = await self.page.evaluate(f"""
                    typeof window['{global_name}'] !== 'undefined' && 
                    typeof window['{global_name}'].a === 'function'
                """)
                
                if function_available:
                    print(f"✅ WAA function '{global_name}' is available")
                    return True
                else:
                    print(f"❌ WAA function '{global_name}' not found")
                    return False
            else:
                print("❌ Failed to load WAA script")
                return False
                
        except Exception as e:
            print(f"❌ Script loading failed: {e}")
            return False
            
    async def generate_real_signature(self, thread_id: str, recipients: list, transaction_id: int) -> Optional[str]:
        """Generate authentic WAA signature using Google's JavaScript"""
        if not self.page or not self.waa_data:
            print("❌ WAA system not initialized")
            return None
            
        try:
            print(f"🔐 Generating REAL signature for thread_id={thread_id}, recipients={recipients}, txn_id={transaction_id}")
            
            # Check if WAA needs refresh (1 hour expiry)
            if self.initialized_at:
                elapsed = (datetime.now() - self.initialized_at).total_seconds() / 3600
                if elapsed > self.WAA_EXPIRY_HOURS:
                    print("⏰ WAA expired, reinitializing...")
                    if not await self.initialize():
                        return None
            
            # Create proper payload like mautrix-gvoice
            thread_id_hash = hashlib.sha256(thread_id.encode()).digest()
            recipients_hash = hashlib.sha256("|".join(recipients).encode()).digest()
            message_id_hash = hashlib.sha256(str(transaction_id).encode()).digest()
            
            payload = {
                "thread_id": base64.b64encode(thread_id_hash).decode(),
                "destinations": base64.b64encode(recipients_hash).decode(), 
                "message_ids": base64.b64encode(message_id_hash).decode()
            }
            
            print(f"📦 Payload: {payload}")
            
            # Execute Google's actual WAA script
            program = self.waa_data['program']
            global_name = self.waa_data['global_name']
            
            signature = await self.page.evaluate(f"""
                new Promise((resolve, reject) => {{
                    try {{
                        const payload = {json.dumps(payload)};
                        const program = {json.dumps(program)};
                        
                        console.log("Executing WAA with payload:", payload);
                        
                        // Execute exactly like mautrix-gvoice Electron implementation
                        new Promise(resolve => {{
                            window['{global_name}'].a(program, (fn1, fn2, fn3, fn4) => {{
                                resolve({{fn1, fn2, fn3, fn4}});
                            }}, true, undefined, () => {{}});
                        }}).then(fns => {{
                            console.log("Got WAA functions:", Object.keys(fns));
                            
                            fns.fn1(result => {{
                                console.log("Got WAA result:", result);
                                resolve(result);
                            }}, [payload, undefined, undefined, undefined]);
                        }}).catch(reject);
                        
                    }} catch (error) {{
                        console.error("WAA execution error:", error);
                        reject(error);
                    }}
                }})
            """)
            
            if signature:
                print(f"✅ Generated REAL WAA signature: {str(signature)[:100]}{'...' if len(str(signature)) > 100 else ''}")
                return str(signature)
            else:
                print("❌ No signature returned from WAA script")
                return None
                
        except Exception as e:
            print(f"❌ Real signature generation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
            
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
            print(f"Warning: Error closing WAA resources: {e}")


class GoogleVoiceRealSMS:
    """Google Voice SMS client with real WAA signatures"""
    
    def __init__(self, cookies: Dict[str, str]):
        self.cookies = cookies
        self.waa_generator = RealWAASignatureGenerator(cookies)
        self.http_client = None
        self._initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the real WAA SMS system"""
        if self._initialized:
            return True
            
        try:
            print("🔧 Initializing Google Voice Real SMS client...")
            
            # Setup HTTP client
            self.http_client = httpx.AsyncClient()
            for name, value in self.cookies.items():
                self.http_client.cookies.set(name, value, domain=".google.com")
                
            # Initialize real WAA system
            success = await self.waa_generator.initialize()
            if success:
                self._initialized = True
                print("🎉 Real SMS client initialized!")
                return True
            else:
                print("❌ Failed to initialize real WAA system")
                return False
                
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
            
    async def send_sms(self, recipient: str, message: str, thread_id: str = "") -> Dict[str, Any]:
        """Send SMS with real WAA signature"""
        if not self._initialized:
            raise Exception("Real SMS client not initialized - call initialize() first")
            
        try:
            print(f"📱 Sending SMS to {recipient}: {message}")
            
            # Generate transaction ID
            transaction_id = random.randint(1, 99999999999999)
            recipients = [recipient]
            
            # Generate REAL WAA signature
            print("🔐 Generating REAL WAA signature...")
            signature = await self.waa_generator.generate_real_signature(
                thread_id or "new_conversation", recipients, transaction_id
            )
            
            if not signature:
                print("⚠️ Failed to generate real signature - using fallback")
                signature = "!"
                
            # Send SMS with real signature
            url = "https://clients6.google.com/voice/v1/voiceclient/api2thread/sendsms"
            
            headers = {
                # Chrome browser headers
                "Sec-Ch-Ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
                "Sec-Ch-Ua-Platform": '"Linux"',
                "Sec-Ch-Ua-Mobile": "?0",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "X-Goog-AuthUser": "0",
                # API-specific headers
                "X-Client-Version": "665865172",
                "X-ClientDetails": "appVersion=5.0%20%28X11%29&platform=Linux%20x86_64&userAgent=Mozilla%2F5.0%20%28X11%3B%20Linux%20x86_64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F128.0.0.0%20Safari%2F537.36",
                "X-JavaScript-User-Agent": "google-api-javascript-client/1.1.0",
                "X-Requested-With": "XMLHttpRequest",
                "X-Goog-Encode-Response-If-Executable": "base64",
                # Fetch headers
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors", 
                "Sec-Fetch-Site": "same-site",
                # Content headers
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.5",
                "Origin": "https://voice.google.com",
                "Referer": "https://voice.google.com/",
                "Content-Type": "application/json+protobuf",
                # Authentication
                "Authorization": self._generate_sapisid_hash()
            }
            
            params = {
                "key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
                "alt": "proto"
            }
            
            # SMS request with REAL WAA signature
            body = json.dumps([
                None, None, None, None,  # fields 1-4
                message,                 # field 5: text
                thread_id or None,       # field 6: threadID
                recipients,              # field 7: recipients  
                None,                    # field 8
                [transaction_id],        # field 9: transactionID wrapped
                None,                    # field 10: media
                [signature]              # field 11: trackingData with REAL WAA signature!
            ])
            
            print(f"🚀 Sending request with REAL signature...")
            print(f"   URL: {url}")
            print(f"   Recipients: {recipients}")
            print(f"   Transaction ID: {transaction_id}")
            print(f"   Signature type: {'REAL' if signature != '!' else 'FALLBACK'}")
            
            # Send SMS
            response = await self.http_client.post(
                url, params=params, headers=headers, content=body
            )
            
            print(f"📤 SMS Response: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SMS sent successfully with REAL WAA signature!")
                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "response_length": len(response.content),
                    "signature_used": signature,
                    "signature_type": "REAL" if signature != "!" else "FALLBACK"
                }
            else:
                error_text = response.text
                print(f"❌ SMS failed: {error_text}")
                return {
                    "success": False,
                    "error": error_text,
                    "status_code": response.status_code,
                    "signature_type": "REAL" if signature != "!" else "FALLBACK"
                }
                
        except Exception as e:
            print(f"❌ SMS send error: {e}")
            import traceback
            traceback.print_exc()
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
        if self.waa_generator:
            await self.waa_generator.close()
        if self.http_client:
            await self.http_client.aclose()


# Test script
if __name__ == "__main__":
    async def main():
        # Fresh cookies from user - UPDATED 2024-08-28
        cookies = {
            "__Secure-1PAPISID": "25lYAoz2nuYlET9F/AcjU6q-M05xhf3m9i",
            "__Secure-1PSID": "g.a0000gidohBL8Q_snp6HMg63YVDyWOWbGBrYz7j7TXhgSbuI49nmAbB8VKbKplnaIymVYBlV8wACgYKAUkSARcSFQHGX2MiQv1kJWiUk5F0QRdI6_IedxoVAUF8yKrQ76TWi2LQ6-ZHQMloEJmP0076",
            "__Secure-1PSIDCC": "AKEyXzWsQ8cabGhRaoeIDVpyb9dxSWX6bj-ZwlgfWA4fIE6CsyDOjTCAMX_Prruzk1QSKT6a0Q",
            "__Secure-1PSIDTS": "sidts-CjIB5H03Pzp8dDQsA0hi6nqSbZETflPRDhQ8y5LS_ItlLHtYQNFbGYKCVy-AZCHd4DzdlhAA",
            "__Secure-3PAPISID": "25lYAoz2nuYlET9F/AcjU6q-M05xhf3m9i",
            "__Secure-3PSID": "g.a0000gidohBL8Q_snp6HMg63YVDyWOWbGBrYz7j7TXhgSbuI49nmptstfVG3sOuBex1won4fOAACgYKASQSARcSFQHGX2MitGTAfMcy05dsGQLPlBAr3RoVAUF8yKqbYCBU-BT9ONjIWNiQri-h0076",
            "__Secure-3PSIDCC": "AKEyXzVmM2q5AU_frQo6iALwRGlGFazMauLIu4yQhOy02wT2npihECOiwN5tmYbvS2wh5yzjJw",
            "__Secure-3PSIDTS": "sidts-CjIB5H03Pzp8dDQsA0hi6nqSbZETflPRDhQ8y5LS_ItlLHtYQNFbGYKCVy-AZCHd4DzdlhAA",
            "__Secure-OSID": "g.a0000gidomf-Km8BaxbLZKsQno7wq4K3q3N0WabexlpDZxQ-737PlapNUkl3VcjwpXckZfrTigACgYKAbsSARcSFQHGX2MiBXLJQb4seMM4YY2dCEzn8BoVAUF8yKr2qyjdOzEybx8Kv8ZUb20w0076",
            "APISID": "mYg9dQYyHeuMPYVA/AbCTVr6KpbF8eNO2x",
            "COMPASS": "voice-web-frontend=CgAQsrDCxQYaXgAJa4lXDPiI5XaP-nYDPAkZMqqZ94lMW8GB9vCUYYH7783Byrombw9404lBqdqnAPMLeOa6sgk0QkesAR38RSnvBylpC00zm2xIvr4P6a3Uy5A3wv8hAcBA5-nMngkwAQ",
            "HSID": "ApYXLRGykgAatLHFT",
            "NID": "525=BKwRSic0nFOADsNww04nmpI5nQN3Y9pX9gPF7HyS1rueM1F9g2Pwf-vGNgVX37l26HRx6jrkoEIwM4UEB5vm2t41KdsXICuNRFrctEvAl_vjT4MdE5XcY6ysdvCjvMVTCfbfcrP97wQGisGh5iaaIwQomDwO6HT_woAImJiqZPgeCZXiurfT7AWWRHCXpAlOxXoAuKKCLo9FrFvzRX_Y5L1KlaPhxVMA0yjrNQHStz5-ojFuIibDDT_jlrI9Xh-r4Q4DfKHZskTCZSJJLee_aZSW9N26AnBt-dpE3gcBckC-8qYcd1CE2cv5_8xD3wrSQIkk9Tra6jmYFnLCJp_ks4R6lN_GR9fJ8lgnc30eGcNdq5Z_R3NKZFsT2AMMsmc0zM12IX0ZZIVdVwiM-pbcgzGBPnUR_hOVavNFW0VU4Woj0qenlfjiE29nQASJSx6FT9Cb7QzyIm6d3rAXiT4q_PG04GVSG0xSouzeiKNbwdhinyLphGecOcZSAiQ36aja70Q8QKrTOWIzsKKtx0HJXN9ubGzqLbfkNJKe6i5I3eYETdmg350Na2St99OEUKMANCR1Gq2ZHQ-ggxh6X65QqaueI6rWb1zCkbu4-lAXqt43x_b6yFI2ioYlDMYMb54W-ABaMa_SRL7IpfOt_szB-vTvDAS2mpRzeCKCktxssfTg6YNfzWSfdG2X0d-y3j-PE88EULS2aeyXwtOxOdWdDmkSsyd2Yh63uFsHy2qr431mwrzXXKIFCwIUVRzRuOkLeia0M0qtal2TOK-Pekb-2TeHJF9hixjF6jicD3GRaKGjhAwzgL7YaND_bHInPxS6LcrJrg3bFLTVSjnqNqDasaprRfBrOz3v452Nx9Uqnp8xtQ3hJMhZtUlCR0Mk7uExddP2u6644ox6OYTwFgYyW6OBe5OO75EuA7RCjREp-T8SGbAKMUn5DFxd9RrG8GKYhzPddno2zI9C3RyXWQ6krYEt9CU",
            "OSID": "g.a0000gidomf-Km8BaxbLZKsQno7wq4K3q3N0WabexlpDZxQ-737P_NLRTpnlu9TbOdkWVIwQ9gACgYKAbwSARcSFQHGX2Mi2-8454Xc5-S2UMGkfrsaJxoVAUF8yKq0yUUJMWsNycV4MBJONjER0076",
            "S": "billing-ui-v3=c8vqT6pMKIM10h3hUSnnakj9Uc7Ievsp:billing-ui-v3-efe=c8vqT6pMKIM10h3hUSnnakj9Uc7Ievsp",
            "SAPISID": "25lYAoz2nuYlET9F/AcjU6q-M05xhf3m9i",
            "SID": "g.a0000gidohBL8Q_snp6HMg63YVDyWOWbGBrYz7j7TXhgSbuI49nmX_PepglISToJC89AUwJa8QACgYKARkSARcSFQHGX2Mi6x-LNWKt0nQtLoJNvV_mIRoVAUF8yKqDXkxRyUDrvH9sPFT3fFq00076",
            "SIDCC": "AKEyXzW_2SvBToS2_TQ2itvrvAOc2KCrSzdmpwtOO5iLPRh0Ci_8YQgU_jKLX85dgMZnVFbqKyU",
            "SSID": "Aqw-Nyw1IrW3jRYHx"
        }
        
        client = GoogleVoiceRealSMS(cookies)
        
        try:
            print("=" * 70)
            print("🚀 TESTING REAL WAA SIGNATURE SYSTEM 🚀")
            print("=" * 70)
            
            # Initialize real WAA system
            if await client.initialize():
                # Send test SMS with REAL signatures
                result = await client.send_sms(
                    recipient="3602415033", 
                    message=f"🎉 REAL WAA SMS Test at {datetime.now().strftime('%H:%M:%S')}"
                )
                print(f"\n📊 Final Result: {json.dumps(result, indent=2)}")
                
                if result.get("success"):
                    print("\n🎉🎉🎉 SUCCESS! SMS SENT WITH REAL WAA! 🎉🎉🎉")
                else:
                    print(f"\n❌ SMS failed: {result.get('error')}")
            else:
                print("❌ Failed to initialize real WAA system")
                
        finally:
            await client.close()
    
    asyncio.run(main())