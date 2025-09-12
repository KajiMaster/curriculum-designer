"""Integration tests for the Lambda handler."""

import pytest
import json
import os
from unittest.mock import patch, Mock, AsyncMock

# Import the main lambda handler
import sys
sys.path.insert(0, '/home/kaji/curriculum-designer/webhook-handler')


class TestLambdaIntegration:
    """Integration tests for Lambda handler."""
    
    @pytest.mark.asyncio
    async def test_lambda_handler_import(self):
        """Test that the new lambda handler can be imported."""
        from src import lambda_handler
        assert lambda_handler is not None
    
    @pytest.mark.asyncio
    async def test_lambda_handler_basic_webhook(self):
        """Test Lambda handler with basic webhook payload."""
        from src import lambda_handler
        
        event = {
            "httpMethod": "POST",
            "path": "/webhook",
            "body": json.dumps({
                "action": {
                    "type": "commentCard",
                    "data": {
                        "text": "@ai hello world",
                        "card": {
                            "id": "test_card_123",
                            "name": "Test Card"
                        }
                    },
                    "memberCreator": {
                        "username": "testuser"
                    }
                }
            }),
            "headers": {
                "content-type": "application/json"
            }
        }
        
        context = Mock()
        context.aws_request_id = "test-request-id"
        
        # Mock external dependencies
        with patch('src.clients.get_trello_client') as mock_trello, \
             patch('src.clients.get_openai_client') as mock_openai, \
             patch('src.utils.get_trello_api_key', return_value="test_key"), \
             patch('src.utils.get_trello_token', return_value="test_token"), \
             patch('src.utils.get_openai_api_key', return_value="test_openai_key"):
            
            # Setup mocks
            trello_client = AsyncMock()
            trello_client.get_card.return_value = {
                "id": "test_card_123",
                "name": "Test Card",
                "desc": "Test description",
                "idBoard": "test_board"
            }
            trello_client.add_comment.return_value = {"id": "comment_123"}
            mock_trello.return_value = trello_client
            
            openai_client = AsyncMock()
            openai_client.get_response.return_value = "Hello! How can I help you today?"
            mock_openai.return_value = openai_client
            
            # Call the handler
            response = await lambda_handler(event, context)
            
            # Verify response structure
            assert isinstance(response, dict)
            assert "statusCode" in response
            assert "body" in response
            assert response["statusCode"] == 200
            
            # Verify the interaction occurred
            trello_client.get_card.assert_called_once_with("test_card_123")
            trello_client.add_comment.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_lambda_handler_health_check(self):
        """Test Lambda handler health check endpoint."""
        from src import lambda_handler
        
        event = {
            "httpMethod": "GET",
            "path": "/health",
            "headers": {}
        }
        
        context = Mock()
        
        with patch('src.utils.get_trello_api_key', return_value="test_key"), \
             patch('src.utils.get_trello_token', return_value="test_token"), \
             patch('src.utils.get_openai_api_key', return_value="test_openai_key"):
            
            response = await lambda_handler(event, context)
            
            assert response["statusCode"] == 200
            
            body = json.loads(response["body"])
            assert body["status"] == "healthy"
            assert "services" in body
            assert body["services"]["trello"] is True
            assert body["services"]["openai"] is True
    
    @pytest.mark.asyncio
    async def test_lambda_handler_error_handling(self):
        """Test Lambda handler error handling."""
        from src import lambda_handler
        
        event = {
            "httpMethod": "POST", 
            "path": "/webhook",
            "body": "invalid json {{"
        }
        
        context = Mock()
        
        response = await lambda_handler(event, context)
        
        # Should handle the error gracefully
        assert "statusCode" in response
        assert response["statusCode"] in [400, 500]
    
    @pytest.mark.asyncio
    async def test_lambda_handler_webhook_verification(self):
        """Test webhook verification responses."""
        from src import lambda_handler
        
        # Test HEAD request
        event = {
            "httpMethod": "HEAD",
            "path": "/webhook",
            "headers": {}
        }
        
        context = Mock()
        
        response = await lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        assert response["body"] == ""
        
        # Test GET request
        event["httpMethod"] = "GET"
        response = await lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "webhook endpoint ready" in body["status"]