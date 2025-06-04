# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from app.core.config import settings
from app.core.logger import logger
from app.api import segment

def create_app() -> FastAPI:
    logger.info("Starting RAG System application")
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware configured")

    # Mount static files
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    
    # Initialize templates
    templates = Jinja2Templates(directory="app/templates")

    app.include_router(segment.router, prefix=settings.API_PREFIX)
    logger.info("API routers configured")

    @app.get("/")
    def home(request: Request):
        logger.debug("Home page accessed")
        return templates.TemplateResponse("index.html", {"request": request})

    @app.get("/health")
    def health_check():
        logger.debug("Health check endpoint accessed")
        return {"status": "ok",
                "message": "AI Disaster Mapping API is running 🚀"}

    logger.success("AI Disaster Mapping application created successfully")
    return app

app = create_app()