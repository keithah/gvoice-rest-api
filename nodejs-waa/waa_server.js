const express = require('express');
const puppeteer = require('puppeteer');
const crypto = require('crypto');
const https = require('https');

const app = express();
app.use(express.json());

let browser = null;
let page = null;
let waaData = null;
let waaExpiry = null;

// Google Voice constants
const WAA_API_KEY = 'AIzaSyBGb5fGAyC-pRcRU6MUHb__b_vKha71HRE';
const WAA_REQUEST_KEY = '/JR8jsAkqotcKsEKhXic';
const WAA_CREATE_URL = 'https://waa-pa.clients6.google.com/$rpc/google.internal.waa.v1.Waa/Create';
const SMS_ENDPOINT = 'https://clients6.google.com/voice/v1/voiceclient/api2thread/sendsms';

// Initialize Puppeteer browser
async function initializeBrowser() {
    try {
        console.log('🚀 Starting Puppeteer browser...');
        
        browser = await puppeteer.launch({
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        });
        
        page = await browser.newPage();
        
        // Set user agent to match Chrome
        await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36');
        
        console.log('✅ Puppeteer browser ready');
        return true;
        
    } catch (error) {
        console.error('❌ Browser initialization failed:', error);
        return false;
    }
}

// Set cookies in browser
async function setCookies(cookies) {
    try {
        const cookieObjects = Object.entries(cookies).map(([name, value]) => ({
            name,
            value,
            domain: '.google.com',
            path: '/',
            secure: true,
            httpOnly: false,
            sameSite: 'None'
        }));
        
        await page.setCookie(...cookieObjects);
        console.log(`🍪 Set ${cookieObjects.length} cookies in browser`);
        return true;
        
    } catch (error) {
        console.error('❌ Cookie setting failed:', error);
        return false;
    }
}

// Get WAA data from Google using Puppeteer's page.evaluate
async function getWAAData(cookies) {
    try {
        console.log('📋 Getting WAA data from Google...');
        const timestamp = Math.floor(Date.now() / 1000);
        const sapisid = cookies.SAPISID || '';
        const hashInput = `${timestamp} ${sapisid} https://voice.google.com`;
        const hashValue = crypto.createHash('sha1').update(hashInput).digest('hex');
        const authHeader = `SAPISIDHASH ${timestamp}_${hashValue}`;
        
        // Use Puppeteer's fetch to make the request from the browser context
        const waaResponse = await page.evaluate(async (WAA_CREATE_URL, WAA_REQUEST_KEY, authHeader, WAA_API_KEY) => {
            try {
                const response = await fetch(WAA_CREATE_URL, {
                    method: 'POST',
                    headers: {
                        'Authorization': authHeader,
                        'X-Goog-Api-Key': WAA_API_KEY,
                        'X-User-Agent': 'grpc-web-javascript/0.1',
                        'Content-Type': 'application/json+protobuf',
                        'Origin': 'https://voice.google.com',
                        'Referer': 'https://voice.google.com/'
                    },
                    body: JSON.stringify([WAA_REQUEST_KEY])
                });
                
                if (response.ok) {
                    return await response.json();
                } else {
                    throw new Error(`WAA request failed: ${response.status}`);
                }
            } catch (error) {
                console.error('WAA fetch error:', error);
                return null;
            }
        }, WAA_CREATE_URL, WAA_REQUEST_KEY, authHeader, WAA_API_KEY);
        
        if (waaResponse) {
            console.log('🔍 WAA response type:', typeof waaResponse);
            console.log('🔍 WAA response:', JSON.stringify(waaResponse).substring(0, 200) + '...');
            
            if (waaResponse[0]) {
                const respData = waaResponse[0];
                console.log('✅ WAA data received, parsing...');
                
                return {
                    interpreterUrl: respData[2] && respData[2][3] ? respData[2][3] : null,
                    interpreterHash: respData[3],
                    program: respData[4],
                    globalName: respData[5]
                };
            } else {
                console.error('❌ WAA response missing data array');
                return null;
            }
        } else {
            console.error('❌ No WAA response received');
            return null;
        }
        
    } catch (error) {
        console.error('❌ WAA data error:', error);
        return null;
    }
}

// Load WAA script in Puppeteer page
async function loadWAAScript(waaData) {
    try {
        const interpreterUrl = waaData.interpreterUrl.startsWith('//') ? 
            'https:' + waaData.interpreterUrl : waaData.interpreterUrl;
        
        console.log('📜 Loading WAA script in Puppeteer...');
        
        // Load script in page context
        await page.addScriptTag({
            url: interpreterUrl,
            type: 'text/javascript'
        });
        
        // Wait for script initialization
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Verify function is available
        const functionAvailable = await page.evaluate((globalName) => {
            return typeof window[globalName] !== 'undefined' && 
                   typeof window[globalName].a === 'function';
        }, waaData.globalName);
        
        if (functionAvailable) {
            console.log(`✅ WAA function '${waaData.globalName}' ready`);
            return true;
        } else {
            throw new Error(`WAA function not found: ${waaData.globalName}`);
        }
        
    } catch (error) {
        console.error('❌ WAA script loading failed:', error);
        throw error;
    }
}

