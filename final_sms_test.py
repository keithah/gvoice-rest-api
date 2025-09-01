#!/usr/bin/env python3
"""
Final SMS test with full WAA system and proper headers
"""
import asyncio
import json
import time
import hashlib
import random
import httpx
from datetime import datetime

# Fresh cookies from user
FRESH_COOKIES = {
    "__Secure-1PAPISID": "25lYAoz2nuYlET9F/AcjU6q-M05xhf3m9i",
    "__Secure-1PSID": "g.a0000gidohBL8Q_snp6HMg63YVDyWOWbGBrYz7j7TXhgSbuI49nmAbB8VKbKplnaIymVYBlV8wACgYKAUkSARcSFQHGX2MiQv1kJWiUk5F0QRdI6_IedxoVAUF8yKrQ76TWi2LQ6-ZHQMloEJmP0076",
    "__Secure-1PSIDCC": "AKEyXzVQZUb5Pun3fT4ZwFZ7Dy_WBBy2HuwT8f5_vt8oB6nRsZp6Dg6CzikM1dVt8-TTijmF",
    "__Secure-1PSIDTS": "sidts-CjIB5H03P3p5ycVr5ZtEkBoVXv7IVxjjXkHn9FGyi7jm7tE-_jndAn8iAF95wZh5Xw7V9hAA",
    "__Secure-3PAPISID": "25lYAoz2nuYlET9F/AcjU6q-M05xhf3m9i",
    "__Secure-3PSID": "g.a0000gidohBL8Q_snp6HMg63YVDyWOWbGBrYz7j7TXhgSbuI49nmptstfVG3sOuBex1won4fOAACgYKASQSARcSFQHGX2MitGTAfMcy05dsGQLPlBAr3RoVAUF8yKqbYCBU-BT9ONjIWNiQri-h0076",
    "__Secure-3PSIDCC": "AKEyXzUIjhXhqdjuoDQcP-Cj2o0EpPlfDJoUMjqZ51m6gVmIua_B-zb0yGO3daqq_qSBMfRA",
    "__Secure-3PSIDTS": "sidts-CjIB5H03P3p5ycVr5ZtEkBoVXv7IVxjjXkHn9FGyi7jm7tE-_jndAn8iAF95wZh5Xw7V9hAA",
    "__Secure-OSID": "g.a0000gidomf-Km8BaxbLZKsQno7wq4K3q3N0WabexlpDZxQ-737PlapNUkl3VcjwpXckZfrTigACgYKAbsSARcSFQHGX2MiBXLJQb4seMM4YY2dCEzn8BoVAUF8yKr2qyjdOzEybx8Kv8ZUb20w0076",
    "APISID": "mYg9dQYyHeuMPYVA/AbCTVr6KpbF8eNO2x",
    "COMPASS": "voice-web-frontend=CgAQ5JPCxQYaXgAJa4lXDPiI5XaP-nYDPAkZMqqZ94lMW8GB9vCUYYH7783Byrombw9404lBqdqnAPMLeOa6sgk0QkesAR38RSnvBylpC00zm2xIvr4P6a3Uy5A3wv8hAcBA5-nMngkwAQ",
    "HSID": "ApYXLRGykgAatLHFT",
    "OSID": "g.a0000gidomf-Km8BaxbLZKsQno7wq4K3q3N0WabexlpDZxQ-737P_NLRTpnlu9TbOdkWVIwQ9gACgYKAbwSARcSFQHGX2Mi2-8454Xc5-S2UMGkfrsaJxoVAUF8yKq0yUUJMWsNycV4MBJONjER0076",
    "S": "billing-ui-v3=c8vqT6pMKIM10h3hUSnnakj9Uc7Ievsp:billing-ui-v3-efe=c8vqT6pMKIM10h3hUSnnakj9Uc7Ievsp",
    "SAPISID": "25lYAoz2nuYlET9F/AcjU6q-M05xhf3m9i",
    "SID": "g.a0000gidohBL8Q_snp6HMg63YVDyWOWbGBrYz7j7TXhgSbuI49nmX_PepglISToJC89AUwJa8QACgYKARkSARcSFQHGX2Mi6x-LNWKt0nQtLoJNvV_mIRoVAUF8yKqDXkxRyUDrvH9sPFT3fFq00076",
    "SIDCC": "AKEyXzX5pSyjNTGRWoAB7kWjHYwUdGrBk9O_W8PqiYz400RZEI56yGvGyL7gs18ak9HsfhIfsA",
    "SSID": "Aqw-Nyw1IrW3jRYHx"
}

async def send_sms_with_full_waa():
    """Send SMS using the complete WAA system"""
    try:
        from waa_client import GoogleVoiceWAASMS
        
        client = GoogleVoiceWAASMS(FRESH_COOKIES)
        
        print("🚀 Starting Full WAA SMS Test...")
        print("=" * 50)
        
        # Initialize with longer timeout and better error handling
        print("🔧 Initializing WAA system...")
        success = await client.initialize()
        
        if success:
            print("✅ WAA system ready!")
            
            # Send test SMS with corrected phone number format
            print("📱 Sending SMS...")
            result = await client.send_sms(
                recipient="3602415033",  # User confirmed format
                message=f"🎉 SUCCESS! Final SMS test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                thread_id=""  # Empty for new conversation
            )
            
            print(f"\n📊 Result: {json.dumps(result, indent=2)}")
            
            if result.get("success"):
                print("\n🎉🎉🎉 SMS SENT SUCCESSFULLY! 🎉🎉🎉")
                print("✅ The Google Voice REST API is now fully working!")
            else:
                print(f"\n❌ SMS failed: {result.get('error', 'Unknown error')}")
                
        else:
            print("❌ Failed to initialize WAA system")
            
        await client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 FINAL GOOGLE VOICE SMS TEST WITH FULL WAA SYSTEM 🚀")
    print("=" * 70)
    
    asyncio.run(send_sms_with_full_waa())