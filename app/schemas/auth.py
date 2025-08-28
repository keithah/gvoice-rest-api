from pydantic import BaseModel, EmailStr
from typing import Optional, Dict

class LoginInput(BaseModel):
    email: EmailStr
    password: str

class LoginWithCookiesInput(BaseModel):
    email: EmailStr
    cookies: Dict[str, str]  # Google cookies from browser

class RegisterInput(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class LoginResponse(BaseModel):
    token: str
    user: Dict
    message: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    has_gv_session: bool = False