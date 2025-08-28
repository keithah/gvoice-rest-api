from fastapi import HTTPException, Depends, Header
from typing import Optional, Dict
from app.core.storage import storage

async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict:
    """Validate session token and return user data"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    session_id = parts[1]
    session_data = await storage.get_session(session_id)
    
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    # Check if user has Google Voice session
    gv_cookies = await storage.get_gv_session(session_data["id"])
    session_data["has_gv_session"] = gv_cookies is not None
    session_data["session_id"] = session_id
    
    return session_data