// Generate WAA signature using Puppeteer
async function generateWAASignature(threadId, recipients, transactionId) {
    try {
        if (!waaData || Date.now() > waaExpiry) {
            throw new Error('WAA data expired');
        }
        
        console.log('🔐 Generating WAA signature...');
        
        const payload = {
            threadId,
            recipients,
            transactionId,
            timestamp: Math.floor(Date.now() / 1000)
        };
        
        // Execute WAA in Puppeteer context
        const signature = await page.evaluate((payload, program, globalName) => {
            return new Promise((resolve, reject) => {
                try {
                    window[globalName].a(program, (fn1, fn2, fn3, fn4) => {
                        fn1(result => {
                            resolve(result);
                        }, [payload]);
                    }, true, undefined, () => {});
                } catch (error) {
                    reject(error);
                }
            });
        }, payload, waaData.program, waaData.globalName);
        
        console.log('✅ WAA signature generated');
        return signature;
        
    } catch (error) {
        console.error('❌ WAA generation failed:', error);
        return null;
    }
}

// Send SMS with WAA signature
async function sendSMS(cookies, recipient, message, threadId = '') {
    try {
        const transactionId = Math.floor(Math.random() * 99999999999999);
        
        // Generate WAA signature
        const waaSignature = await generateWAASignature(
            threadId || 'new_conversation',
            [recipient],
            transactionId
        ) || '!';
        
        // Send SMS
        const timestamp = Math.floor(Date.now() / 1000);
        const sapisid = cookies.SAPISID || '';
        const hashInput = `${timestamp} ${sapisid} https://voice.google.com`;
        const hashValue = crypto.createHash('sha1').update(hashInput).digest('hex');
        const authHeader = `SAPISIDHASH ${timestamp}_${hashValue}`;
        
        // Send SMS using Puppeteer's page context
        const smsResponse = await page.evaluate(async (SMS_ENDPOINT, authHeader, message, threadId, recipient, transactionId, waaSignature) => {
            try {
                const response = await fetch(SMS_ENDPOINT + '?key=AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg&alt=proto', {
                    method: 'POST',
                    headers: {
                        'Authorization': authHeader,
                        'X-Goog-Api-Key': 'AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg',
                        'X-Client-Version': '665865172',
                        'Content-Type': 'application/json+protobuf',
                        'Origin': 'https://voice.google.com',
                        'Referer': 'https://voice.google.com/',
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
                    },
                    body: JSON.stringify([
                        null, null, null, null,
                        message,
                        threadId || null,
                        [recipient],
                        null,
                        [transactionId],
                        null,
                        [waaSignature]
                    ])
                });
                
                return {
                    ok: response.ok,
                    status: response.status,
                    text: response.ok ? 'SUCCESS' : await response.text()
                };
            } catch (error) {
                return {
                    ok: false,
                    status: 0,
                    text: error.message
                };
            }
        }, SMS_ENDPOINT, authHeader, message, threadId, recipient, transactionId, waaSignature);
        
        const response = smsResponse;
        
        console.log(`📤 SMS Response: ${response.status}`);
        
        if (response.ok) {
            return {
                success: true,
                transactionId,
                signatureType: waaSignature === '!' ? 'FALLBACK' : 'PUPPETEER_WAA'
            };
        } else {
            const error = await response.text();
            return {
                success: false,
                error,
                statusCode: response.status
            };
        }
        
    } catch (error) {
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
        
        if (!browser) {
            const browserReady = await initializeBrowser();
            if (!browserReady) {
                return res.status(500).json({ success: false, error: 'Browser failed' });
            }
        }
        
        // Set cookies
        await setCookies(cookies);
        
        // Navigate to Google Voice
        await page.goto('https://voice.google.com/u/0/messages', { waitUntil: 'domcontentloaded' });
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Get WAA data
        waaData = await getWAAData(cookies);
        if (!waaData) {
            return res.status(500).json({ success: false, error: 'WAA data failed' });
        }
        
        // Load WAA script
        await loadWAAScript(waaData);
        
        waaExpiry = Date.now() + (60 * 60 * 1000); // 1 hour
        
        res.json({ success: true });
        
    } catch (error) {
        console.error('❌ Initialization error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.post('/send-sms', async (req, res) => {
    try {
        const { cookies, recipient, message, threadId } = req.body;
        const result = await sendSMS(cookies, recipient, message, threadId);
        res.json(result);
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

app.get('/health', (req, res) => {
    res.json({
        status: 'running',
        browserReady: !!browser,
        waaInitialized: !!waaData,
        waaExpiry
    });
});

// Start server
const PORT = 3002;
app.listen(PORT, 'localhost', () => {
    console.log(`🚀 Node.js WAA server running on http://localhost:${PORT}`);
});

// Handle cleanup
process.on('SIGINT', async () => {
    console.log('🛑 Shutting down WAA server...');
    if (browser) {
        await browser.close();
    }
    process.exit(0);
});