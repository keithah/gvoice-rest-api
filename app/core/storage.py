"""File-based storage for sessions and user data"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Any
import asyncio
import aiofiles
from datetime import datetime, timedelta
import uuid

class FileStorage:
    """File-based storage using .config/gvoice directory"""
    
    def __init__(self):
        self.base_dir = Path.home() / ".config" / "gvoice"
        self.sessions_dir = self.base_dir / "sessions"
        self.users_dir = self.base_dir / "users"
        self.gv_sessions_dir = self.base_dir / "gv_sessions"
        
        # Create directories if they don't exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        for dir_path in [self.sessions_dir, self.users_dir, self.gv_sessions_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    async def save_json_file(self, filepath: Path, data: Dict) -> None:
        """Save data to JSON file asynchronously"""
        async with aiofiles.open(filepath, 'w') as f:
            await f.write(json.dumps(data, indent=2, default=str))
    
    async def load_json_file(self, filepath: Path) -> Optional[Dict]:
        """Load data from JSON file asynchronously"""
        if not filepath.exists():
            return None
        try:
            async with aiofiles.open(filepath, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except Exception:
            return None
    
    async def delete_file(self, filepath: Path) -> bool:
        """Delete a file"""
        try:
            if filepath.exists():
                filepath.unlink()
                return True
        except Exception:
            pass
        return False
    
    # User management
    async def save_user(self, email: str, user_data: Dict) -> None:
        """Save user data"""
        safe_email = email.replace("@", "_at_").replace(".", "_")
        filepath = self.users_dir / f"{safe_email}.json"
        await self.save_json_file(filepath, user_data)
    
    async def get_user(self, email: str) -> Optional[Dict]:
        """Get user data by email"""
        safe_email = email.replace("@", "_at_").replace(".", "_")
        filepath = self.users_dir / f"{safe_email}.json"
        return await self.load_json_file(filepath)
    
    async def user_exists(self, email: str) -> bool:
        """Check if user exists"""
        safe_email = email.replace("@", "_at_").replace(".", "_")
        filepath = self.users_dir / f"{safe_email}.json"
        return filepath.exists()
    
    # Session management
    async def create_session(self, user_data: Dict, expire_minutes: int = 1440) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        session_data = {
            **user_data,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(minutes=expire_minutes)).isoformat()
        }
        
        filepath = self.sessions_dir / f"{session_id}.json"
        await self.save_json_file(filepath, session_data)
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data by ID"""
        filepath = self.sessions_dir / f"{session_id}.json"
        session_data = await self.load_json_file(filepath)
        
        if session_data:
            # Check expiration
            expires_at = datetime.fromisoformat(session_data["expires_at"])
            if datetime.utcnow() > expires_at:
                # Session expired, delete it
                await self.delete_file(filepath)
                return None
        
        return session_data
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        filepath = self.sessions_dir / f"{session_id}.json"
        return await self.delete_file(filepath)
    
    async def update_session(self, session_id: str, data: Dict) -> bool:
        """Update session data"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.update(data)
        filepath = self.sessions_dir / f"{session_id}.json"
        await self.save_json_file(filepath, session)
        return True
    
    # Google Voice session management
    async def save_gv_session(self, user_id: str, cookies: Dict[str, str]) -> None:
        """Save Google Voice session cookies"""
        filepath = self.gv_sessions_dir / f"{user_id}.json"
        data = {
            "cookies": cookies,
            "saved_at": datetime.utcnow().isoformat()
        }
        await self.save_json_file(filepath, data)
    
    async def get_gv_session(self, user_id: str) -> Optional[Dict[str, str]]:
        """Get Google Voice session cookies"""
        filepath = self.gv_sessions_dir / f"{user_id}.json"
        data = await self.load_json_file(filepath)
        if data:
            return data.get("cookies")
        return None
    
    async def delete_gv_session(self, user_id: str) -> bool:
        """Delete Google Voice session"""
        filepath = self.gv_sessions_dir / f"{user_id}.json"
        return await self.delete_file(filepath)
    
    # Cleanup expired sessions
    async def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        for session_file in self.sessions_dir.glob("*.json"):
            session_data = await self.load_json_file(session_file)
            if session_data:
                expires_at = datetime.fromisoformat(session_data["expires_at"])
                if datetime.utcnow() > expires_at:
                    await self.delete_file(session_file)

# Singleton instance
storage = FileStorage()