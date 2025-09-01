#!/usr/bin/env python3
"""
Debug SMS sending with exact mautrix-gvoice format
"""
import asyncio
import json
import time
import hashlib
import random
import httpx
from datetime import datetime

# Fresh cookies from user - UPDATED 2024-08-28
FRESH_COOKIES = {
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
    "NID": "525=BKwRSic0nFOADsNww04nmpI5nQN3Y9pX9gPF7HyS1rueM1F9g2Pwf-vGNgVX37l26HRx6jrkoEIwM4UEB5vm2t41KdsXICuNRFrctEvAl_vjT4MdE5XcY6ysdvCjvMVTCfbfcrP97wQGisGh5iaaIwQomDwO6HT_woAImJiqZPgeCZXiurfT7AWWRHCXpAlOxXoAuKKCLo9FrFvzRX_Y5L1KlaPhxVMA0yjrNQHStz5-ojFuIibDDT_jlrI9Xh-r4Q4DfKHZskTCZSJJLee_aZSW9N26AnBt-dpE3gcBckC-8qYcd1CE2cv5_8xD3wrSQIkk9Tra6jmYFnLCJp_ks4R6lN_GR9fJ8lgnc30eGcNdq5Z_R3NKZFsT2AMMsmc0zM12IX0ZZIVdVwiM-pbcgzGBPnUR_hOVavNFW0VU4Woj0qenlfjiE29nQASJSx6FT9Cb7QzyIm6d3rAXiT4q_PG04GVSG0xSouzeiKNbwdhinyLphGecOcZSAiQ36aja70Q8QKrTOWIzsKKtx0HJXN9ubGzqLbfkNJKe6i5I3eYETdmg350Na2St99OEUKMANCR1Gq2ZHQ-ggxh6X65QqaueI6rWb1zCkbu4-lAXqt43x_b6yFI2ioYlDMYMb54W-ABaMa_SRL7IpfOt_szB-vTvDAS2mpRzeCKCktxssfTg6YNfzWSfdG2X0d-y3j-PE88EULS2aeyXwtOxOdWdDmkSsyd2Yh63uFsHy2qr431mwrzXXKIFCwIUVRzRuOkLeia0M0qtal2TOK-Pekb-2TeHJF9hixjF6jicD3GRaKGjhAwzgL7YaND_bHInPxS6LcrJrg3bFLTVSjnqNqDasaprRfBrOz3v452Nx9Uqnp8xtQ3hJMhZtUlCR0Mk7uExddP2u6644ox6OYTwFgYyW6OBe5OO75EuA7RCjREp-T8SGbAKMUn5DFxd9RrG8GKYhzPddno2zI9C3RyXWQ6krYEt9CU",
    "OSID": "g.a0000gidomf-Km8BaxbLZKsQno7wq4K3q3N0WabexlpDZxQ-737P_NLRTpnlu9TbOdkWVIwQ9gACgYKAbwSARcSFQHGX2Mi2-8454Xc5-S2UMGkfrsaJxoVAUF8yKq0yUUJMWsNycV4MBJONjER0076",
    "S": "billing-ui-v3=c8vqT6pMKIM10h3hUSnnakj9Uc7Ievsp:billing-ui-v3-efe=c8vqT6pMKIM10h3hUSnnakj9Uc7Ievsp",
    "SAPISID": "25lYAoz2nuYlET9F/AcjU6q-M05xhf3m9i",
    "SID": "g.a0000gidohBL8Q_snp6HMg63YVDyWOWbGBrYz7j7TXhgSbuI49nmX_PepglISToJC89AUwJa8QACgYKARkSARcSFQHGX2Mi6x-LNWKt0nQtLoJNvV_mIRoVAUF8yKqDXkxRyUDrvH9sPFT3fFq00076",
    "SIDCC": "AKEyXzW_2SvBToS2_TQ2itvrvAOc2KCrSzdmpwtOO5iLPRh0Ci_8YQgU_jKLX85dgMZnVFbqKyU",
    "SSID": "Aqw-Nyw1IrW3jRYHx"
}

def generate_sapisid_hash() -> str:
    timestamp = int(time.time())
    origin = "https://voice.google.com"
    sapisid = FRESH_COOKIES.get("SAPISID", "")
    hash_input = f"{timestamp} {sapisid} {origin}"
    hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
    return f"SAPISIDHASH {timestamp}_{hash_value}"

def generate_transaction_id() -> int:
    """Generate transaction ID like mautrix-gvoice (max 100000000000000)"""
    return random.randint(1, 99999999999999)

