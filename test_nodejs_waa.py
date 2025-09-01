#!/usr/bin/env python3
"""
Test Node.js WAA server
"""
import asyncio
import json
import httpx
from datetime import datetime


async def test_nodejs_waa():
    """Test the Node.js WAA server"""
    
    # Load fresh cookies
    with open('fresh_cookies.json', 'r') as f:
        cookies = json.load(f)
    
    async with httpx.AsyncClient() as client:
        try:
            print("="*70)
            print("🚀 TESTING NODE.JS WAA SERVER")
            print("="*70)
            
            # Check if server is running
            print("🔍 Checking server health...")
            try:
                health = await client.get("http://localhost:3002/health")
                if health.status_code == 200:
                    print("✅ Node.js WAA server is running")
                else:
                    print("❌ Server not responding")
                    return False
            except Exception as e:
                print(f"❌ Cannot reach server: {e}")
                return False
            
            # Initialize WAA
            print("\n🔧 Initializing WAA...")
            init_response = await client.post(
                "http://localhost:3002/initialize",
                json={"cookies": cookies},
                timeout=60.0
            )
            
            if init_response.status_code == 200:
                init_result = init_response.json()
                if init_result.get("success"):
                    print("✅ WAA initialized successfully")
                else:
                    print(f"❌ WAA init failed: {init_result.get('error')}")
                    return False
            else:
                print(f"❌ Init request failed: {init_response.status_code}")
                return False
            
            # Send SMS
            print("\n📱 Sending SMS with Node.js WAA...")
            sms_response = await client.post(
                "http://localhost:3002/send-sms",
                json={
                    "cookies": cookies,
                    "recipient": "3602415033",  # Replace with your number
                    "message": f"Node.js WAA Test {datetime.now().strftime('%H:%M:%S')}",
                    "threadId": ""
                },
                timeout=30.0
            )
            
            if sms_response.status_code == 200:
                result = sms_response.json()
                print(f"\n📊 SMS Result:")
                print(json.dumps(result, indent=2))
                
                if result.get("success"):
                    print("\n🎉🎉🎉 SUCCESS! NODE.JS WAA SMS SENT! 🎉🎉🎉")
                    print(f"Signature type: {result.get('signatureType', 'unknown')}")
                    return True
                else:
                    print(f"\n❌ SMS failed: {result.get('error')}")
                    
                    # Analyze the error
                    error = result.get('error', '')
                    if 'FAILED_PRECONDITION' in error:
                        print("🚫 Google detected automation despite WAA")
                    elif 'authentication' in error.lower():
                        print("🔑 Authentication issue")
                    elif 'unsafe' in error:
                        print("🔒 Security policy violation")
                    
                    return False
            else:
                print(f"❌ SMS request failed: {sms_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Test error: {e}")
            return False


if __name__ == "__main__":
    success = asyncio.run(test_nodejs_waa())
    
    print("\n" + "="*70)
    if success:
        print("✅ Node.js WAA test PASSED!")
        print("The system successfully sent SMS using Node.js + Puppeteer WAA!")
    else:
        print("❌ Node.js WAA test FAILED")
        print("Check server logs and error messages above")
    print("="*70)