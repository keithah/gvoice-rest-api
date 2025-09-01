from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
from datetime import datetime

from app.api import auth, sms, websocket, webhooks
from app.core.storage import storage
from app.services.realtime import realtime_manager
from app.services.webhook_service import webhook_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Google Voice REST API",
    description="REST API for Google Voice SMS operations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(sms.router, prefix="/api/sms", tags=["SMS Operations"])
app.include_router(websocket.router, prefix="/api/ws", tags=["WebSocket"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Google Voice REST API...")
    # Clean up expired sessions
    await storage.cleanup_expired_sessions()
    # Start webhook delivery service
    await webhook_service.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Google Voice REST API...")
    # Stop all realtime clients
    await realtime_manager.stop_all()
    # Stop webhook service
    await webhook_service.stop()

@app.get("/")
async def root():
    return {
        "message": "Google Voice REST API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": str(exc)}
    )