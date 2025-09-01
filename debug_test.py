#!/usr/bin/env python3
"""
Debug test to check Google Voice authentication
"""
import asyncio
import httpx
import json
from datetime import datetime
import hashlib
import time

# Your cookies
COOKIES = {
    "SAPISID": "GjfTX7q-BcEw9cRE/Ao7WL3H89RBOSiG9Q",
    "HSID": "AcvDwpgrPA3Np_b_f",
    "SSID": "AQZcF9pzX7SCL1ZFK", 
    "APISID": "qW3CGJXrJMAUgDnq/AE0szFtN-ymXjEyZJ",
    "SID": "g.a0000gjAouZjfqg3cumlvmMVeSS0xZt2ZSXhXLVevEHnt_drASD_ijoJR-Izp-O4cqXDy9kHbgACgYKAZESARISFQHGX2MiupijAjtQdfaeCxpLUdc4TRoVAUF8yKpy_aQqwYTGWecKLJI_Fe9u0076"
}

def generate_sapisid_hash(sapisid: str) -> str:
    """Generate SAPISID hash for authorization"""
    timestamp = int(time.time())
    origin = "https://voice.google.com"
    hash_input = f"{timestamp} {sapisid} {origin}"
    hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
    return f"SAPISIDHASH {timestamp}_{hash_value}"

async def test_auth():
    """Test Google Voice authentication"""
    async with httpx.AsyncClient() as client:
        # Test endpoint - get account
        url = "https://clients6.google.com/voice/v1/voiceclient/account/get"
        
        # Prepare headers
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Origin": "https://voice.google.com",
            "Referer": "https://voice.google.com/",
            "Authorization": generate_sapisid_hash(COOKIES["SAPISID"]),
            "Cookie": "; ".join(f"{k}={v}" for k, v in COOKIES.items()),
            "X-Client-Version": "665865172",
            "X-Goog-AuthUser": "0",
            "Content-Type": "application/json+protobuf"
        }
        
        # Request params
        params = {
            "key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
            "alt": "proto"
        }
        
        # Simple request body
        body = json.dumps({"unknown_int2": 1})
        
        print("Testing Google Voice authentication...")
        print(f"URL: {url}")
        print(f"Authorization: {headers['Authorization']}")
        print()
        
        try:
            response = await client.post(url, params=params, headers=headers, content=body)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("\n✅ Authentication successful!")
                print("Response body (first 500 chars):")
                print(response.text[:500])
            else:
                print("\n❌ Authentication failed!")
                print(f"Response body: {response.text}")
                
        except Exception as e:
            print(f"\n❌ Error: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_auth())