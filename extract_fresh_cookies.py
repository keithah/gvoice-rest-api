#!/usr/bin/env python3
"""
Cookie Extraction Tool
Opens Google Voice in browser and extracts fresh cookies for testing
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def extract_fresh_cookies():
    """Extract fresh cookies by opening Google Voice login"""
    playwright = None
    browser = None
    
    try:
        print("🌐 Opening Google Voice for fresh cookie extraction...")
        print("Please log in to Google Voice in the browser window that opens")
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,  # Show browser for login
            args=['--no-sandbox']
        )
        
        context = await browser.new_context()
        page = await context.new_page()
        
        # Navigate to Google Voice
        await page.goto("https://voice.google.com/u/0/", wait_until="domcontentloaded")
        
        print("\n" + "="*50)
        print("📝 INSTRUCTIONS:")
        print("1. Log in to Google Voice in the browser")
        print("2. Navigate to your messages page")
        print("3. Press Enter in this terminal when ready")
        print("="*50)
        
        # Wait for user to complete login
        input("Press Enter when you're logged in and ready to extract cookies...")
        
        # Extract all cookies
        cookies = await context.cookies()
        
        # Filter for Google cookies
        google_cookies = {}
        for cookie in cookies:
            if cookie['domain'] in ['.google.com', 'google.com', 'voice.google.com']:
                google_cookies[cookie['name']] = cookie['value']
        
        print(f"\n✅ Extracted {len(google_cookies)} Google cookies")
        
        # Save cookies to file
        with open('fresh_cookies.json', 'w') as f:
            json.dump(google_cookies, f, indent=2)
        
        print("💾 Cookies saved to fresh_cookies.json")
        
        # Print cookie dict for easy copy-paste
        print("\n🍪 Cookies for copy-paste:")
        print("cookies = {")
        for name, value in google_cookies.items():
            print(f'    "{name}": "{value}",')
        print("}")
        
        return google_cookies
        
    except Exception as e:
        print(f"❌ Cookie extraction failed: {e}")
        return None
        
    finally:
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()


if __name__ == "__main__":
    cookies = asyncio.run(extract_fresh_cookies())
    if cookies:
        print(f"\n✅ Successfully extracted {len(cookies)} cookies")
    else:
        print("\n❌ Cookie extraction failed")