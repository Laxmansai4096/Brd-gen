import os
from pydantic import BaseModel
from typing import Optional, Dict, Any

class AISettings(BaseModel):
    active_provider: str = "google"  # "google", "azure", "aws"
    
    # Google AI Studio / Vertex AI
    google_api_key: Optional[str] = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    google_model: str = "gemini-2.5-flash"
    
    # Microsoft Azure OpenAI
    azure_endpoint: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_api_key: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_deployment: str = "gpt-4o"
    azure_api_version: str = "2024-06-01"
    
    # Amazon Web Services (AWS Bedrock)
    aws_region: str = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    aws_model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"

# In-memory global settings
global_settings = AISettings()

def get_settings() -> AISettings:
    return global_settings

def update_settings(new_settings: AISettings):
    global global_settings
    global_settings = new_settings
