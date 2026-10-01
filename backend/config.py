import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

# Load environment variables from .env and admin_data/.env
load_dotenv()
load_dotenv(os.path.join("admin_data", ".env"), override=True)

class AISettings(BaseModel):
    active_provider: str = os.getenv("ACTIVE_PROVIDER", "google")  # "google", "azure", "aws", "openai"
    
    # Google AI Studio / GCP Gemini / Vertex AI
    google_api_key: Optional[str] = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    google_endpoint: Optional[str] = os.getenv("GOOGLE_AI_ENDPOINT", "https://generativelanguage.googleapis.com")
    google_model: str = os.getenv("GOOGLE_MODEL", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    google_temperature: float = 0.2
    
    # Microsoft Azure OpenAI
    azure_endpoint: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_api_key: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", os.getenv("AZURE_DEPLOYMENT", "gpt-4o"))
    azure_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
    azure_temperature: float = 0.2
    
    # Amazon Web Services (AWS Bedrock)
    aws_region: str = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    aws_session_token: Optional[str] = os.getenv("AWS_SESSION_TOKEN", "")
    aws_model_id: str = os.getenv("AWS_MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0")
    
    # Custom / OpenAI-Compatible Endpoint
    openai_endpoint: Optional[str] = os.getenv("OPENAI_ENDPOINT", "https://api.openai.com/v1")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")

# In-memory global settings
global_settings = AISettings()

def get_settings() -> AISettings:
    return global_settings

def update_settings(new_settings: AISettings) -> AISettings:
    global global_settings
    global_settings = new_settings
    return global_settings
