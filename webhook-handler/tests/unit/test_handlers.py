"""Tests for request handlers."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import json

from src.handlers import CommentHandler, WebhookHandler
from src.models import LambdaResponse


class TestCommentHandler:
    """Test comment handler."""
    
    @pytest.mark.asyncio
    async def test_handle_general_ai_request(self, mock_trello_client):
        """Test handling general AI requests."""
        with patch('src.handlers.get_trello_client', return_value=mock_trello_client), \
             patch('src.handlers.get_ai_service') as mock_ai_service:
            
            mock_ai_service.return_value.get_response = AsyncMock(return_value="AI response")
            
            handler = CommentHandler()
            
            action = {
                "data": {
                    "text": "@ai help me with grammar",
                    "card": {"id": "card123"}
                },
                "memberCreator": {"username": "teacher1"}
            }
            
            await handler.handle(action)
            
            # Verify Trello client was called to get card details
            mock_trello_client.get_card.assert_called_once_with("card123")
            
            # Verify AI response was posted as comment
            mock_trello_client.add_comment.assert_called()
            call_args = mock_trello_client.add_comment.call_args[0]
            assert "🤖 **AI Assistant:**" in call_args[1]
    
    @pytest.mark.asyncio
    async def test_skip_bot_comments(self, mock_trello_client):
        """Test that bot comments are skipped to prevent loops."""
        with patch('src.handlers.get_trello_client', return_value=mock_trello_client):
            handler = CommentHandler()
            
            action = {
                "data": {
                    "text": "🤖 **AI Assistant:** This is a bot response",
                    "card": {"id": "card123"}
                },
                "memberCreator": {"username": "bot"}
            }
            
            await handler.handle(action)
            
            # Verify no API calls were made
            mock_trello_client.get_card.assert_not_called()
            mock_trello_client.add_comment.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_ignore_non_ai_comments(self, mock_trello_client):
        """Test that comments without @ai are ignored."""
        with patch('src.handlers.get_trello_client', return_value=mock_trello_client):
            handler = CommentHandler()
            
            action = {
                "data": {
                    "text": "This is just a regular comment",
                    "card": {"id": "card123"}
                },
                "memberCreator": {"username": "teacher1"}
            }
            
            await handler.handle(action)
            
            # Verify no processing occurred
            mock_trello_client.get_card.assert_not_called()
            mock_trello_client.add_comment.assert_not_called()


class TestWebhookHandler:
    """Test main webhook handler."""
    
    @pytest.mark.asyncio
    async def test_handle_webhook_post(self):
        """Test handling webhook POST requests."""
        handler = WebhookHandler()
        
        event = {
            "httpMethod": "POST",
            "path": "/webhook",
            "body": json.dumps({
                "action": {
                    "type": "commentCard",
                    "data": {
                        "text": "@ai hello",
                        "card": {"id": "card123", "name": "Test Card"}
                    }
                }
            })
        }
        
        with patch.object(handler.comment_handler, 'handle', new_callable=AsyncMock) as mock_handle:
            response = await handler.handle(event, {})
            
            assert response.statusCode == 200
            mock_handle.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_health_check(self):
        """Test health check endpoint."""
        handler = WebhookHandler()
        
        event = {
            "httpMethod": "GET",
            "path": "/health"
        }
        
        with patch('src.handlers.get_trello_api_key', return_value="test_key"), \
             patch('src.handlers.get_trello_token', return_value="test_token"), \
             patch('src.handlers.get_openai_api_key', return_value="test_openai_key"):
            
            response = await handler.handle(event, {})
            
            assert response.statusCode == 200
            body = json.loads(response.body)
            assert body["status"] == "healthy"
            assert body["services"]["trello"] is True
            assert body["services"]["openai"] is True
    
    @pytest.mark.asyncio
    async def test_handle_webhook_verification(self):
        """Test webhook verification (GET/HEAD requests)."""
        handler = WebhookHandler()
        
        # Test GET request
        event = {
            "httpMethod": "GET",
            "path": "/webhook"
        }
        
        response = await handler.handle(event, {})
        
        assert response.statusCode == 200
        body = json.loads(response.body)
        assert "webhook endpoint ready" in body["status"]
        
        # Test HEAD request
        event["httpMethod"] = "HEAD"
        response = await handler.handle(event, {})
        
        assert response.statusCode == 200
        assert response.body == ""
    
    @pytest.mark.asyncio
    async def test_handle_invalid_json(self):
        """Test handling invalid JSON in webhook payload."""
        handler = WebhookHandler()
        
        event = {
            "httpMethod": "POST",
            "path": "/webhook",
            "body": "invalid json {{"
        }
        
        response = await handler.handle(event, {})
        
        # Should handle gracefully and still return 500 or appropriate error
        assert response.statusCode in [400, 500]
    
    @pytest.mark.asyncio
    async def test_handle_404(self):
        """Test 404 handling for unknown paths."""
        handler = WebhookHandler()
        
        event = {
            "httpMethod": "GET",
            "path": "/unknown"
        }
        
        response = await handler.handle(event, {})
        
        assert response.statusCode == 404
        body = json.loads(response.body)
        assert body["message"] == "Not found"