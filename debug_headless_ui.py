#!/usr/bin/env python3
"""
Debug Google Voice UI in headless mode
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def debug_headless_ui():
    """Debug UI in headless mode and save screenshot"""
    
    with open('fresh_cookies.json', 'r') as f:
        cookies = json.load(f)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    
    try:
        context = await browser.new_context()
        
        # Add cookies
        cookie_objects = []
        for name, value in cookies.items():
            cookie_objects.append({
                "name": name,
                "value": value,
                "domain": ".google.com",
                "path": "/",
                "secure": True,
                "httpOnly": False,
                "sameSite": "None"
            })
        await context.add_cookies(cookie_objects)
        
        page = await context.new_page()
        await page.goto("https://voice.google.com/u/0/messages", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        # Take screenshot
        await page.screenshot(path="google_voice_debug.png")
        print("📸 Screenshot saved to google_voice_debug.png")
        
        # Get page info
        title = await page.title()
        url = page.url
        print(f"📄 Page: {title} - {url}")
        
        # Check for various button selectors
        selectors_to_try = [
            'button',
            '[role="button"]',
            'div[jsaction*="click"]',
            '[aria-label*="compose"]',
            '[aria-label*="message"]',
            '[aria-label*="send"]',
            '.gb_qc',  # Google apps button
            'gv-compose-button',
            '[data-tooltip*="compose"]'
        ]
        
        for selector in selectors_to_try:
            elements = await page.query_selector_all(selector)
            if elements and len(elements) > 0:
                print(f"✅ {selector}: {len(elements)} elements")
                
                # Get first few elements info
                for i, element in enumerate(elements[:3]):
                    try:
                        aria_label = await element.get_attribute('aria-label')
                        text = await element.text_content()
                        if aria_label or (text and len(text.strip()) > 0):
                            print(f"   [{i}] {aria_label or text}")
                    except:
                        pass
        
        # Check if logged in
        logged_in_indicators = [
            '[data-userid]',
            '.gb_Ca',  # Google account avatar
            'gv-web-inbox',
            '[role="main"]'
        ]
        
        print("\n🔍 Login status:")
        for indicator in logged_in_indicators:
            element = await page.query_selector(indicator)
            if element:
                print(f"✅ Found: {indicator}")
        
        # Get page HTML for analysis
        page_content = await page.content()
        print(f"\n📝 Page content length: {len(page_content)} chars")
        
        # Look for specific Google Voice elements
        if 'voice.google.com' in url:
            print("✅ On Google Voice domain")
        if 'inbox' in page_content.lower():
            print("✅ Inbox content detected")
        if 'compose' in page_content.lower():
            print("✅ Compose functionality detected")
        
    finally:
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    asyncio.run(debug_headless_ui())