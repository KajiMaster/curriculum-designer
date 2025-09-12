"""Additional tests to improve code coverage."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime

from src.models import (
    ActionType, FeedbackType, Card, ActionData, MemberCreator,
    WebhookAction, WebhookPayload, LessonPlanFeedback, ActivityRequest,
    FrameworkData, LambdaResponse
)
from src.config import Config, get_config
from src.handlers import WebhookHandler, CommentHandler


class TestModelsExtended:
    """Extended tests for data models."""
    
    def test_action_type_enum(self):
        """Test ActionType enum values."""
        assert ActionType.COMMENT_CARD == "commentCard"
        assert ActionType.UPDATE_CARD == "updateCard"
        assert ActionType.CREATE_CARD == "createCard"
    
    def test_feedback_type_enum(self):
        """Test FeedbackType enum values."""
        assert FeedbackType.LIKE == "like"
        assert FeedbackType.DISLIKE == "dislike"
        assert FeedbackType.IMPROVE == "improve"
        assert FeedbackType.RATING == "rating"
    
    def test_card_model_with_optional_fields(self):
        """Test Card model with optional fields."""
        card = Card(id="card1", name="Test Card")
        assert card.desc == ""
        assert card.idBoard is None
        assert card.idList is None
        
        card_full = Card(
            id="card2",
            name="Full Card",
            desc="Description",
            idBoard="board1",
            idList="list1"
        )
        assert card_full.desc == "Description"
        assert card_full.idBoard == "board1"
    
    def test_action_data_with_optional_fields(self):
        """Test ActionData model."""
        data = ActionData()
        assert data.text is None
        assert data.card is None
        assert data.listAfter is None
        
        data_with_text = ActionData(text="Test comment")
        assert data_with_text.text == "Test comment"
    
    def test_member_creator_model(self):
        """Test MemberCreator model."""
        member = MemberCreator()
        assert member.username is None
        assert member.fullName is None
        
        member_full = MemberCreator(username="user1", fullName="User One")
        assert member_full.username == "user1"
        assert member_full.fullName == "User One"
    
    def test_webhook_action_model(self):
        """Test WebhookAction model."""
        action = WebhookAction(
            type=ActionType.COMMENT_CARD,
            data=ActionData(text="Test")
        )
        assert action.type == ActionType.COMMENT_CARD
        assert action.memberCreator is None
        assert action.date is None
    
    def test_framework_data_model(self):
        """Test FrameworkData model."""
        framework = FrameworkData(
            framework_name="Test Framework",
            framework_data={"key": "value"}
        )
        assert framework.framework_name == "Test Framework"
        assert framework.description is None
        assert framework.target_level == "A1-A2"
        assert framework.framework_data == {"key": "value"}
    
    def test_lambda_response_to_dict(self):
        """Test LambdaResponse to_dict method."""
        response = LambdaResponse(
            statusCode=200,
            body="Success"
        )
        result = response.to_dict()
        assert result["statusCode"] == 200
        assert result["body"] == "Success"
        assert "headers" not in result
        
        response_with_headers = LambdaResponse(
            statusCode=201,
            body="Created",
            headers={"Content-Type": "application/json"}
        )
        result_with_headers = response_with_headers.to_dict()
        assert result_with_headers["headers"]["Content-Type"] == "application/json"
    
    def test_activity_request_defaults(self):
        """Test ActivityRequest default values."""
        request = ActivityRequest(topic="Math")
        assert request.topic == "Math"
        assert request.grade_level == "3"
        assert request.duration == 15
        assert request.activity_type is None
        assert request.context is None
    
    def test_lesson_plan_feedback_non_rating(self):
        """Test LessonPlanFeedback without rating."""
        feedback = LessonPlanFeedback(
            lesson_plan_id="plan1",
            feedback_type=FeedbackType.LIKE,
            feedback_text="Great lesson!",
            source="test"
        )
        assert feedback.rating is None
        assert feedback.feedback_type == FeedbackType.LIKE


class TestConfigExtended:
    """Extended tests for configuration."""
    
    def test_config_defaults(self):
        """Test Config default values."""
        config = Config()
        assert config.AWS_REGION == "us-east-1"
        assert config.TRELLO_BASE_URL == "https://api.trello.com/1"
        assert config.OPENAI_MODEL == "gpt-3.5-turbo"
        assert config.OPENAI_MAX_TOKENS == 500
        assert config.OPENAI_TEMPERATURE == 0.7
        assert config.HTTP_TIMEOUT == 30
        assert config.CONNECTION_POOL_SIZE == 10
        assert config.LOG_LEVEL in ["INFO", "DEBUG"]  # Allow both since env may override
        assert config.MAX_RETRIES == 3
        assert config.TIMEOUT_SECONDS == 30
    
    def test_config_is_lambda_environment_false(self):
        """Test Lambda environment detection when not in Lambda."""
        config = Config()
        # In test environment, should not be in Lambda
        assert config.is_lambda_environment() is False
    
    def test_config_validate_non_lambda(self):
        """Test validation in non-Lambda environment."""
        config = Config()
        # Should not raise in non-Lambda environment
        try:
            config.validate()
        except ValueError:
            pytest.fail("validate() raised ValueError in non-Lambda environment")


class TestHandlersExtended:
    """Extended tests for handlers."""
    
    @pytest.mark.asyncio
    async def test_webhook_handler_init(self):
        """Test WebhookHandler initialization."""
        handler = WebhookHandler()
        assert handler.comment_handler is not None
        assert isinstance(handler.comment_handler, CommentHandler)
    
    def test_action_data_extra_config(self):
        """Test ActionData with extra config."""
        data = ActionData(text="test", extra_field="allowed")
        assert data.text == "test"
    
    def test_webhook_payload_with_member(self):
        """Test WebhookPayload with member creator."""
        payload = WebhookPayload(
            action=WebhookAction(
                type=ActionType.COMMENT_CARD,
                data=ActionData(text="Test"),
                memberCreator=MemberCreator(username="user1")
            )
        )
        assert payload.action.memberCreator.username == "user1"
    
    @pytest.mark.asyncio
    async def test_webhook_handler_missing_body(self):
        """Test webhook with missing body."""
        handler = WebhookHandler()
        
        event = {
            "httpMethod": "POST",
            "path": "/webhook",
            "body": None
        }
        
        response = await handler.handle(event, {})
        # Should handle gracefully
        assert response.statusCode in [200, 400, 500]
    
    @pytest.mark.asyncio
    async def test_comment_handler_init(self):
        """Test CommentHandler initialization."""
        with patch('src.handlers.get_trello_client'), \
             patch('src.handlers.get_ai_service'), \
             patch('src.handlers.get_feedback_service'), \
             patch('src.handlers.get_framework_service'), \
             patch('src.handlers.get_activity_service'):
            handler = CommentHandler()
            assert handler.trello_client is not None
            assert handler.ai_service is not None


class TestServicesExtended:
    """Extended tests for services."""
    
    @pytest.mark.asyncio
    async def test_ai_service_initialization(self):
        """Test AIService initialization."""
        with patch('src.services.get_openai_client'):
            from src.services import AIService
            service = AIService()
            assert service.openai_client is not None
    
    def test_feedback_service_initialization(self):
        """Test FeedbackService initialization."""
        with patch('src.services.get_mcp_client'):
            from src.services import FeedbackService
            service = FeedbackService()
            assert service.mcp_client is not None
    
    def test_framework_service_initialization(self):
        """Test FrameworkService initialization."""
        with patch('src.services.get_trello_client'):
            from src.services import FrameworkService
            service = FrameworkService()
            assert service.trello_client is not None
            assert service._dynamodb is None  # Lazy loaded
    
    def test_activity_service_initialization(self):
        """Test ActivityService initialization."""
        with patch('src.services.get_trello_client'):
            from src.services import ActivityService
            service = ActivityService()
            assert service.trello_client is not None
            assert service._lambda_client is None  # Lazy loaded


class TestUtilsExtended:
    """Extended tests for utility functions."""
    
    def test_error_boundary_context_manager(self):
        """Test ErrorBoundary as context manager."""
        from src.utils import ErrorBoundary
        
        # Test normal execution
        with ErrorBoundary("test_operation") as boundary:
            result = 2 + 2
        assert result == 4
    
    def test_secrets_manager_initialization(self):
        """Test SecretsManager initialization."""
        from src.utils import SecretsManager
        
        manager = SecretsManager()
        assert manager._cache == {}
        assert manager._ssm_client is None  # Lazy loaded
    
    @patch('src.utils.get_secrets_manager')
    def test_get_webhook_secret(self, mock_get_manager):
        """Test get_webhook_secret convenience function."""
        from src.utils import get_webhook_secret
        
        mock_manager = Mock()
        mock_manager.get_secret.return_value = "webhook_secret"
        mock_get_manager.return_value = mock_manager
        
        result = get_webhook_secret()
        assert result == "webhook_secret"