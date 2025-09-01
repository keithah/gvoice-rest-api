#!/usr/bin/env python3
"""
Validate Google Voice cookies
"""
import asyncio
import httpx
import json
from datetime import datetime


async def validate_cookies():
    """Test if the cookies are valid for Google Voice"""
    
    print("🍪 COOKIE VALIDATION TEST")
    print("="*50)
    
    # Load cookies
    with open('fresh_cookies.json', 'r') as f:
        cookies = json.load(f)
    
    print(f"✅ Loaded {len(cookies)} cookies")
    
    # Convert to httpx format
    cookie_jar = {}
    for name, value in cookies.items():
        cookie_jar[name] = value
    
    async with httpx.AsyncClient(cookies=cookie_jar, timeout=30.0) as client:
        
        # Test 1: Basic Google Voice account access
        print("\n1️⃣ Testing Google Voice account access...")
        try:
            response = await client.get("https://voice.google.com/u/0/")
            print(f"📄 Homepage: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                if "voice.google.com" in content and "Google Voice" in content:
                    print("✅ Successfully accessed Google Voice homepage")
                else:
                    print("⚠️ Unexpected homepage content")
                    
            else:
                print(f"❌ Homepage access failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Homepage error: {e}")
            return False
        
        # Test 2: Account info API
        print("\n2️⃣ Testing account info API...")
        try:
            # Generate SAPISID hash
            timestamp = int(datetime.utcnow().timestamp())
            sapisid = cookies.get('SAPISID', '')
            
            if not sapisid:
                print("❌ No SAPISID cookie found")
                return False
            
            import hashlib
            hash_input = f"{timestamp} {sapisid} https://voice.google.com"
            hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
            auth_header = f"SAPISIDHASH {timestamp}_{hash_value}"
            
            headers = {
                'Authorization': auth_header,
                'X-Goog-Api-Key': 'AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg',
                'X-Client-Version': '665865172',
                'Content-Type': 'application/json+protobuf',
                'Origin': 'https://voice.google.com',
                'Referer': 'https://voice.google.com/',
                'X-Goog-AuthUser': '0'
            }
            
            response = await client.post(
                "https://clients6.google.com/voice/v1/voiceclient/account/get?key=AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg&alt=proto",
                headers=headers,
                content=b'[]'
            )
            
            print(f"🔐 Account API: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Account API access successful")
                account_data = response.text[:200]
                print(f"📄 Account data preview: {account_data}")
            else:
                print(f"❌ Account API failed: {response.status_code}")
                print(f"📄 Error: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Account API error: {e}")
            return False
        
        # Test 3: Check if cookies are personal vs workspace
        print("\n3️⃣ Checking account type...")
        try:
            response = await client.get("https://voice.google.com/u/0/settings")
            content = response.text
            
            if "workspace.google.com" in content:
                print("⚠️ Cookies appear to be for Google Workspace Voice")
                print("💡 You may need personal Google Voice cookies instead")
            elif "voice.google.com" in content:
                print("✅ Cookies appear to be for personal Google Voice")
            else:
                print("❓ Cannot determine account type")
                
        except Exception as e:
            print(f"⚠️ Account type check failed: {e}")
        
        return True


if __name__ == "__main__":
    success = asyncio.run(validate_cookies())
    print(f"\n{'='*60}")
    print(f"🍪 COOKIE STATUS: {'VALID' if success else 'INVALID'}")
    print(f"{'='*60}")