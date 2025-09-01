#!/usr/bin/env python3
"""
Working API test with proper Google Voice authentication
"""
import asyncio
import json
import time
import hashlib
import random
import httpx
from datetime import datetime
from typing import Dict


async def test_google_voice_api():
    """Test Google Voice API with proper authentication format"""
    
    # Load fresh cookies
    with open('fresh_cookies.json', 'r') as f:
        cookies = json.load(f)
    
    print("🔑 Testing Google Voice API with fresh authentication...")
    print(f"🍪 Using {len(cookies)} cookies")
    
    # Build proper cookie string
    cookie_header = "; ".join([f"{name}={value}" for name, value in cookies.items()])
    
    async with httpx.AsyncClient() as client:
        
        # Test 1: Basic account info
        print("\n1️⃣ Testing account endpoint...")
        account_success = await test_account_endpoint(client, cookies, cookie_header)
        
        if account_success:
            print("✅ Authentication working!")
            
            # Test 2: Try SMS sending
            print("\n2️⃣ Testing SMS sending...")
            sms_success = await test_sms_sending(client, cookies, cookie_header)
            
            return sms_success
        else:
            print("❌ Authentication failed")
            return False


async def test_account_endpoint(client: httpx.AsyncClient, cookies: Dict[str, str], cookie_header: str) -> bool:
    """Test account endpoint with proper auth"""
    try:
        url = "https://clients6.google.com/voice/v1/voiceclient/account/get"
        
        # Generate proper SAPISID hash
        sapisid = cookies.get("SAPISID", "")
        timestamp = int(time.time())
        hash_input = f"{timestamp} {sapisid} https://voice.google.com"
        hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
        auth_header = f"SAPISIDHASH {timestamp}_{hash_value}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Cookie": cookie_header,
            "Authorization": auth_header,
            "X-Goog-Api-Key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
            "X-Client-Version": "665865172", 
            "X-Goog-AuthUser": "0",
            "Content-Type": "application/json+protobuf",
            "Origin": "https://voice.google.com",
            "Referer": "https://voice.google.com/",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        params = {"key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg", "alt": "proto"}
        body = json.dumps([{"unknownInt2": 1}])
        
        response = await client.post(url, params=params, headers=headers, content=body)
        
        print(f"   📤 Account status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Account data received: {len(response.content)} bytes")
            return True
        else:
            print(f"   ❌ Account failed: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ Account error: {e}")
        return False


async def test_sms_sending(client: httpx.AsyncClient, cookies: Dict[str, str], cookie_header: str) -> bool:
    """Test SMS sending with various WAA approaches"""
    try:
        url = "https://clients6.google.com/voice/v1/voiceclient/api2thread/sendsms"
        recipient = "3602415033"
        message = f"API Test {datetime.now().strftime('%H:%M:%S')}"
        
        # Generate auth
        sapisid = cookies.get("SAPISID", "")
        timestamp = int(time.time())
        hash_input = f"{timestamp} {sapisid} https://voice.google.com"
        hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
        auth_header = f"SAPISIDHASH {timestamp}_{hash_value}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Cookie": cookie_header,
            "Authorization": auth_header,
            "X-Goog-Api-Key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
            "X-Client-Version": "665865172",
            "X-Goog-AuthUser": "0",
            "Content-Type": "application/json+protobuf",
            "Origin": "https://voice.google.com", 
            "Referer": "https://voice.google.com/",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        params = {"key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg", "alt": "proto"}
        
        # Try different WAA signatures
        waa_signatures = [
            "!",  # Standard
            "",   # Empty
            f"fake_{int(time.time())}",  # Time-based fake
            generate_complex_waa(recipient, message)  # Complex fake
        ]
        
        for i, waa in enumerate(waa_signatures):
            transaction_id = random.randint(1, 99999999999999)
            
            print(f"\n   🔐 SMS Attempt {i+1}: WAA = {repr(waa)}")
            
            body = json.dumps([
                None, None, None, None,
                message,
                None,  # thread_id
                [recipient],
                None,
                [transaction_id],
                None,
                [waa]
            ])
            
            response = await client.post(url, params=params, headers=headers, content=body)
            
            print(f"   📤 SMS Response: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   🎉 SUCCESS! SMS sent with WAA: {repr(waa)}")
                return True
            else:
                error = response.text
                if "FAILED_PRECONDITION" in error:
                    print(f"   🚫 Anti-automation detected")
                elif "unsafe" in error:
                    print(f"   🔒 Security policy blocked")
                else:
                    print(f"   ❌ Error: {error[:100]}...")
        
        return False
        
    except Exception as e:
        print(f"❌ SMS error: {e}")
        return False


def generate_complex_waa(recipient: str, message: str) -> str:
    """Generate complex WAA signature"""
    timestamp = int(time.time())
    data = f"{recipient}:{message}:{timestamp}"
    hash1 = hashlib.md5(data.encode()).hexdigest()[:16]
    hash2 = hashlib.sha1(data.encode()).hexdigest()[:16] 
    return f"{hash1}-{hash2}-{timestamp}"


if __name__ == "__main__":
    success = asyncio.run(test_google_voice_api())
    print(f"\n{'='*60}")
    print(f"Final Result: {'SUCCESS' if success else 'FAILED'}")
    print(f"{'='*60}")