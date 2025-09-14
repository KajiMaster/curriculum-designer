"""Business logic services."""

import logging
import re
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from ..config import get_config
from ..models import LessonPlanFeedback, FeedbackType, ActivityRequest, FrameworkData
from ..clients import get_trello_client, get_openai_client, get_mcp_client
from ..utils import ErrorBoundary

logger = logging.getLogger(__name__)
config = get_config()


class AIService:
    """Service for AI-related operations."""
    
    def __init__(self):
        self.openai_client = get_openai_client()
    
    async def get_response(self, prompt: str, max_tokens: int = None) -> str:
        """Get AI response for general assistance."""
        return await self.openai_client.get_response(prompt, max_tokens)
    
    async def suggest_activities(self, student_level: str, focus: str, duration: int) -> str:
        """Suggest activities for a lesson."""
        prompt = f"""
        Suggest 3-4 English learning activities for:
        - Student level: {student_level}
        - Focus area: {focus}  
        - Total duration: {duration} minutes
        
        For each activity, provide:
        - Name and brief description
        - Duration (in minutes)
        - Materials needed
        - Learning objectives
        
        Format as a clear, practical list.
        """
        return await self.openai_client.get_response(prompt)
    
    async def create_lesson_plan(self, activities_text: str, duration: int) -> str:
        """Create optimized lesson plan."""
        prompt = f"""
        Create a {duration}-minute lesson plan using these activities:
        {activities_text}
        
        Organize into:
        1. Warm-up (5-10 minutes)
        2. Main activities (with timing)
        3. Wrap-up (5 minutes)
        
        Include transitions and timing for each section.
        """
        return await self.openai_client.get_response(prompt)
    
    async def analyze_activity(self, activity_name: str, description: str) -> str:
        """Analyze an activity and suggest improvements."""
        prompt = f"""
        Analyze this English teaching activity:
        
        Activity: {activity_name}
        Description: {description}
        
        Provide:
        1. Strengths of this activity
        2. Potential improvements
        3. Variations for different levels
        4. What to teach before/after this
        """
        return await self.openai_client.get_response(prompt, max_tokens=600)


