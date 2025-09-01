#!/usr/bin/env python3
"""
Test with the exact same request format as mautrix-gvoice
"""
import asyncio
import httpx
import json
import hashlib
import time

# Fresh cookies
COOKIES = {
    "SAPISID": "GjfTX7q-BcEw9cRE/Ao7WL3H89RBOSiG9Q",
    "HSID": "AcvDwpgrPA3Np_b_f",
    "SSID": "AQZcF9pzX7SCL1ZFK",
    "APISID": "qW3CGJXrJMAUgDnq/AE0szFtN-ymXjEyZJ",
    "SID": "g.a0000gjAouZjfqg3cumlvmMVeSS0xZt2ZSXhXLVevEHnt_drASD_ijoJR-Izp-O4cqXDy9kHbgACgYKAZESARISFQHGX2MiupijAjtQdfaeCxpLUdc4TRoVAUF8yKpy_aQqwYTGWecKLJI_Fe9u0076",
    "__Secure-1PSID": "g.a0000gjAouZjfqg3cumlvmMVeSS0xZt2ZSXhXLVevEHnt_drASD_ACFxn0xOc9CMuXZDoCh6MQACgYKAXgSARISFQHGX2MiAXyXyiEpN7UtygQt0TlP8xoVAUF8yKqPNr0X_HgXcnaZXEVgGv9J0076",
    "__Secure-3PSID": "g.a0000gjAouZjfqg3cumlvmMVeSS0xZt2ZSXhXLVevEHnt_drASD_zEjJOei8xRfARwAwgpC0HwACgYKAUoSARISFQHGX2MiA32MnMBazgKNO7auwcDsmBoVAUF8yKq360zWEBlBY1cwl2rg5uNr0076",
    "OSID": "g.a0000gjAoojj64DmhVUAvK08uX0aawiSjFwaT1FX239ZBbtpvCWJcz2bto9McNFXC9JhnJmtKgACgYKAbESARISFQHGX2MiTK78brOZJywuSHjtS3bJrhoVAUF8yKqCzBhVzyqJiJ_zi6hEuvw_0076",
    "__Secure-OSID": "g.a0000gjAoojj64DmhVUAvK08uX0aawiSjFwaT1FX239ZBbtpvCWJ4qk8H1AYAm8cuU838ta5AwACgYKAUESARISFQHGX2Mi5hAEjOmsAMwpmFvd-p-eKBoVAUF8yKpdw8VS9DQ5GTW_IPGxmmER0076",
    "COMPASS": "voice-web-frontend=CgAQ0IXCxQYaXgAJa4lX_sZ31YHPtuSrdPAVDdGsVPZPzjqrGKPkj_G7pZKHq_zulxeR8gf5mFwl2HCkG4k7aOLc5UF2O1tfN5S1KQwqbsIv2NfvCpsc0nWfuN7Sk7FTuy-zX9N3qmowAQ",
    "__Secure-1PSIDTS": "sidts-CjAB5H03P-9B7z2TDyPLOKqzK5WawC2bq8XmjHqCRmDYKwK9tAwFJEV04w4iZLXAxgMQAA"
}

def generate_sapisid_hash(sapisid: str) -> str:
    timestamp = int(time.time())
    origin = "https://voice.google.com"
    hash_input = f"{timestamp} {sapisid} {origin}"
    hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
    return f"SAPISIDHASH {timestamp}_{hash_value}"

async def test_with_minimal_request():
    """Test with minimal request like a fresh browser might send"""
    # Create a jar for automatic cookie handling
    jar = httpx.Cookies()
    for name, value in COOKIES.items():
        jar.set(name, value, domain=".google.com")
        
    async with httpx.AsyncClient(cookies=jar) as client:
        url = "https://clients6.google.com/voice/v1/voiceclient/account/get"
        
        # Minimal headers - just what's absolutely necessary
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Origin": "https://voice.google.com",
            "Referer": "https://voice.google.com/",
            "Authorization": generate_sapisid_hash(COOKIES["SAPISID"]),
            "Content-Type": "application/json+protobuf"
        }
        
        params = {"key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg"}
        body = json.dumps([None, 1])
        
        print("Testing with minimal request and cookie jar...")
        print(f"Authorization: {headers['Authorization']}")
        print()
        
        try:
            response = await client.post(url, params=params, headers=headers, content=body)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Success!")
                print(f"Response length: {len(response.content)}")
            else:
                print(f"❌ Failed: {response.text[:500]}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

async def test_different_api_key():
    """Test with different or no API key"""
    jar = httpx.Cookies()
    for name, value in COOKIES.items():
        jar.set(name, value, domain=".google.com")
        
    async with httpx.AsyncClient(cookies=jar) as client:
        url = "https://clients6.google.com/voice/v1/voiceclient/account/get"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Origin": "https://voice.google.com",
            "Referer": "https://voice.google.com/",
            "Authorization": generate_sapisid_hash(COOKIES["SAPISID"]),
            "Content-Type": "application/json+protobuf"
        }
        
        # Try without API key
        body = json.dumps([None, 1])
        
        print("\nTesting without API key...")
        
        try:
            response = await client.post(url, headers=headers, content=body)
            print(f"Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"Response: {response.text[:200]}")
        except Exception as e:
            print(f"❌ Error: {e}")

async def test_send_sms_endpoint():
    """Test the SMS endpoint which might have different auth requirements"""
    jar = httpx.Cookies()
    for name, value in COOKIES.items():
        jar.set(name, value, domain=".google.com")
        
    async with httpx.AsyncClient(cookies=jar) as client:
        url = "https://clients6.google.com/voice/v1/voiceclient/api2thread/sendsms"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Origin": "https://voice.google.com",
            "Referer": "https://voice.google.com/",
            "Authorization": generate_sapisid_hash(COOKIES["SAPISID"]),
            "Content-Type": "application/json+protobuf"
        }
        
        params = {"key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg"}
        
        # SMS request with minimal fields
        # [field1, field2, field3, field4, text(5), threadID(6), recipients(7), field8, transactionID(9), media(10), trackingData(11)]
        body = json.dumps([
            None, None, None, None, 
            "Test message",  # text field 5
            None,  # threadID field 6 (optional for new conversation)
            ["+13602415033"],  # recipients field 7
            None,  # field 8
            [42],  # transactionID field 9 - wrapped in array for WrappedTxnID
            None,  # media field 10
            ["!"]  # trackingData field 11 - simple signature
        ])
        
        print("\nTesting SMS send endpoint...")
        print(f"Body: {body}")
        
        try:
            response = await client.post(url, params=params, headers=headers, content=body)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SMS endpoint works!")
            elif response.status_code == 403:
                print("❌ 403 - might need WAA signatures")
            else:
                print(f"❌ SMS failed: {response.text[:300]}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_with_minimal_request())
    asyncio.run(test_different_api_key())
    asyncio.run(test_send_sms_endpoint())