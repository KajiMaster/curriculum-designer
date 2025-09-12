"""HTTP clients for external services."""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from functools import lru_cache
import httpx
import json

from ..config import get_config
from ..models import Card, LessonPlanFeedback, ActivityRequest
from ..utils import get_trello_api_key, get_trello_token, get_openai_api_key, ErrorBoundary

logger = logging.getLogger(__name__)
config = get_config()


class TrelloClient:
    """Async Trello API client with connection pooling."""
    
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._auth_params = {
            "key": get_trello_api_key(),
            "token": get_trello_token()
        }
    
    @property
    async def client(self) -> httpx.AsyncClient:
        """Lazy-loaded HTTP client with connection pooling."""
        if self._client is None or self._client.is_closed:
            limits = httpx.Limits(
                max_keepalive_connections=config.CONNECTION_POOL_SIZE,
                max_connections=config.CONNECTION_POOL_SIZE * 2
            )
            timeout = httpx.Timeout(config.HTTP_TIMEOUT)
            
            self._client = httpx.AsyncClient(
                limits=limits,
                timeout=timeout,
                base_url=config.TRELLO_BASE_URL
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def add_comment(self, card_id: str, text: str) -> Dict[str, Any]:
        """Add comment to a card."""
        with ErrorBoundary(f"add_comment to {card_id}", logger):
            client = await self.client
            url = f"/cards/{card_id}/actions/comments"
            data = {"text": text, **self._auth_params}
            
            response = await client.post(url, data=data)
            response.raise_for_status()
            return response.json()
    
    async def get_card(self, card_id: str) -> Dict[str, Any]:
        """Get card details."""
        with ErrorBoundary(f"get_card {card_id}", logger):
            client = await self.client
            url = f"/cards/{card_id}"
            params = {"fields": "name,desc,labels,list,idBoard", **self._auth_params}
            
            response = await client.get(url, params=params)
            if response.status_code != 200:
                logger.error(f"Error getting card {card_id}: {response.status_code} - {response.text}")
                return {}
            return response.json()
    
    async def create_card(self, list_id: str, name: str, desc: str = "", pos: str = "bottom") -> Optional[str]:
        """Create a new card and return its ID."""
        with ErrorBoundary(f"create_card in list {list_id}", logger):
            client = await self.client
            data = {
                "idList": list_id,
                "name": name,
                "desc": desc,
                "pos": pos,
                **self._auth_params
            }
            
            response = await client.post("/cards", data=data)
            response.raise_for_status()
            return response.json().get("id")
    
    async def get_or_create_list(self, board_id: str, list_name: str) -> Optional[str]:
        """Get existing list or create new one."""
        with ErrorBoundary(f"get_or_create_list {list_name} in board {board_id}", logger):
            client = await self.client
            
            # Get existing lists
            response = await client.get(f"/boards/{board_id}/lists", params=self._auth_params)
            response.raise_for_status()
            lists = response.json()
            
            # Check if list exists
            for lst in lists:
                if lst['name'] == list_name:
                    return lst['id']
            
            # Create new list
            create_params = {
                'name': list_name,
                'idBoard': board_id,
                'pos': 'bottom',
                **self._auth_params
            }
            
            create_response = await client.post("/lists", data=create_params)
            create_response.raise_for_status()
            return create_response.json().get('id')
    
    async def add_checklist(self, card_id: str, name: str, items: List[str]) -> Optional[Dict[str, Any]]:
        """Add checklist to card."""
        with ErrorBoundary(f"add_checklist to {card_id}", logger):
            client = await self.client
            
            # Create checklist
            data = {"idCard": card_id, "name": name, **self._auth_params}
            response = await client.post("/checklists", data=data)
            response.raise_for_status()
            checklist = response.json()
            
            # Add items
            for item in items:
                item_data = {"name": item, **self._auth_params}
                await client.post(f"/checklists/{checklist['id']}/checkItems", data=item_data)
            
            return checklist


class OpenAIClient:
    """Async OpenAI API client."""
    
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._api_key = get_openai_api_key()
    
    @property
    async def client(self) -> httpx.AsyncClient:
        """Lazy-loaded HTTP client."""
        if self._client is None or self._client.is_closed:
            limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
            timeout = httpx.Timeout(60.0)  # OpenAI can be slow
            
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json"
            }
            
            self._client = httpx.AsyncClient(
                limits=limits,
                timeout=timeout,
                headers=headers,
                base_url="https://api.openai.com/v1"
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def get_response(self, prompt: str, max_tokens: int = None, temperature: float = None) -> str:
        """Get response from OpenAI."""
        if not self._api_key:
            logger.error("OpenAI API key not configured")
            return "OpenAI API key not configured"
        
        max_tokens = max_tokens or config.OPENAI_MAX_TOKENS
        temperature = temperature or config.OPENAI_TEMPERATURE
        
        with ErrorBoundary("OpenAI API request", logger):
            client = await self.client
            
            data = {
                "model": config.OPENAI_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an English teaching assistant. Help teachers with curriculum planning, activity suggestions, and lesson organization. Be practical and concise."
                    },
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            logger.debug(f"Making OpenAI request with model {config.OPENAI_MODEL}")
            
            response = await client.post("/chat/completions", json=data)
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"OpenAI API error ({response.status_code}): {error_text}")
                return f"OpenAI API error ({response.status_code}): {error_text}"
            
            result = response.json()
            logger.debug("OpenAI request successful")
            
            if "choices" in result and result["choices"]:
                return result["choices"][0]["message"]["content"]
            return "Sorry, I couldn't generate a response."


class MCPClient:
    """Client for MCP (Curriculum) API."""
    
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    async def client(self) -> httpx.AsyncClient:
        """Lazy-loaded HTTP client."""
        if self._client is None or self._client.is_closed:
            timeout = httpx.Timeout(config.HTTP_TIMEOUT)
            self._client = httpx.AsyncClient(timeout=timeout)
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def submit_feedback(self, feedback: LessonPlanFeedback) -> Optional[Dict[str, Any]]:
        """Submit feedback to MCP API."""
        with ErrorBoundary("submit_feedback to MCP", logger):
            client = await self.client
            url = f"{config.MCP_API_URL}/feedback"
            
            response = await client.post(url, json=feedback.dict())
            response.raise_for_status()
            result = response.json()
            logger.info(f"Feedback submitted to MCP: {result}")
            return result


# Singleton instances
@lru_cache(maxsize=1)
def get_trello_client() -> TrelloClient:
    """Get singleton Trello client instance."""
    return TrelloClient()


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAIClient:
    """Get singleton OpenAI client instance."""
    return OpenAIClient()


@lru_cache(maxsize=1)
def get_mcp_client() -> MCPClient:
    """Get singleton MCP client instance."""
    return MCPClient()


# Cleanup function for Lambda
async def cleanup_clients():
    """Clean up all HTTP clients."""
    clients = [
        get_trello_client(),
        get_openai_client(),
        get_mcp_client()
    ]
    
    await asyncio.gather(
        *[client.close() for client in clients],
        return_exceptions=True
    )