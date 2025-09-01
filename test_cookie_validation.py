#!/usr/bin/env python3
"""
Test to validate if cookies are working by testing different Google services
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
    "__Secure-3PSID": "g.a0000gjAouZjfqg3cumlvmMVeSS0xZt2ZSXhXLVevEHnt_drASD_zEjJOei8xRfARwAwgpC0HwACgYKAUoSARISFQHGX2MiA32MnMBazgKNO7auwcDsmBoVAUF8yKq360zWEBlBY1cwl2rg5uNr0076"
}

def generate_sapisid_hash(sapisid: str, origin: str = "https://voice.google.com") -> str:
    timestamp = int(time.time())
    hash_input = f"{timestamp} {sapisid} {origin}"
    hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
    return f"SAPISIDHASH {timestamp}_{hash_value}"

async def test_voice_main_page():
    """Test if we can access Google Voice main page with authentication"""
    jar = httpx.Cookies()
    for name, value in COOKIES.items():
        jar.set(name, value, domain=".google.com")
        
    async with httpx.AsyncClient(cookies=jar, follow_redirects=True) as client:
        url = "https://voice.google.com/"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        }
        
        print("Testing Google Voice main page access...")
        
        try:
            response = await client.get(url, headers=headers)
            print(f"Status Code: {response.status_code}")
            print(f"Final URL: {response.url}")
            
            if response.status_code == 200:
                # Check for authentication indicators
                content = response.text
                if "messages" in content.lower() or "conversations" in content.lower():
                    print("✅ Successfully authenticated to Google Voice!")
                elif "sign in" in content.lower() or "login" in content.lower():
                    print("❌ Not authenticated - page asking for login")
                else:
                    print("⚠️ Unclear authentication status")
                    print(f"Page title: {content[content.find('<title>'):content.find('</title>')+8] if '<title>' in content else 'No title found'}")
            else:
                print(f"❌ Failed to access main page: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

async def test_sapisid_variations():
    """Test different SAPISID hash variations"""
    jar = httpx.Cookies()
    for name, value in COOKIES.items():
        jar.set(name, value, domain=".google.com")
        
    async with httpx.AsyncClient(cookies=jar) as client:
        url = "https://clients6.google.com/voice/v1/voiceclient/account/get"
        
        # Test different origins for SAPISID hash
        test_origins = [
            "https://voice.google.com",
            "https://clients6.google.com",
            "https://google.com",
            "https://voice.google.com/",  # with trailing slash
        ]
        
        params = {"key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg"}
        body = json.dumps([None, 1])
        
        print("\nTesting different SAPISID hash origins...")
        
        for origin in test_origins:
            auth_hash = generate_sapisid_hash(COOKIES["SAPISID"], origin)
            
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Origin": "https://voice.google.com",
                "Referer": "https://voice.google.com/",
                "Authorization": auth_hash,
                "Content-Type": "application/json+protobuf"
            }
            
            print(f"  Testing origin: {origin}")
            
            try:
                response = await client.post(url, params=params, headers=headers, content=body)
                if response.status_code == 200:
                    print(f"  ✅ SUCCESS with origin: {origin}")
                    return  # Stop on first success
                else:
                    print(f"  ❌ {response.status_code} with origin: {origin}")
            except Exception as e:
                print(f"  ❌ Error with origin {origin}: {e}")

async def test_raw_cookie_string():
    """Test by examining the exact cookie string being sent"""
    jar = httpx.Cookies()
    for name, value in COOKIES.items():
        jar.set(name, value, domain=".google.com")
    
    # Print what cookies would be sent
    print("\nCookies that would be sent to clients6.google.com:")
    for cookie in jar:
        if "google.com" in cookie.domain and cookie.name in COOKIES:
            print(f"  {cookie.name}={cookie.value[:50]}{'...' if len(cookie.value) > 50 else ''}")
    
    # Test with both domain variants
    domains_to_test = [".google.com", "google.com", "clients6.google.com"]
    
    for domain in domains_to_test:
        print(f"\nTesting with cookies set for domain: {domain}")
        
        test_jar = httpx.Cookies()
        for name, value in COOKIES.items():
            test_jar.set(name, value, domain=domain)
            
        async with httpx.AsyncClient(cookies=test_jar) as client:
            url = "https://clients6.google.com/voice/v1/voiceclient/account/get"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Origin": "https://voice.google.com",
                "Referer": "https://voice.google.com/",
                "Authorization": generate_sapisid_hash(COOKIES["SAPISID"]),
                "Content-Type": "application/json+protobuf"
            }
            
            params = {"key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg"}
            body = json.dumps([None, 1])
            
            try:
                response = await client.post(url, params=params, headers=headers, content=body)
                if response.status_code == 200:
                    print(f"  ✅ SUCCESS with domain: {domain}")
                    return
                else:
                    print(f"  ❌ {response.status_code} with domain: {domain}")
            except Exception as e:
                print(f"  ❌ Error with domain {domain}: {e}")

if __name__ == "__main__":
    asyncio.run(test_voice_main_page())
    asyncio.run(test_sapisid_variations())
    asyncio.run(test_raw_cookie_string())