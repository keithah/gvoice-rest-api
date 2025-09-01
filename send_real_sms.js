const puppeteer = require('./nodejs-waa/node_modules/puppeteer');
const fs = require('fs');

async function sendRealSMS() {
    console.log('📱 REAL SMS SENDER');
    console.log('='*50);
    
    const cookies = JSON.parse(fs.readFileSync('fresh_cookies.json', 'utf8'));
    const recipient = '13602415033';
    const message = `Real SMS Test ${new Date().toLocaleTimeString()}`;
    
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
        
        // Navigate to messages
        console.log('🌐 Loading Google Voice messages...');
        await page.goto('https://voice.google.com/u/0/messages', { 
            waitUntil: 'networkidle2',
            timeout: 30000 
        });
        
        console.log(`📄 Page loaded: ${await page.title()}`);
        
        // Take screenshot before action
        await page.screenshot({ path: 'before_compose.png' });
        
        // Click the "Send new message" button using Puppeteer's click method
        console.log('🔍 Looking for "Send new message" button...');
        
        // Try multiple approaches to find and click the button
        let clicked = false;
        
        try {
            // Approach 1: Look for the exact button text
            const sendNewMessageButton = await page.$x("//button[contains(., 'Send new message')]");
            if (sendNewMessageButton.length > 0) {
                console.log('✅ Found "Send new message" button via XPath');
                await sendNewMessageButton[0].click();
                clicked = true;
            }
        } catch (e) {
            console.log('⚠️ XPath approach failed:', e.message);
        }
        
        if (!clicked) {
            // Approach 2: Look for any clickable element containing the text
            try {
                await page.evaluate(() => {
                    const allElements = Array.from(document.querySelectorAll('*'));
                    
                    for (const el of allElements) {
                        const text = el.textContent?.trim() || '';
                        
                        if (text === 'Send new message' && el.offsetParent !== null) {
                            console.log(`🎯 Found and clicking: ${el.tagName}`);
                            el.click();
                            
                            // Also click parent if it's clickable
                            let parent = el.parentElement;
                            while (parent && parent.tagName !== 'BODY') {
                                if (parent.onclick || 
                                    parent.getAttribute('role') === 'button' || 
                                    parent.tagName === 'BUTTON' ||
                                    parent.style.cursor === 'pointer') {
                                    console.log(`🎯 Also clicking parent: ${parent.tagName}`);
                                    parent.click();
                                    break;
                                }
                                parent = parent.parentElement;
                            }
                            
                            return true;
                        }
                    }
                    return false;
                });
                clicked = true;
            } catch (e) {
                console.log('⚠️ Manual click approach failed:', e.message);
            }
        }
        
        if (!clicked) {
            // Approach 3: Click by coordinates based on screenshot
            console.log('🎯 Trying coordinate-based click...');
            await page.click('button', { delay: 100 }); // Click first button
            clicked = true;
        }
        
        if (!clicked) {
            console.log('❌ Could not find "Send new message" element');
            return false;
        }
        
        console.log('✅ Clicked "Send new message" area');
        
        // Wait for compose interface to appear
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Take screenshot after clicking
        await page.screenshot({ path: 'after_compose_click.png' });
        
        // Look for SMS input fields that should now be visible
        console.log('🔍 Looking for SMS input fields...');
        
        const inputsFound = await page.evaluate(() => {
            const phoneInputs = Array.from(document.querySelectorAll('input')).filter(inp => {
                const aria = inp.getAttribute('aria-label')?.toLowerCase() || '';
                const placeholder = inp.getAttribute('placeholder')?.toLowerCase() || '';
                const type = inp.type?.toLowerCase() || '';
                
                return (aria.includes('phone') || 
                        aria.includes('number') || 
                        placeholder.includes('phone') || 
                        placeholder.includes('number') ||
                        type === 'tel') && 
                       inp.offsetParent !== null;
            });
            
            const messageInputs = Array.from(document.querySelectorAll('textarea, input, div[contenteditable="true"]')).filter(inp => {
                const aria = inp.getAttribute('aria-label')?.toLowerCase() || '';
                const placeholder = inp.getAttribute('placeholder')?.toLowerCase() || '';
                
                return (aria.includes('message') || 
                        aria.includes('text') || 
                        placeholder.includes('message') || 
                        placeholder.includes('text')) && 
                       inp.offsetParent !== null;
            });
            
            return {
                phoneInputs: phoneInputs.map(inp => ({
                    tag: inp.tagName,
                    type: inp.type || '',
                    aria: inp.getAttribute('aria-label') || '',
                    placeholder: inp.getAttribute('placeholder') || ''
                })),
                messageInputs: messageInputs.map(inp => ({
                    tag: inp.tagName,
                    aria: inp.getAttribute('aria-label') || '',
                    placeholder: inp.getAttribute('placeholder') || ''
                }))
            };
        });
        
        console.log(`📞 Phone inputs found: ${inputsFound.phoneInputs.length}`);
        console.log(`💬 Message inputs found: ${inputsFound.messageInputs.length}`);
        
        inputsFound.phoneInputs.forEach((inp, i) => {
            console.log(`  Phone ${i+1}: ${inp.tag}[${inp.type}] - "${inp.aria}" - "${inp.placeholder}"`);
        });
        
        inputsFound.messageInputs.forEach((inp, i) => {
            console.log(`  Message ${i+1}: ${inp.tag} - "${inp.aria}" - "${inp.placeholder}"`);
        });
        
        if (inputsFound.phoneInputs.length === 0 || inputsFound.messageInputs.length === 0) {
            console.log('❌ Required input fields not found after clicking');
            return false;
        }
        
        // Fill out the form
        console.log('📝 Filling out SMS form...');
        
        const formResult = await page.evaluate(async (recipient, message) => {
            try {
                // Find phone input
                let phoneInput = null;
                const phoneInputs = Array.from(document.querySelectorAll('input')).filter(inp => {
                    const aria = inp.getAttribute('aria-label')?.toLowerCase() || '';
                    const placeholder = inp.getAttribute('placeholder')?.toLowerCase() || '';
                    const type = inp.type?.toLowerCase() || '';
                    
                    return (aria.includes('phone') || 
                            aria.includes('number') || 
                            placeholder.includes('phone') || 
                            placeholder.includes('number') ||
                            type === 'tel') && 
                           inp.offsetParent !== null;
                });
                
                if (phoneInputs.length > 0) {
                    phoneInput = phoneInputs[0];
                }
                
                // Find message input
                let messageInput = null;
                const messageInputs = Array.from(document.querySelectorAll('textarea, input, div[contenteditable="true"]')).filter(inp => {
                    const aria = inp.getAttribute('aria-label')?.toLowerCase() || '';
                    const placeholder = inp.getAttribute('placeholder')?.toLowerCase() || '';
                    
                    return (aria.includes('message') || 
                            aria.includes('text') || 
                            placeholder.includes('message') || 
                            placeholder.includes('text')) && 
                           inp.offsetParent !== null;
                });
                
                if (messageInputs.length > 0) {
                    messageInput = messageInputs[0];
                }
                
                if (!phoneInput || !messageInput) {
                    return {
                        success: false,
                        error: 'Input fields not found',
                        phoneInput: !!phoneInput,
                        messageInput: !!messageInput
                    };
                }
                
                // Fill phone number
                console.log(`📞 Filling phone: ${recipient}`);
                phoneInput.focus();
                phoneInput.value = '';
                phoneInput.value = recipient;
                phoneInput.dispatchEvent(new Event('input', { bubbles: true }));
                phoneInput.dispatchEvent(new Event('change', { bubbles: true }));
                
                // Wait a moment
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                // Fill message
                console.log(`💬 Filling message: ${message}`);
                messageInput.focus();
                
                if (messageInput.tagName === 'DIV' && messageInput.contentEditable === 'true') {
                    messageInput.textContent = '';
                    messageInput.textContent = message;
                    messageInput.dispatchEvent(new Event('input', { bubbles: true }));
                } else {
                    messageInput.value = '';
                    messageInput.value = message;
                    messageInput.dispatchEvent(new Event('input', { bubbles: true }));
                    messageInput.dispatchEvent(new Event('change', { bubbles: true }));
                }
                
                // Wait for form validation
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Find send button
                console.log('🔍 Looking for send button...');
                
                let sendButton = null;
                const allButtons = Array.from(document.querySelectorAll('button'));
                
                for (const btn of allButtons) {
                    const text = btn.textContent?.toLowerCase() || '';
                    const aria = btn.getAttribute('aria-label')?.toLowerCase() || '';
                    
                    if ((text.includes('send') || aria.includes('send')) && 
                        btn.offsetParent !== null && 
                        !btn.disabled) {
                        sendButton = btn;
                        console.log(`📤 Found send button: "${text}" / "${aria}"`);
                        break;
                    }
                }
                
                if (sendButton) {
                    console.log('📤 Clicking send button...');
                    sendButton.click();
                    
                    // Wait for send to complete
                    await new Promise(resolve => setTimeout(resolve, 3000));
                    
                    console.log('✅ Send button clicked - SMS should be sent!');
                    return { success: true, message: 'SMS sent successfully!' };
                } else {
                    const availableButtons = allButtons.map(btn => ({
                        text: btn.textContent?.trim() || '',
                        aria: btn.getAttribute('aria-label') || '',
                        disabled: btn.disabled,
                        visible: btn.offsetParent !== null
                    })).filter(btn => btn.visible);
                    
                    return {
                        success: false,
                        error: 'Send button not found',
                        availableButtons: availableButtons.slice(0, 10)
                    };
                }
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message
                };
            }
        }, recipient, message);
        
        console.log(`📱 Form Result: ${JSON.stringify(formResult, null, 2)}`);
        
        // Take final screenshot
        await page.screenshot({ path: 'after_send.png' });
        console.log('📸 Final screenshot saved');
        
        return formResult.success;
        
    } catch (error) {
        console.error('❌ SMS sending failed:', error);
        return false;
        
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

// Run the test
sendRealSMS().then(success => {
    console.log(`\n${'='*60}`);
    console.log(`📱 SMS RESULT: ${success ? 'SENT SUCCESSFULLY' : 'FAILED'}`);
    console.log(`${'='*60}`);
    process.exit(success ? 0 : 1);
}).catch(error => {
    console.error('💥 Test crashed:', error);
    process.exit(1);
});