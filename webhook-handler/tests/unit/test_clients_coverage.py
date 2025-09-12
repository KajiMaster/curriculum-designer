"""Tests to increase client coverage."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx

from src.clients import get_trello_client, get_openai_client, get_mcp_client


class TestClientsCoverage:
    """Test clients for coverage."""
    
    @pytest.mark.asyncio
    async def test_trello_client_initialization(self):
        """Test TrelloClient initialization and methods."""
        with patch('src.clients.get_trello_api_key', return_value="test_key"), \
             patch('src.clients.get_trello_token', return_value="test_token"):
            
            client = get_trello_client()
            assert client is not None
            
            # Test that client is singleton
            client2 = get_trello_client()
            assert client is client2
    
    @pytest.mark.asyncio  
    async def test_openai_client_initialization(self):
        """Test OpenAIClient initialization."""
        with patch('src.clients.get_openai_api_key', return_value="test_key"):
            client = get_openai_client()
            assert client is not None
            
            # Test singleton
            client2 = get_openai_client()
            assert client is client2
    
    @pytest.mark.asyncio
    async def test_mcp_client_initialization(self):
        """Test MCPClient initialization."""
        with patch('src.clients.config.MCP_SERVICE_BASE_URL', 'http://test.com'), \
             patch('src.clients.config.MCP_API_KEY', 'test_key'):
            
            client = get_mcp_client()
            assert client is not None
            
            # Test singleton
            client2 = get_mcp_client()
            assert client is client2
    
    @pytest.mark.asyncio
    async def test_trello_client_close(self):
        """Test TrelloClient close method."""
        with patch('src.clients.get_trello_api_key', return_value="test_key"), \
             patch('src.clients.get_trello_token', return_value="test_token"):
            
            from src.clients import TrelloClient
            client = TrelloClient()
            
            # Mock the http client
            mock_http_client = AsyncMock()
            mock_http_client.is_closed = False
            mock_http_client.aclose = AsyncMock()
            client._client = mock_http_client
            
            await client.close()
            mock_http_client.aclose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_openai_client_close(self):
        """Test OpenAIClient close method."""
        with patch('src.clients.get_openai_api_key', return_value="test_key"):
            from src.clients import OpenAIClient
            client = OpenAIClient()
            
            # Mock the http client
            mock_http_client = AsyncMock()
            mock_http_client.is_closed = False
            mock_http_client.aclose = AsyncMock()
            client._client = mock_http_client
            
            await client.close()
            mock_http_client.aclose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mcp_client_close(self):
        """Test MCPClient close method."""
        with patch('src.clients.config.MCP_SERVICE_BASE_URL', 'http://test.com'), \
             patch('src.clients.config.MCP_API_KEY', 'test_key'):
            
            from src.clients import MCPClient
            client = MCPClient()
            
            # Mock the http client
            mock_http_client = AsyncMock()
            mock_http_client.is_closed = False
            mock_http_client.aclose = AsyncMock()
            client._client = mock_http_client
            
            await client.close()
            mock_http_client.aclose.assert_called_once()