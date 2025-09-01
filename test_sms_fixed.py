#!/usr/bin/env python3
"""
Test SMS with corrected protobuf structure
"""
import asyncio
import httpx
import json
import hashlib
import time
import random

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
    "SIDCC": "AKEyXzX5pSyjNTGRWoAB7kWjHYwUdGrBk9O_W8PqiYz400RZEI56yGvGyL7gs18ak9HsfhIfsA",
    "SSID": "Aqw-Nyw1IrW3jRYHx"
}

def generate_sapisid_hash(sapisid: str) -> str:
    timestamp = int(time.time())
    origin = "https://voice.google.com"
    hash_input = f"{timestamp} {sapisid} {origin}"
    hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
    return f"SAPISIDHASH {timestamp}_{hash_value}"

def generate_transaction_id():
    """Generate a transaction ID as int64 (not in array)"""
    return random.randint(1000000000000000, 9999999999999999)

async def test_sms_variations():
    """Test different SMS request formats"""
    jar = httpx.Cookies()
    for name, value in FRESH_COOKIES.items():
        jar.set(name, value, domain=".google.com")
        
    async with httpx.AsyncClient(cookies=jar) as client:
        url = "https://clients6.google.com/voice/v1/voiceclient/api2thread/sendsms"
        
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
        
        message_text = f"API Test at {time.strftime('%H:%M:%S')}"
        recipient = "+13602415033"
        
        # Test different formats
        test_formats = [
            {
                "name": "Format 1: TransactionID as nested object",
                "body": [
                    None, None, None, None,  # fields 1-4
                    message_text,            # field 5: text
                    None,                    # field 6: threadID  
                    [recipient],             # field 7: recipients
                    None,                    # field 8
                    {"ID": generate_transaction_id()},  # field 9: transactionID as object
                    None,                    # field 10: media
                    {"data": "!"}           # field 11: trackingData as object
                ]
            },
            {
                "name": "Format 2: TransactionID as simple int",  
                "body": [
                    None, None, None, None,
                    message_text,
                    None,
                    [recipient], 
                    None,
                    generate_transaction_id(),  # field 9: transactionID as simple int
                    None,
                    {"data": "!"}
                ]
            },
            {
                "name": "Format 3: Minimal fields only",
                "body": [
                    None, None, None, None,
                    message_text,         # text
                    None,                 # threadID
                    [recipient],          # recipients  
                    None,
                    generate_transaction_id(),
                    None,
                    ["!"]                # trackingData as array
                ]
            },
            {
                "name": "Format 4: Without transaction ID",
                "body": [
                    None, None, None, None,
                    message_text,         # text
                    None,                 # threadID
                    [recipient],          # recipients
                    None, None, None,     # skip transactionID
                    ["!"]                # trackingData
                ]
            }
        ]
        
        for test_format in test_formats:
            print(f"\nTesting {test_format['name']}...")
            body_json = json.dumps(test_format['body'])
            print(f"Body: {body_json}")
            
            try:
                response = await client.post(url, params=params, headers=headers, content=body_json)
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("✅ SMS sent successfully!")
                    return True
                else:
                    error_text = response.text[:200]
                    print(f"❌ Failed: {error_text}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
        
        return False

if __name__ == "__main__":
    success = asyncio.run(test_sms_variations())
    if not success:
        print("\n❌ All SMS format attempts failed")
    else:
        print("\n✅ SMS successfully sent to +13602415033!")