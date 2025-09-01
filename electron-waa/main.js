const { app, BrowserWindow, ipcMain } = require('electron');
const express = require('express');
const path = require('path');
const crypto = require('crypto');

// Express server for Python communication
const server = express();
server.use(express.json());

let mainWindow;
let waaData = null;
let waaExpiry = null;

// Google Voice constants
const WAA_API_KEY = 'AIzaSyBGb5fGAyC-pRcRU6MUHb__b_vKha71HRE';
const WAA_REQUEST_KEY = '/JR8jsAkqotcKsEKhXic';
const WAA_CREATE_URL = 'https://waa-pa.clients6.google.com/$rpc/google.internal.waa.v1.Waa/Create';
const SMS_ENDPOINT = 'https://clients6.google.com/voice/v1/voiceclient/api2thread/sendsms';

function createWindow() {
    // Create browser window similar to mautrix-gvoice
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        show: false, // Hidden like mautrix-gvoice
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            enableRemoteModule: false,
            webSecurity: true, // Keep web security enabled
            preload: path.join(__dirname, 'preload.js'),
            // Add sandbox flags for headless environment
            additionalArguments: ['--no-sandbox', '--disable-gpu']
        }
    });

    // Load Google Voice like mautrix-gvoice does
    console.log('🌐 Loading Google Voice in Electron...');
    mainWindow.loadURL('https://voice.google.com/u/0/');
    
    // Wait for page load
    mainWindow.webContents.on('did-finish-load', () => {
        console.log('✅ Google Voice loaded in Electron');
    });

    // Handle errors
    mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
        console.log(`❌ Failed to load Google Voice: ${errorDescription}`);
    });
}

// Initialize WAA system
async function initializeWAA(cookies) {
    try {
        console.log('🚀 Initializing Electron WAA system...');
        
        // Set cookies in Electron browser
        const session = mainWindow.webContents.session;
        for (const [name, value] of Object.entries(cookies)) {
            await session.cookies.set({
                url: 'https://voice.google.com',
                name: name,
                value: value,
                domain: '.google.com',
                path: '/',
                secure: true,
                httpOnly: false
            });
        }
        
        // Navigate to Google Voice with cookies
        await mainWindow.loadURL('https://voice.google.com/u/0/messages');
        
        // Wait for page to be ready
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Get WAA data from Google
        waaData = await getWAAData(cookies);
        if (!waaData) {
            throw new Error('Failed to get WAA data');
        }
        
        // Load WAA script in Electron context
        await loadWAAScript(waaData);
        
        waaExpiry = Date.now() + (60 * 60 * 1000); // 1 hour
        console.log('✅ Electron WAA initialized successfully!');
        return true;
        
    } catch (error) {
        console.error('❌ WAA initialization failed:', error);
        return false;
    }
}

// Get WAA data from Google's service
async function getWAAData(cookies) {
    try {
        const timestamp = Math.floor(Date.now() / 1000);
        const sapisid = cookies.SAPISID || '';
        const hashInput = `${timestamp} ${sapisid} https://voice.google.com`;
        const hashValue = crypto.createHash('sha1').update(hashInput).digest('hex');
        const authHeader = `SAPISIDHASH ${timestamp}_${hashValue}`;
        
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
            const data = await response.json();
            console.log('✅ WAA data received');
            
            // Parse PBLite response
            const respData = data[0];
            return {
                interpreterUrl: respData[2][3],
                interpreterHash: respData[3],
                program: respData[4], 
                globalName: respData[5]
            };
        } else {
            console.error('❌ WAA request failed:', response.status);
            return null;
        }
        
    } catch (error) {
        console.error('❌ WAA data error:', error);
        return null;
    }
}

// Load WAA script in Electron context
async function loadWAAScript(waaData) {
    try {
        const interpreterUrl = waaData.interpreterUrl.startsWith('//') ? 
            'https:' + waaData.interpreterUrl : waaData.interpreterUrl;
        
        console.log('📜 Loading WAA script in Electron...');
        
        // Execute in main world context like mautrix-gvoice
        await mainWindow.webContents.executeJavaScript(`
            new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = '${interpreterUrl}';
                script.onload = () => {
                    console.log('WAA script loaded in Electron');
                    resolve(true);
                };
                script.onerror = (err) => {
                    console.error('WAA script load failed:', err);
                    reject(err);
                };
                document.head.appendChild(script);
            })
        `);
        
        // Wait for script initialization
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Verify WAA function is available
        const functionAvailable = await mainWindow.webContents.executeJavaScript(`
            typeof window['${waaData.globalName}'] !== 'undefined' && 
            typeof window['${waaData.globalName}'].a === 'function'
        `);
        
        if (functionAvailable) {
            console.log(`✅ WAA function '${waaData.globalName}' ready in Electron`);
            return true;
        } else {
            throw new Error(`WAA function '${waaData.globalName}' not found`);
        }
        
    } catch (error) {
        console.error('❌ WAA script loading failed:', error);
        throw error;
    }
}

