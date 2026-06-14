# Entry point for the FastAPI application. Registers all routers and creates database tables on startup.

from fastapi import FastAPI, Request
from app.db.database import engine, Base
from fastapi.responses import JSONResponse
from app.models import User, Case, Message, Analysis
from app.api.routes import auth, cases, messages, analysis

app = FastAPI(
    title="SafeGuard AI",
    description="AI-Powered Detection and Analysis of Toxic Communication Patterns",
    version="0.1.0"
)

# Create all tables
Base.metadata.create_all(bind=engine)

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "An unexpected error occurred.",
            "detail": str(exc)
        }
    )


# Register routers
app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(messages.router)
app.include_router(analysis.router)

@app.get("/")
def root():
    return {
        "message": "SafeGuard AI API is running",
        "version": "0.1.0",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}