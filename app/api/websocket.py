"""WebSocket endpoint for real-time message delivery"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Dict, List
import json
import asyncio
import logging

from app.core.auth import get_current_user
from app.core.storage import storage
from app.services.realtime import realtime_manager

router = APIRouter()
logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a WebSocket for a user"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected for user: {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a WebSocket"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            # Remove user if no more connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        logger.info(f"WebSocket disconnected for user: {user_id}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to all connections for a user"""
        if user_id in self.active_connections:
            dead_connections = []
            
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket: {e}")
                    dead_connections.append(connection)
            
            # Remove dead connections
            for dead_conn in dead_connections:
                self.disconnect(dead_conn, user_id)
    
    def get_user_count(self) -> int:
        """Get number of connected users"""
        return len(self.active_connections)
    
    def get_connection_count(self) -> int:
        """Get total number of connections"""
        return sum(len(conns) for conns in self.active_connections.values())

# Global connection manager
manager = ConnectionManager()

async def authenticate_websocket(token: str) -> dict:
    """Authenticate WebSocket connection using session token"""
    if not token:
        raise ValueError("No token provided")
    
    session_data = await storage.get_session(token)
    if not session_data:
        raise ValueError("Invalid or expired token")
    
    return session_data

@router.websocket("/realtime")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="Session token for authentication")
):
    """WebSocket endpoint for real-time message receiving"""
    
    try:
        # Authenticate user
        user_data = await authenticate_websocket(token)
        user_id = user_data["id"]
        
        # Connect WebSocket
        await manager.connect(websocket, user_id)
        
        # Get Google Voice cookies
        gv_cookies = await storage.get_gv_session(user_id)
        if not gv_cookies:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "No Google Voice session found. Please login with cookies first."
            }))
            return
        
        # Define event handlers for realtime messages
        async def on_message(message_data):
            """Handle incoming real-time message"""
            await manager.send_to_user(user_id, {
                "type": "message",
                "data": message_data,
                "timestamp": asyncio.get_event_loop().time()
            })
        
        async def on_connected():
            """Handle realtime connection established"""
            await manager.send_to_user(user_id, {
                "type": "connected",
                "message": "Real-time connection established"
            })
        
        # Start realtime client
        event_handlers = {
            "message": on_message,
            "connected": on_connected
        }
        
        await realtime_manager.start_client(user_id, gv_cookies, event_handlers)
        
        # Send connection success
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": f"Real-time messaging started for {user_data['email']}"
        }))
        
        # Keep connection alive and handle client messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "status":
                    await websocket.send_text(json.dumps({
                        "type": "status",
                        "connected_users": manager.get_user_count(),
                        "total_connections": manager.get_connection_count()
                    }))
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON received"
                }))
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
    
    except ValueError as e:
        # Authentication failed
        try:
            await websocket.close(code=1008, reason=str(e))
        except:
            pass
        return
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Internal server error"
            }))
        except:
            pass
    
    finally:
        # Cleanup
        if 'user_id' in locals():
            manager.disconnect(websocket, user_id)
            # Note: Keep realtime client running for other connections
            # Only stop if this was the last connection for this user
            if user_id not in manager.active_connections:
                await realtime_manager.stop_client(user_id)

@router.get("/realtime/status")
async def get_realtime_status():
    """Get real-time connection status"""
    return {
        "connected_users": manager.get_user_count(),
        "total_connections": manager.get_connection_count(),
        "active_users": list(manager.active_connections.keys())
    }