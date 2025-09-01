#!/usr/bin/env python3
"""
Test the full integration: FastAPI SMS endpoint with UI automation
"""
import asyncio
import json
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from services.ui_automation_client import UIAutomationClient
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Install dependencies: pip install --break-system-packages httpx")
    sys.exit(1)


async def test_integration():
    """Test the UI automation client directly"""
    
    print("🧪 TESTING UI AUTOMATION INTEGRATION")
    print("="*50)
    
    # Load cookies
    with open('fresh_cookies.json', 'r') as f:
        cookies = json.load(f)
    
    print(f"✅ Loaded {len(cookies)} cookies")
    
    # Test UI automation client
    client = UIAutomationClient(cookies)
    
    # Test 1: Health check
    print("\n1️⃣ Testing service health...")
    health = await client.health_check()
    print(f"📊 Health: {json.dumps(health, indent=2)}")
    
    if health.get('status') != 'running':
        print("❌ Service not healthy")
        return False
    
    # Test 2: Initialize
    print("\n2️⃣ Initializing UI automation...")
    init_success = await client.initialize()
    print(f"🚀 Init success: {init_success}")
    
    if not init_success:
        print("❌ Failed to initialize")
        return False
    
    # Test 3: Send SMS
    print("\n3️⃣ Sending SMS via UI automation...")
    result = await client.send_sms("3602415033", f"Full Integration Test {int(asyncio.get_event_loop().time())}")
    print(f"📱 SMS Result: {json.dumps(result, indent=2)}")
    
    if result.get("success"):
        print("🎉 FULL INTEGRATION SUCCESS! 🎉")
        return True
    else:
        print(f"❌ SMS failed: {result.get('error')}")
        return False
    
    # Cleanup
    await client.close()


if __name__ == "__main__":
    success = asyncio.run(test_integration())
    print(f"\n{'='*60}")
    print(f"🎯 FINAL RESULT: {'SUCCESS' if success else 'FAILED'}")
    print(f"{'='*60}")