#!/usr/bin/env python3
"""
Debug account type and Voice service access
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

async def check_account_info():
    """Check what type of account this is"""
    jar = httpx.Cookies()
    for name, value in COOKIES.items():
        jar.set(name, value, domain=".google.com")
    
    async with httpx.AsyncClient(cookies=jar, follow_redirects=False) as client:
        print("Checking account type and service access...")
        
        # Check different Google services to understand account type
        test_urls = [
            ("Gmail", "https://mail.google.com/"),
            ("Google Drive", "https://drive.google.com/"),
            ("Google Account", "https://myaccount.google.com/"),
            ("Old Voice", "https://www.google.com/voice"),
            ("Voice Legacy", "https://voice.google.com/legacy"),
            ("Voice Settings", "https://voice.google.com/settings"),
        ]
        
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        for service, url in test_urls:
            print(f"\n{service}: {url}")
            try:
                response = await client.get(url, headers=headers)
                print(f"  Status: {response.status_code}")
                
                if response.status_code in [301, 302]:
                    location = response.headers.get('location', '')
                    print(f"  Redirects to: {location}")
                elif response.status_code == 200:
                    if "sign in" in response.text.lower() or "login" in response.text.lower():
                        print(f"  ❌ Not authenticated to {service}")
                    else:
                        print(f"  ✅ Authenticated to {service}")
                        
            except Exception as e:
                print(f"  ❌ Error: {e}")

async def test_different_auth_user():
    """Test with different X-Goog-AuthUser values"""
    jar = httpx.Cookies()
    for name, value in COOKIES.items():
        jar.set(name, value, domain=".google.com")
    
    async with httpx.AsyncClient(cookies=jar) as client:
        url = "https://clients6.google.com/voice/v1/voiceclient/account/get"
        
        # Test different auth user values (0-9)
        print("\nTesting different X-Goog-AuthUser values...")
        
        for auth_user in range(10):
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Origin": "https://voice.google.com",
                "Referer": "https://voice.google.com/",
                "Authorization": f"SAPISIDHASH {int(time.time())}_" + hashlib.sha1(f"{int(time.time())} {COOKIES['SAPISID']} https://voice.google.com".encode()).hexdigest(),
                "Content-Type": "application/json+protobuf",
                "X-Goog-AuthUser": str(auth_user)
            }
            
            params = {"key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg", "alt": "proto"}
            body = json.dumps([None, 1])
            
            try:
                response = await client.post(url, params=params, headers=headers, content=body)
                
                if response.status_code == 200:
                    print(f"  ✅ SUCCESS with AuthUser={auth_user}!")
                    return auth_user
                elif response.status_code != 401:
                    print(f"  ⚠️ AuthUser={auth_user}: {response.status_code}")
                else:
                    print(f"  ❌ AuthUser={auth_user}: 401")
                    
            except Exception as e:
                print(f"  ❌ AuthUser={auth_user}: {e}")
        
        return None

async def test_workspace_voice_api():
    """Test if there's a different API endpoint for workspace accounts"""
    jar = httpx.Cookies()
    for name, value in COOKIES.items():
        jar.set(name, value, domain=".google.com")
    
    async with httpx.AsyncClient(cookies=jar) as client:
        print("\nTesting workspace/business Google Voice endpoints...")
        
        # Different potential API endpoints
        test_endpoints = [
            "https://voice-pa.googleapis.com/v1/accounts:get",
            "https://businesscommunications.googleapis.com/v1/brands",
            "https://voice.googleapis.com/v1/accounts",
            "https://clients6.google.com/voice/v1/voiceclient/account/get",
            "https://voice.google.com/voice/v1/voiceclient/account/get"
        ]
        
        for endpoint in test_endpoints:
            print(f"  Testing: {endpoint}")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Authorization": f"SAPISIDHASH {int(time.time())}_" + hashlib.sha1(f"{int(time.time())} {COOKIES['SAPISID']} https://voice.google.com".encode()).hexdigest(),
                "Content-Type": "application/json+protobuf",
            }
            
            try:
                response = await client.post(endpoint, headers=headers, json={})
                
                if response.status_code == 200:
                    print(f"    ✅ SUCCESS!")
                    return endpoint
                elif response.status_code == 404:
                    print(f"    ❌ 404 - Endpoint doesn't exist")
                elif response.status_code == 401:
                    print(f"    ❌ 401 - Auth failed")
                else:
                    print(f"    ⚠️ {response.status_code}")
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")
                
        return None

if __name__ == "__main__":
    asyncio.run(check_account_info())
    asyncio.run(test_different_auth_user()) 
    asyncio.run(test_workspace_voice_api())