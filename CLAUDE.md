# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Google Voice REST API implementation that provides HTTP endpoints for SMS operations. The project extracts Google Voice protocol logic from mautrix-gvoice and implements it as a standalone FastAPI service with file-based storage.

**Key Challenge**: Google Voice has strong anti-automation protections that require browser-based WAA (Web Application Authenticator) signatures to send SMS messages successfully.

## Development Commands

### Running the Application
```bash
# Development server with auto-reload
python run.py

# Or manually with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Testing and Development
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Code formatting and linting (when available)
black app/
flake8 app/
mypy app/

# Testing various components
python debug_sms.py                    # Test SMS sending
python test_fresh_cookies.py           # Test with fresh cookies
python persistent_session_client.py    # Test persistent sessions
python real_waa_client.py             # Test real WAA signatures
```

### Docker Usage
```bash
# Build and run with docker-compose
docker-compose up --build

# Or manually
docker build -t gvoice-api .
docker run -p 8000:8000 gvoice-api
```

## Architecture Overview

### Core Components

**FastAPI Application (`app/main.py`)**
- Main application entry point with CORS, routers, and lifecycle management
- Includes startup/shutdown events for session cleanup and webhook service management

**File-based Storage (`app/core/storage.py`)**
- Uses `~/.config/gvoice/` for all persistent data
- Stores sessions, users, Google Voice cookies, webhooks, and delivery logs
- No database required - all data stored as JSON files

**Google Voice Client (`app/services/gvoice_client.py`)**
- Implements Google Voice HTTP protocol based on mautrix-gvoice reverse engineering
- Handles SAPISID authentication, header generation, and cookie management
- Contains logic for different Google domains (API, contacts, WAA, upload)

**WAA (Web Application Authenticator) System**
- `waa_client.py` - Basic WAA implementation with placeholder signatures
- `real_waa_client.py` - Advanced implementation using Playwright to execute Google's JavaScript
- `persistent_session_client.py` - Session management with automatic cookie updates

### API Structure

**Authentication (`app/api/auth.py`)**
- Cookie-based authentication (primary method)
- Email/password registration (limited functionality)
- Session management with file-based tokens

**SMS Operations (`app/api/sms.py`)**
- Send SMS messages (requires working WAA signatures)
- List conversation threads
- Get message history
- Thread management (delete, mark as read)
- Account information retrieval

**Real-time Features (`app/api/websocket.py`)**
- WebSocket endpoint for live message notifications
- Connection management and authentication

**Webhooks (`app/api/webhooks.py`)**
- HTTP webhook configuration for message events
- HMAC signature verification
- Delivery retry logic with exponential backoff

### Constants and Configuration

**Google Voice Protocol (`app/core/constants.py`)**
- API keys, domains, and endpoints extracted from mautrix-gvoice
- User agents and client details that match Chrome browser
- Content types and header configurations for different Google services

## Key Technical Details

### Authentication Flow
1. User provides Google cookies from browser session
2. System validates cookies against Google Voice account endpoint
3. Creates internal session token for API access
4. Automatically updates cookies from API responses to maintain session

### WAA Challenge
Google Voice requires Web Application Authenticator signatures for SMS sending:
- Basic approach uses placeholder signatures ("!") - gets blocked
- Advanced approach uses Playwright to execute Google's actual JavaScript in browser context
- mautrix-gvoice succeeds because it runs in full Electron browser environment

### File Storage Structure
```
~/.config/gvoice/
├── sessions/          # User session tokens
├── users/            # User account data  
├── gv_sessions/      # Google Voice cookies
├── webhooks/         # Webhook configurations
└── webhook_deliveries/ # Webhook delivery logs
```

## Current State and Limitations

### Working Components
- Complete FastAPI REST API structure
- Authentication with Google Voice (200 responses)
- File-based session and data persistence
- Real-time WebSocket framework
- Webhook delivery system
- Automatic cookie management

### Primary Challenge
**SMS sending blocked by Google's anti-automation** (`FAILED_PRECONDITION` error):
- Authentication works fine (200 from account endpoints)
- SMS endpoint specifically detects automated behavior
- Requires real browser environment to execute Google's WAA JavaScript

### Test Files Purpose
- `debug_*.py` - Various debugging and testing scripts
- `test_*.py` - Feature testing with different approaches
- `real_waa_client.py` - Playwright-based browser automation attempt
- `persistent_session_client.py` - Session management like mautrix-gvoice

## Development Notes

### When Working on WAA/Browser Issues
The core challenge is bypassing Google's anti-automation. Key files to examine:
- `real_waa_client.py` - Most advanced attempt at browser-based signatures
- `persistent_session_client.py` - Automatic cookie management
- `/home/keith/src/gvoice/gvoice/pkg/connector/electron.mjs` - Reference mautrix-gvoice Electron implementation

### API Testing
Use fresh browser cookies from Google Voice session:
1. Login to https://voice.google.com
2. Extract cookies via dev tools
3. Test with `debug_sms.py` or API endpoints
4. Monitor for `FAILED_PRECONDITION` vs authentication errors

### Adding New Endpoints
Follow the pattern in existing API modules:
1. Add endpoint constants to `app/core/constants.py`
2. Implement client method in `app/services/gvoice_client.py`
3. Create API route in appropriate `app/api/*.py` file
4. Add request/response schemas in `app/schemas/`

The codebase is well-structured and ready for development, with the primary challenge being Google's SMS anti-automation protections rather than architectural issues.