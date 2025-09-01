#!/usr/bin/env python3
"""
Fixed authentication test based on mautrix-gvoice analysis
"""
import asyncio
import httpx
import json
from datetime import datetime
import hashlib
import time

# Fresh cookies from user
ALL_COOKIES = {
    "__Secure-1PAPISID": "GjfTX7q-BcEw9cRE/Ao7WL3H89RBOSiG9Q",
    "__Secure-1PSID": "g.a0000gjAouZjfqg3cumlvmMVeSS0xZt2ZSXhXLVevEHnt_drASD_ACFxn0xOc9CMuXZDoCh6MQACgYKAXgSARISFQHGX2MiAXyXyiEpN7UtygQt0TlP8xoVAUF8yKqPNr0X_HgXcnaZXEVgGv9J0076",
    "__Secure-1PSIDCC": "AKEyXzVhUVBdGCUtfl6Cn5scjw49ovrDbFhhmbBdTQNL7Jd2nZQhdPqr5fGk2FWvrFgGxGQR-KEs",
    "__Secure-1PSIDTS": "sidts-CjAB5H03P-9B7z2TDyPLOKqzK5WawC2bq8XmjHqCRmDYKwK9tAwFJEV04w4iZLXAxgMQAA",
    "__Secure-3PAPISID": "GjfTX7q-BcEw9cRE/Ao7WL3H89RBOSiG9Q",
    "__Secure-3PSID": "g.a0000gjAouZjfqg3cumlvmMVeSS0xZt2ZSXhXLVevEHnt_drASD_zEjJOei8xRfARwAwgpC0HwACgYKAUoSARISFQHGX2MiA32MnMBazgKNO7auwcDsmBoVAUF8yKq360zWEBlBY1cwl2rg5uNr0076",
    "__Secure-3PSIDCC": "AKEyXzVaMNJH3_tF1ImvMtZ3xTtpb0zGy3RLTz4g3thgHtFFLyHHkypQ4h8gV9y7jGr_jdV0Z0Ev",
    "__Secure-3PSIDTS": "sidts-CjAB5H03P-9B7z2TDyPLOKqzK5WawC2bq8XmjHqCRmDYKwK9tAwFJEV04w4iZLXAxgMQAA",
    "__Secure-ENID": "27.SE=TIzbjrG2OJBP8lyHNef_qGHaS5o0v3c_bB2d2fyt_ydckg_XWSiU1IdJP4lOnE6LvpkOjGcoA3nrUXU4euhkOTJ-6L3cHJyXkgn_l4fK4wdUWj9TqN0J1Gf6cxiEo-MjMaXetUQdR-7B7p2mRbpLjtqzx75TsNqDJQ4DgAhO39E9BjcJncRyNv6Kgm3bxM-yeYM6f4KjxWNzkjVZb2M-FH9WY3SncR-Oae2gF5otAHfW0I2h0fwTmyOt2xpqX0uk0CPfanc4vrHD6teb-QuLbIQTcIHgJZgQ63XRWTPyxEjg44s3dolc7e7mBkakxThjphEoH5K0Pi6zLnXrpNsKXxAXPqlG3LfCyHa4el4BQfNHYZDUdwHHriv49DwYudbkAprp0iqOc1Pz",
    "__Secure-OSID": "g.a0000gjAoojj64DmhVUAvK08uX0aawiSjFwaT1FX239ZBbtpvCWJ4qk8H1AYAm8cuU838ta5AwACgYKAUESARISFQHGX2Mi5hAEjOmsAMwpmFvd-p-eKBoVAUF8yKpdw8VS9DQ5GTW_IPGxmmER0076",
    "AEC": "AVh_V2h8NUR4T1X-naFZpABWtoKMKWtN51L1YMlKLmgF5UWyMvZ_GfBLSu0",
    "APISID": "qW3CGJXrJMAUgDnq/AE0szFtN-ymXjEyZJ",
    "COMPASS": "voice-web-frontend=CgAQ0IXCxQYaXgAJa4lX_sZ31YHPtuSrdPAVDdGsVPZPzjqrGKPkj_G7pZKHq_zulxeR8gf5mFwl2HCkG4k7aOLc5UF2O1tfN5S1KQwqbsIv2NfvCpsc0nWfuN7Sk7FTuy-zX9N3qmowAQ",
    "HSID": "AcvDwpgrPA3Np_b_f",
    "OSID": "g.a0000gjAoojj64DmhVUAvK08uX0aawiSjFwaT1FX239ZBbtpvCWJcz2bto9McNFXC9JhnJmtKgACgYKAbESARISFQHGX2MiTK78brOZJywuSHjtS3bJrhoVAUF8yKqCzBhVzyqJiJ_zi6hEuvw_0076",
    "S": "billing-ui-v3=C6tSQSYTyvcSnHni5vkYSYayiFJqBkD_:billing-ui-v3-efe=C6tSQSYTyvcSnHni5vkYSYayiFJqBkD_",
    "SAPISID": "GjfTX7q-BcEw9cRE/Ao7WL3H89RBOSiG9Q",
    "SEARCH_SAMESITE": "CgQIu54B",
    "SID": "g.a0000gjAouZjfqg3cumlvmMVeSS0xZt2ZSXhXLVevEHnt_drASD_ijoJR-Izp-O4cqXDy9kHbgACgYKAZESARISFQHGX2MiupijAjtQdfaeCxpLUdc4TRoVAUF8yKpy_aQqwYTGWecKLJI_Fe9u0076",
    "SIDCC": "AKEyXzVUSHtk3nnDt93StR9_cry8C7MIPUmeNbMGrMkaEeoQnRDDPE1XNdxbyJktyc86lEyroMc",
    "SSID": "AQZcF9pzX7SCL1ZFK"
}

