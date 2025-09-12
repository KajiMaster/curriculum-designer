"""Configuration management for the webhook handler."""

import os
from typing import Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class Config:
    """Application configuration with environment variable support."""
    
    # AWS Configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_LAMBDA_FUNCTION_NAME: Optional[str] = os.getenv("AWS_LAMBDA_FUNCTION_NAME")
    
    # Trello Configuration
    TRELLO_API_KEY_PARAM: str = os.getenv("TRELLO_API_KEY_PARAM", "")
    TRELLO_TOKEN_PARAM: str = os.getenv("TRELLO_TOKEN_PARAM", "")
    TRELLO_WEBHOOK_SECRET_PARAM: str = os.getenv("TRELLO_WEBHOOK_SECRET_PARAM", "")
    TRELLO_BASE_URL: str = "https://api.trello.com/1"
    
    # OpenAI Configuration
    OPENAI_API_KEY_PARAM: str = os.getenv("OPENAI_API_KEY_PARAM", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "500"))
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    
    # Board IDs (moved from hardcoded values)
    LESSON_PLANS_BOARD_ID: str = os.getenv("LESSON_PLANS_BOARD_ID", "68a646dba9f202dbd275b7e8")
    DEFAULT_BOARD_ID: str = os.getenv("DEFAULT_BOARD_ID", "68a5fba51647caf78fc40866")
    
    # API Configuration
    MCP_API_URL: str = os.getenv("MCP_API_URL", "https://89npxchg5j.execute-api.us-east-1.amazonaws.com/dev")
    
    # HTTP Client Configuration
    HTTP_TIMEOUT: int = int(os.getenv("HTTP_TIMEOUT", "30"))
    CONNECTION_POOL_SIZE: int = int(os.getenv("CONNECTION_POOL_SIZE", "10"))
    
    # DynamoDB Configuration
    FRAMEWORKS_TABLE: str = os.getenv("FRAMEWORKS_TABLE", "curriculum-frameworks")
    
    # Lambda Configuration
    ACTIVITY_GENERATOR_FUNCTION: str = os.getenv("ACTIVITY_GENERATOR_FUNCTION", "curriculum-activity-generator")
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def is_lambda_environment(cls) -> bool:
        """Check if running in AWS Lambda environment."""
        return cls.AWS_LAMBDA_FUNCTION_NAME is not None
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if cls.is_lambda_environment():
            required = [
                ("TRELLO_API_KEY_PARAM", cls.TRELLO_API_KEY_PARAM),
                ("TRELLO_TOKEN_PARAM", cls.TRELLO_TOKEN_PARAM),
                ("OPENAI_API_KEY_PARAM", cls.OPENAI_API_KEY_PARAM),
            ]
            
            missing = [name for name, value in required if not value]
            if missing:
                raise ValueError(f"Missing required configuration: {', '.join(missing)}")


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Get singleton configuration instance."""
    config = Config()
    config.validate()
    return config