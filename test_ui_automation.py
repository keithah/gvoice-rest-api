#!/usr/bin/env python3
"""
Test the UI automation SMS service
"""
import asyncio
import json
import httpx


async def test_ui_automation():
    """Test the UI automation service"""
    
    print("🧪 TESTING UI AUTOMATION SMS SERVICE")
    print("="*50)
    
    # Load fresh cookies
    with open('fresh_cookies.json', 'r') as f:
        cookies = json.load(f)
    
    print(f"✅ Loaded {len(cookies)} cookies")
    
    base_url = "http://localhost:3004"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test 1: Health check
        print("\n1️⃣ Testing health...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                health = response.json()
                print(f"✅ Health: {health}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot reach server: {e}")
            print("💡 Start server with: node ui_automation_sms.js")
            return False
        
        # Test 2: Initialize browser
        print("\n2️⃣ Initializing browser...")
        try:
            response = await client.post(
                f"{base_url}/initialize",
                json={"cookies": cookies},
                timeout=45.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Init: {result}")
                if not result.get("success"):
                    return False
            else:
                print(f"❌ Init failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Init error: {e}")
            return False
        
        # Test 3: Send SMS
        print("\n3️⃣ Sending SMS...")
        try:
            sms_data = {
                "recipient": "3602415033",
                "message": f"UI Automation Test {asyncio.get_event_loop().time():.0f}"
            }
            
            response = await client.post(
                f"{base_url}/send-sms",
                json=sms_data,
                timeout=30.0
            )
            
            result = response.json()
            print(f"📱 SMS Result: {json.dumps(result, indent=2)}")
            
            if result.get("success"):
                print("🎉 SMS SENT SUCCESSFULLY! 🎉")
                return True
            else:
                print(f"❌ SMS failed: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ SMS error: {e}")
            return False


if __name__ == "__main__":
    success = asyncio.run(test_ui_automation())
    print(f"\n{'='*60}")
    print(f"🎯 FINAL RESULT: {'SUCCESS' if success else 'FAILED'}")
    print(f"{'='*60}")