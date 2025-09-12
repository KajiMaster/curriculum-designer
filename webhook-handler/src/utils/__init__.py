"""Utility functions and classes."""

import logging
from typing import Optional, Dict
from functools import lru_cache
import boto3
from botocore.exceptions import ClientError

from ..config import get_config

logger = logging.getLogger(__name__)
config = get_config()


class SecretsManager:
    """Thread-safe secrets manager with caching."""
    
    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._ssm_client: Optional[boto3.client] = None
    
    @property
    def ssm_client(self) -> boto3.client:
        """Lazy-loaded SSM client."""
        if self._ssm_client is None:
            self._ssm_client = boto3.client('ssm', region_name=config.AWS_REGION)
        return self._ssm_client
    
    def get_secret(self, param_env: str, fallback_env: str = None) -> str:
        """Get secret from Parameter Store or environment variable with caching."""
        # Check cache first
        cache_key = f"{param_env}:{fallback_env}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        value = ""
        
        # Try Parameter Store if in Lambda
        if config.is_lambda_environment():
            param_name = getattr(config, param_env, "")
            if param_name:
                try:
                    response = self.ssm_client.get_parameter(
                        Name=param_name, 
                        WithDecryption=True
                    )
                    value = response['Parameter']['Value']
                    logger.debug(f"Retrieved parameter {param_name} from SSM")
                except ClientError as e:
                    logger.error(f"Error getting parameter {param_name}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error getting parameter {param_name}: {e}")
        
        # Fall back to environment variable
        if not value and fallback_env:
            import os
            value = os.getenv(fallback_env, "")
            if value:
                logger.debug(f"Using environment variable {fallback_env}")
        
        # Cache the result (even if empty to avoid repeated failures)
        self._cache[cache_key] = value
        
        if not value:
            logger.warning(f"No value found for {param_env}/{fallback_env}")
        
        return value
    
    def clear_cache(self) -> None:
        """Clear the secrets cache."""
        self._cache.clear()
        logger.debug("Secrets cache cleared")


# Singleton instance
@lru_cache(maxsize=1)
def get_secrets_manager() -> SecretsManager:
    """Get singleton secrets manager instance."""
    return SecretsManager()


# Convenience functions
def get_trello_api_key() -> str:
    """Get Trello API key."""
    return get_secrets_manager().get_secret("TRELLO_API_KEY_PARAM", "TRELLO_API_KEY")


def get_trello_token() -> str:
    """Get Trello token."""
    return get_secrets_manager().get_secret("TRELLO_TOKEN_PARAM", "TRELLO_TOKEN")


def get_openai_api_key() -> str:
    """Get OpenAI API key."""
    return get_secrets_manager().get_secret("OPENAI_API_KEY_PARAM", "OPENAI_API_KEY")


def get_webhook_secret() -> str:
    """Get webhook secret."""
    return get_secrets_manager().get_secret("TRELLO_WEBHOOK_SECRET_PARAM", "TRELLO_WEBHOOK_SECRET")


class ErrorBoundary:
    """Context manager for error handling."""
    
    def __init__(self, context: str, logger: logging.Logger = None):
        self.context = context
        self.logger = logger or logging.getLogger(__name__)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(
                f"Error in {self.context}: {exc_val}", 
                exc_info=True
            )
        return False  # Don't suppress the exception