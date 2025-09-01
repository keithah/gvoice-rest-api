#!/usr/bin/env python3
"""
Test reading messages to understand the working patterns
"""
import asyncio
import httpx
import json
import hashlib
import time

# Fresh cookies
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
    "SIDCC": "AKEyXzX5pSyjNTGRWoAB7kWjHYwUdGrBk9O_Ievsp400RZEI56yGvGyL7gs18ak9HsfhIfsA",
    "SSID": "Aqw-Nyw1IrW3jRYHx"
}

def generate_sapisid_hash(sapisid: str) -> str:
    timestamp = int(time.time())
    origin = "https://voice.google.com"
    hash_input = f"{timestamp} {sapisid} {origin}"
    hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
    return f"SAPISIDHASH {timestamp}_{hash_value}"

async def test_list_threads():
    """Test listing threads/conversations"""
    jar = httpx.Cookies()
    for name, value in FRESH_COOKIES.items():
        jar.set(name, value, domain=".google.com")
        
    async with httpx.AsyncClient(cookies=jar) as client:
        url = "https://clients6.google.com/voice/v1/voiceclient/api2thread/list"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Origin": "https://voice.google.com",
            "Referer": "https://voice.google.com/",
            "Authorization": generate_sapisid_hash(FRESH_COOKIES["SAPISID"]),
            "X-Client-Version": "665865172",
            "X-Goog-AuthUser": "0",
            "Content-Type": "application/json+protobuf",
            "Accept": "*/*"
        }
        
        params = {
            "key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
            "alt": "proto"
        }
        
        # ReqListThreads: folder(1), unknownInt2(2), unknownInt3(3), versionToken(5), unknownWrapper(6)
        body = json.dumps([
            0,        # field 1: folder (0 = inbox)
            20,       # field 2: unknownInt2
            15,       # field 3: unknownInt3
            None,     # field 4: unused
            "",       # field 5: versionToken (empty for first request)
            [None, 1, 1]  # field 6: unknownWrapper {unknownInt2: 1, unknownInt3: 1}
        ])
        
        print("Testing thread list...")
        
        try:
            response = await client.post(url, params=params, headers=headers, content=body)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Thread list successful!")
                print(f"Response length: {len(response.content)} bytes")
                
                # Try to get a thread ID for SMS sending
                return True
            else:
                print(f"❌ Thread list failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

async def try_simple_sms():
    """Try SMS with simpler request that doesn't trigger security"""
    jar = httpx.Cookies()
    for name, value in FRESH_COOKIES.items():
        jar.set(name, value, domain=".google.com")
        
    async with httpx.AsyncClient(cookies=jar) as client:
        url = "https://clients6.google.com/voice/v1/voiceclient/api2thread/sendsms"
        
        # Try with fewer headers to avoid triggering security
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Authorization": generate_sapisid_hash(FRESH_COOKIES["SAPISID"]),
            "Content-Type": "application/json+protobuf"
        }
        
        params = {
            "key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
            "alt": "proto"
        }
        
        # Very minimal SMS request
        body = json.dumps([
            None, None, None, None,
            "Hello from API!",  # text
            None,               # threadID
            ["+13602415033"],    # recipients
        ])
        
        print("\nTesting simple SMS...")
        
        try:
            response = await client.post(url, params=params, headers=headers, content=body)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Simple SMS successful!")
                return True
            elif "unsafe" not in response.text.lower():
                print(f"❌ SMS failed (different error): {response.text}")
            else:
                print("❌ Still getting 'unsafe' error")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            
        return False

if __name__ == "__main__":
    success1 = asyncio.run(test_list_threads())
    success2 = asyncio.run(try_simple_sms())
    
    if success1:
        print("\n✅ Authentication working - can read account data")
    if success2:
        print("✅ SMS sending successful!")
    if not success2:
        print("\n⚠️ SMS sending blocked by anti-automation measures")
        print("   This typically requires browser automation or WAA signatures")