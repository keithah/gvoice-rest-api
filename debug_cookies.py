#!/usr/bin/env python3
"""
Debug cookie handling - check if cookies are being sent properly
"""
import asyncio
import httpx
import json
import hashlib
import time

# Fresh cookies
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

async def test_with_manual_cookie_header():
    """Try manually setting Cookie header instead of using httpx cookies parameter"""
    async with httpx.AsyncClient() as client:
        url = "https://clients6.google.com/voice/v1/voiceclient/account/get"
        
        # Build cookie string manually
        cookie_string = "; ".join(f"{k}={v}" for k, v in ALL_COOKIES.items())
        
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Origin": "https://voice.google.com",
            "Referer": "https://voice.google.com/",
            "Authorization": generate_sapisid_hash(ALL_COOKIES["SAPISID"]),
            "Cookie": cookie_string,
            "X-Client-Version": "665865172",
            "X-Goog-AuthUser": "0",
            "Content-Type": "application/json+protobuf",
            "Accept": "*/*"
        }
        
        params = {
            "key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
            "alt": "proto"
        }
        
        body = json.dumps([None, 1])
        
        print("Testing with manual Cookie header...")
        print(f"Cookie length: {len(cookie_string)} chars")
        print(f"Authorization: {headers['Authorization']}")
        print(f"SAPISID: {ALL_COOKIES['SAPISID']}")
        print()
        
        try:
            response = await client.post(url, params=params, headers=headers, content=body)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Success with manual cookie header!")
            elif response.status_code == 401:
                print("❌ Still 401 with manual cookie header")
                # Check if server is setting new cookies
                set_cookies = response.headers.get('set-cookie', '')
                if set_cookies:
                    print(f"Server trying to set cookies: {set_cookies[:200]}...")
            else:
                print(f"❌ Other error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {str(e)}")

async def test_simple_get_request():
    """Test a simple GET request to see if cookies work at all"""
    async with httpx.AsyncClient() as client:
        # Try accessing the main Google Voice page
        url = "https://voice.google.com/"
        
        cookie_string = "; ".join(f"{k}={v}" for k, v in ALL_COOKIES.items())
        
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Cookie": cookie_string,
        }
        
        print("\nTesting simple GET to voice.google.com...")
        
        try:
            response = await client.get(url, headers=headers, follow_redirects=False)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Can access Google Voice main page")
                if "Google Voice" in response.text:
                    print("✅ Page contains 'Google Voice' - authenticated")
                else:
                    print("⚠️ Page doesn't contain expected content")
            elif response.status_code in [301, 302]:
                location = response.headers.get('location', 'unknown')
                print(f"⚠️ Redirected to: {location}")
            else:
                print(f"❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_simple_get_request())
    asyncio.run(test_with_manual_cookie_header())