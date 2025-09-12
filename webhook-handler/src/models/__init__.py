"""Data models for the webhook handler."""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class ActionType(str, Enum):
    """Trello webhook action types."""
    COMMENT_CARD = "commentCard"
    UPDATE_CARD = "updateCard"
    CREATE_CARD = "createCard"


class FeedbackType(str, Enum):
    """Types of feedback for lesson plans."""
    LIKE = "like"
    DISLIKE = "dislike"
    IMPROVE = "improve"
    RATING = "rating"


class Card(BaseModel):
    """Trello card model."""
    id: str
    name: str
    desc: Optional[str] = ""
    idBoard: Optional[str] = None
    idList: Optional[str] = None
    
    class Config:
        extra = "allow"


class ActionData(BaseModel):
    """Trello action data model."""
    text: Optional[str] = None
    card: Optional[Card] = None
    listAfter: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"


class MemberCreator(BaseModel):
    """Trello member who created the action."""
    username: Optional[str] = None
    fullName: Optional[str] = None
    
    class Config:
        extra = "allow"


class WebhookAction(BaseModel):
    """Trello webhook action model."""
    type: ActionType
    data: ActionData
    memberCreator: Optional[MemberCreator] = None
    date: Optional[datetime] = None
    
    class Config:
        extra = "allow"


class WebhookPayload(BaseModel):
    """Complete webhook payload from Trello."""
    action: WebhookAction
    
    class Config:
        extra = "allow"


class LessonPlanFeedback(BaseModel):
    """Feedback for a lesson plan."""
    lesson_plan_id: str
    feedback_type: FeedbackType
    feedback_text: str
    rating: Optional[int] = Field(None, ge=1, le=5)
    source: str
    
    @validator('rating')
    def rating_required_for_rating_type(cls, v, values):
        if values.get('feedback_type') == FeedbackType.RATING and v is None:
            raise ValueError('Rating value required for rating feedback type')
        return v


class ActivityRequest(BaseModel):
    """Request for activity generation."""
    topic: str
    grade_level: str = "3"
    duration: int = Field(15, ge=5, le=120)
    activity_type: Optional[str] = None
    context: Optional[str] = Field(None, max_length=500)


class FrameworkData(BaseModel):
    """Framework data structure."""
    framework_name: str
    description: Optional[str] = None
    target_level: str = "A1-A2"
    framework_data: Dict[str, Any]
    
    class Config:
        extra = "allow"


class LambdaResponse(BaseModel):
    """Standard Lambda response format."""
    statusCode: int
    body: str
    headers: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Lambda response dictionary."""
        response = {
            "statusCode": self.statusCode,
            "body": self.body
        }
        if self.headers:
            response["headers"] = self.headers
        return response