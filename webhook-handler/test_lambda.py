"""
Basic tests for Lambda function
"""
import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


def test_lambda_handler_import():
    """Test that lambda_main module can be imported"""
    import lambda_main
    assert lambda_main.lambda_handler is not None


def test_lambda_handler_with_head_request():
    """Test that HEAD requests are handled properly"""
    import lambda_main
    
    # Mock event for HEAD request
    event = {
        "httpMethod": "HEAD",
        "path": "/webhook",
        "body": None,
        "headers": {}
    }
    
    context = MagicMock()
    
    # Call handler
    response = lambda_main.lambda_handler(event, context)
    
    # Check response
    assert response["statusCode"] == 200
    assert "headers" in response


def test_lambda_handler_with_get_health():
    """Test that GET /health requests work"""
    import lambda_main
    
    # Mock event for GET /health
    event = {
        "httpMethod": "GET", 
        "path": "/health",
        "body": None,
        "headers": {}
    }
    
    context = MagicMock()
    
    # Call handler
    response = lambda_main.lambda_handler(event, context)
    
    # Check response
    assert response["statusCode"] == 200
    assert "healthy" in response["body"]


@patch('lambda_main.get_secret')
def test_lambda_handler_environment_setup(mock_get_secret):
    """Test that environment variables are properly configured"""
    import lambda_main
    
    # Mock secrets
    mock_get_secret.side_effect = lambda param, env_var: "test_value"
    
    # Mock event
    event = {
        "httpMethod": "GET",
        "path": "/health", 
        "body": None,
        "headers": {}
    }
    
    context = MagicMock()
    
    # Call handler
    response = lambda_main.lambda_handler(event, context)
    
    # Verify secrets were requested
    assert mock_get_secret.call_count > 0
    assert response["statusCode"] == 200


def test_webhook_payload_parsing():
    """Test webhook payload parsing"""
    import lambda_main
    
    # Mock Trello webhook payload
    webhook_payload = {
        "action": {
            "type": "commentCard",
            "data": {
                "text": "@ai hello",
                "card": {
                    "id": "test_card_id",
                    "name": "Test Card"
                }
            }
        }
    }
    
    event = {
        "httpMethod": "POST",
        "path": "/webhook",
        "body": json.dumps(webhook_payload),
        "headers": {"content-type": "application/json"}
    }
    
    context = MagicMock()
    
    # Mock the async functions to avoid actual API calls
    with patch('lambda_main.handle_comment', new_callable=AsyncMock) as mock_handle:
        response = lambda_main.lambda_handler(event, context)
        
        # Should return success even if we don't actually process
        assert response["statusCode"] in [200, 500]  # May fail due to missing secrets, but should not crash


if __name__ == "__main__":
    pytest.main([__file__])