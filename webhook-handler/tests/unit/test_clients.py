"""Tests for client modules."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx

from src.clients import TrelloClient, OpenAIClient, MCPClient


class TestTrelloClient:
    """Test Trello client."""
    
    @pytest.mark.asyncio
    async def test_get_card_success(self):
        """Test successful card retrieval."""
        with patch('src.clients.get_trello_api_key', return_value="test_key"), \
             patch('src.clients.get_trello_token', return_value="test_token"):
            client = TrelloClient()
            
            mock_response = Mock()
            mock_response.json.return_value = {"id": "card123", "name": "Test Card"}
            mock_response.raise_for_status.return_value = None
            
            mock_http_client = AsyncMock()
            mock_http_client.get = AsyncMock(return_value=mock_response)
            client._client = mock_http_client
            
            result = await client.get_card("card123")
            
            assert result["id"] == "card123"
            mock_http_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_card_error(self):
        """Test card retrieval with error."""
        with patch('src.clients.get_trello_api_key', return_value="test_key"), \
             patch('src.clients.get_trello_token', return_value="test_token"):
            client = TrelloClient()
            
            mock_http_client = AsyncMock()
            mock_http_client.get = AsyncMock(side_effect=httpx.HTTPError("Network error"))
            client._client = mock_http_client
            
            result = await client.get_card("card123")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_add_comment_error_handling(self):
        """Test comment addition error handling."""
        with patch('src.clients.get_trello_api_key', return_value="test_key"), \
             patch('src.clients.get_trello_token', return_value="test_token"):
            client = TrelloClient()
            
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized", 
                request=Mock(), 
                response=Mock(status_code=401)
            )
            
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(return_value=mock_response)
            client._client = mock_http_client
            
            result = await client.add_comment("card123", "Test comment")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_create_card_success(self):
        """Test successful card creation."""
        with patch('src.clients.get_trello_api_key', return_value="test_key"), \
             patch('src.clients.get_trello_token', return_value="test_token"):
            client = TrelloClient()
            
            mock_response = Mock()
            mock_response.json.return_value = {"id": "new_card_123"}
            mock_response.raise_for_status.return_value = None
            
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(return_value=mock_response)
            client._client = mock_http_client
            
            result = await client.create_card("list123", "New Card", "Description")
            
            assert result == "new_card_123"
            mock_http_client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_or_create_list(self):
        """Test get or create list functionality."""
        with patch('src.clients.get_trello_api_key', return_value="test_key"), \
             patch('src.clients.get_trello_token', return_value="test_token"):
            client = TrelloClient()
            
            # Mock getting lists
            mock_lists_response = Mock()
            mock_lists_response.json.return_value = [
                {"id": "list1", "name": "Existing List"},
                {"id": "list2", "name": "Another List"}
            ]
            mock_lists_response.raise_for_status.return_value = None
            
            mock_http_client = AsyncMock()
            mock_http_client.get = AsyncMock(return_value=mock_lists_response)
            client._client = mock_http_client
            
            result = await client.get_or_create_list("board123", "Existing List")
            assert result == "list1"
    
    @pytest.mark.asyncio
    async def test_get_or_create_list_create_new(self):
        """Test creating new list when not found."""
        with patch('src.clients.get_trello_api_key', return_value="test_key"), \
             patch('src.clients.get_trello_token', return_value="test_token"):
            client = TrelloClient()
            
            # Mock getting empty lists
            mock_lists_response = Mock()
            mock_lists_response.json.return_value = []
            mock_lists_response.raise_for_status.return_value = None
            
            # Mock creating new list
            mock_create_response = Mock()
            mock_create_response.json.return_value = {"id": "new_list_123"}
            mock_create_response.raise_for_status.return_value = None
            
            mock_http_client = AsyncMock()
            mock_http_client.get = AsyncMock(return_value=mock_lists_response)
            mock_http_client.post = AsyncMock(return_value=mock_create_response)
            client._client = mock_http_client
            
            result = await client.get_or_create_list("board123", "New List")
            assert result == "new_list_123"


class TestOpenAIClient:
    """Test OpenAI client."""
    
    @pytest.mark.asyncio
    async def test_get_response_success(self):
        """Test successful OpenAI response."""
        with patch('src.clients.get_openai_api_key', return_value="test_key"):
            client = OpenAIClient()
            
            mock_response = Mock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "AI response"}}]
            }
            mock_response.raise_for_status.return_value = None
            
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(return_value=mock_response)
            client._client = mock_http_client
            
            result = await client.get_response("Test prompt")
            assert result == "AI response"
    
    @pytest.mark.asyncio
    async def test_get_response_with_max_tokens(self):
        """Test OpenAI response with max tokens."""
        with patch('src.clients.get_openai_api_key', return_value="test_key"):
            client = OpenAIClient()
            
            mock_response = Mock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Limited response"}}]
            }
            mock_response.raise_for_status.return_value = None
            
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(return_value=mock_response)
            client._client = mock_http_client
            
            result = await client.get_response("Test prompt", max_tokens=100)
            assert result == "Limited response"
            
            # Verify max_tokens was passed
            call_args = mock_http_client.post.call_args[1]["json"]
            assert call_args["max_tokens"] == 100
    
    @pytest.mark.asyncio
    async def test_get_response_error(self):
        """Test OpenAI response with API error."""
        with patch('src.clients.get_openai_api_key', return_value="test_key"):
            client = OpenAIClient()
            
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized",
                request=Mock(),
                response=Mock(status_code=401, text='{"error": {"message": "Invalid API key"}}')
            )
            
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(return_value=mock_response)
            client._client = mock_http_client
            
            result = await client.get_response("Test prompt")
            assert "Error communicating with OpenAI" in result


class TestMCPClient:
    """Test MCP client."""
    
    @pytest.mark.asyncio
    async def test_submit_feedback_success(self):
        """Test successful feedback submission."""
        with patch('src.clients.config.MCP_SERVICE_BASE_URL', 'http://test.com'), \
             patch('src.clients.config.MCP_API_KEY', 'test_key'):
            client = MCPClient()
            
            mock_response = Mock()
            mock_response.json.return_value = {"status": "success", "id": "feedback123"}
            mock_response.raise_for_status.return_value = None
            
            from src.models import LessonPlanFeedback, FeedbackType
            feedback = LessonPlanFeedback(
                lesson_plan_id="plan123",
                feedback_type=FeedbackType.LIKE,
                feedback_text="Great!",
                source="test"
            )
            
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(return_value=mock_response)
            client._client = mock_http_client
            
            result = await client.submit_feedback(feedback)
            assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_submit_feedback_error(self):
        """Test feedback submission with error."""
        with patch('src.clients.config.MCP_SERVICE_BASE_URL', 'http://test.com'), \
             patch('src.clients.config.MCP_API_KEY', 'test_key'):
            client = MCPClient()
            
            from src.models import LessonPlanFeedback, FeedbackType
            feedback = LessonPlanFeedback(
                lesson_plan_id="plan123",
                feedback_type=FeedbackType.LIKE,
                feedback_text="Great!",
                source="test"
            )
            
            mock_http_client = AsyncMock()
            mock_http_client.post = AsyncMock(side_effect=httpx.HTTPError("Network error"))
            client._client = mock_http_client
            
            result = await client.submit_feedback(feedback)
            assert result is None