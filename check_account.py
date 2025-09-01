#!/usr/bin/env python3
"""
Check Google Voice account details to understand available numbers and format
"""
import asyncio
import json
import time
import hashlib
import httpx

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

async def get_account_info():
    """Get detailed account information"""
    async with httpx.AsyncClient() as client:
        # Set cookies
        for name, value in FRESH_COOKIES.items():
            client.cookies.set(name, value, domain=".google.com")
            
        url = "https://clients6.google.com/voice/v1/voiceclient/account/get"
        
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
            "Authorization": generate_sapisid_hash()
        }
        
        params = {
            "key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
            "alt": "proto"
        }
        
        # Account request format: ReqGetAccount has unknownInt2 = 1 (field 2)
        body = json.dumps([None, 1])  # Field 2 = 1 as per protobuf
        
        print("🔍 Getting account information...")
        response = await client.post(url, params=params, headers=headers, content=body)
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            # Try to parse response as JSON
            try:
                account_data = response.json()
                print("📋 Account Data (first 2000 chars):")
                print(json.dumps(account_data, indent=2)[:2000])
                
                # Look for phone numbers
                if isinstance(account_data, list) and len(account_data) > 0:
                    print("\n📞 Searching for phone numbers in account data...")
                    account_info = account_data[0] if account_data[0] else {}
                    
                    def find_phone_numbers(obj, path=""):
                        """Recursively search for phone numbers"""
                        if isinstance(obj, dict):
                            for key, value in obj.items():
                                new_path = f"{path}.{key}" if path else key
                                if "phone" in key.lower() or "number" in key.lower():
                                    print(f"   Found {new_path}: {value}")
                                find_phone_numbers(value, new_path)
                        elif isinstance(obj, list):
                            for i, item in enumerate(obj):
                                find_phone_numbers(item, f"{path}[{i}]")
                        elif isinstance(obj, str) and obj.startswith("+1") and len(obj) >= 10:
                            print(f"   Found phone-like string at {path}: {obj}")
                    
                    find_phone_numbers(account_info)
                    
            except Exception as e:
                print(f"   Could not parse as JSON: {e}")
                print(f"   Raw response: {response.text[:1000]}")
        else:
            print(f"❌ Failed: {response.text[:500]}")

async def list_threads():
    """List recent threads to see message format"""
    async with httpx.AsyncClient() as client:
        # Set cookies
        for name, value in FRESH_COOKIES.items():
            client.cookies.set(name, value, domain=".google.com")
            
        url = "https://clients6.google.com/voice/v1/voiceclient/api2thread/list"
        
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
            "Authorization": generate_sapisid_hash()
        }
        
        params = {
            "key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
            "alt": "proto"
        }
        
        # List threads request - ReqListThreads format
        body = json.dumps([
            1,      # field 1: folder (INBOX = 1)
            20,     # field 2: unknownInt2 
            15,     # field 3: unknownInt3
            None,   # field 4: (unused)
            "",     # field 5: versionToken (empty for first request)
            [None, 1, 1]  # field 6: UnknownWrapper with unknownInt2=1, unknownInt3=1
        ])
        
        print("\n🗂️  Getting thread list...")
        response = await client.post(url, params=params, headers=headers, content=body)
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            try:
                threads_data = response.json()
                print("📋 Threads Data (first 1500 chars):")
                print(json.dumps(threads_data, indent=2)[:1500])
            except Exception as e:
                print(f"   Could not parse as JSON: {e}")
                print(f"   Raw response: {response.text[:1000]}")
        else:
            print(f"❌ Failed: {response.text[:500]}")

if __name__ == "__main__":
    print("=" * 60)
    print("Google Voice Account Information")
    print("=" * 60)
    
    async def main():
        await get_account_info()
        await list_threads()
    
    asyncio.run(main())