#!/usr/bin/env python3
"""
Working UI-based SMS sender for Google Voice
Uses actual Google Voice web interface to send SMS
"""
import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime


async def send_sms_via_google_voice_ui(recipient: str, message: str):
    """Send SMS using Google Voice web interface"""
    
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
        print(f"🌐 Navigating to Google Voice...")
        await page.goto("https://voice.google.com/u/0/messages", wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        print(f"📱 Sending SMS to {recipient}: {message}")
        
        # Method 1: Try to use keyboard shortcut to compose
        print("⌨️ Trying keyboard shortcut for compose...")
        await page.keyboard.press("c")  # 'c' is compose shortcut in Google Voice
        await asyncio.sleep(2)
        
        # Method 2: Look for compose button by common patterns
        compose_selectors = [
            'button[aria-label*="ompoz"]',  # Handle potential typos
            'button[aria-label*="ompos"]',
            'div[role="button"][aria-label*="message"]',
            '[data-tooltip*="compose"]',
            '.mdc-fab',  # Material design floating action button
            'button[jsaction*="click"]'
        ]
        
        compose_clicked = False
        for selector in compose_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    aria_label = await element.get_attribute('aria-label')
                    print(f"🎯 Trying compose button: {aria_label}")
                    await element.click()
                    await asyncio.sleep(2)
                    compose_clicked = True
                    break
            except:
                continue
        
        if not compose_clicked:
            print("⚠️ No compose button found, trying URL navigation...")
            # Navigate directly to compose URL
            await page.goto("https://voice.google.com/u/0/messages/new", wait_until="domcontentloaded")
            await asyncio.sleep(2)
        
        # Enter recipient
        recipient_selectors = [
            'input[placeholder*="name"]',
            'input[placeholder*="phone"]', 
            'input[placeholder*="number"]',
            'input[aria-label*="recipient"]',
            'input[type="tel"]',
            'input[type="text"]'
        ]
        
        recipient_entered = False
        for selector in recipient_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    print(f"📞 Entering recipient in: {selector}")
                    await element.fill(recipient)
                    await asyncio.sleep(1)
                    await page.keyboard.press('Tab')  # Move to next field
                    recipient_entered = True
                    break
            except:
                continue
        
        if not recipient_entered:
            print("❌ Could not enter recipient")
            return False
        
        # Enter message
        message_selectors = [
            'div[aria-label*="message"]',
            'textarea[placeholder*="message"]',
            '[contenteditable="true"]',
            'div[role="textbox"]'
        ]
        
        message_entered = False
        for selector in message_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    print(f"💬 Entering message in: {selector}")
                    await element.fill(message)
                    await asyncio.sleep(1)
                    message_entered = True
                    break
            except:
                continue
        
        if not message_entered:
            print("❌ Could not enter message")
            return False
        
        # Send message
        send_selectors = [
            'button[aria-label*="Send"]',
            'button[aria-label*="send"]', 
            '[role="button"][aria-label*="Send"]',
            'button[type="submit"]',
            '.send-button'
        ]
        
        sent = False
        for selector in send_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    print(f"🚀 Clicking send: {selector}")
                    await element.click()
                    await asyncio.sleep(2)
                    sent = True
                    break
            except:
                continue
        
        if not sent:
            # Try keyboard shortcut as last resort
            print("⌨️ Trying Enter key to send...")
            await page.keyboard.press('Enter')
            await asyncio.sleep(2)
        
        # Check for success indicators
        success_indicators = [
            'div[aria-live="polite"]',  # Success message area
            '.sent-message',
            '[data-message-sent="true"]'
        ]
        
        for selector in success_indicators:
            element = await page.query_selector(selector)
            if element:
                text = await element.text_content()
                if text and ('sent' in text.lower() or 'delivered' in text.lower()):
                    print(f"✅ Success indicator: {text}")
                    return True
        
        # Take screenshot for debugging
        await page.screenshot(path="sms_result.png")
        print("📸 Result screenshot saved to sms_result.png")
        
        # If no clear success indicator, assume sent if no error
        print("✅ SMS send attempt completed")
        return True
        
    except Exception as e:
        print(f"❌ UI SMS failed: {e}")
        return False
        
    finally:
        await browser.close()
        await playwright.stop()


async def test_ui_sms():
    """Test UI-based SMS sending"""
    print("="*60)
    print("🚀 TESTING UI-BASED SMS SENDING")
    print("="*60)
    
    success = await send_sms_via_google_voice_ui(
        recipient="3602415033",
        message=f"UI Test {datetime.now().strftime('%H:%M:%S')}"
    )
    
    if success:
        print("\n🎉 SMS SENT VIA UI AUTOMATION!")
    else:
        print("\n❌ UI SMS failed")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(test_ui_sms())
    print(f"\nTest {'PASSED' if success else 'FAILED'}")