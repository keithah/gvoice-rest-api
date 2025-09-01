const puppeteer = require('./nodejs-waa/node_modules/puppeteer');
const crypto = require('crypto');

// Test direct Puppeteer approach
async function testDirectPuppeteer() {
    console.log('🚀 DIRECT PUPPETEER TEST');
    console.log('='*50);
    
    // Load cookies from Python-generated file
    const fs = require('fs');
    const cookies = JSON.parse(fs.readFileSync('fresh_cookies.json', 'utf8'));
    
    console.log(`🍪 Loaded ${Object.keys(cookies).length} cookies`);
    
    let browser;
    let page;
    
    try {
        // Start browser
        console.log('🚀 Starting Puppeteer...');
        browser = await puppeteer.launch({
            headless: "new",
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        });
        
        page = await browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36');
        
        // Set cookies
        const cookieObjects = Object.entries(cookies).map(([name, value]) => ({
            name,
            value,
            domain: '.google.com',
            path: '/',
            secure: true,
            httpOnly: false
        }));
        
        await page.setCookie(...cookieObjects);
        console.log('✅ Cookies set in browser');
        
        // Navigate to Google Voice
        console.log('🌐 Loading Google Voice...');
        await page.goto('https://voice.google.com/u/0/', { 
            waitUntil: 'domcontentloaded',
            timeout: 30000 
        });
        
        // Wait and check if we get redirected properly
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // If we're on workspace page, navigate directly to messages
        const currentUrl = page.url();
        if (currentUrl.includes('workspace.google.com')) {
            console.log('🔄 Redirected to workspace, navigating to personal Voice...');
            await page.goto('https://voice.google.com/', { 
                waitUntil: 'domcontentloaded',
                timeout: 30000 
            });
        }
        
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        // Check page
        const title = await page.title();
        const url = page.url();
        console.log(`📄 Page: ${title} - ${url}`);
        
        if (title.includes('Voice')) {
            console.log('✅ Google Voice loaded successfully!');
            
            // Test SMS sending from browser context
            console.log('\n📱 Testing SMS from browser context...');
            const smsResult = await testSMSFromBrowser(page, cookies);
            
            if (smsResult.success) {
                console.log('🎉🎉🎉 SUCCESS! SMS SENT FROM PUPPETEER! 🎉🎉🎉');
                return true;
            } else {
                console.log(`❌ SMS failed: ${smsResult.error}`);
                return false;
            }
        } else {
            console.log('❌ Failed to load Google Voice');
            return false;
        }
        
    } catch (error) {
        console.error('❌ Test failed:', error);
        return false;
        
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

// Test SMS from browser context
async function testSMSFromBrowser(page, cookies) {
    try {
        const recipient = '13602415033';
        const message = `Direct Puppeteer Test ${new Date().toLocaleTimeString()}`;
        const transactionId = Math.floor(Math.random() * 99999999999999);
        
        // Generate auth in Node.js
        const timestamp = Math.floor(Date.now() / 1000);
        const sapisid = cookies.SAPISID || '';
        const hashInput = `${timestamp} ${sapisid} https://voice.google.com`;
        const hashValue = crypto.createHash('sha1').update(hashInput).digest('hex');
        const authHeader = `SAPISIDHASH ${timestamp}_${hashValue}`;
        
        // First, check if Google Voice WAA is available on the page
        const waaCheck = await page.evaluate(() => {
            // Look for WAA objects that mautrix-gvoice would use
            const waaKeys = Object.keys(window).filter(key => key.includes('_') && window[key] && typeof window[key] === 'object');
            return {
                foundWAA: waaKeys.length > 0,
                keys: waaKeys.slice(0, 5), // First 5 keys
                hasWAA: typeof window.waa !== 'undefined',
                windowKeys: Object.keys(window).filter(k => k.startsWith('AF_') || k.includes('goog') || k.includes('_')).slice(0, 10)
            };
        });
        
        console.log(`🔍 WAA Check: ${JSON.stringify(waaCheck, null, 2)}`);
        
        // Navigate to messages page to use Google Voice UI
        console.log('🌐 Navigating to messages page...');
        await page.goto('https://voice.google.com/u/0/messages', { 
            waitUntil: 'domcontentloaded',
            timeout: 30000 
        });
        
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Try UI automation approach - simulate real user interaction
        console.log('🎭 Attempting UI automation...');
        
        const uiResult = await page.evaluate(async (message, recipient) => {
            try {
                console.log('🔍 Looking for compose UI elements...');
                
                // Look for "Send new message" element specifically
                console.log('🔍 Searching for "Send new message" element...');
                
                // Find elements containing "Send new message" text
                const allElements = Array.from(document.querySelectorAll('*'));
                let composeButton = null;
                
                for (const el of allElements) {
                    const text = el.textContent?.trim() || '';
                    const aria = el.getAttribute('aria-label') || '';
                    const title = el.getAttribute('title') || '';
                    
                    if ((text.includes('Send new message') || 
                         aria.includes('Send new message') || 
                         title.includes('Send new message')) &&
                        el.offsetParent !== null) {
                        
                        composeButton = el;
                        console.log(`✅ Found "Send new message": ${el.tagName} with text "${text.substring(0, 50)}"`);
                        break;
                    }
                }
                
                // If not found, try generic selectors
                if (!composeButton) {
                    const composeSelectors = [
                        '[aria-label*="Compose"]',
                        '[aria-label*="New message"]',
                        'button[title*="compose"]',
                        '[role="button"][aria-label*="new"]'
                    ];
                    
                    for (const selector of composeSelectors) {
                        composeButton = document.querySelector(selector);
                        if (composeButton) {
                            console.log(`✅ Found compose button with: ${selector}`);
                            break;
                        }
                    }
                }
                
                if (composeButton) {
                    // Click compose button
                    console.log('📝 Found compose button, clicking...');
                    composeButton.click();
                    
                    // Wait for compose dialog and verify it opened
                    await new Promise(resolve => setTimeout(resolve, 3000));
                    
                    // Check if compose dialog actually opened
                    const dialogOpen = document.querySelector('input[aria-label*="phone"], input[placeholder*="phone"], textarea[aria-label*="message"], textarea[placeholder*="message"]');
                    
                    if (dialogOpen) {
                        console.log('✅ Compose dialog opened successfully');
                        return { success: true, message: 'UI automation started successfully' };
                    } else {
                        console.log('❌ Compose dialog did not open');
                        
                        // Check what happened after clicking
                        const pageState = {
                            url: window.location.href,
                            title: document.title,
                            visibleInputs: Array.from(document.querySelectorAll('input, textarea')).length,
                            visibleButtons: Array.from(document.querySelectorAll('button')).length
                        };
                        
                        return { success: false, error: 'Compose dialog did not open', pageState };
                    }
                } else {
                    console.log('❌ No compose button found');
                    
                    // List all buttons for debugging
                    const allButtons = Array.from(document.querySelectorAll('button')).map(btn => ({
                        text: btn.textContent?.trim() || '',
                        aria: btn.getAttribute('aria-label') || '',
                        title: btn.getAttribute('title') || '',
                        visible: btn.offsetParent !== null
                    })).filter(btn => (btn.text || btn.aria || btn.title) && btn.visible);
                    
                    console.log('Available visible buttons:', allButtons.slice(0, 15));
                    
                    return { success: false, error: 'No compose button found', buttons: allButtons.slice(0, 15) };
                }
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }, message, recipient);
        
        console.log(`🎭 UI Result: ${JSON.stringify(uiResult, null, 2)}`);
        
        if (uiResult.success) {
            // Continue with filling out the form
            console.log('📝 Continuing with form automation...');
            
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            const formResult = await page.evaluate(async (message, recipient) => {
                try {
                    // Look for phone input
                    const phoneInputSelectors = [
                        'input[aria-label*="phone" i]',
                        'input[placeholder*="phone" i]',
                        'input[type="tel"]',
                        'input[name*="phone"]',
                        'input[id*="phone"]'
                    ];
                    
                    let phoneInput = null;
                    for (const selector of phoneInputSelectors) {
                        phoneInput = document.querySelector(selector);
                        if (phoneInput) break;
                    }
                    
                    // Look for message input
                    const messageInputSelectors = [
                        'textarea[aria-label*="message" i]',
                        'textarea[placeholder*="message" i]',
                        'div[contenteditable="true"]',
                        'input[aria-label*="message" i]'
                    ];
                    
                    let messageInput = null;
                    for (const selector of messageInputSelectors) {
                        messageInput = document.querySelector(selector);
                        if (messageInput) break;
                    }
                    
                    if (phoneInput && messageInput) {
                        // Fill out the form
                        phoneInput.focus();
                        phoneInput.value = recipient;
                        phoneInput.dispatchEvent(new Event('input', { bubbles: true }));
                        
                        messageInput.focus();
                        if (messageInput.tagName === 'DIV') {
                            messageInput.textContent = message;
                        } else {
                            messageInput.value = message;
                        }
                        messageInput.dispatchEvent(new Event('input', { bubbles: true }));
                        
                        // Look for send button
                        const sendSelectors = [
                            'button[aria-label*="send"]',
                            'button[title*="send"]',
                            'button[aria-label*="Send"]',
                            'button[title*="Send"]',
                            '[role="button"][aria-label*="send"]'
                        ];
                        
                        let sendButton = null;
                        for (const selector of sendSelectors) {
                            sendButton = document.querySelector(selector);
                            if (sendButton) break;
                        }
                        
                        // Also look for buttons with "Send" text
                        if (!sendButton) {
                            const allButtons = Array.from(document.querySelectorAll('button'));
                            sendButton = allButtons.find(btn => 
                                btn.textContent?.toLowerCase().includes('send') ||
                                btn.getAttribute('aria-label')?.toLowerCase().includes('send')
                            );
                        }
                        
                        if (sendButton) {
                            console.log('📤 Found send button, clicking...');
                            sendButton.click();
                            
                            return { success: true, message: 'SMS sent via UI automation!' };
                        } else {
                            // List available buttons for debugging
                            const allButtons = Array.from(document.querySelectorAll('button')).map(btn => ({
                                text: btn.textContent?.trim() || '',
                                aria: btn.getAttribute('aria-label') || '',
                                title: btn.getAttribute('title') || ''
                            })).filter(btn => btn.text || btn.aria || btn.title);
                            
                            return { 
                                success: false, 
                                error: 'Send button not found',
                                availableButtons: allButtons.slice(0, 10)
                            };
                        }
                        
                    } else {
                        return { 
                            success: false, 
                            error: 'Form inputs not found',
                            phoneInput: !!phoneInput,
                            messageInput: !!messageInput
                        };
                    }
                    
                } catch (error) {
                    return {
                        success: false,
                        error: error.message
                    };
                }
            }, message, recipient);
            
            console.log(`📝 Form Result: ${JSON.stringify(formResult, null, 2)}`);
            return formResult;
        }
        
        return uiResult;
        
        console.log(`📊 SMS Result: ${JSON.stringify(result, null, 2)}`);
        return result;
        
    } catch (error) {
        console.error('❌ SMS test error:', error);
        return { success: false, error: error.message };
    }
}

// Run the test
testDirectPuppeteer().then(success => {
    console.log(`\n${'='*60}`);
    console.log(`🎯 FINAL RESULT: ${success ? 'SUCCESS' : 'FAILED'}`);
    console.log(`${'='*60}`);
    process.exit(success ? 0 : 1);
}).catch(error => {
    console.error('💥 Test crashed:', error);
    process.exit(1);
});