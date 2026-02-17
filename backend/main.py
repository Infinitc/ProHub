"""
ProHub FastAPI Backend v2.0 - Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn

from database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="ProHub API v2.0",
    description="Complete Productivity Hub with Notes, Calendar, Finance, Mail",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
try:
    from routers import auth, notes, calendar, finance, mail
    from caldav import caldav_server
    from routers import savings

    app.include_router(savings.router, prefix="/api/finance/savings", tags=["savings"])
    app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(notes.router, prefix="/api/notes", tags=["Notes"])
    app.include_router(calendar.router, prefix="/api/calendar", tags=["Calendar"])
    app.include_router(finance.router, prefix="/api/finance", tags=["Finance"])
    app.include_router(mail.router, prefix="/api/mail", tags=["Mail"])
    app.include_router(caldav_server.router, prefix="/caldav", tags=["CalDAV"])
except ImportError as e:
    print(f"Warning: Could not import routers: {e}")

# Mount static files
try:
    app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
except RuntimeError:
    pass

# Health check
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "ProHub API v2.0 is running",
        "version": "2.0.0",
        "features": [
            "Notes with sorting & archiving",
            "Calendar with Apple CalDAV sync",
            "Finance with categories, budgets & savings",
            "Mail client (IMAP/SMTP)"
        ]
    }


# Root
@app.get("/api")
async def root():
    return {
        "app": "ProHub API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
