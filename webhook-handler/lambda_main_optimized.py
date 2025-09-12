"""
Optimized Lambda Main Entry Point

This file serves as the main entry point for the AWS Lambda function,
using the refactored modular architecture for better maintainability,
security, and performance.
"""

import os
import sys
import logging
from typing import Dict, Any

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Import the optimized handler
from src import lambda_handler as optimized_lambda_handler


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function.
    
    This is the main entry point that delegates to the optimized handler.
    Maintains backward compatibility while using the new architecture.
    
    Args:
        event: AWS Lambda event object
        context: AWS Lambda context object
        
    Returns:
        Dict containing statusCode, body, and optional headers
    """
    logger.info(f"Processing Lambda event: {event.get('httpMethod')} {event.get('path')}")
    
    try:
        # Use the optimized async handler
        import asyncio
        
        # Handle the event with the new architecture
        response = asyncio.run(optimized_lambda_handler(event, context))
        
        logger.info(f"Lambda processing completed with status: {response.get('statusCode')}")
        return response
        
    except Exception as e:
        logger.error(f"Lambda handler error: {e}", exc_info=True)
        
        # Fallback error response
        return {
            "statusCode": 500,
            "body": f'{{"status": "error", "message": "Internal server error: {str(e)}"}}',
            "headers": {
                "Content-Type": "application/json"
            }
        }


# For backward compatibility
handler = lambda_handler

# Version info
__version__ = "2.0.0-optimized"

if __name__ == "__main__":
    # For local testing
    import json
    
    test_event = {
        "httpMethod": "GET",
        "path": "/health",
        "headers": {}
    }
    
    class MockContext:
        aws_request_id = "test-request-id"
        function_name = "test-function"
        
    result = lambda_handler(test_event, MockContext())
    print("Test result:", json.dumps(result, indent=2))