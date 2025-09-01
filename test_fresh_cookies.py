#\!/usr/bin/env python3
"""
Test with fresh cookies using the persistent session system
"""
import asyncio
import json
from datetime import datetime
from persistent_session_client import PersistentGoogleVoiceSession

async def main():
    # Fresh cookies from user
    fresh_cookies = {
        "__Secure-1PAPISID": "25lYAoz2nuYlET9F/AcjU6q-M05xhf3m9i",
        "__Secure-1PSID": "g.a0000gidohBL8Q_snp6HMg63YVDyWOWbGBrYz7j7TXhgSbuI49nmAbB8VKbKplnaIymVYBlV8wACgYKAUkSARcSFQHGX2MiQv1kJWiUk5F0QRdI6_IedxoVAUF8yKrQ76TWi2LQ6-ZHQMloEJmP0076",
        "__Secure-1PSIDCC": "AKEyXzWsQ8cabGhRaoeIDVpyb9dxSWX6bj-ZwlgfWA4fIE6CsyDOjTCAMX_Prruzk1QSKT6a0Q",
        "__Secure-1PSIDTS": "sidts-CjIB5H03Pzp8dDQsA0hi6nqSbZETflPRDhQ8y5LS_ItlLHtYQNFbGYKCVy-AZCHd4DzdlhAA",
        "__Secure-3PAPISID": "25lYAoz2nuYlET9F/AcjU6q-M05xhf3m9i",
        "__Secure-3PSID": "g.a0000gidohBL8Q_snp6HMg63YVDyWOWbGBrYz7j7TXhgSbuI49nmptstfVG3sOuBex1won4fOAACgYKASQSARcSFQHGX2MitGTAfMcy05dsGQLPlBAr3RoVAUF8yKqbYCBU-BT9ONjIWNiQri-h0076",
        "__Secure-3PSIDCC": "AKEyXzVmM2q5AU_frQo6iALwRGlGFazMauLIu4yQhOy02wT2npihECOiwN5tmYbvS2wh5yzjJw",
        "__Secure-3PSIDTS": "sidts-CjIB5H03Pzp8dDQsA0hi6nqSbZETflPRDhQ8y5LS_ItlLHtYQNFbGYKCVy-AZCHd4DzdlhAA",
        "__Secure-OSID": "g.a0000gidomf-Km8BaxbLZKsQno7wq4K3q3N0WabexlpDZxQ-737PlapNUkl3VcjwpXckZfrTigACgYKAbsSARcSFQHGX2MiBXLJQb4seMM4YY2dCEzn8BoVAUF8yKr2qyjdOzEybx8Kv8ZUb20w0076",
        "APISID": "mYg9dQYyHeuMPYVA/AbCTVr6KpbF8eNO2x",
        "COMPASS": "voice-web-frontend=CgAQsrDCxQYaXgAJa4lXDPiI5XaP-nYDPAkZMqqZ94lMW8GB9vCUYYH7783Byrombw9404lBqdqnAPMLeOa6sgk0QkesAR38RSnvBylpC00zm2xIvr4P6a3Uy5A3wv8hAcBA5-nMngkwAQ",
        "HSID": "ApYXLRGykgAatLHFT",
        "OSID": "g.a0000gidomf-Km8BaxbLZKsQno7wq4K3q3N0WabexlpDZxQ-737P_NLRTpnlu9TbOdkWVIwQ9gACgYKAbwSARcSFQHGX2Mi2-8454Xc5-S2UMGkfrsaJxoVAUF8yKq0yUUJMWsNycV4MBJONjER0076",
        "S": "billing-ui-v3=c8vqT6pMKIM10h3hUSnnakj9Uc7Ievsp:billing-ui-v3-efe=c8vqT6pMKIM10h3hUSnnakj9Uc7Ievsp",
        "SAPISID": "25lYAoz2nuYlET9F/AcjU6q-M05xhf3m9i",
        "SID": "g.a0000gidohBL8Q_snp6HMg63YVDyWOWbGBrYz7j7TXhgSbuI49nmX_PepglISToJC89AUwJa8QACgYKARkSARcSFQHGX2Mi6x-LNWKt0nQtLoJNvV_mIRoVAUF8yKqDXkxRyUDrvH9sPFT3fFq00076",
        "SIDCC": "AKEyXzW_2SvBToS2_TQ2itvrvAOc2KCrSzdmpwtOO5iLPRh0Ci_8YQgU_jKLX85dgMZnVFbqKyU",
        "SSID": "Aqw-Nyw1IrW3jRYHx"
    }
    
    client = PersistentGoogleVoiceSession(fresh_cookies, "fresh_session.pkl")
    
    try:
        print("=" * 80)
        print("🚀 TESTING PERSISTENT SESSION WITH FRESH COOKIES 🚀")
        print("=" * 80)
        
        # Initialize persistent session
        if await client.initialize_session():
            print("\n✅ Persistent session initialized successfully!")
            
            # Send test SMS
            result = await client.send_sms_with_persistent_session(
                recipient="3602415033", 
                message=f"🎉 SUCCESS! Fresh cookies test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            print(f"\n📊 SMS Result:")
            print(json.dumps(result, indent=2))
            
            if result.get("success"):
                print("\n🎉🎉🎉 SMS SENT SUCCESSFULLY! 🎉🎉🎉")
                print("✅ The Google Voice REST API is now working!")
                print("✅ Session will be maintained automatically with cookie updates")
                
                if result.get("cookies_updated"):
                    print("🔄 Cookies were automatically updated from API responses")
                    
            else:
                print(f"\n❌ SMS failed: {result.get('error')}")
                print(f"Status code: {result.get('status_code')}")
                
        else:
            print("❌ Failed to initialize persistent session")
            
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
