"""Pytest configuration and fixtures."""

import pytest
import os
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Set test environment variables
os.environ.update({
    "TRELLO_API_KEY": "test_trello_key",
    "TRELLO_TOKEN": "test_trello_token",
    "OPENAI_API_KEY": "test_openai_key",
    "TRELLO_WEBHOOK_SECRET": "test_webhook_secret",
    "LOG_LEVEL": "DEBUG"
})


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_trello_client():
    """Mock Trello client."""
    client = AsyncMock()
    client.add_comment.return_value = {"id": "comment_123"}
    client.get_card.return_value = {
        "id": "card_123",
        "name": "Test Card",
        "desc": "Test description",
        "idBoard": "board_123"
    }
    client.create_card.return_value = "new_card_123"
    return client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    client = AsyncMock()
    client.get_response.return_value = "This is a test AI response."
    return client


@pytest.fixture
def webhook_payload():
    """Sample webhook payload."""
    return {
        "action": {
            "type": "commentCard",
            "data": {
                "text": "@ai hello world",
                "card": {
                    "id": "test_card_id",
                    "name": "Test Card"
                }
            },
            "memberCreator": {
                "username": "testuser"
            }
        }
    }


@pytest.fixture
def api_gateway_event():
    """Sample API Gateway event."""
    return {
        "httpMethod": "POST",
        "path": "/webhook",
        "body": None,
        "headers": {"content-type": "application/json"}
    }


@pytest.fixture
def mock_secrets_manager():
    """Mock secrets manager."""
    with patch('src.utils.get_secrets_manager') as mock:
        manager = Mock()
        manager.get_secret.return_value = "test_secret_value"
        mock.return_value = manager
        yield manager


@pytest.fixture
def mock_boto3_clients():
    """Mock boto3 clients."""
    with patch('boto3.client') as mock_client, \
         patch('boto3.resource') as mock_resource:
        
        # Mock SSM client
        ssm_client = Mock()
        ssm_client.get_parameter.return_value = {
            'Parameter': {'Value': 'test_parameter_value'}
        }
        
        # Mock Lambda client
        lambda_client = Mock()
        lambda_client.invoke.return_value = {
            'Payload': Mock(read=Mock(return_value='{"statusCode": 200, "body": "{\\"result\\": \\"success\\"}"}'))
        }
        
        # Mock DynamoDB resource
        dynamodb_resource = Mock()
        table = Mock()
        table.put_item.return_value = {}
        table.get_item.return_value = {'Item': {'test': 'data'}}
        table.scan.return_value = {'Items': []}
        dynamodb_resource.Table.return_value = table
        
        mock_client.return_value = ssm_client
        mock_resource.return_value = dynamodb_resource
        
        yield {
            'ssm': ssm_client,
            'lambda': lambda_client,
            'dynamodb': dynamodb_resource
        }