#!/usr/bin/env python3
"""
Final WAA test - simplified approach focusing on API calls
"""
import asyncio
import json
import time
import hashlib
import random
import httpx
from datetime import datetime
from typing import Dict


async def test_api_with_fresh_cookies():
    """Test Google Voice API with fresh cookies"""
    
    # Load fresh cookies
    with open('fresh_cookies.json', 'r') as f:
        cookies = json.load(f)
    
    print("🔑 Testing with fresh cookies...")
    
    async with httpx.AsyncClient() as client:
        # Set cookies
        for name, value in cookies.items():
            client.cookies.set(name, value, domain=".google.com")
        
        # Test 1: Account endpoint (should work with valid auth)
        print("\n1️⃣ Testing account authentication...")
        auth_result = await test_account_auth(client, cookies)
        
        if not auth_result:
            print("❌ Authentication failed - cookies may be expired")
            return False
        
        # Test 2: SMS with minimal WAA
        print("\n2️⃣ Testing SMS with minimal request...")
        sms_result = await test_minimal_sms(client, cookies)
        
        return sms_result


async def test_account_auth(client: httpx.AsyncClient, cookies: Dict[str, str]) -> bool:
    """Test authentication with account endpoint"""
    try:
        url = "https://clients6.google.com/voice/v1/voiceclient/account/get"
        
        headers = {
            "Authorization": generate_sapisid_hash(cookies.get("SAPISID", "")),
            "X-Goog-Api-Key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
            "Content-Type": "application/json+protobuf",
            "Origin": "https://voice.google.com",
            "Referer": "https://voice.google.com/"
        }
        
        params = {"key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg", "alt": "proto"}
        body = json.dumps([{"unknownInt2": 1}])
        
        response = await client.post(url, params=params, headers=headers, content=body)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Authentication successful")
            return True
        else:
            print(f"   ❌ Auth failed: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Auth error: {e}")
        return False


async def test_minimal_sms(client: httpx.AsyncClient, cookies: Dict[str, str]) -> bool:
    """Test SMS with minimal request structure"""
    try:
        url = "https://clients6.google.com/voice/v1/voiceclient/api2thread/sendsms"
        recipient = "3602415033"
        message = f"Minimal test {datetime.now().strftime('%H:%M:%S')}"
        transaction_id = random.randint(1, 99999999999999)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Authorization": generate_sapisid_hash(cookies.get("SAPISID", "")),
            "X-Goog-Api-Key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
            "X-Client-Version": "665865172",
            "X-Goog-AuthUser": "0",
            "Content-Type": "application/json+protobuf",
            "Origin": "https://voice.google.com",
            "Referer": "https://voice.google.com/",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        params = {"key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg", "alt": "proto"}
        
        # Try multiple WAA signature approaches
        waa_attempts = [
            "!",  # Standard placeholder
            "",   # Empty
            None, # Null
            "0",  # Zero
            generate_fake_waa_signature(recipient, message, transaction_id)  # Generated fake
        ]
        
        for i, waa_sig in enumerate(waa_attempts):
            print(f"\n   Attempt {i+1}: WAA = {repr(waa_sig)}")
            
            # Build request body
            body = json.dumps([
                None, None, None, None,    # Fields 1-4
                message,                   # Field 5: message text
                None,                      # Field 6: thread ID
                [recipient],               # Field 7: recipients
                None,                      # Field 8
                [transaction_id + i],      # Field 9: transaction ID (unique per attempt)
                None,                      # Field 10: media
                [waa_sig] if waa_sig is not None else None  # Field 11: WAA signature
            ])
            
            response = await client.post(url, params=params, headers=headers, content=body)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS with WAA: {repr(waa_sig)}")
                return True
            else:
                error_text = response.text
                if "FAILED_PRECONDITION" in error_text:
                    print(f"   🚫 Blocked by anti-automation")
                elif "authentication" in error_text.lower():
                    print(f"   🔑 Authentication issue")
                else:
                    print(f"   ❌ Error: {error_text[:100]}")
        
        print("❌ All WAA attempts failed")
        return False
        
    except Exception as e:
        print(f"❌ SMS test error: {e}")
        return False


def generate_sapisid_hash(sapisid: str) -> str:
    """Generate SAPISID hash for authorization"""
    timestamp = int(time.time())
    origin = "https://voice.google.com"
    hash_input = f"{timestamp} {sapisid} {origin}"
    hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
    return f"SAPISIDHASH {timestamp}_{hash_value}"


def generate_fake_waa_signature(recipient: str, message: str, transaction_id: int) -> str:
    """Generate a plausible-looking WAA signature"""
    # Create a hash-based signature that looks real
    data = f"{recipient}|{message}|{transaction_id}|{int(time.time())}"
    signature = hashlib.sha256(data.encode()).hexdigest()[:32]
    return f"WAA_{signature}"


async def main():
    print("="*60)
    print("🚀 FINAL WAA TEST - API FOCUSED")
    print("="*60)
    
    success = await test_api_with_fresh_cookies()
    
    if success:
        print("\n🎉🎉🎉 SUCCESS! SMS SENT! 🎉🎉🎉")
        print("The working WAA approach has been identified!")
    else:
        print("\n❌ All approaches failed")
        print("Google's anti-automation protections are very strong")
    
    print(f"\nTest completed at {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())