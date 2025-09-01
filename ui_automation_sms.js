const express = require('express');
const puppeteer = require('./nodejs-waa/node_modules/puppeteer');

const app = express();
app.use(express.json());

let browser = null;
let page = null;

// Initialize browser with Google Voice
async function initializeGoogleVoice(cookies) {
    try {
        console.log('🚀 Initializing Google Voice browser...');
        
        // Always restart browser for fresh session
        if (browser) {
            try {
                await browser.close();
            } catch (e) {
                console.log('⚠️ Error closing existing browser:', e.message);
            }
            browser = null;
            page = null;
        }
        
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
        console.log(`✅ Set ${cookieObjects.length} cookies`);
        
        // Navigate to Google Voice messages
        await page.goto('https://voice.google.com/u/0/messages', { 
            waitUntil: 'domcontentloaded',
            timeout: 30000 
        });
        
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        const title = await page.title();
        console.log(`📄 Loaded: ${title}`);
        
        return title.includes('Voice');
        
    } catch (error) {
        console.error('❌ Browser initialization failed:', error);
        return false;
    }
}

// Send SMS using UI automation
async function sendSMSViaUI(recipient, message) {
    try {
        console.log(`📱 Sending SMS to ${recipient}: ${message}`);
        
        if (!page) {
            throw new Error('Browser not initialized');
        }
        
        // Click compose button
        const composeResult = await page.evaluate(() => {
            const composeSelectors = [
                '[aria-label*="Compose"]',
                '[data-e2e*="compose"]', 
                'button[title*="compose"]',
                '[role="button"][aria-label*="new"]'
            ];
            
            for (const selector of composeSelectors) {
                const button = document.querySelector(selector);
                if (button) {
                    button.click();
                    console.log(`✅ Clicked compose: ${selector}`);
                    return { success: true, selector };
                }
            }
            
            return { success: false, error: 'Compose button not found' };
        });
        
        if (!composeResult.success) {
            return { success: false, error: composeResult.error };
        }
        
        // Wait for compose dialog to open
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Fill out the SMS form
        const formResult = await page.evaluate(async (message, recipient) => {
            try {
                // Find phone input
                const phoneInputSelectors = [
                    'input[aria-label*="phone"]',
                    'input[placeholder*="phone"]',
                    'input[type="tel"]',
                    'input[name*="phone"]',
                    'input[id*="phone"]'
                ];
                
                let phoneInput = null;
                for (const selector of phoneInputSelectors) {
                    phoneInput = document.querySelector(selector);
                    if (phoneInput) {
                        console.log(`📞 Found phone input: ${selector}`);
                        break;
                    }
                }
                
                // Find message input
                const messageInputSelectors = [
                    'textarea[aria-label*="message"]',
                    'textarea[placeholder*="message"]',
                    'div[contenteditable="true"]',
                    'input[aria-label*="message"]'
                ];
                
                let messageInput = null;
                for (const selector of messageInputSelectors) {
                    messageInput = document.querySelector(selector);
                    if (messageInput) {
                        console.log(`💬 Found message input: ${selector}`);
                        break;
                    }
                }
                
                if (!phoneInput || !messageInput) {
                    // Debug available inputs
                    const allInputs = Array.from(document.querySelectorAll('input, textarea')).map(inp => ({
                        tag: inp.tagName,
                        type: inp.type || '',
                        aria: inp.getAttribute('aria-label') || '',
                        placeholder: inp.getAttribute('placeholder') || ''
                    }));
                    
                    return { 
                        success: false, 
                        error: 'Form inputs not found',
                        phoneInput: !!phoneInput,
                        messageInput: !!messageInput,
                        availableInputs: allInputs.slice(0, 10)
                    };
                }
                
                // Fill phone number
                phoneInput.focus();
                phoneInput.value = recipient;
                phoneInput.dispatchEvent(new Event('input', { bubbles: true }));
                phoneInput.dispatchEvent(new Event('change', { bubbles: true }));
                
                console.log(`📞 Entered phone: ${recipient}`);
                
                // Fill message
                messageInput.focus();
                if (messageInput.tagName === 'DIV') {
                    messageInput.textContent = message;
                } else {
                    messageInput.value = message;
                }
                messageInput.dispatchEvent(new Event('input', { bubbles: true }));
                messageInput.dispatchEvent(new Event('change', { bubbles: true }));
                
                console.log(`💬 Entered message: ${message}`);
                
                // Wait a moment for form validation
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                // Find and click send button
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
                    console.log('📤 Clicking send button...');
                    sendButton.click();
                    
                    // Wait for send to complete
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    
                    return { success: true, message: 'SMS sent successfully via UI!' };
                } else {
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
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }, message, recipient);
        
        return formResult;
        
    } catch (error) {
        console.error('❌ SMS sending failed:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

// API endpoints
app.post('/initialize', async (req, res) => {
    try {
        const { cookies } = req.body;
        console.log('📥 Initialize request received');
        
        const success = await initializeGoogleVoice(cookies);
        res.json({ 
            success,
            message: success ? 'Google Voice initialized' : 'Initialization failed'
        });
        
    } catch (error) {
        console.error('❌ Init error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.post('/send-sms', async (req, res) => {
    try {
        const { recipient, message } = req.body;
        console.log('📥 SMS request received');
        
        if (!recipient || !message) {
            return res.status(400).json({ 
                success: false, 
                error: 'recipient and message are required' 
            });
        }
        
        const result = await sendSMSViaUI(recipient, message);
        res.json(result);
        
    } catch (error) {
        console.error('❌ SMS API error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.get('/health', (req, res) => {
    res.json({
        status: 'running',
        browserReady: !!browser && !!page,
        timestamp: new Date().toISOString()
    });
});

// Start server
const PORT = 3005;
app.listen(PORT, 'localhost', () => {
    console.log(`🚀 UI Automation SMS Service running on http://localhost:${PORT}`);
    console.log('✅ Ready to send SMS via Google Voice UI automation!');
});

// Cleanup
process.on('SIGINT', async () => {
    console.log('🛑 Shutting down...');
    if (browser) {
        await browser.close();
    }
    process.exit(0);
});