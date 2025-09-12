"""Tests for data models."""

import pytest
from pydantic import ValidationError

from src.models import WebhookPayload, LessonPlanFeedback, FeedbackType, ActivityRequest


def test_webhook_payload_validation():
    """Test webhook payload validation."""
    payload_data = {
        "action": {
            "type": "commentCard",
            "data": {
                "text": "Test comment",
                "card": {
                    "id": "card123",
                    "name": "Test Card"
                }
            }
        }
    }
    
    payload = WebhookPayload(**payload_data)
    assert payload.action.type == "commentCard"
    assert payload.action.data.card.id == "card123"


def test_lesson_plan_feedback_validation():
    """Test lesson plan feedback model validation."""
    feedback_data = {
        "lesson_plan_id": "plan123",
        "feedback_type": FeedbackType.LIKE,
        "feedback_text": "Great lesson plan!",
        "source": "trello_comment:card123"
    }
    
    feedback = LessonPlanFeedback(**feedback_data)
    assert feedback.lesson_plan_id == "plan123"
    assert feedback.feedback_type == FeedbackType.LIKE


def test_lesson_plan_feedback_rating_validation():
    """Test rating validation for feedback."""
    # Valid rating feedback
    feedback_data = {
        "lesson_plan_id": "plan123",
        "feedback_type": FeedbackType.RATING,
        "feedback_text": "Rating: 4/5",
        "rating": 4,
        "source": "trello_comment:card123"
    }
    
    feedback = LessonPlanFeedback(**feedback_data)
    assert feedback.rating == 4
    
    # Invalid rating feedback (missing rating for rating type)
    with pytest.raises(ValidationError):
        LessonPlanFeedback(
            lesson_plan_id="plan123",
            feedback_type=FeedbackType.RATING,
            feedback_text="Rating feedback",
            source="test"
        )


def test_activity_request_validation():
    """Test activity request validation."""
    request_data = {
        "topic": "Food and Drinks",
        "grade_level": "3",
        "duration": 20,
        "activity_type": "preference_choice"
    }
    
    request = ActivityRequest(**request_data)
    assert request.topic == "Food and Drinks"
    assert request.duration == 20
    
    # Test duration constraints
    with pytest.raises(ValidationError):
        ActivityRequest(topic="Test", duration=200)  # Too long
    
    with pytest.raises(ValidationError):
        ActivityRequest(topic="Test", duration=2)  # Too short