def generate_sapisid_hash(sapisid: str) -> str:
    """Generate SAPISID hash exactly like mautrix-gvoice"""
    timestamp = int(time.time())
    origin = "https://voice.google.com"
    hash_input = f"{timestamp} {sapisid} {origin}"
    hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
    return f"SAPISIDHASH {timestamp}_{hash_value}"

async def test_account_get():
    """Test account/get endpoint exactly like mautrix-gvoice"""
    async with httpx.AsyncClient() as client:
        url = "https://clients6.google.com/voice/v1/voiceclient/account/get"
        
        # Headers exactly like mautrix-gvoice
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Sec-Ch-Ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            "Sec-Ch-Ua-Platform": '"Linux"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Origin": "https://voice.google.com",
            "Referer": "https://voice.google.com/",
            "Authorization": generate_sapisid_hash(ALL_COOKIES["SAPISID"]),
            "X-Client-Version": "665865172",
            "X-ClientDetails": "appVersion=5.0%20(X11)&platform=Linux%20x86_64&userAgent=Mozilla%2F5.0%20(X11%3B%20Linux%20x86_64)%20AppleWebKit%2F537.36%20(KHTML%2C%20like%20Gecko)%20Chrome%2F128.0.0.0%20Safari%2F537.36",
            "X-JavaScript-User-Agent": "google-api-javascript-client/1.1.0",
            "X-Requested-With": "XMLHttpRequest",
            "X-Goog-Encode-Response-If-Executable": "base64",
            "X-Goog-AuthUser": "0",
            "Content-Type": "application/json+protobuf",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors", 
            "Sec-Fetch-Site": "same-site",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        # Query parameters like mautrix-gvoice
        params = {
            "key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
            "alt": "proto"
        }
        
        # Request body in PBLite format like mautrix-gvoice
        # unknownInt2 field has protobuf number 2, so it goes at index 1 in 0-based array
        body = json.dumps([None, 1])  # PBLite array format: [field1(unused), field2(unknownInt2=1)]
        
        print("Testing account/get with mautrix-gvoice format...")
        print(f"URL: {url}")
        print(f"Authorization: {headers['Authorization']}")
        print(f"Body: {body}")
        print()
        
        try:
            response = await client.post(
                url, 
                params=params, 
                headers=headers, 
                content=body,
                cookies=ALL_COOKIES
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers:")
            for k, v in response.headers.items():
                print(f"  {k}: {v}")
            
            if response.status_code == 200:
                print("\n✅ Authentication successful!")
                print(f"Response body length: {len(response.content)} bytes")
                
                # Check content type
                content_type = response.headers.get('content-type', '')
                print(f"Content-Type: {content_type}")
                
                if response.content:
                    # Try to show first part as hex
                    content_preview = response.content[:50]
                    print(f"Content preview (hex): {content_preview.hex()}")
                    
                    # Try to decode as text if possible
                    try:
                        text_preview = response.content.decode('utf-8', errors='ignore')[:200]
                        if text_preview.strip():
                            print(f"Content preview (text): {text_preview}")
                    except:
                        pass
                        
            elif response.status_code == 401:
                print("\n❌ Authentication failed (401)!")
                print(f"Response: {response.text}")
                
            elif response.status_code == 403:
                print("\n❌ Forbidden (403) - might need WAA signatures")
                print(f"Response: {response.text}")
                
            else:
                print(f"\n❌ Request failed: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"\n❌ Error: {type(e).__name__}: {str(e)}")

async def test_simple_endpoint():
    """Test a simpler endpoint first"""
    async with httpx.AsyncClient() as client:
        # Try the thread list endpoint which might be simpler
        url = "https://clients6.google.com/voice/v1/voiceclient/api2thread/list"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Origin": "https://voice.google.com",
            "Referer": "https://voice.google.com/",
            "Authorization": generate_sapisid_hash(ALL_COOKIES["SAPISID"]),
            "X-Goog-AuthUser": "0",
            "Content-Type": "application/json+protobuf",
            "Accept": "*/*"
        }
        
        params = {
            "key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
            "alt": "proto"
        }
        
        # Simple list request body
        body = json.dumps([None, None, None, None, None, None, None, 1])  # Limit to 1 thread
        
        print("\nTesting thread list endpoint...")
        print(f"URL: {url}")
        
        try:
            response = await client.post(
                url,
                params=params,
                headers=headers,
                content=body,
                cookies=ALL_COOKIES
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Thread list successful!")
            else:
                print(f"❌ Thread list failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_account_get())
    asyncio.run(test_simple_endpoint())