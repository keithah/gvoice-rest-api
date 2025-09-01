#!/usr/bin/env python3
"""
Quick SMS test with fresh cookies and WAA system
"""
import asyncio
import json
import time
import base64
import hashlib
import random
import httpx
from datetime import datetime

# Fresh cookies from user
FRESH_COOKIES = {
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

def generate_sapisid_hash() -> str:
    timestamp = int(time.time())
    origin = "https://voice.google.com"
    sapisid = FRESH_COOKIES.get("SAPISID", "")
    hash_input = f"{timestamp} {sapisid} {origin}"
    hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
    return f"SAPISIDHASH {timestamp}_{hash_value}"

async def send_sms_with_waa():
    """Send SMS using the full WAA system"""
    try:
        from waa_client import GoogleVoiceWAASMS
        
        client = GoogleVoiceWAASMS(FRESH_COOKIES)
        
        print("🚀 Starting WAA SMS client...")
        
        # Initialize with timeout
        if await client.initialize():
            # Send the SMS
            result = await client.send_sms(
                recipient="+13602415033",
                message=f"SUCCESS! WAA SMS from API at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                thread_id=""
            )
            
            print(f"\n📱 SMS Result: {result}")
            
            if result.get("success"):
                print("🎉 SMS SENT SUCCESSFULLY!")
            else:
                print(f"❌ SMS failed: {result.get('error', 'Unknown error')}")
                
        else:
            print("❌ Failed to initialize WAA system")
            
        await client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def try_simple_sms_with_basic_signature():
    """Try SMS with basic signature - faster fallback"""
    
    async with httpx.AsyncClient() as client:
        # Set cookies
        for name, value in FRESH_COOKIES.items():
            client.cookies.set(name, value, domain=".google.com")
            
        url = "https://clients6.google.com/voice/v1/voiceclient/api2thread/sendsms"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Origin": "https://voice.google.com",
            "Referer": "https://voice.google.com/",
            "Authorization": generate_sapisid_hash(),
            "X-Client-Version": "665865172",
            "X-Goog-AuthUser": "0",
            "Content-Type": "application/json+protobuf",
            "Accept": "*/*"
        }
        
        params = {
            "key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
            "alt": "proto"
        }
        
        message = f"Basic SMS test at {datetime.now().strftime('%H:%M:%S')}"
        recipient = "+13602415033"
        transaction_id = random.randint(1000000000000000, 9999999999999999)
        
        # Generate simple hash signature (like early mautrix-gvoice)
        thread_id_hash = hashlib.sha256("new_conversation".encode()).digest()
        recipients_hash = hashlib.sha256(recipient.encode()).digest()  
        message_id_hash = hashlib.sha256(str(transaction_id).encode()).digest()
        
        simple_signature = base64.b64encode(
            thread_id_hash + recipients_hash + message_id_hash
        ).decode()[:50]  # Truncate for simplicity
        
        body = json.dumps([
            None, None, None, None,  # fields 1-4
            message,                 # field 5: text
            None,                    # field 6: threadID 
            [recipient],             # field 7: recipients
            None,                    # field 8
            [transaction_id],        # field 9: transactionID wrapped
            None,                    # field 10: media
            [simple_signature]       # field 11: simple signature
        ])
        
        print(f"📱 Trying basic SMS to {recipient}...")
        print(f"   Message: {message}")
        print(f"   Signature: {simple_signature}")
        
        try:
            response = await client.post(url, params=params, headers=headers, content=body)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ BASIC SMS SUCCESS!")
                return True
            else:
                print(f"❌ Basic SMS failed: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Basic SMS error: {e}")
            return False

if __name__ == "__main__":
    print("=" * 60)
    print("Google Voice SMS Test with WAA")
    print("=" * 60)
    
    async def main():
        # Try basic SMS first (faster)
        print("1️⃣ Testing basic SMS...")
        basic_success = await try_simple_sms_with_basic_signature()
        
        if not basic_success:
            print("\n2️⃣ Basic SMS failed, trying full WAA system...")
            await send_sms_with_waa()
        else:
            print("\n🎉 Basic SMS worked! No need for full WAA.")
    
    asyncio.run(main())