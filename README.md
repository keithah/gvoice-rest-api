# Google Voice REST API

A Python REST API for Google Voice SMS operations, extracted from the mautrix-gvoice implementation without dependencies. Uses file-based session storage in `~/.config/gvoice/`.

## Features

- **Direct Google Voice Integration**: Based on mautrix-gvoice protocol implementation
- **File-based Storage**: Sessions stored in `~/.config/gvoice/` (no database required)
- **Cookie-based Authentication**: Login using browser cookies (no password storage needed)
- **SMS Operations**: Send SMS, list conversations, get message history
- **Thread Management**: Delete conversations, mark as read
- **Session Management**: Automatic cleanup of expired sessions

## Setup

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run the Server**:
```bash
python run.py
```

The API will be available at `http://localhost:8000`

## Authentication Methods

### Method 1: Cookie-based Login (Recommended)

1. Login to https://voice.google.com in your browser
2. Open Developer Tools (F12)
3. Go to Application/Storage → Cookies → https://voice.google.com
4. Copy the following cookie values:
   - `SAPISID`
   - `HSID`
   - `SSID`
   - `APISID`
   - `SID`

5. Login via API:
```bash
curl -X POST "http://localhost:8000/api/auth/login-with-cookies" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@gmail.com",
    "cookies": {
      "SAPISID": "your_sapisid_value",
      "HSID": "your_hsid_value",
      "SSID": "your_ssid_value",
      "APISID": "your_apisid_value",
      "SID": "your_sid_value"
    }
  }'
```

### Method 2: Email/Password (Limited)

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@gmail.com",
    "password": "your-password",
    "name": "Your Name"
  }'
```

**Note**: Direct password login to Google is not implemented due to 2FA/security challenges. Use cookie method instead.

## API Usage

### Send SMS

```bash
curl -X POST "http://localhost:8000/api/sms/send" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": ["+1234567890"],
    "message": "Hello from Google Voice API!"
  }'
```

### List Conversations

```bash
curl -X GET "http://localhost:8000/api/sms/threads?folder=inbox" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"
```

### Get Thread Messages

```bash
curl -X GET "http://localhost:8000/api/sms/threads/THREAD_ID" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"
```

### Get Account Info

```bash
curl -X GET "http://localhost:8000/api/sms/account" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"
```

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## File Storage Structure

```
~/.config/gvoice/
├── sessions/          # User sessions (JWT-like tokens)
│   ├── uuid1.json
│   └── uuid2.json
├── users/            # User account data
│   ├── email_at_domain_com.json
│   └── ...
└── gv_sessions/      # Google Voice cookies
    ├── user_id1.json
    └── user_id2.json
```

## Key Endpoints

### Authentication
- `POST /api/auth/register` - Register with email/password
- `POST /api/auth/login` - Login with email/password  
- `POST /api/auth/login-with-cookies` - Login with Google cookies
- `GET /api/auth/who-am-i` - Get current user info
- `POST /api/auth/logout` - Logout and delete session
- `POST /api/auth/logout-gvoice` - Remove Google Voice cookies

### SMS Operations
- `POST /api/sms/send` - Send SMS message(s)
- `GET /api/sms/threads` - List conversation threads
- `GET /api/sms/threads/{thread_id}` - Get messages in thread
- `DELETE /api/sms/threads/{thread_id}` - Delete thread
- `POST /api/sms/mark-all-read` - Mark all messages as read
- `GET /api/sms/account` - Get Google Voice account info

## Security Notes

- Sessions are stored as files in `~/.config/gvoice/`
- Google cookies are stored securely and only used for API calls
- Sessions auto-expire after 24 hours (configurable)
- No passwords are stored for cookie-based authentication

## Implementation Notes

This API extracts the Google Voice protocol implementation from mautrix-gvoice:
- Uses the same HTTP endpoints and headers
- Implements the same authentication flow
- Handles the same protobuf-like message format
- No dependency on the mautrix-gvoice binary

The Google Voice client (`app/services/gvoice_client.py`) replicates the mautrix-gvoice request patterns including:
- SAPISID hash generation for authorization
- Proper header configuration for different Google domains
- Transaction ID generation
- Cookie management

## Limitations

- Direct Google login not implemented (use cookie method)
- Protobuf parsing is simplified (uses JSON approximation)
- Real-time message receiving not implemented
- Voice calls not supported (SMS only)

## Development

Run in development mode:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```