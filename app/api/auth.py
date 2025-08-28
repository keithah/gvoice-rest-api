from fastapi import APIRouter, HTTPException, Depends
from passlib.context import CryptContext
import uuid

from app.schemas.auth import (
    LoginInput, LoginWithCookiesInput, RegisterInput, 
    LoginResponse, UserResponse
)
from app.core.storage import storage
from app.services.auth_service import GoogleAuthService
from app.core.auth import get_current_user

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register", response_model=LoginResponse)
async def register(input_data: RegisterInput):
    """Register a new user account"""
    # Check if user already exists
    if await storage.user_exists(input_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = pwd_context.hash(input_data.password)
    
    user_data = {
        "id": user_id,
        "email": input_data.email,
        "name": input_data.name,
        "password": hashed_password,
        "created_at": datetime.utcnow().isoformat()
    }
    
    await storage.save_user(input_data.email, user_data)
    
    # Create session
    session_id = await storage.create_session({
        "id": user_id,
        "email": input_data.email,
        "name": input_data.name
    })
    
    return LoginResponse(
        token=session_id,
        user={
            "id": user_id,
            "email": input_data.email,
            "name": input_data.name
        }
    )

@router.post("/login", response_model=LoginResponse)
async def login(input_data: LoginInput):
    """Login with email and password"""
    # Get user from storage
    user_data = await storage.get_user(input_data.email)
    
    if not user_data or not pwd_context.verify(input_data.password, user_data["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create session
    session_id = await storage.create_session({
        "id": user_data["id"],
        "email": user_data["email"],
        "name": user_data.get("name")
    })
    
    return LoginResponse(
        token=session_id,
        user={
            "id": user_data["id"],
            "email": user_data["email"],
            "name": user_data.get("name")
        }
    )

@router.post("/login-with-cookies", response_model=LoginResponse)
async def login_with_cookies(input_data: LoginWithCookiesInput):
    """Login with Google cookies (for users who manually extract cookies)"""
    # Validate cookies
    auth_service = GoogleAuthService()
    if not auth_service.validate_cookies(input_data.cookies):
        raise HTTPException(
            status_code=400, 
            detail="Invalid cookies. Required: SAPISID, HSID, SSID, APISID, SID"
        )
    
    # Get or create user
    user_data = await storage.get_user(input_data.email)
    if not user_data:
        # Auto-register user with cookie-based login
        user_id = str(uuid.uuid4())
        user_data = {
            "id": user_id,
            "email": input_data.email,
            "name": None,
            "password": None,  # No password for cookie-based users
            "auth_method": "cookies",
            "created_at": datetime.utcnow().isoformat()
        }
        await storage.save_user(input_data.email, user_data)
    
    # Save Google Voice session
    await storage.save_gv_session(user_data["id"], input_data.cookies)
    
    # Create session
    session_id = await storage.create_session({
        "id": user_data["id"],
        "email": user_data["email"],
        "name": user_data.get("name")
    })
    
    return LoginResponse(
        token=session_id,
        user={
            "id": user_data["id"],
            "email": user_data["email"],
            "name": user_data.get("name"),
            "has_gv_session": True
        },
        message="Successfully logged in with Google cookies"
    )

@router.get("/who-am-i", response_model=UserResponse)
async def who_am_i(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user.get("name"),
        has_gv_session=current_user.get("has_gv_session", False)
    )

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout and delete session"""
    await storage.delete_session(current_user["session_id"])
    return {"message": "Logged out successfully"}

@router.post("/logout-gvoice")
async def logout_gvoice(current_user: dict = Depends(get_current_user)):
    """Logout from Google Voice (delete stored cookies)"""
    await storage.delete_gv_session(current_user["id"])
    return {"message": "Google Voice session deleted"}

# Add missing import
from datetime import datetime