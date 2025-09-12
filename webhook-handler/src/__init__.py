"""
Optimized Curriculum AI Webhook Handler

This module provides a refactored, secure, and performant webhook handler
for processing Trello events with AI assistance.
"""

import logging
import sys
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

# Import main components
from handlers import WebhookHandler
from config import get_config

# Initialize configuration on module import
config = get_config()
logger.info("Configuration loaded successfully")


async def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function.
    
    This is the main entry point for the Lambda function.
    It handles API Gateway events and processes webhook requests.
    """
    handler = WebhookHandler()
    response = await handler.handle(event, context)
    return response.to_dict()


# For backward compatibility
handler = lambda_handler

__version__ = "2.0.0"
__all__ = ["lambda_handler", "handler"]