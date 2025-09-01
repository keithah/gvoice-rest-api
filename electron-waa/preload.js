const { contextBridge, ipcRenderer } = require('electron');

// Expose secure APIs to the renderer process
contextBridge.exposeInMainWorld('electronAPI', {
    // Communication with main process
    sendMessage: (channel, data) => ipcRenderer.invoke(channel, data),
    
    // WAA-related functions
    generateSignature: (data) => ipcRenderer.invoke('generate-waa', data),
    
    // Utility functions
    log: (message) => console.log(message)
});

// Set up console logging
window.addEventListener('DOMContentLoaded', () => {
    console.log('✅ Electron preload script loaded');
    console.log('🌐 Context: Google Voice in Electron');
});

// Intercept and log any WAA-related activity
const originalFetch = window.fetch;
window.fetch = function(...args) {
    const url = args[0];
    if (typeof url === 'string' && (url.includes('waa') || url.includes('sendsms'))) {
        console.log('🔍 Intercepted WAA/SMS request:', url);
    }
    return originalFetch.apply(this, args);
};