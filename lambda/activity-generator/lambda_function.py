import json
import os
import random
from typing import Dict, List, Optional, Any
import boto3
from datetime import datetime
import httpx
import asyncio

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('TABLE_NAME', 'curriculum-activities'))

class ActivityGenerator:
    def __init__(self):
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        self.templates = {
            "preference_choice": self.generate_preference_choice,
            "compare_contrast": self.generate_compare_contrast,
            "vocabulary_builder": self.generate_vocabulary_builder,
            "sequence_builder": self.generate_sequence_builder,
            "story_response": self.generate_story_response,
            "interactive_game": self.generate_interactive_game,
            "discovery_exploration": self.generate_discovery_exploration
        }
    
    async def generate_activity(self, topic: str, duration: int, 
                               activity_type: Optional[str] = None,
                               context: Optional[str] = None,
                               student_age: Optional[str] = None) -> Dict:
        """Generate a complete, tier_3 quality student-ready activity."""
        
        # Select activity type based on parameters or choose intelligently
        if not activity_type:
            activity_type = self.select_activity_type(topic, duration)
        
        # Generate activity using selected template - ALWAYS aiming for tier_3 quality
        if activity_type in self.templates:
            activity = await self.templates[activity_type](topic, duration, context, student_age)
        else:
            activity = await self.generate_custom_activity(topic, duration, activity_type, context, student_age)
        
        # Add metadata with quality tracking
        activity['metadata'] = {
            'generated_at': datetime.now().isoformat(),
            'topic': topic,
            'duration': f"{duration} minutes",
            'activity_type': activity_type,
            'student_age': student_age or 'unspecified',
            'energy_level': self.determine_energy_level(activity_type),
            'cognitive_stage': self.determine_cognitive_stage(activity_type),
            'quality_status': 'pending_evaluation',  # Will be evaluated by humans
            'quality_tier': None,  # To be assigned by evaluation system (tier_3=best, tier_2=good, tier_1=basic)
            'feedback': None  # To be filled by evaluation system
        }
        
        return activity
    
    def select_activity_type(self, topic: str, duration: int) -> str:
        """Intelligently select activity type based on duration and topic."""
        # Duration-based selection for optimal learning outcomes
        if duration <= 10:
            options = ["vocabulary_builder", "preference_choice", "interactive_game"]
        elif duration <= 20:
            options = ["compare_contrast", "sequence_builder", "story_response"]
        else:
            options = ["discovery_exploration", "project_based"]
        
        # Topic-based enhancements (same curriculum approach for all ages)
        if any(keyword in topic.lower() for keyword in ["vocabulary", "words", "language"]):
            if "vocabulary_builder" not in options:
                options.append("vocabulary_builder")
        
        if any(keyword in topic.lower() for keyword in ["story", "narrative", "reading"]):
            if "story_response" not in options:
                options.append("story_response")
        
        return random.choice(options)
    
    def determine_energy_level(self, activity_type: str) -> str:
        """Determine energy level for sequencing."""
        high_energy = ["interactive_game", "discovery_exploration", "movement_activity"]
        low_energy = ["story_response", "reflection", "vocabulary_builder"]
        
        if activity_type in high_energy:
            return "high"
        elif activity_type in low_energy:
            return "low"
        return "medium"
    
    def determine_cognitive_stage(self, activity_type: str) -> str:
        """Determine cognitive stage for progression."""
        introduce = ["vocabulary_builder", "discovery_exploration"]
        practice = ["preference_choice", "interactive_game", "sequence_builder"]
        apply = ["story_response", "compare_contrast", "project_based"]
        
        if activity_type in introduce:
            return "introduce"
        elif activity_type in practice:
            return "practice"
        elif activity_type in apply:
            return "apply"
        return "practice"
    
    async def generate_preference_choice(self, topic: str, duration: int, 
                                        context: Optional[str], student_age: Optional[str]) -> Dict:
        """Generate a tier_3 preference choice activity like the example."""
        
        age_note = f" (content adapted for {student_age} learners)" if student_age else ""
        
        prompt = f"""
        Create a single, focused preference choice ACTIVITY{age_note} about {topic}.
        Duration: {duration} minutes
        Context: {context or 'Online 1-on-1 teaching'}
        
        CRITICAL: Create ONE focused activity component, not a full lesson. Follow this EXACT structure:
        
        ACTIVITY STRUCTURE:
        1. Title: "All About Me: My Favorite [aspect of {topic}]"
        2. Vocabulary Section: 9 items related to {topic} in a 3x3 grid
        3. Practice Section: 5 "this or that" preference questions using the vocabulary
        
        VOCABULARY SECTION:
        - Display exactly 9 vocabulary items in a visual grid
        - Each item should have: emoji/icon + word label
        - Items must be directly related to {topic}
        - Keep labels simple and clear
        
        PRACTICE SECTION:
        - Instructions: "Look at the two choices and say each one out loud. Then say which one you prefer."
        - Example: "For example: [Item1] or [Item2]? I prefer [Item1]."
        - Create exactly 5 preference questions using emojis from the vocabulary
        - Format: "🎯 or 🎯? _________________________."
        - Each question uses different vocabulary items
        
        Output as JSON with this EXACT structure:
        {{
            "activity_type": "preference_choice",
            "title": "All About Me: My Favorite [topic aspect]",
            "vocabulary_section": {{
                "items": [
                    {{"emoji": "🎯", "word": "word1"}},
                    {{"emoji": "🎯", "word": "word2"}},
                    ... (exactly 9 items)
                ]
            }},
            "practice_section": {{
                "instructions": "Look at the two choices and say each one out loud. Then say which one you prefer.",
                "example": "For example: (Word1) 🎯 or (Word2) 🎯? I prefer Word1.",
                "questions": [
                    "🎯 or 🎯? _________________________.",
                    ... (exactly 5 questions)
                ]
            }},
            "teacher_notes": "Simple activity for preference practice using {topic} vocabulary",
            "estimated_time": "{duration} minutes"
        }}
        
        This is a SINGLE activity component, not a lesson. Keep it simple, focused, and reusable.
        """
        
        response = await self.call_claude(prompt)
        return json.loads(response)
    
    async def generate_vocabulary_builder(self, topic: str, duration: int,
                                         context: Optional[str], student_age: Optional[str]) -> Dict:
        """Generate a tier_3 vocabulary building activity."""
        
        age_note = f" (content adapted for {student_age} learners)" if student_age else ""
        
        prompt = f"""
        Create a complete, tier_3 quality vocabulary building activity{age_note}.
        Topic: {topic}
        Duration: {duration} minutes
        Context: {context or 'Online 1-on-1 teaching'}
        
        CRITICAL: This must be tier_3 quality - systematic, scaffolded, and highly engaging.
        
        Generate 2-3 slides that systematically teach and practice vocabulary:
        
        SLIDE 1 - Vocabulary Introduction:
        - Present 6-8 key vocabulary words with clear visual support
        - Include pronunciation guides for challenging words
        - Use simple, memorable definitions with examples
        - Interactive elements to maintain engagement
        
        SLIDE 2 - Guided Practice:
        - Create interactive practice using the vocabulary
        - Include: matching, categorization, or context clues
        - Provide clear examples and scaffolding
        - Multiple practice opportunities
        
        SLIDE 3 (if duration > 10 min) - Application:
        - Students use vocabulary in meaningful contexts
        - Provide sentence frames and word banks for support
        - Personal connection opportunities
        
        Output as structured JSON with engaging, student-facing content.
        All instructions should be written FOR the student with tier_3 clarity.
        """
        
        response = await self.call_claude(prompt)
        return json.loads(response)
    
    async def generate_compare_contrast(self, topic: str, duration: int,
                                       context: Optional[str], student_age: Optional[str]) -> Dict:
        """Generate a tier_3 compare and contrast activity."""
        
        age_note = f" (content adapted for {student_age} learners)" if student_age else ""
        
        prompt = f"""
        Create a complete, tier_3 quality compare and contrast activity{age_note}.
        Topic: {topic}
        Duration: {duration} minutes
        Context: {context or 'Online 1-on-1 teaching'}
        
        CRITICAL: This must be tier_3 quality - clear structure, engaging visuals, systematic thinking.
        
        Structure for excellence:
        - Slide 1: Visual introduction to two compelling things being compared
        - Slide 2: Finding similarities with guided discovery prompts
        - Slide 3: Finding differences with structured thinking support
        - Include appropriate sentence frames and thinking tools
        - Visual organizers and interactive elements
        
        Make it highly visual, interactive, and cognitively engaging.
        Output as structured JSON with tier_3 pedagogical design.
        """
        
        response = await self.call_claude(prompt)
        return json.loads(response)
    
    async def generate_sequence_builder(self, topic: str, duration: int,
                                       context: Optional[str], student_age: Optional[str]) -> Dict:
        """Generate a tier_3 sequencing activity."""
        
        age_note = f" (content adapted for {student_age} learners)" if student_age else ""
        
        prompt = f"""
        Create a tier_3 quality step-by-step sequencing activity{age_note}.
        Topic: {topic}
        Duration: {duration} minutes
        Context: {context or 'Online 1-on-1 teaching'}
        
        CRITICAL: This must be tier_3 quality - logical progression, clear scaffolding, engaging practice.
        
        Include for excellence:
        - Clear, logical steps to arrange in meaningful order
        - Strategic use of transition words (first, next, then, finally)
        - Strong visual support for each step
        - Multiple opportunities to practice sequencing
        - Interactive elements and student engagement strategies
        - Real-world connections
        
        Output as structured JSON with tier_3 instructional design.
        """
        
        response = await self.call_claude(prompt)
        return json.loads(response)
    
    async def generate_story_response(self, topic: str, duration: int,
                                     context: Optional[str], student_age: Optional[str]) -> Dict:
        """Generate a tier_3 story response activity."""
        
        age_note = f" (content adapted for {student_age} learners)" if student_age else ""
        
        prompt = f"""
        Create a tier_3 quality story-based response activity{age_note}.
        Topic: {topic}
        Duration: {duration} minutes
        Context: {context or 'Online 1-on-1 teaching'}
        
        CRITICAL: This must be tier_3 quality - compelling story, thoughtful questions, meaningful connections.
        
        Structure for excellence:
        - Slide 1: Engaging story prompt or scenario (rich visuals + compelling text)
        - Slide 2: Thoughtful comprehension questions with strategic scaffolding
        - Slide 3: Personal connection and critical thinking activities
        
        Include sophisticated sentence starters, word banks, and thinking prompts.
        Ensure high engagement and deep learning opportunities.
        Output as structured JSON with tier_3 narrative design.
        """
        
        response = await self.call_claude(prompt)
        return json.loads(response)
    
    async def generate_interactive_game(self, topic: str, duration: int,
                                       context: Optional[str], student_age: Optional[str]) -> Dict:
        """Generate a tier_3 interactive game activity."""
        
        age_note = f" (content adapted for {student_age} players)" if student_age else ""
        
        prompt = f"""
        Create a tier_3 quality interactive, game-based learning activity{age_note}.
        Topic: {topic}
        Duration: {duration} minutes
        Context: {context or 'Online 1-on-1 teaching'}
        
        CRITICAL: This must be tier_3 quality - crystal clear rules, high engagement, solid learning.
        
        The game should achieve excellence through:
        - Crystal clear, simple rules that promote success
        - Meaningful practice of topic content
        - Perfect adaptation for 1-on-1 online setting
        - Multiple engaging rounds with progression
        - Fun format that maintains educational focus
        - Built-in assessment opportunities
        
        Examples: Advanced memory games, strategic Would You Rather, investigative 20 Questions, 
        topic-based Simon Says, or custom game formats.
        
        Output as structured JSON with complete tier_3 game design and implementation.
        """
        
        response = await self.call_claude(prompt)
        return json.loads(response)
    
    async def generate_discovery_exploration(self, topic: str, duration: int,
                                            context: Optional[str], student_age: Optional[str]) -> Dict:
        """Generate a tier_3 discovery/exploration activity."""
        
        age_note = f" (content adapted for {student_age} explorers)" if student_age else ""
        
        prompt = f"""
        Create a tier_3 quality discovery and exploration activity{age_note}.
        Topic: {topic}
        Duration: {duration} minutes
        Context: {context or 'Online 1-on-1 teaching'}
        
        CRITICAL: This must be tier_3 quality - compelling mystery, scaffolded inquiry, meaningful discovery.
        
        Structure for excellent inquiry learning:
        - Slide 1: Captivating introduction with intriguing mystery or essential question
        - Slide 2-3: Strategic guided exploration with carefully sequenced clues and information
        - Slide 4: Synthesis and celebration of discoveries with extension opportunities
        
        Make it genuinely inquiry-based, student-driven, and intellectually stimulating.
        Include think-alouds, hypothesis formation, and evidence evaluation.
        Output as structured JSON with tier_3 inquiry design.
        """
        
        response = await self.call_claude(prompt)
        return json.loads(response)
    
    async def generate_custom_activity(self, topic: str, duration: int,
                                      activity_type: str, context: Optional[str],
                                      student_age: Optional[str]) -> Dict:
        """Generate a tier_3 custom activity based on specific type request."""
        
        age_note = f" (content adapted for {student_age} learners)" if student_age else ""
        
        prompt = f"""
        Create a complete, tier_3 quality {activity_type} activity{age_note}.
        Topic: {topic}
        Duration: {duration} minutes
        Context: {context or 'Online 1-on-1 teaching'}
        
        CRITICAL: This must be tier_3 quality - exceptional design, clear execution, high engagement.
        
        Generate appropriate number of slides (typically 2-4) with tier_3 features:
        - Crystal clear student-facing instructions
        - Highly engaging content with developmental appropriateness
        - Interactive elements that promote active learning
        - Comprehensive support materials (word banks, sentence frames, examples)
        - Strategic scaffolding and differentiation opportunities
        
        Output as structured JSON with complete tier_3 content for each slide.
        Optimize for excellence in 1-on-1 online teaching environment.
        """
        
        response = await self.call_claude(prompt)
        return json.loads(response)
    
    async def call_claude(self, prompt: str) -> str:
        """Make API call to Claude."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 4000,
                    "messages": [{
                        "role": "user",
                        "content": prompt
                    }],
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['content'][0]['text']
            else:
                raise Exception(f"API call failed: {response.text}")

async def save_activity(activity: Dict) -> str:
    """Save activity to DynamoDB for reuse and quality tracking."""
    activity_id = f"act_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
    
    item = {
        'activity_id': activity_id,
        'created_at': datetime.now().isoformat(),
        'activity_data': activity,
        'usage_count': 0,
        'quality_rating': None,  # For human quality evaluation
        'teacher_feedback': None,  # For teacher feedback collection
        'topic': activity['metadata']['topic'],
        'student_age': activity['metadata']['student_age'],
        'activity_type': activity['metadata']['activity_type'],
        'duration': activity['metadata']['duration'],
        'quality_status': activity['metadata']['quality_status'],
        'quality_tier': activity['metadata']['quality_tier']
    }
    
    table.put_item(Item=item)
    return activity_id

def handler(event, context):
    """AWS Lambda handler for activity generation."""
    return asyncio.run(async_handler(event, context))

async def async_handler(event, context):
    """Async handler for activity generation."""
    
    # Parse request
    body = json.loads(event.get('body', '{}'))
    
    topic = body.get('topic')
    duration = body.get('duration', 15)  # Default 15 minutes
    activity_type = body.get('activity_type')
    context_info = body.get('context')
    student_age = body.get('student_age')  # Optional for age-appropriate content
    
    if not topic:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing required parameter: topic'})
        }
    
    try:
        # Generate activity
        generator = ActivityGenerator()
        activity = await generator.generate_activity(
            topic=topic,
            duration=duration,
            activity_type=activity_type,
            context=context_info,
            student_age=student_age
        )
        
        # Save to database
        activity_id = await save_activity(activity)
        activity['activity_id'] = activity_id
        
        return {
            'statusCode': 200,
            'body': json.dumps(activity)
        }
        
    except Exception as e:
        print(f"Error generating activity: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Failed to generate activity: {str(e)}'})
        }

# For local testing  
if __name__ == "__main__":
    test_event = {
        'body': json.dumps({
            'topic': 'Food and Drinks',
            'student_age': 'adult',
            'duration': 15,
            'activity_type': 'preference_choice'
        })
    }
    
    result = asyncio.run(handler(test_event, None))
    print(json.dumps(json.loads(result['body']), indent=2))