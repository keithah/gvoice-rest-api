#!/usr/bin/env python3
"""
Fixed authentication test with all required cookies
"""
import asyncio
import httpx
import json
from datetime import datetime
import hashlib
import time

# ALL cookies from your browser
ALL_COOKIES = {
    "__Secure-1PAPISID": "GjfTX7q-BcEw9cRE/Ao7WL3H89RBOSiG9Q",
    "__Secure-1PSID": "g.a0000gjAouZjfqg3cumlvmMVeSS0xZt2ZSXhXLVevEHnt_drASD_ACFxn0xOc9CMuXZDoCh6MQACgYKAXgSARISFQHGX2MiAXyXyiEpN7UtygQt0TlP8xoVAUF8yKqPNr0X_HgXcnaZXEVgGv9J0076",
    "__Secure-1PSIDCC": "AKEyXzWQwpDwwQKpmsQOd2rKBOlD1DxSclpxxWgP-H-o4CUIboyyUA-CuWDvtfZptGaMipchLw04",
    "__Secure-1PSIDTS": "sidts-CjAB5H03PwcHDJmftOrHgtmvQjjPeqlt8HdjV_xHIwXWtC0qVfoc0keu6UwPEyp14HUQAA",
    "__Secure-3PAPISID": "GjfTX7q-BcEw9cRE/Ao7WL3H89RBOSiG9Q",
    "__Secure-3PSID": "g.a0000gjAouZjfqg3cumlvmMVeSS0xZt2ZSXhXLVevEHnt_drASD_zEjJOei8xRfARwAwgpC0HwACgYKAUoSARISFQHGX2MiA32MnMBazgKNO7auwcDsmBoVAUF8yKq360zWEBlBY1cwl2rg5uNr0076",
    "__Secure-3PSIDCC": "AKEyXzVQfWwCWWvAs_P1-W0Y7PNZR0xVYl0uLxcYJv8Iz4Vx8lHqmqruJsRwSFQAluWg674xrHZc",
    "__Secure-3PSIDTS": "sidts-CjAB5H03PwcHDJmftOrHgtmvQjjPeqlt8HdjV_xHIwXWtC0qVfoc0keu6UwPEyp14HUQAA",
    "__Secure-ENID": "27.SE=TIzbjrG2OJBP8lyHNef_qGHaS5o0v3c_bB2d2fyt_ydckg_XWSiU1IdJP4lOnE6LvpkOjGcoA3nrUXU4euhkOTJ-6L3cHJyXkgn_l4fK4wdUWj9TqN0J1Gf6cxiEo-MjMaXetUQdR-7B7p2mRbpLjtqzx75TsNqDJQ4DgAhO39E9BjcJncRyNv6Kgm3bxM-yeYM6f4KjxWNzkjVZb2M-FH9WY3SncR-Oae2gF5otAHfW0I2h0fwTmyOt2xpqX0uk0CPfanc4vrHD6teb-QuLbIQTcIHgJZgQ63XRWTPyxEjg44s3dolc7e7mBkakxThjphEoH5K0Pi6zLnXrpNsKXxAXPqlG3LfCyHa4el4BQfNHYZDUdwHHriv49DwYudbkAprp0iqOc1Pz",
    "__Secure-OSID": "g.a0000gjAoojj64DmhVUAvK08uX0aawiSjFwaT1FX239ZBbtpvCWJ4qk8H1AYAm8cuU838ta5AwACgYKAUESARISFQHGX2Mi5hAEjOmsAMwpmFvd-p-eKBoVAUF8yKpdw8VS9DQ5GTW_IPGxmmER0076",
    "AEC": "AVh_V2h8NUR4T1X-naFZpABWtoKMKWtN51L1YMlKLmgF5UWyMvZ_GfBLSu0",
    "APISID": "qW3CGJXrJMAUgDnq/AE0szFtN-ymXjEyZJ",
    "COMPASS": "voice-web-frontend=CgAQ0IXCxQYaXgAJa4lX_sZ31YHPtuSrdPAVDdGsVPZPzjqrGKPkj_G7pZKHq_zulxeR8gf5mFwl2HCkG4k7aOLc5UF2O1tfN5S1KQwqbsIv2NfvCpsc0nWfuN7Sk7FTuy-zX9N3qmowAQ",
    "HSID": "AcvDwpgrPA3Np_b_f",
    "NID": "525=OlYjxtuBHu8ACbDEGLp9trtfCHOX11SywspIClQ-QUZ4eKJ_0fsKh52x8jNJMk-OIAJO5ifhWe50Gom88Wn1kmAqWUK4P4dYp_vQ4_Q8UVeltj5PAyjsADR7GD2GD68SYxw5sEEWSFogDke48QwuiCQ790w2GnPqcPC6dSnRPD46_PZHNP7jn07eLnU6qx3ucJeK5Z0mCHnOBb3EHcOvY9kaDdbyMs63fpSXwaQp-8KbmfTaWYs1uocNN0pNoDFT3wguyiC3XZTDtVaVIZsUpxMmVA2plBjpmIMUmoFcb81nnBWUiWlXwGmdqJNHaJOE9hhlPDe2UgttBkZ62NC1MWK4xbibuHNcYk9LMfwS4fMigRtyIEW7FyNyCWE9q5jsww_8EnUk8_G4RLn800n3jldB5KMT6jBAeykiGyxzOwgxQB8RDf-usrv-VB6nepP_2j-0G3ayCIE0o567fTSaSfCuFA5IptOfiqslMLWUbnsuWNy8et-DJU8X7xyBcQrQzi6N7H7k9r3fBzHnpYIyqzT9-In3jNvwW_5Ss1alIR3cOqD5pGLF9htwCAAXhs7ZN579ydc_1a0AOOUCEEVCJ-x6PyEQ3yow55kqC0LP6XTqkwpmMB7DubZ6DOHmZ8b-_9y0zS_qum3fk9BBniS2D8xZxqWojR7NFMonIGLrNrv21NChYIjXJUahOKw60OlEN747sz3byu7wSGX28EtjmY68j7CSbl7T-rLMeRgQRA0gQDKMY2-ZJB5j1EhhoTs6jNmBTGHFUpvYj1O7Kh96FNE1pulVNKREXqRY08iTEeCdPTsGsP7Rb2toiO76iQoF4Nlxsem3AcqIvGfo7UHjrTEDc2EdAPzchd7jjyRCS8Eh81IK2oQRTIHrMAptmshFOS9kQUM6csds-CGCgGOyccuDyRVaI88TS67sVfTbYbAN4wpQv7LJgl09bt5lCO6fC9u4bvrc9RW0YcZFF10yEhAPfeuNoWuXcn2mWtsDqE7kkMPHO_Muu8kfit4x4xAjH903qYNIsGAVgcM89Ucf6pTrstXkMSv9gvzEHzf6eyXjp-frKQqdXkVugoIw28hFkIYTNmoqOOiYIFZzSFbxzU9F8SRZEET8cN3cDXA5rAvFKYjE0r4l1hS5gsAYtmDCkF2Ffju6cZ_OP5VYeHv2SwteJGeYmADmCvLR0FRvuH6qx7C7uJet15-54mgWab8mNDHpSW8OdQ1ZALLj65IFKjl5G0VSU5WhqtzQGKr4EqCaUWnh8CqxyiOMFGA7up84ENGOWODIvFTUMY-p2WFiN0SQX3dxmiqnUuYDxgtdOO3NL89Nlq1wn__hkS6_HllMcPSpDr3TY04FRst4zwtV4tXCGCB2l6cxr2T7HFj3zVYt5QFntdTkfd1n1BUmsPcm9Bmq00KH_aNd9wuhw3nuGDGaJsyaPD_TjYBytr3TZs7wwEPYfRxOI8AeLASwwlcy6b9iPrJ3aQQ7vW-wmFt1MI69r2jvSHcKmGc3hIfHUQoUWBUfEhXP2YdSS9p4el4WG-MTUaOW3H1PIJaqbKw8X33hUfn3uzK-qjYf0G0ZAZl0bOhe8Aowz4lN03h19gy-CU2p4b6hWV_JOqbzRAzlKjCPBcZJVe9uLtU3lgM47HDkmZcBQ0xLAZO9Lz0OEz4dE7tvZePfMveYggxqMx2fI834LvD8-wYL7pyHhu67W-BPE3oHlB4AucVxrbEi_gL13Hzb1XyTbt3pORfLNVxqGpiNwvpuQ87hA6XJorjVgJmdjXaH6Pcj9-urGk4E8Bl-fygZ0J7d9DzqnO1w4ijR2-oeF8CVwrMNjLj1GAff1PrN9cq2Uo0-0Rc3DoMRLWoAYcuqFoZwOnqBazaLylFUzWthAQOMcgBYGjOdxz_3Co90hof8JZDr_Ryi4wjxtJufBvv4Y8qfRkqt-DNZ3RMXm_EE6TROwdfR0YfOzlY4tm_b0i_PtPN2KcYCi2qO0A1-ZhSMhGN-vLAFtCpqTGiO8nfYQ60iZIwfX_Gf4JlLDYx41s-1uhDtRV_Nwp_XMFA7nU3pyMIw-_4tWaV9Z0Mw3-FdNtJG5I0x0SRje_hCT-SMzVk89FC7OjUosm9jyUW0QHgeVfQ6kNaVTihuNs0j-mEkggGWFQE4R9d4rUr2I8wJ9qO1RhxMMzc0zsuVr-PvSXE2R4naTCUiyjPCtwfZUerWETR3bI2HbZ0MBBw7OOlUSXbfxGMEYcOK2L8EhAbv_VKpwixg-Hiv5tWQ5eAVR-bli4s1KxDMHXOXU-xSABHGiVVSIC1fs8UnhFeZRlc1aTT5TmLRGvzAtl9bW3S5m7QbppoGgzKyYnim7s_h1sNLgcloxljqRfj4PcKJb-K2nL8jszoCWxj2sAvwc1E",
    "OSID": "g.a0000gjAoojj64DmhVUAvK08uX0aawiSjFwaT1FX239ZBbtpvCWJcz2bto9McNFXC9JhnJmtKgACgYKAbESARISFQHGX2MiTK78brOZJywuSHjtS3bJrhoVAUF8yKqCzBhVzyqJiJ_zi6hEuvw_0076",
    "S": "billing-ui-v3=C6tSQSYTyvcSnHni5vkYSYayiFJqBkD_:billing-ui-v3-efe=C6tSQSYTyvcSnHni5vkYSYayiFJqBkD_",
    "SAPISID": "GjfTX7q-BcEw9cRE/Ao7WL3H89RBOSiG9Q",
    "SEARCH_SAMESITE": "CgQIu54B",
    "SID": "g.a0000gjAouZjfqg3cumlvmMVeSS0xZt2ZSXhXLVevEHnt_drASD_ijoJR-Izp-O4cqXDy9kHbgACgYKAZESARISFQHGX2MiupijAjtQdfaeCxpLUdc4TRoVAUF8yKpy_aQqwYTGWecKLJI_Fe9u0076",
    "SIDCC": "AKEyXzUDid8OioeDCfK4SPF_2uNPsIYfwKIH9aeCi1mZBuW99IME0INYPwPOyEFmnEjbBvXcyfw",
    "SSID": "AQZcF9pzX7SCL1ZFK",
    "_ga": "GA1.1.667142936.1749406970",
    "_ga_PD06WTLS6G": "GS2.1.s1756394563$o2$g1$t1756394715$j45$l0$h0"
}