async def check_account_first():
    """First verify account access"""
    async with httpx.AsyncClient() as client:
        # Set cookies
        for name, value in FRESH_COOKIES.items():
            client.cookies.set(name, value, domain=".google.com")
            
        url = "https://clients6.google.com/voice/v1/voiceclient/account/get"
        
        headers = {
            # Chrome browser headers
            "Sec-Ch-Ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            "Sec-Ch-Ua-Platform": '"Linux"',
            "Sec-Ch-Ua-Mobile": "?0",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "X-Goog-AuthUser": "0",
            # API-specific headers
            "X-Client-Version": "665865172",
            "X-ClientDetails": "appVersion=5.0%20%28X11%29&platform=Linux%20x86_64&userAgent=Mozilla%2F5.0%20%28X11%3B%20Linux%20x86_64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F128.0.0.0%20Safari%2F537.36",
            "X-JavaScript-User-Agent": "google-api-javascript-client/1.1.0",
            "X-Requested-With": "XMLHttpRequest",
            "X-Goog-Encode-Response-If-Executable": "base64",
            # Fetch headers
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors", 
            "Sec-Fetch-Site": "same-site",
            # Content headers
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Origin": "https://voice.google.com",
            "Referer": "https://voice.google.com/",
            "Content-Type": "application/json+protobuf",
            # Authentication
            "Authorization": generate_sapisid_hash()
        }
        
        params = {
            "key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
            "alt": "proto"
        }
        
        # Account request format: ReqGetAccount has unknownInt2 = 1 (field 2)
        body = json.dumps([None, 1])  # Field 2 = 1 as per protobuf
        
        print("🔍 Checking account access...")
        response = await client.post(url, params=params, headers=headers, content=body)
        
        print(f"   Account Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Account access confirmed")
            return True
        else:
            print(f"❌ Account access failed: {response.text[:200]}")
            return False

async def try_simple_sms_exact_format():
    """Try SMS with exact mautrix-gvoice format"""
    
    async with httpx.AsyncClient() as client:
        # Set cookies
        for name, value in FRESH_COOKIES.items():
            client.cookies.set(name, value, domain=".google.com")
            
        url = "https://clients6.google.com/voice/v1/voiceclient/api2thread/sendsms"
        
        headers = {
            # Chrome browser headers
            "Sec-Ch-Ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            "Sec-Ch-Ua-Platform": '"Linux"',
            "Sec-Ch-Ua-Mobile": "?0",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "X-Goog-AuthUser": "0",
            # API-specific headers
            "X-Client-Version": "665865172",
            "X-ClientDetails": "appVersion=5.0%20%28X11%29&platform=Linux%20x86_64&userAgent=Mozilla%2F5.0%20%28X11%3B%20Linux%20x86_64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F128.0.0.0%20Safari%2F537.36",
            "X-JavaScript-User-Agent": "google-api-javascript-client/1.1.0",
            "X-Requested-With": "XMLHttpRequest",
            "X-Goog-Encode-Response-If-Executable": "base64",
            # Fetch headers
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors", 
            "Sec-Fetch-Site": "same-site",
            # Content headers
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Origin": "https://voice.google.com",
            "Referer": "https://voice.google.com/",
            "Content-Type": "application/json+protobuf",
            # Authentication
            "Authorization": generate_sapisid_hash()
        }
        
        params = {
            "key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
            "alt": "proto"
        }
        
        message = f"TEST SMS from fixed API at {datetime.now().strftime('%H:%M:%S')}"
        recipient = "3602415033"
        transaction_id = generate_transaction_id()
        
        print(f"📱 Sending SMS to {recipient}...")
        print(f"   Message: {message}")
        print(f"   Transaction ID: {transaction_id}")
        
        # Exact mautrix-gvoice ReqSendSMS format:
        # text(5), threadID(6), recipients(7), transactionID(9), trackingData(11)
        # WrappedTxnID format: [transaction_id] (array with the ID as first element)
        body = json.dumps([
            None, None, None, None,   # fields 1-4
            message,                  # field 5: text
            None,                     # field 6: threadID (None for new conversation) 
            [recipient],              # field 7: recipients (array)
            None,                     # field 8: (unused)
            [transaction_id],         # field 9: WrappedTxnID (array with ID)
            None,                     # field 10: media
            ["!"]                     # field 11: TrackingData (array with data)
        ])
        
        print(f"   Request Body: {body}")
        
        try:
            response = await client.post(url, params=params, headers=headers, content=body)
            
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            
            if response.status_code == 200:
                print("✅ SMS SENT SUCCESSFULLY!")
                return True
            else:
                print(f"❌ SMS failed")
                return False
                
        except Exception as e:
            print(f"❌ SMS error: {e}")
            return False

if __name__ == "__main__":
    print("=" * 60)
    print("Debug SMS with mautrix-gvoice format")
    print("=" * 60)
    
    async def main():
        # First check account access
        if await check_account_first():
            print("\n📤 Attempting SMS send...")
            await try_simple_sms_exact_format()
        else:
            print("❌ Cannot proceed - no account access")
    
    asyncio.run(main())