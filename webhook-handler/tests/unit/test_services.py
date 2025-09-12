"""Tests for service layer."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import json

from src.services import FeedbackService, AIService, FrameworkService
from src.models import FeedbackType


class TestFeedbackService:
    """Test feedback service."""
    
    def test_parse_like_feedback(self):
        """Test parsing like feedback from comment."""
        service = FeedbackService()
        comment_text = "@ai like: This lesson plan is excellent!"
        card_details = {
            "id": "card123",
            "desc": "**Plan ID:** plan123"
        }
        
        feedback = service.parse_feedback_from_comment(comment_text, card_details)
        
        assert feedback is not None
        assert feedback.feedback_type == FeedbackType.LIKE
        assert feedback.lesson_plan_id == "plan123"
        assert "excellent" in feedback.feedback_text
    
    def test_parse_rating_feedback(self):
        """Test parsing rating feedback from comment."""
        service = FeedbackService()
        comment_text = "@ai rating: 4/5"
        card_details = {
            "id": "card123",
            "desc": "Plan ID:** plan123"
        }
        
        feedback = service.parse_feedback_from_comment(comment_text, card_details)
        
        assert feedback is not None
        assert feedback.feedback_type == FeedbackType.RATING
        assert feedback.rating == 4
    
    def test_extract_lesson_plan_id_fallback(self):
        """Test lesson plan ID extraction with fallback."""
        service = FeedbackService()
        card_details = {
            "id": "card123",
            "name": "My Lesson Plan",
            "desc": "No plan ID here"
        }
        
        plan_id = service._extract_lesson_plan_id(card_details)
        assert plan_id == "my_lesson_plan"


class TestAIService:
    """Test AI service."""
    
    @pytest.mark.asyncio
    async def test_suggest_activities(self, mock_openai_client):
        """Test activity suggestion."""
        with patch('src.services.get_openai_client', return_value=mock_openai_client):
            service = AIService()
            
            result = await service.suggest_activities("intermediate", "grammar", 30)
            
            mock_openai_client.get_response.assert_called_once()
            assert result == "This is a test AI response."
    
    @pytest.mark.asyncio
    async def test_analyze_activity(self, mock_openai_client):
        """Test activity analysis."""
        with patch('src.services.get_openai_client', return_value=mock_openai_client):
            service = AIService()
            
            result = await service.analyze_activity("Grammar Game", "A fun grammar activity")
            
            mock_openai_client.get_response.assert_called_once()
            call_args = mock_openai_client.get_response.call_args
            assert "Grammar Game" in call_args[0][0]
            assert "fun grammar activity" in call_args[0][0]


class TestFrameworkService:
    """Test framework service."""
    
    @pytest.mark.asyncio
    async def test_save_framework(self, mock_boto3_clients):
        """Test framework saving."""
        with patch('boto3.resource', return_value=mock_boto3_clients['dynamodb']):
            service = FrameworkService()
            
            framework_data = {"name": "Test Framework", "level": "A1"}
            framework_id = await service.save_framework(
                framework_data, "Test Framework", "board123"
            )
            
            assert framework_id is not None
            assert len(framework_id) == 36  # UUID length
    
    def test_get_framework(self, mock_boto3_clients):
        """Test framework retrieval."""
        mock_table = mock_boto3_clients['dynamodb'].Table.return_value
        mock_table.get_item.return_value = {
            'Item': {'framework_id': 'test123', 'framework_name': 'Test'}
        }
        
        with patch('boto3.resource', return_value=mock_boto3_clients['dynamodb']):
            service = FrameworkService()
            
            result = service.get_framework('test123')
            
            assert result is not None
            assert result['framework_id'] == 'test123'
    
    def test_list_frameworks(self, mock_boto3_clients):
        """Test framework listing."""
        mock_table = mock_boto3_clients['dynamodb'].Table.return_value
        mock_table.scan.return_value = {
            'Items': [
                {'framework_id': 'fw1', 'framework_name': 'Framework 1'},
                {'framework_id': 'fw2', 'framework_name': 'Framework 2'}
            ]
        }
        
        with patch('boto3.resource', return_value=mock_boto3_clients['dynamodb']):
            service = FrameworkService()
            
            result = service.list_frameworks('board123')
            
            assert len(result) == 2
            assert result[0]['framework_name'] == 'Framework 1'