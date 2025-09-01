#!/usr/bin/env python3
"""
Test accessing the actual Google Voice app interface
"""
import asyncio
import httpx
import hashlib
import time
import json

# Fresh cookies
COOKIES = {
    "SAPISID": "GjfTX7q-BcEw9cRE/Ao7WL3H89RBOSiG9Q",
    "HSID": "AcvDwpgrPA3Np_b_f",
    "SSID": "AQZcF9pzX7SCL1ZFK",
    "APISID": "qW3CGJXrJMAUgDnq/AE0szFtN-ymXjEyZJ",
    "SID": "g.a0000gjAouZjfqg3cumlvmMVeSS0xZt2ZSXhXLVevEHnt_drASD_ijoJR-Izp-O4cqXDy9kHbgACgYKAZESARISFQHGX2MiupijAjtQdfaeCxpLUdc4TRoVAUF8yKpy_aQqwYTGWecKLJI_Fe9u0076",
    "__Secure-1PSID": "g.a0000gjAouZjfqg3cumlvmMVeSS0xZt2ZSXhXLVevEHnt_drASD_ACFxn0xOc9CMuXZDoCh6MQACgYKAXgSARISFQHGX2MiAXyXyiEpN7UtygQt0TlP8xoVAUF8yKqPNr0X_HgXcnaZXEVgGv9J0076",
    "__Secure-3PSID": "g.a0000gjAouZjfqg3cumlvmMVeSS0xZt2ZSXhXLVevEHnt_drASD_zEjJOei8xRfARwAwgpC0HwACgYKAUoSARISFQHGX2MiA32MnMBazgKNO7auwcDsmBoVAUF8yKq360zWEBlBY1cwl2rg5uNr0076",
    "COMPASS": "voice-web-frontend=CgAQ0IXCxQYaXgAJa4lX_sZ31YHPtuSrdPAVDdGsVPZPzjqrGKPkj_G7pZKHq_zulxeR8gf5mFwl2HCkG4k7aOLc5UF2O1tfN5S1KQwqbsIv2NfvCpsc0nWfuN7Sk7FTuy-zX9N3qmowAQ"
}

def generate_sapisid_hash(sapisid: str, origin: str = "https://voice.google.com") -> str:
    timestamp = int(time.time())
    hash_input = f"{timestamp} {sapisid} {origin}"
    hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
    return f"SAPISIDHASH {timestamp}_{hash_value}"

async def test_voice_web_app():
    """Access the actual Google Voice web app interface"""
    jar = httpx.Cookies()
    for name, value in COOKIES.items():
        jar.set(name, value, domain=".google.com")
    
    async with httpx.AsyncClient(cookies=jar, follow_redirects=False) as client:
        # Try different Voice URLs that should load the actual app
        voice_urls = [
            "https://voice.google.com/u/0/messages",
            "https://voice.google.com/u/0/",
            "https://voice.google.com/u/0/calls",
            "https://voice.google.com/u/0"
        ]
        
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        
        print("Testing Google Voice app URLs...")
        
        for url in voice_urls:
            print(f"\n  Testing: {url}")
            try:
                response = await client.get(url, headers=headers)
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    content = response.text
                    if "Google Voice" in content:
                        print(f"  ✅ Accessed Google Voice app at {url}")
                        print(f"  Content length: {len(content)} bytes")
                        
                        # Now try API call immediately after
                        await test_api_after_app_access(client)
                        return
                    else:
                        print(f"  ⚠️ Page loaded but no 'Google Voice' found")
                elif response.status_code in [301, 302]:
                    location = response.headers.get('location', '')
                    print(f"  ⚠️ Redirected to: {location}")
                else:
                    print(f"  ❌ Failed with status: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")

async def test_api_after_app_access(client):
    """Test API call using same client after accessing the app"""
    print("\n  Testing API call with same session...")
    
    url = "https://clients6.google.com/voice/v1/voiceclient/account/get"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Origin": "https://voice.google.com",
        "Referer": "https://voice.google.com/u/0/messages",
        "Authorization": generate_sapisid_hash(COOKIES["SAPISID"]),
        "Content-Type": "application/json+protobuf",
        "X-Client-Version": "665865172",
        "X-Goog-AuthUser": "0",
    }
    
    params = {"key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg", "alt": "proto"}
    body = json.dumps([None, 1])
    
    try:
        response = await client.post(url, params=params, headers=headers, content=body)
        
        if response.status_code == 200:
            print("  ✅ API call succeeded after app access!")
        else:
            print(f"  ❌ API call still failed: {response.status_code}")
            if response.status_code == 401:
                print("  Still getting 401 authentication error")
                
    except Exception as e:
        print(f"  ❌ API error: {e}")

async def test_manual_browser_simulation():
    """Simulate exact browser workflow"""
    jar = httpx.Cookies()
    for name, value in COOKIES.items():
        jar.set(name, value, domain=".google.com")
    
    async with httpx.AsyncClient(cookies=jar, follow_redirects=True) as client:
        print("\nSimulating browser workflow...")
        
        # Step 1: Visit main Google Voice page
        print("1. Visiting voice.google.com...")
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        response1 = await client.get("https://voice.google.com/", headers=headers)
        print(f"   Status: {response1.status_code}, Final URL: {response1.url}")
        
        # Step 2: Try to access messages page directly
        print("2. Accessing messages page...")
        response2 = await client.get("https://voice.google.com/u/0/messages", headers=headers)
        print(f"   Status: {response2.status_code}, Final URL: {response2.url}")
        
        # Step 3: Now try API call with fresh headers
        print("3. Making API call...")
        
        api_headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Sec-Ch-Ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Linux"',
            "Origin": "https://voice.google.com",
            "Referer": "https://voice.google.com/u/0/messages",
            "Authorization": generate_sapisid_hash(COOKIES["SAPISID"]),
            "X-Client-Version": "665865172",
            "X-Goog-AuthUser": "0",
            "Content-Type": "application/json+protobuf",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        }
        
        api_url = "https://clients6.google.com/voice/v1/voiceclient/account/get"
        params = {"key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg", "alt": "proto"}
        body = json.dumps([None, 1])
        
        api_response = await client.post(api_url, params=params, headers=api_headers, content=body)
        
        print(f"   API Status: {api_response.status_code}")
        if api_response.status_code == 200:
            print("   ✅ API call successful!")
            print(f"   Response length: {len(api_response.content)} bytes")
        else:
            print(f"   ❌ API failed: {api_response.text[:200]}...")

if __name__ == "__main__":
    asyncio.run(test_voice_web_app())
    asyncio.run(test_manual_browser_simulation())