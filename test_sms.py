#!/usr/bin/env python3
"""
Test script to send SMS using the Google Voice REST API
"""
import asyncio
from datetime import datetime
import sys
import os

# Add project to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.gvoice_client import GVoiceClient

# Your Google Voice cookies
COOKIES = {
    "SAPISID": "GjfTX7q-BcEw9cRE/Ao7WL3H89RBOSiG9Q",
    "HSID": "AcvDwpgrPA3Np_b_f",
    "SSID": "AQZcF9pzX7SCL1ZFK",
    "APISID": "qW3CGJXrJMAUgDnq/AE0szFtN-ymXjEyZJ",
    "SID": "g.a0000gjAouZjfqg3cumlvmMVeSS0xZt2ZSXhXLVevEHnt_drASD_ijoJR-Izp-O4cqXDy9kHbgACgYKAZESARISFQHGX2MiupijAjtQdfaeCxpLUdc4TRoVAUF8yKpy_aQqwYTGWecKLJI_Fe9u0076",
    "__Secure-1PSID": "g.a0000gjAouZjfqg3cumlvmMVeSS0xZt2ZSXhXLVevEHnt_drASD_ACFxn0xOc9CMuXZDoCh6MQACgYKAXgSARISFQHGX2MiAXyXyiEpN7UtygQt0TlP8xoVAUF8yKqPNr0X_HgXcnaZXEVgGv9J0076",
    "__Secure-3PSID": "g.a0000gjAouZjfqg3cumlvmMVeSS0xZt2ZSXhXLVevEHnt_drASD_zEjJOei8xRfARwAwgpC0HwACgYKAUoSARISFQHGX2MiA32MnMBazgKNO7auwcDsmBoVAUF8yKq360zWEBlBY1cwl2rg5uNr0076"
}

# Test configuration
RECIPIENT_PHONE = "+13602415033"
TEST_MESSAGE = f"Test from GVoice API at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

async def test_send_sms():
    """Test sending an SMS"""
    print(f"Initializing Google Voice client...")
    client = GVoiceClient(cookies=COOKIES)
    
    try:
        print(f"Sending SMS to {RECIPIENT_PHONE}...")
        print(f"Message: {TEST_MESSAGE}")
        
        result = await client.send_sms(RECIPIENT_PHONE, TEST_MESSAGE)
        
        print("\nResult:")
        print(f"Success: {result.get('success', False)}")
        print(f"Message ID: {result.get('message_id', 'N/A')}")
        print(f"Timestamp: {result.get('timestamp', 'N/A')}")
        
        if result.get('error'):
            print(f"Error: {result['error']}")
            
    except Exception as e:
        print(f"\nError occurred: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()
        print("\nClient closed.")

if __name__ == "__main__":
    print("=" * 60)
    print("Google Voice SMS Test")
    print("=" * 60)
    
    # Run the test
    asyncio.run(test_send_sms())