#!/usr/bin/env python3
"""
Simple test for browser WAA SMS sending
"""
import asyncio
import json
from datetime import datetime
from browser_waa_client import BrowserWAAClient


async def test_sms_only():
    """Test only SMS sending with browser WAA"""
    
    # Load fresh cookies
    with open('fresh_cookies.json', 'r') as f:
        cookies = json.load(f)
    
    client = BrowserWAAClient(cookies)
    
    try:
        print("="*60)
        print("🚀 BROWSER WAA SMS TEST")
        print("="*60)
        
        # Initialize browser
        if await client.initialize():
            print("✅ Browser initialized")
            
            # Skip conversation test, go straight to SMS
            print("\n📱 Sending SMS with browser WAA...")
            result = await client.send_sms_with_real_waa(
                recipient="3602415033",  # Replace with your number
                message=f"Browser WAA Test {datetime.now().strftime('%H:%M:%S')}"
            )
            
            print(f"\n📊 Result: {json.dumps(result, indent=2)}")
            
            if result.get("success"):
                print("\n🎉 SUCCESS! SMS SENT WITH BROWSER WAA!")
                return True
            else:
                print(f"\n❌ Failed: {result.get('error')}")
                return False
        else:
            print("❌ Browser initialization failed")
            return False
            
    finally:
        await client.close()
        print("🧹 Cleanup done")


if __name__ == "__main__":
    success = asyncio.run(test_sms_only())
    print(f"\nTest {'PASSED' if success else 'FAILED'}")