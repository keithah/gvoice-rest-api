#!/usr/bin/env python3
"""
Debug Google Voice UI to find correct selectors
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def debug_google_voice_ui():
    """Debug the Google Voice interface"""
    
    # Load cookies
    with open('fresh_cookies.json', 'r') as f:
        cookies = json.load(f)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)  # Show browser
    
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
        
        print("🔍 Analyzing Google Voice UI...")
        await asyncio.sleep(5)  # Let page load
        
        # Check what's on the page
        page_title = await page.title()
        print(f"📄 Page title: {page_title}")
        
        # Look for compose button patterns
        compose_selectors = [
            '[aria-label*="compose"]',
            '[aria-label*="message"]', 
            '[aria-label*="send"]',
            'button[aria-label*="Send"]',
            'div[aria-label*="Send"]',
            '.compose',
            '.send-message',
            'gv-compose-button',
            'gv-send-button'
        ]
        
        print("\n🔍 Checking for compose button selectors...")
        for selector in compose_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    aria_label = await element.get_attribute('aria-label')
                    text_content = await element.text_content()
                    print(f"✅ Found: {selector}")
                    print(f"   Label: {aria_label}")
                    print(f"   Text: {text_content}")
            except:
                pass
        
        # Get all buttons
        print("\n🔍 All buttons on page:")
        buttons = await page.query_selector_all('button')
        for i, button in enumerate(buttons[:10]):  # First 10 buttons
            try:
                aria_label = await button.get_attribute('aria-label')
                text = await button.text_content()
                if aria_label or text:
                    print(f"   Button {i}: {aria_label or text}")
            except:
                pass
        
        print(f"\nTotal buttons found: {len(buttons)}")
        
        # Check for input fields
        print("\n🔍 Input fields:")
        inputs = await page.query_selector_all('input, textarea, [contenteditable]')
        for i, inp in enumerate(inputs[:5]):
            try:
                placeholder = await inp.get_attribute('placeholder')
                aria_label = await inp.get_attribute('aria-label')
                if placeholder or aria_label:
                    print(f"   Input {i}: {placeholder or aria_label}")
            except:
                pass
        
        print("\n✋ Browser will stay open for 30 seconds for manual inspection...")
        await asyncio.sleep(30)
        
    finally:
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    asyncio.run(debug_google_voice_ui())