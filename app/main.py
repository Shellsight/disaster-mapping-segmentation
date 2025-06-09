# app/main.py
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.core.config import settings
from app.core.logger import logger
from app.api import segment


def create_directories():
    """Create necessary directories if they don't exist."""
    directories = ["app/static", "app/templates"]
    
    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created directory: {directory}")
            except OSError as e:
                logger.error(f"Failed to create directory {directory}: {e}")
                raise


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    logger.info("Starting Disaster Mapping Application")
    
    # Ensure required directories exist
    create_directories()
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
    )
    
    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Consider restricting this in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware configured")
    
    # Mount static files
    try:
        app.mount("/static", StaticFiles(directory="app/static"), name="static")
        logger.info("Static files mounted successfully")
    except Exception as e:
        logger.error(f"Failed to mount static files: {e}")
        raise
    
    # Initialize templates
    templates = Jinja2Templates(directory="app/templates")
    logger.info("Templates initialized")
    
    # Include API routers
    app.include_router(segment.router)
    logger.info("API routers configured")
    
    # Route handlers
    @app.get("/")
    def home(request: Request):
        """Home page endpoint."""
        logger.debug("Home page accessed")
        return templates.TemplateResponse("index.html", {"request": request})
    
    @app.get("/health")
    def health_check():
        """Health check endpoint."""
        logger.debug("Health check endpoint accessed")
        return {
            "status": "ok",
            "message": "AI Disaster Mapping API is running 🚀"
        }
    
    logger.success("AI Disaster Mapping application created successfully")
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )