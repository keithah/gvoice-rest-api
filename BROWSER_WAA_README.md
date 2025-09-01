# Browser-Based WAA Implementation

This implementation uses Playwright to execute Google's actual JavaScript for generating authentic WAA (Web Application Authenticator) signatures, similar to how mautrix-gvoice uses Electron.

## Overview

Google Voice has strong anti-automation protections that require real WAA signatures to send SMS messages. This browser-based approach:

1. **Uses Playwright** instead of Electron (like mautrix-gvoice)
2. **Executes Google's actual JavaScript** for authentic signatures
3. **Maintains browser context** for session persistence
4. **Extracts updated cookies** automatically

## Key Files

- `browser_waa_client.py` - Complete browser-based WAA implementation
- `app/services/browser_waa_service.py` - Service integration for FastAPI
- `extract_fresh_cookies.py` - Tool to get fresh Google cookies
- `test_browser_waa.py` - Test script for validation

## Usage

### 1. Extract Fresh Cookies

```bash
python3 extract_fresh_cookies.py
```

This opens a browser window where you:
1. Log in to Google Voice
2. Navigate to messages
3. Press Enter to extract cookies
4. Cookies are saved to `fresh_cookies.json`

### 2. Test Browser WAA

```bash
python3 test_browser_waa.py
```

Tests the browser WAA implementation with fresh cookies.

### 3. Use Enhanced API Endpoint

The FastAPI server now includes an enhanced endpoint:

```bash
POST /api/sms/send-enhanced
```

This endpoint uses browser-based WAA signatures instead of placeholder signatures.

## How It Works

### WAA Flow

1. **Request WAA Data**: Get interpreter URL and program from Google's WAA service
2. **Initialize Browser**: Start Playwright browser with proper user agent and cookies
3. **Load WAA Script**: Load Google's JavaScript interpreter in browser context
4. **Generate Signature**: Execute Google's actual WAA program with message payload
5. **Send SMS**: Use authentic signature in SMS request

### Key Differences from mautrix-gvoice

| Aspect | mautrix-gvoice | This Implementation |
|--------|----------------|-------------------|
| Browser | Electron | Playwright |
| Runtime | Node.js | Python |
| Persistence | Session files | Cookie extraction |
| Integration | Matrix bridge | REST API |

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Browser WAA    │    │   Google Voice  │
│   /send-enhanced│───▶│   Service        │───▶│   SMS Endpoint  │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Playwright     │
                       │   Browser        │
                       │   (Google's JS)  │
                       └──────────────────┘
```

## Installation

Add to your requirements.txt:
```
playwright==1.55.0
```

Install browser dependencies:
```bash
playwright install chromium
```

## Configuration

The browser WAA service automatically:
- Uses headless mode for server environments
- Configures proper Chrome user agent
- Sets secure cookie attributes
- Handles WAA data expiry (1 hour)

## Error Handling

Common issues and solutions:

### Authentication Errors (401)
- **Cause**: Expired cookies
- **Solution**: Run `extract_fresh_cookies.py` to get fresh cookies

### FAILED_PRECONDITION Errors
- **Cause**: Google's anti-automation detected
- **Solution**: Browser WAA should solve this by using authentic signatures

### Script Loading Failures
- **Cause**: Network issues or WAA service unavailable
- **Solution**: Automatic retry with fresh WAA data

## Testing

### Manual Testing
```bash
# Extract cookies first
python3 extract_fresh_cookies.py

# Test implementation
python3 test_browser_waa.py
```

### API Testing
```bash
# Start server
python run.py

# Test enhanced endpoint
curl -X POST "http://localhost:8000/api/sms/send-enhanced" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "recipients": ["1234567890"],
       "message": "Test message"
     }'
```

## Performance Considerations

- **Browser Startup**: ~2-3 seconds for initialization
- **WAA Generation**: ~1-2 seconds per signature
- **Memory Usage**: ~100MB for browser instance
- **Persistence**: WAA data cached for 1 hour

## Deployment

For production deployment:

1. **Install browser dependencies** in Docker/container
2. **Configure headless mode** (already enabled)
3. **Set up cookie refresh mechanism** for long-running instances
4. **Monitor browser memory usage** and restart if needed

## Comparison with Previous Attempts

### Basic WAA Client (`waa_client.py`)
- ❌ Uses placeholder signatures ("!")
- ❌ Gets blocked by Google's anti-automation

### Real WAA Client (`real_waa_client.py`)
- ✅ Attempts to execute Google's JavaScript
- ❌ Complex implementation with parsing issues

### Browser WAA Client (`browser_waa_client.py`)
- ✅ Uses Playwright for real browser environment
- ✅ Executes Google's actual JavaScript
- ✅ Handles cookie extraction and updates
- ✅ Integrated with FastAPI service

## Next Steps

1. **Monitor Success Rate**: Track how often browser WAA signatures work
2. **Optimize Performance**: Cache browser instances for faster requests
3. **Add Retry Logic**: Implement automatic retry on signature failures
4. **Cookie Refresh**: Automate cookie refresh for long-running services

This implementation provides the closest approximation to mautrix-gvoice's Electron approach while working within a Python/FastAPI environment.