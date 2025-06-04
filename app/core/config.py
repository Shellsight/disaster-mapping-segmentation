# app/core/config.py
import os
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path
import torch

load_dotenv(override=True)

class Settings(BaseSettings):
    # API Settings
    APP_NAME: str = "AI Disaster Mapping API"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    
    # Model Settings
    MODEL_PATH: Path = Path("app/models/sam_vit_h_4b8939.pth")
    MODEL_TYPE: str = "vit_h"
    DEVICE: str = "cuda" if torch.cuda.is_available() else "cpu"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()