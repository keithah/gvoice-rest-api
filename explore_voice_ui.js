const puppeteer = require('./nodejs-waa/node_modules/puppeteer');
const fs = require('fs');

async function exploreVoiceUI() {
    console.log('🔍 EXPLORE GOOGLE VOICE UI');
    console.log('='*50);
    
    const cookies = JSON.parse(fs.readFileSync('fresh_cookies.json', 'utf8'));
    
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
        
        // Navigate to messages
        await page.goto('https://voice.google.com/u/0/messages', { 
            waitUntil: 'networkidle2',
            timeout: 30000 
        });
        
        console.log(`📄 Page: ${await page.title()}`);
        
        // First, let's see if there are any existing conversations we can click
        console.log('\n🔍 Step 1: Exploring conversation list...');
        
        const conversations = await page.evaluate(() => {
            const convElements = Array.from(document.querySelectorAll('[role="listitem"], .conversation, .thread')).map(el => ({
                text: el.textContent?.trim().substring(0, 100) || '',
                clickable: el.onclick || el.getAttribute('role') === 'button' || el.style.cursor === 'pointer'
            })).filter(conv => conv.text);
            
            return convElements.slice(0, 5);
        });
        
        console.log('📋 Conversations found:');
        conversations.forEach((conv, i) => {
            console.log(`  ${i+1}. "${conv.text}" (clickable: ${conv.clickable})`);
        });
        
        // Try clicking on an existing conversation first
        if (conversations.length > 0) {
            console.log('\n🔍 Step 2: Clicking first conversation...');
            
            await page.evaluate(() => {
                const convElements = Array.from(document.querySelectorAll('[role="listitem"], .conversation, .thread'));
                if (convElements.length > 0) {
                    console.log('📱 Clicking first conversation');
                    convElements[0].click();
                    return true;
                }
                return false;
            });
            
            await new Promise(resolve => setTimeout(resolve, 3000));
            await page.screenshot({ path: 'after_conversation_click.png' });
            
            // Now look for message input in the conversation view
            const messageInterface = await page.evaluate(() => {
                const inputs = Array.from(document.querySelectorAll('input, textarea, div[contenteditable="true"]')).map(inp => ({
                    tag: inp.tagName,
                    type: inp.type || '',
                    aria: inp.getAttribute('aria-label') || '',
                    placeholder: inp.getAttribute('placeholder') || '',
                    visible: inp.offsetParent !== null,
                    contentEditable: inp.contentEditable === 'true'
                })).filter(inp => inp.visible);
                
                const buttons = Array.from(document.querySelectorAll('button')).map(btn => ({
                    text: btn.textContent?.trim() || '',
                    aria: btn.getAttribute('aria-label') || '',
                    title: btn.getAttribute('title') || '',
                    visible: btn.offsetParent !== null,
                    enabled: !btn.disabled
                })).filter(btn => btn.visible && btn.enabled && (btn.text || btn.aria || btn.title));
                
                return { inputs, buttons };
            });
            
            console.log('\n📝 Message interface found:');
            console.log(`Inputs: ${messageInterface.inputs.length}`);
            messageInterface.inputs.forEach((inp, i) => {
                console.log(`  ${i+1}. ${inp.tag}[${inp.type}] - "${inp.aria}" - "${inp.placeholder}" - editable: ${inp.contentEditable}`);
            });
            
            console.log(`Buttons: ${messageInterface.buttons.length}`);
            messageInterface.buttons.forEach((btn, i) => {
                console.log(`  ${i+1}. "${btn.text}" | aria: "${btn.aria}" | title: "${btn.title}"`);
            });
            
            // Try to send SMS in existing conversation
            if (messageInterface.inputs.length > 0) {
                console.log('\n📱 Step 3: Trying to send SMS in existing conversation...');
                
                const smsResult = await page.evaluate(async (recipient, message) => {
                    try {
                        // Find message input (should be visible in conversation)
                        const messageInputs = Array.from(document.querySelectorAll('textarea, input, div[contenteditable="true"]')).filter(inp => {
                            const aria = inp.getAttribute('aria-label')?.toLowerCase() || '';
                            const placeholder = inp.getAttribute('placeholder')?.toLowerCase() || '';
                            
                            return (aria.includes('message') || 
                                    aria.includes('text') || 
                                    placeholder.includes('message') || 
                                    placeholder.includes('text') ||
                                    inp.contentEditable === 'true') && 
                                   inp.offsetParent !== null;
                        });
                        
                        if (messageInputs.length === 0) {
                            return { success: false, error: 'No message input found in conversation' };
                        }
                        
                        const messageInput = messageInputs[0];
                        console.log(`💬 Using message input: ${messageInput.tagName}`);
                        
                        // Fill message
                        messageInput.focus();
                        
                        if (messageInput.contentEditable === 'true') {
                            messageInput.textContent = message;
                            messageInput.dispatchEvent(new Event('input', { bubbles: true }));
                        } else {
                            messageInput.value = message;
                            messageInput.dispatchEvent(new Event('input', { bubbles: true }));
                            messageInput.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                        
                        console.log(`💬 Entered message: "${message}"`);
                        
                        // Wait for typing
                        await new Promise(resolve => setTimeout(resolve, 1000));
                        
                        // Look for send button
                        const sendButtons = Array.from(document.querySelectorAll('button')).filter(btn => {
                            const text = btn.textContent?.toLowerCase() || '';
                            const aria = btn.getAttribute('aria-label')?.toLowerCase() || '';
                            
                            return (text.includes('send') || aria.includes('send')) && 
                                   btn.offsetParent !== null && 
                                   !btn.disabled;
                        });
                        
                        if (sendButtons.length === 0) {
                            return { success: false, error: 'No send button found' };
                        }
                        
                        const sendButton = sendButtons[0];
                        console.log(`📤 Clicking send button: "${sendButton.textContent?.trim()}"`);
                        sendButton.click();
                        
                        // Wait for send
                        await new Promise(resolve => setTimeout(resolve, 3000));
                        
                        console.log('✅ SMS send attempted!');
                        return { success: true, message: 'SMS sent in existing conversation!' };
                        
                    } catch (error) {
                        return { success: false, error: error.message };
                    }
                }, '13602415033', `Conversation SMS Test ${new Date().toLocaleTimeString()}`);
                
                console.log(`📱 SMS Result: ${JSON.stringify(smsResult, null, 2)}`);
                
                // Take final screenshot
                await page.screenshot({ path: 'after_sms_send.png' });
                
                return smsResult.success;
            }
        }
        
        console.log('❌ No suitable interface found for SMS');
        return false;
        
    } catch (error) {
        console.error('❌ Exploration failed:', error);
        return false;
        
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

// Run exploration
exploreVoiceUI().then(success => {
    console.log(`\n${'='*60}`);
    console.log(`🔍 EXPLORATION: ${success ? 'SMS SENT' : 'FAILED'}`);
    console.log(`${'='*60}`);
    process.exit(success ? 0 : 1);
}).catch(error => {
    console.error('💥 Exploration crashed:', error);
    process.exit(1);
});