// Generate authentic WAA signature in Electron context
async function generateWAASignature(threadId, recipients, transactionId) {
    try {
        if (!waaData || Date.now() > waaExpiry) {
            throw new Error('WAA data expired or not initialized');
        }
        
        console.log('🔐 Generating WAA signature in Electron...');
        
        // Create signature payload
        const payload = {
            threadId: threadId,
            recipients: recipients,
            transactionId: transactionId,
            timestamp: Math.floor(Date.now() / 1000)
        };
        
        // Execute WAA in Electron's main world - just like mautrix-gvoice
        const signature = await mainWindow.webContents.executeJavaScript(`
            new Promise((resolve, reject) => {
                try {
                    const payload = ${JSON.stringify(payload)};
                    const program = ${JSON.stringify(waaData.program)};
                    const globalName = '${waaData.globalName}';
                    
                    console.log('Executing WAA in Electron context...');
                    
                    // Execute exactly like mautrix-gvoice does
                    window[globalName].a(program, (fn1, fn2, fn3, fn4) => {
                        console.log('WAA functions received');
                        fn1(result => {
                            console.log('WAA result:', result);
                            resolve(result);
                        }, [payload]);
                    }, true, undefined, () => {});
                    
                } catch (error) {
                    console.error('WAA execution error:', error);
                    reject(error);
                }
            })
        `);
        
        console.log('✅ WAA signature generated in Electron!');
        return signature;
        
    } catch (error) {
        console.error('❌ WAA signature generation failed:', error);
        return null;
    }
}

// Send SMS using Electron-generated WAA signature
async function sendSMS(cookies, recipient, message, threadId = '') {
    try {
        const transactionId = Math.floor(Math.random() * 99999999999999);
        
        // Generate authentic WAA signature
        const waaSignature = await generateWAASignature(
            threadId || 'new_conversation',
            [recipient], 
            transactionId
        );
        
        if (!waaSignature) {
            console.log('⚠️ Failed to generate WAA signature, using fallback');
            waaSignature = '!';
        }
        
        // Send SMS with Electron-generated signature
        const timestamp = Math.floor(Date.now() / 1000);
        const sapisid = cookies.SAPISID || '';
        const hashInput = `${timestamp} ${sapisid} https://voice.google.com`;
        const hashValue = crypto.createHash('sha1').update(hashInput).digest('hex');
        const authHeader = `SAPISIDHASH ${timestamp}_${hashValue}`;
        
        const response = await fetch(SMS_ENDPOINT, {
            method: 'POST',
            headers: {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
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
                message,           // message text
                threadId || null,  // thread ID
                [recipient],       // recipients
                null,
                [transactionId],   // transaction ID
                null,
                [waaSignature]     // WAA signature from Electron!
            ])
        });
        
        console.log(`📤 SMS Response: ${response.status}`);
        
        if (response.ok) {
            console.log('✅ SMS sent successfully with Electron WAA!');
            return {
                success: true,
                transactionId: transactionId,
                signatureType: waaSignature === '!' ? 'FALLBACK' : 'ELECTRON_WAA'
            };
        } else {
            const error = await response.text();
            console.log('❌ SMS failed:', error);
            return {
                success: false,
                error: error,
                statusCode: response.status
            };
        }
        
    } catch (error) {
        console.error('❌ SMS send error:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

// Express server for Python communication
server.post('/initialize', async (req, res) => {
    try {
        const { cookies } = req.body;
        const success = await initializeWAA(cookies);
        res.json({ success });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

server.post('/send-sms', async (req, res) => {
    try {
        const { cookies, recipient, message, threadId } = req.body;
        const result = await sendSMS(cookies, recipient, message, threadId);
        res.json(result);
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

server.get('/health', (req, res) => {
    res.json({ 
        status: 'running',
        waaInitialized: !!waaData,
        waaExpiry: waaExpiry
    });
});

// Start Electron app
app.whenReady().then(() => {
    createWindow();
    
    // Start Express server
    const port = 3001;
    server.listen(port, 'localhost', () => {
        console.log(`🚀 Electron WAA server running on http://localhost:${port}`);
    });
    
    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

// Prevent navigation away from Google Voice
app.on('web-contents-created', (event, contents) => {
    contents.on('will-navigate', (event, navigationUrl) => {
        const parsedUrl = new URL(navigationUrl);
        
        if (parsedUrl.origin !== 'https://voice.google.com') {
            console.log(`🚫 Blocking navigation to: ${navigationUrl}`);
            event.preventDefault();
        }
    });
});

console.log('🚀 Starting Electron WAA Service...');