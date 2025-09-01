const puppeteer = require('./nodejs-waa/node_modules/puppeteer');
const fs = require('fs');

async function debugUIDetailed() {
    console.log('🔍 DETAILED UI DEBUG');
    console.log('='*50);
    
    // Load cookies
    const cookies = JSON.parse(fs.readFileSync('fresh_cookies.json', 'utf8'));
    console.log(`🍪 Loaded ${Object.keys(cookies).length} cookies`);
    
    let browser;
    let page;
    
    try {
        // Start browser
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
        console.log('✅ Cookies set');
        
        // Navigate to Google Voice messages
        console.log('🌐 Loading Google Voice messages...');
        await page.goto('https://voice.google.com/u/0/messages', { 
            waitUntil: 'domcontentloaded',
            timeout: 30000 
        });
        
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        const title = await page.title();
        const url = page.url();
        console.log(`📄 Page: ${title} - ${url}`);
        
        // Take screenshot for debugging
        await page.screenshot({ path: 'debug_voice_page.png' });
        console.log('📸 Screenshot saved as debug_voice_page.png');
        
        // Detailed UI analysis
        const uiAnalysis = await page.evaluate(() => {
            // Get all interactive elements
            const buttons = Array.from(document.querySelectorAll('button')).map(btn => ({
                text: btn.textContent?.trim() || '',
                aria: btn.getAttribute('aria-label') || '',
                title: btn.getAttribute('title') || '',
                classes: btn.className || '',
                visible: btn.offsetParent !== null,
                enabled: !btn.disabled
            })).filter(btn => btn.visible && btn.enabled && (btn.text || btn.aria || btn.title));
            
            const inputs = Array.from(document.querySelectorAll('input, textarea')).map(inp => ({
                type: inp.type || inp.tagName,
                aria: inp.getAttribute('aria-label') || '',
                placeholder: inp.getAttribute('placeholder') || '',
                visible: inp.offsetParent !== null
            })).filter(inp => inp.visible);
            
            const links = Array.from(document.querySelectorAll('a')).map(link => ({
                text: link.textContent?.trim() || '',
                href: link.href || '',
                aria: link.getAttribute('aria-label') || ''
            })).filter(link => link.text && link.text.toLowerCase().includes('compose'));
            
            return {
                buttons: buttons.slice(0, 20),
                inputs: inputs.slice(0, 10),
                composeLinks: links,
                pageReady: document.readyState,
                hasAngular: typeof angular !== 'undefined',
                hasReact: document.querySelector('[data-reactroot]') !== null,
                bodyContent: document.body.innerHTML.substring(0, 500)
            };
        });
        
        console.log('\n🔍 UI ANALYSIS:');
        console.log(`📱 Buttons found: ${uiAnalysis.buttons.length}`);
        console.log(`📝 Inputs found: ${uiAnalysis.inputs.length}`);
        console.log(`🔗 Compose links: ${uiAnalysis.composeLinks.length}`);
        console.log(`📄 Page ready: ${uiAnalysis.pageReady}`);
        
        // Show available buttons
        console.log('\n🔲 Available buttons:');
        uiAnalysis.buttons.forEach((btn, i) => {
            console.log(`  ${i+1}. "${btn.text}" | aria: "${btn.aria}" | title: "${btn.title}"`);
        });
        
        // Show inputs
        console.log('\n📝 Available inputs:');
        uiAnalysis.inputs.forEach((inp, i) => {
            console.log(`  ${i+1}. ${inp.type} | aria: "${inp.aria}" | placeholder: "${inp.placeholder}"`);
        });
        
        // Look specifically for compose-related elements
        console.log('\n🔍 Looking for compose elements...');
        const composeElements = await page.evaluate(() => {
            const elements = [];
            
            // Search for compose-related text
            const allElements = document.querySelectorAll('*');
            for (const el of allElements) {
                const text = el.textContent?.toLowerCase() || '';
                const aria = el.getAttribute('aria-label')?.toLowerCase() || '';
                const title = el.getAttribute('title')?.toLowerCase() || '';
                
                if ((text.includes('compose') || text.includes('new message') || 
                     aria.includes('compose') || aria.includes('new message') ||
                     title.includes('compose') || title.includes('new message')) &&
                    el.offsetParent !== null) {
                    
                    elements.push({
                        tag: el.tagName,
                        text: el.textContent?.trim().substring(0, 50),
                        aria: el.getAttribute('aria-label') || '',
                        title: el.getAttribute('title') || '',
                        classes: el.className || '',
                        clickable: el.tagName === 'BUTTON' || el.tagName === 'A' || el.getAttribute('role') === 'button'
                    });
                }
            }
            
            return elements.slice(0, 10);
        });
        
        console.log('🎯 Compose-related elements:');
        composeElements.forEach((el, i) => {
            console.log(`  ${i+1}. ${el.tag}: "${el.text}" | aria: "${el.aria}" | clickable: ${el.clickable}`);
        });
        
        return true;
        
    } catch (error) {
        console.error('❌ Debug failed:', error);
        return false;
        
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

// Run debug
debugUIDetailed().then(success => {
    console.log(`\n${'='*60}`);
    console.log(`🎯 DEBUG RESULT: ${success ? 'COMPLETE' : 'FAILED'}`);
    console.log(`${'='*60}`);
    process.exit(success ? 0 : 1);
}).catch(error => {
    console.error('💥 Debug crashed:', error);
    process.exit(1);
});