def generate_sapisid_hash(sapisid: str) -> str:
    """Generate SAPISID hash for authorization"""
    timestamp = int(time.time())
    origin = "https://voice.google.com"
    hash_input = f"{timestamp} {sapisid} {origin}"
    hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
    return f"SAPISIDHASH {timestamp}_{hash_value}"

async def test_auth():
    """Test Google Voice authentication with all cookies"""
    async with httpx.AsyncClient() as client:
        # Test endpoint - get account
        url = "https://clients6.google.com/voice/v1/voiceclient/account/get"
        
        # Prepare headers exactly like mautrix-gvoice
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Sec-Ch-Ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            "Sec-Ch-Ua-Platform": '"Linux"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Origin": "https://voice.google.com",
            "Referer": "https://voice.google.com/",
            "Authorization": generate_sapisid_hash(ALL_COOKIES["SAPISID"]),
            "X-Client-Version": "665865172",
            "X-ClientDetails": "appVersion=5.0%20(X11)&platform=Linux%20x86_64&userAgent=" + 
                              "Mozilla%2F5.0%20(X11%3B%20Linux%20x86_64)%20AppleWebKit%2F537.36%20" +
                              "(KHTML%2C%20like%20Gecko)%20Chrome%2F128.0.0.0%20Safari%2F537.36",
            "X-JavaScript-User-Agent": "google-api-javascript-client/1.1.0",
            "X-Requested-With": "XMLHttpRequest",
            "X-Goog-Encode-Response-If-Executable": "base64",
            "X-Goog-AuthUser": "0",
            "Content-Type": "application/json+protobuf",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors", 
            "Sec-Fetch-Site": "same-site",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        # Add cookies individually like mautrix-gvoice does
        cookies = {}
        for name, value in ALL_COOKIES.items():
            cookies[name] = value
        
        # Request params
        params = {
            "key": "AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg",
            "alt": "proto"
        }
        
        # Simple request body - just like mautrix sends
        body = json.dumps([[None, None, 1]])  # This matches the protobuf structure
        
        print("Testing Google Voice authentication with all cookies...")
        print(f"URL: {url}")
        print(f"Authorization: {headers['Authorization']}")
        print(f"Total cookies: {len(cookies)}")
        print()
        
        try:
            response = await client.post(
                url, 
                params=params, 
                headers=headers, 
                content=body,
                cookies=cookies
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("\n✅ Authentication successful!")
                print("Response headers:")
                for k, v in response.headers.items():
                    if k.lower() in ['content-type', 'content-length', 'date']:
                        print(f"  {k}: {v}")
                print(f"\nResponse body length: {len(response.content)} bytes")
                
                # Try to decode as protobuf/pblite
                content_type = response.headers.get('content-type', '')
                if 'protobuf' in content_type:
                    print("Response is protobuf format")
                else:
                    print(f"Response format: {content_type}")
                    
            else:
                print("\n❌ Authentication failed!")
                print(f"Response headers: {dict(response.headers)}")
                print(f"Response body: {response.text}")
                
        except Exception as e:
            print(f"\n❌ Error: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_auth())