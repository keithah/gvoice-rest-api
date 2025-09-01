#!/usr/bin/env python3
"""
Test script for browser-based WAA implementation
Run this after extracting fresh cookies from extract_fresh_cookies.py
"""
import asyncio
import json
import os
from datetime import datetime
from browser_waa_client import BrowserWAAClient


async def test_with_fresh_cookies():
    """Test browser WAA with fresh cookies"""
    
    # Try to load fresh cookies from file
    cookies = None
    if os.path.exists('fresh_cookies.json'):
        print("📂 Loading fresh cookies from file...")
        with open('fresh_cookies.json', 'r') as f:
            cookies = json.load(f)
        print(f"✅ Loaded {len(cookies)} cookies from fresh_cookies.json")
    else:
        print("❌ No fresh_cookies.json found")
        print("Please run: python3 extract_fresh_cookies.py first")
        return False
    
    # Validate essential cookies
    required_cookies = ["SAPISID", "SID"]
    missing_cookies = [c for c in required_cookies if c not in cookies]
    if missing_cookies:
        print(f"❌ Missing required cookies: {missing_cookies}")
        print("Please extract fresh cookies using extract_fresh_cookies.py")
        return False
    
    client = BrowserWAAClient(cookies)
    
    try:
        print("=" * 70)
        print("🚀 TESTING BROWSER WAA WITH FRESH COOKIES 🚀")
        print("=" * 70)
        
        # Initialize browser WAA
        if await client.initialize():
            print("\n📞 Testing conversation retrieval...")
            conversations = await client.get_conversations()
            
            if conversations.get("success"):
                print("✅ Conversations retrieved - authentication working")
            else:
                print(f"❌ Authentication failed: {conversations.get('error')}")
                print("Please get fresh cookies using extract_fresh_cookies.py")
                return False
            
            print("\n📱 Testing SMS with browser WAA...")
            result = await client.send_sms_with_real_waa(
                recipient="3602415033",  # Replace with your test number
                message=f"🎯 Browser WAA Test {datetime.now().strftime('%H:%M:%S')}"
            )
            
            print(f"\n📊 SMS Result:")
            print(json.dumps(result, indent=2))
            
            if result.get("success"):
                print("\n🎉🎉🎉 SUCCESS! BROWSER WAA SMS WORKED! 🎉🎉🎉")
                
                # Save successful result for analysis
                with open('successful_waa_result.json', 'w') as f:
                    json.dump(result, f, indent=2)
                print("💾 Success details saved to successful_waa_result.json")
                
                return True
            else:
                print(f"\n❌ SMS failed: {result.get('error')}")
                error_code = result.get('status_code')
                if error_code == 401:
                    print("🔑 Authentication issue - try fresh cookies")
                elif error_code == 400:
                    print("📝 Request format issue - check WAA signature")
                elif 'FAILED_PRECONDITION' in str(result.get('error')):
                    print("🚫 Google detected automation - WAA signature may need improvement")
                return False
        else:
            print("❌ Failed to initialize browser WAA system")
            return False
            
    finally:
        await client.close()
        print("🧹 Browser cleanup completed")


def check_fresh_cookies():
    """Check if we have fresh cookies available"""
    if not os.path.exists('fresh_cookies.json'):
        print("❌ No fresh cookies found!")
        print("\n📋 To get fresh cookies:")
        print("1. Run: python3 extract_fresh_cookies.py")
        print("2. Log in to Google Voice in the browser")
        print("3. Complete the cookie extraction")
        print("4. Then run this test again")
        return False
    
    try:
        with open('fresh_cookies.json', 'r') as f:
            cookies = json.load(f)
        
        required = ["SAPISID", "SID"]
        missing = [c for c in required if c not in cookies]
        
        if missing:
            print(f"❌ Missing required cookies: {missing}")
            return False
        
        print(f"✅ Fresh cookies available ({len(cookies)} cookies)")
        return True
        
    except Exception as e:
        print(f"❌ Error checking cookies: {e}")
        return False


if __name__ == "__main__":
    print("🔍 Checking for fresh cookies...")
    
    if check_fresh_cookies():
        print("🚀 Starting browser WAA test...")
        success = asyncio.run(test_with_fresh_cookies())
        
        if success:
            print("\n✅ Browser WAA test completed successfully!")
            print("The system is ready to send SMS with authentic signatures!")
        else:
            print("\n❌ Browser WAA test failed")
            print("Check logs above for specific issues")
    else:
        print("\n❌ Cannot test without fresh cookies")
        print("Run extract_fresh_cookies.py first")