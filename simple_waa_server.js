const express = require('express');
const puppeteer = require('puppeteer');
const crypto = require('crypto');

const app = express();
app.use(express.json());

let browser = null;
let page = null;

// Initialize Puppeteer and navigate to Google Voice
async function initializeBrowser(cookies) {
    try {
        console.log('🚀 Starting browser with cookies...');
        
        if (!browser) {
            browser = await puppeteer.launch({
                headless: true,
                args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            });
        }
        
        if (!page) {
            page = await browser.newPage();
            await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36');
        }
        
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
        console.log(`🍪 Set ${cookieObjects.length} cookies`);
        
        // Navigate to Google Voice
        console.log('🌐 Navigating to Google Voice...');
        await page.goto('https://voice.google.com/u/0/messages', { 
            waitUntil: 'domcontentloaded',
            timeout: 30000
        });
        
        // Wait for page to load
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        // Check if logged in
        const title = await page.title();
        console.log(`📄 Page title: ${title}`);
        
        if (title.includes('Voice') || title.includes('Messages')) {
            console.log('✅ Successfully loaded Google Voice');
            return true;
        } else {
            console.log('❌ Failed to load Google Voice properly');
            return false;
        }
        
    } catch (error) {
        console.error('❌ Browser initialization failed:', error);
        return false;
    }
}

// Test SMS sending with simple approach
async function testSMSSending(cookies, recipient, message) {
    try {
        console.log(`📱 Testing SMS to ${recipient}: ${message}`);
        
        // Use the browser's fetch to make the SMS request
        const timestamp = Math.floor(Date.now() / 1000);
        const sapisid = cookies.SAPISID || '';
        const hashInput = `${timestamp} ${sapisid} https://voice.google.com`;
        const hashValue = crypto.createHash('sha1').update(hashInput).digest('hex');
        const authHeader = `SAPISIDHASH ${timestamp}_${hashValue}`;
        
        const transactionId = Math.floor(Math.random() * 99999999999999);
        
        // Make SMS request from browser context (same-origin)
        const result = await page.evaluate(async (authHeader, message, recipient, transactionId) => {
            try {
                const response = await fetch('https://clients6.google.com/voice/v1/voiceclient/api2thread/sendsms?key=AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg&alt=proto', {
                    method: 'POST',
                    headers: {
                        'Authorization': authHeader,
                        'X-Goog-Api-Key': 'AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg',
                        'X-Client-Version': '665865172',
                        'Content-Type': 'application/json+protobuf',
                        'Origin': 'https://voice.google.com',
                        'Referer': 'https://voice.google.com/',
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-Goog-AuthUser': '0'
                    },
                    body: JSON.stringify([
                        null, null, null, null,
                        message,
                        null,
                        [recipient],
                        null,
                        [transactionId],
                        null,
                        ['!']  // Simple placeholder WAA for now
                    ])
                });
                
                return {
                    ok: response.ok,
                    status: response.status,
                    statusText: response.statusText,
                    text: response.ok ? 'SUCCESS' : await response.text()
                };
            } catch (error) {
                return {
                    ok: false,
                    status: 0,
                    statusText: 'FETCH_ERROR',
                    text: error.message
                };
            }
        }, authHeader, message, recipient, transactionId);
        
        console.log(`📤 SMS result: ${JSON.stringify(result, null, 2)}`);
        
        return {
            success: result.ok,
            transactionId: transactionId,
            result: result
        };
        
    } catch (error) {
        console.error('❌ SMS test failed:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

// API endpoints
app.post('/test-init', async (req, res) => {
    try {
        const { cookies } = req.body;
        console.log('📥 Test initialization request received');
        
        const success = await initializeBrowser(cookies);
        res.json({ 
            success,
            message: success ? 'Browser initialized' : 'Browser initialization failed'
        });
        
    } catch (error) {
        console.error('❌ Test init error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.post('/test-sms', async (req, res) => {
    try {
        const { cookies, recipient, message } = req.body;
        console.log('📥 Test SMS request received');
        
        const result = await testSMSSending(cookies, recipient, message);
        res.json(result);
        
    } catch (error) {
        console.error('❌ Test SMS error:', error);
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
const PORT = 3003;
app.listen(PORT, 'localhost', () => {
    console.log(`🚀 Simple Node.js WAA test server running on http://localhost:${PORT}`);
});

// Cleanup
process.on('SIGINT', async () => {
    console.log('🛑 Shutting down...');
    if (browser) {
        await browser.close();
    }
    process.exit(0);
});