class FeedbackService:
    """Service for handling lesson plan feedback."""
    
    def __init__(self):
        self.mcp_client = get_mcp_client()
    
    def parse_feedback_from_comment(self, comment_text: str, card_details: Dict[str, Any]) -> Optional[LessonPlanFeedback]:
        """Parse feedback from a Trello comment."""
        # Extract lesson plan ID from card description
        lesson_plan_id = self._extract_lesson_plan_id(card_details)
        comment_lower = comment_text.lower()
        
        # Parse different types of feedback
        if "like:" in comment_lower or "@ai like" in comment_lower:
            feedback_text = self._extract_feedback_text(comment_text, ["like:", "@ai like"])
            return LessonPlanFeedback(
                lesson_plan_id=lesson_plan_id,
                feedback_type=FeedbackType.LIKE,
                feedback_text=feedback_text,
                source=f"trello_comment:{card_details.get('id', '')}"
            )
        
        elif "dislike:" in comment_lower or "@ai dislike" in comment_lower:
            feedback_text = self._extract_feedback_text(comment_text, ["dislike:", "@ai dislike"])
            return LessonPlanFeedback(
                lesson_plan_id=lesson_plan_id,
                feedback_type=FeedbackType.DISLIKE,
                feedback_text=feedback_text,
                source=f"trello_comment:{card_details.get('id', '')}"
            )
        
        elif "improve:" in comment_lower or "@ai improve" in comment_lower:
            feedback_text = self._extract_feedback_text(comment_text, ["improve:", "@ai improve"])
            return LessonPlanFeedback(
                lesson_plan_id=lesson_plan_id,
                feedback_type=FeedbackType.IMPROVE,
                feedback_text=feedback_text,
                source=f"trello_comment:{card_details.get('id', '')}"
            )
        
        elif "rating:" in comment_lower:
            rating_match = re.search(r'rating:\s*(\d+)(?:/\d+)?', comment_text, re.IGNORECASE)
            if rating_match:
                rating = int(rating_match.group(1))
                return LessonPlanFeedback(
                    lesson_plan_id=lesson_plan_id,
                    feedback_type=FeedbackType.RATING,
                    feedback_text=comment_text,
                    rating=rating,
                    source=f"trello_comment:{card_details.get('id', '')}"
                )
        
        return None
    
    def _extract_lesson_plan_id(self, card_details: Dict[str, Any]) -> str:
        """Extract lesson plan ID from card description."""
        card_desc = card_details.get("desc", "")
        
        # Try different patterns
        patterns = [
            r'\*\*Plan ID:\*\* (\w+)',
            r'Plan ID:\*\* (\w+)',
            r'Stored in DynamoDB as: (\w+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, card_desc)
            if match:
                return match.group(1)
        
        # Fallback: use card name or ID
        return card_details.get("name", card_details.get("id", "")).replace(" ", "_").lower()
    
    def _extract_feedback_text(self, comment_text: str, markers: List[str]) -> str:
        """Extract feedback text after markers."""
        for marker in markers:
            if marker in comment_text:
                return comment_text.split(marker, 1)[1].strip()
        return comment_text.strip()
    
    async def submit_feedback(self, feedback: LessonPlanFeedback) -> Optional[Dict[str, Any]]:
        """Submit feedback to the MCP API."""
        return await self.mcp_client.submit_feedback(feedback)


class FrameworkService:
    """Service for managing curriculum frameworks."""
    
    def __init__(self):
        self.trello_client = get_trello_client()
        self.ai_service = AIService()
        self._dynamodb = None
    
    @property
    def dynamodb(self):
        """Lazy-loaded DynamoDB resource."""
        if self._dynamodb is None:
            self._dynamodb = boto3.resource('dynamodb', region_name=config.AWS_REGION)
        return self._dynamodb
    
    @property
    def table(self):
        """Get the frameworks table."""
        return self.dynamodb.Table(config.FRAMEWORKS_TABLE)
    
    async def save_framework(self, framework_data: Dict[str, Any], framework_name: str, board_id: str) -> str:
        """Save a framework to DynamoDB."""
        with ErrorBoundary("save_framework to DynamoDB", logger):
            framework_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            item = {
                'framework_id': framework_id,
                'board_id': board_id,
                'framework_name': framework_name,
                'framework_data': framework_data,
                'metadata': {'source': 'trello_card'},
                'created_at': timestamp,
                'updated_at': timestamp,
                'version': 1,
                'is_active': True
            }
            
            self.table.put_item(Item=item)
            logger.info(f"Framework saved with ID: {framework_id}")
            return framework_id
    
    def get_framework(self, framework_id: str) -> Optional[Dict[str, Any]]:
        """Get a framework from DynamoDB."""
        with ErrorBoundary(f"get_framework {framework_id}", logger):
            response = self.table.get_item(Key={'framework_id': framework_id})
            return response.get('Item')
    
    def list_frameworks(self, board_id: str) -> List[Dict[str, Any]]:
        """List frameworks for a board."""
        with ErrorBoundary(f"list_frameworks for board {board_id}", logger):
            # Note: In production, consider using a GSI for better performance
            response = self.table.scan(
                FilterExpression='board_id = :bid',
                ExpressionAttributeValues={':bid': board_id}
            )
            return response.get('Items', [])
    
    async def generate_framework_variants(
        self, 
        framework_id: str, 
        framework_data: Dict[str, Any], 
        num_variants: int, 
        board_id: str
    ) -> List[str]:
        """Generate framework variants and create Trello cards."""
        with ErrorBoundary("generate_framework_variants", logger):
            # Get or create variants list
            variants_list_id = await self.trello_client.get_or_create_list(board_id, "Framework Variants")
            if not variants_list_id:
                raise ValueError("Could not create Framework Variants list")
            
            themes = ['Technology & Innovation', 'Travel & Culture', 'Business Communication', 
                     'Environmental Issues', 'Health & Wellness', 'Arts & Entertainment']
            levels = ['A2', 'B1', 'B2', 'C1']
            
            created_cards = []
            
            for i in range(min(num_variants, len(themes))):
                theme = themes[i % len(themes)]
                level = levels[i % len(levels)]
                
                # Generate detailed variant with AI
                prompt = self._build_variant_prompt(framework_data, theme, level)
                ai_response = await self.ai_service.get_response(prompt, max_tokens=3000)
                
                # Create card
                variant_name = f"{framework_data.get('framework_name', 'Framework')} - {theme} ({level})"
                card_id = await self.trello_client.create_card(
                    variants_list_id, 
                    variant_name, 
                    ai_response
                )
                
                if card_id:
                    created_cards.append(card_id)
                    logger.info(f"Created variant card: {variant_name}")
            
            return created_cards
    
    def _build_variant_prompt(self, framework_data: Dict[str, Any], theme: str, level: str) -> str:
        """Build prompt for variant generation."""
        return f"""
Create a detailed 2-hour English class framework based on the pedagogical approach from this original framework.

Base Framework: {framework_data.get('framework_name', 'Framework')}
Original Focus: {framework_data.get('description', '')}
Original Level: {framework_data.get('target_level', 'A1-A2')}

NEW VARIANT PARAMETERS:
- Theme: {theme}
- Target Level: {level}
- Duration: 2 hours (120 minutes)

Generate a COMPLETE detailed framework following this exact structure:

# Class Title: [Framework Name] - {theme} ({level})

## Class Objectives:
- [3-4 specific learning objectives related to {theme}]

## Warm-up Activity (15-20 minutes)
**Format:** Multiple choice with "None, I..." completion
**Instructions:** Look at two options and answer, or say "None, I..." and complete

Create 8-10 theme-specific questions with:
- Question about {theme} topic
- Two emoji options  
- Model answer using "None, I..."

## Target Vocabulary (theme-specific)
🟦 **Verbs (with -ing):** [8 verbs related to {theme}]
🟩 **Adjectives of opinion:** [8 adjectives: fun, boring, exciting, challenging, etc.]
🟥 **Connectors:** because, and, but
🟨 **Theme nouns:** [6-8 nouns specific to {theme}]

## Grammar Focus (20-25 minutes)
### Verbs of Preference + -ing + Connectors
**Focus:** like/love/hate/enjoy + verb + -ing + connectors

## Communicative Practice (30-40 minutes)
### Speaking Challenge
**Prompts:**
- "Tell me 3 {theme} things you enjoy and why"
- "Tell me something about {theme} you hate and explain why"

## Extension Activities
### Idiomatic Expressions: "Piece of Cake" / "Not My Cup of Tea"
**Application:** Use expressions with {theme} activities

## Mini Wrap-Up and Assessment (10-15 minutes)
**Review questions:**
1. Which verbs do we use followed by -ing when talking about likes and dislikes?
2. How would you describe {theme} activities using opinion adjectives?
3. Say something about {theme} that your family member likes/doesn't like

**Materials needed:** [Specific materials for {theme} activities]
**Assessment criteria:** [4-5 specific criteria for this {theme} class]

Make it practical, engaging, and immediately usable by teachers. Include emojis and specific examples throughout.
        """


class ActivityService:
    """Service for activity generation and management."""
    
    def __init__(self):
        self.trello_client = get_trello_client()
        self._lambda_client = None
    
    @property
    def lambda_client(self):
        """Lazy-loaded Lambda client."""
        if self._lambda_client is None:
            self._lambda_client = boto3.client('lambda', region_name=config.AWS_REGION)
        return self._lambda_client
    
    def parse_activity_request(self, ai_request: str, card_details: Dict[str, Any]) -> ActivityRequest:
        """Parse activity request from AI command."""
        # Extract parameters using regex
        topic_match = re.search(r'"([^"]+)"', ai_request) or re.search(r'topic[:\s]+([^\s,]+)', ai_request)
        level_match = re.search(r'level[:\s]+([^\s,]+)', ai_request) or re.search(r'\b(beginner|elementary|intermediate|upper-intermediate|advanced|a1|a2|b1|b2|c1|c2)\b', ai_request, re.IGNORECASE)
        duration_match = re.search(r'duration[:\s]+(\d+)', ai_request) or re.search(r'(\d+)\s*min', ai_request)
        type_match = re.search(r'type[:\s]+([^\s,]+)', ai_request)
        
        # Get topic from card if not specified
        topic = topic_match.group(1) if topic_match else card_details.get('name', 'English Language Learning')
        
        return ActivityRequest(
            topic=topic,
            esl_level=level_match.group(1) if level_match else "intermediate",
            duration=int(duration_match.group(1)) if duration_match else 15,
            activity_type=type_match.group(1) if type_match else None,
            context=card_details.get('desc', '')[:500] if card_details.get('desc') else None
        )
    
    async def generate_activity(self, request: ActivityRequest) -> Dict[str, Any]:
        """Generate activity using Lambda function."""
        with ErrorBoundary("generate_activity", logger):
            payload = {
                'body': json.dumps(request.dict())
            }
            
            response = self.lambda_client.invoke(
                FunctionName=config.ACTIVITY_GENERATOR_FUNCTION,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                return json.loads(result.get('body', '{}'))
            else:
                error_msg = json.loads(result.get('body', '{}')).get('error', 'Unknown error')
                raise ValueError(f"Activity generation failed: {error_msg}")


# Service instances
def get_ai_service() -> AIService:
    """Get AI service instance."""
    return AIService()


def get_feedback_service() -> FeedbackService:
    """Get feedback service instance."""
    return FeedbackService()


def get_framework_service() -> FrameworkService:
    """Get framework service instance."""
    return FrameworkService()


def get_activity_service() -> ActivityService:
    """Get activity service instance."""
    return ActivityService()