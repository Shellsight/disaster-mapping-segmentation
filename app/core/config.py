# app/core/config.py
import os
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv

load_dotenv(override=True)

class Settings(BaseSettings):
    APP_NAME: str = "AI Disaster Mapping"
    API_PREFIX: str = "/api"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()