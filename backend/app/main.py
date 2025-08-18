from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.database import engine
from .models import Base
from .api import auth, availability, bookings, admin, teams, public
from .core.init_db import init_db

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize database with default admin user
init_db()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A full-fledged calendar booking application like Calendly",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(availability.router, prefix="/api/calendar", tags=["Calendar"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["Bookings"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(teams.router, prefix="/api/teams", tags=["Teams"])
app.include_router(public.router, prefix="/api/public", tags=["Public Booking"])


@app.get("/", tags=["Root"])
def read_root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Welcome to BCal API",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}
