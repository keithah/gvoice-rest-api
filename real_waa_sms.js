const puppeteer = require('./nodejs-waa/node_modules/puppeteer');
const crypto = require('crypto');
const fs = require('fs');

async function sendSMSWithRealWAA() {
    console.log('🎯 REAL WAA SMS SENDER');
    console.log('='*50);
    
    const cookies = JSON.parse(fs.readFileSync('fresh_cookies.json', 'utf8'));
    const recipient = '13602415033';
    const message = `Real WAA SMS ${new Date().toLocaleTimeString()}`;
    
    let browser;
    let page;
    
    try {
        browser = await puppeteer.launch({
            headless: "new",
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        });
        
        page = await browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36');
        
        // Set cookies
        const cookieObjects = Object.entries(cookies).map(([name, value]) => ({
            name, value, domain: '.google.com', path: '/', secure: true, httpOnly: false
        }));
        
        await page.setCookie(...cookieObjects);
        console.log(`✅ Set ${cookieObjects.length} cookies`);
        
        // Navigate to Google Voice
        console.log('🌐 Loading Google Voice...');
        await page.goto('https://voice.google.com/about', { 
            waitUntil: 'networkidle2',
            timeout: 30000 
        });
        
        console.log(`📄 Page: ${await page.title()}`);
        
        // Step 1: Get WAA data from Google Voice
        console.log('\n🔍 Step 1: Getting WAA configuration...');
        
        const waaData = await page.evaluate(async () => {
            try {
                console.log('📡 Fetching WAA data...');
                
                // Get WAA data (this is what mautrix-gvoice does)
                const response = await fetch('https://waa-pa.clients6.google.com/$rpc/google.internal.waa.v1.Waa/Create', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json+protobuf',
                        'X-Goog-Api-Key': 'AIzaSyBGb5fGAyC-pRcRU6MUHb__b_vKha71HRE'
                    },
                    body: JSON.stringify([null, null, ['/JR8jsAkqotcKsEKhXic'], null, null, null, null, []])
                });
                
                if (!response.ok) {
                    return { success: false, error: `WAA data fetch failed: ${response.status}` };
                }
                
                const responseText = await response.text();
                console.log('📦 WAA response:', responseText.substring(0, 200));
                
                // Parse the response (simplified - mautrix-gvoice has complex parsing)
                let waaConfig;
                try {
                    const data = JSON.parse(responseText);
                    waaConfig = data[0];
                } catch (e) {
                    console.log('⚠️ WAA response not JSON, using raw text');
                    waaConfig = responseText;
                }
                
                return { success: true, waaConfig };
                
            } catch (error) {
                return { success: false, error: error.message };
            }
        });
        
        console.log(`🔧 WAA Data: ${JSON.stringify(waaData, null, 2)}`);
        
        if (!waaData.success) {
            console.log('❌ Failed to get WAA data');
            return false;
        }
        
        // Step 2: Try to load WAA script and generate signature
        console.log('\n🔍 Step 2: Loading WAA script...');
        
        const scriptLoaded = await page.evaluate(async (waaConfig) => {
            try {
                // Extract script URL from WAA config (simplified)
                let scriptUrl = '';
                
                if (typeof waaConfig === 'string' && waaConfig.includes('//')) {
                    // Find URL in response
                    const urlMatch = waaConfig.match(/\/\/[^"'\s]+\.js/);
                    if (urlMatch) {
                        scriptUrl = 'https:' + urlMatch[0];
                    }
                } else if (waaConfig && waaConfig.script_source) {
                    scriptUrl = waaConfig.script_source;
                }
                
                if (!scriptUrl) {
                    return { success: false, error: 'No script URL found in WAA config' };
                }
                
                console.log(`📜 Loading WAA script: ${scriptUrl}`);
                
                // Load the WAA script
                const script = document.createElement('script');
                script.src = scriptUrl;
                
                return new Promise((resolve) => {
                    script.onload = () => {
                        console.log('✅ WAA script loaded');
                        resolve({ success: true, scriptUrl });
                    };
                    script.onerror = (err) => {
                        console.log('❌ WAA script failed to load:', err);
                        resolve({ success: false, error: 'Script load failed' });
                    };
                    document.head.appendChild(script);
                });
                
            } catch (error) {
                return { success: false, error: error.message };
            }
        }, waaData.waaConfig);
        
        console.log(`📜 Script Load: ${JSON.stringify(scriptLoaded, null, 2)}`);
        
        if (!scriptLoaded.success) {
            console.log('❌ Failed to load WAA script');
            return false;
        }
        
        // Step 3: Generate WAA signature and send SMS
        console.log('\n📱 Step 3: Generating WAA signature and sending SMS...');
        
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        const smsResult = await page.evaluate(async (recipient, message) => {
            try {
                console.log('🔐 Generating WAA signature...');
                
                // Look for WAA global objects
                const waaKeys = Object.keys(window).filter(key => 
                    key.includes('_') && 
                    window[key] && 
                    typeof window[key] === 'object' &&
                    window[key].a && 
                    typeof window[key].a === 'function'
                );
                
                console.log('🔍 Found WAA keys:', waaKeys);
                
                if (waaKeys.length === 0) {
                    return { success: false, error: 'No WAA functions found after script load' };
                }
                
                // Use the first WAA function (like mautrix-gvoice does)
                const globalName = waaKeys[0];
                const waaFunction = window[globalName];
                
                console.log(`🎯 Using WAA function: ${globalName}`);
                
                // Generate WAA signature (simplified version of mautrix-gvoice approach)
                const transactionId = Math.floor(Math.random() * 99999999999999);
                
                // This is the payload format mautrix-gvoice uses
                const payload = {
                    message_ids: [],
                    destinations: [recipient],
                    thread_id: null
                };
                
                const program = null; // Will be populated by WAA service
                
                // Execute WAA signature generation
                const waaSignature = await new Promise((resolve, reject) => {
                    try {
                        waaFunction.a(program, (fn1, fn2, fn3, fn4) => {
                            fn1(result => {
                                console.log('🔐 WAA signature generated:', result);
                                resolve(result);
                            }, [payload, undefined, undefined, undefined]);
                        }, true, undefined, () => {});
                    } catch (error) {
                        reject(error);
                    }
                });
                
                console.log('🔐 Generated WAA signature:', waaSignature);
                
                // Now send SMS with real WAA signature
                const timestamp = Math.floor(Date.now() / 1000);
                const sapisid = getCookie('SAPISID') || '';
                const hashInput = `${timestamp} ${sapisid} https://voice.google.com`;
                const hashValue = btoa(String.fromCharCode(...new Uint8Array(await crypto.subtle.digest('SHA-1', new TextEncoder().encode(hashInput)))));
                const authHeader = `SAPISIDHASH ${timestamp}_${hashValue}`;
                
                const response = await fetch('https://clients6.google.com/voice/v1/voiceclient/api2thread/sendsms?key=AIzaSyDTYc1N4xiODyrQYK0Kl6g_y279LjYkrBg&alt=proto', {
                    method: 'POST',
                    credentials: 'include',
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
                        [waaSignature]  // Real WAA signature instead of "!"
                    ])
                });
                
                const responseText = await response.text();
                
                return {
                    success: response.ok,
                    status: response.status,
                    responseText: responseText,
                    waaSignature: waaSignature
                };
                
            } catch (error) {
                return { success: false, error: error.message };
            }
        }, recipient, message);
        
        console.log(`📱 SMS Result: ${JSON.stringify(smsResult, null, 2)}`);
        
        return smsResult.success;
        
    } catch (error) {
        console.error('❌ Real WAA SMS failed:', error);
        return false;
        
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

// Helper function to get cookie value
function getCookie(name) {
    const cookies = JSON.parse(fs.readFileSync('fresh_cookies.json', 'utf8'));
    return cookies[name] || '';
}

// Run the test
sendSMSWithRealWAA().then(success => {
    console.log(`\n${'='*60}`);
    console.log(`🎯 REAL WAA RESULT: ${success ? 'SUCCESS' : 'FAILED'}`);
    console.log(`${'='*60}`);
    process.exit(success ? 0 : 1);
}).catch(error => {
    console.error('💥 Test crashed:', error);
    process.exit(1);
});