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
    
    async def generate_activity(self, topic: str, grade_level: str, duration: int, 
                               activity_type: Optional[str] = None,
                               context: Optional[str] = None) -> Dict:
        """Generate a complete, student-ready activity."""
        
        # Select activity type based on parameters or choose intelligently
        if not activity_type:
            activity_type = self.select_activity_type(topic, grade_level, duration)
        
        # Generate activity using selected template
        if activity_type in self.templates:
            activity = await self.templates[activity_type](topic, grade_level, duration, context)
        else:
            activity = await self.generate_custom_activity(topic, grade_level, duration, activity_type, context)
        
        # Add metadata
        activity['metadata'] = {
            'generated_at': datetime.now().isoformat(),
            'topic': topic,
            'grade_level': grade_level,
            'duration': f"{duration} minutes",
            'activity_type': activity_type,
            'energy_level': self.determine_energy_level(activity_type),
            'cognitive_stage': self.determine_cognitive_stage(activity_type)
        }
        
        return activity
    
    def select_activity_type(self, topic: str, grade_level: str, duration: int) -> str:
        """Intelligently select activity type based on parameters."""
        # Simple logic for now, can be enhanced with ML later
        if duration <= 10:
            options = ["vocabulary_builder", "preference_choice", "interactive_game"]
        elif duration <= 20:
            options = ["compare_contrast", "sequence_builder", "story_response"]
        else:
            options = ["discovery_exploration", "project_based"]
        
        # For younger grades, prefer more visual and interactive
        if grade_level in ["K", "1", "2", "3"]:
            if "preference_choice" not in options:
                options.append("preference_choice")
            if "interactive_game" not in options:
                options.append("interactive_game")
        
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
    
    async def generate_preference_choice(self, topic: str, grade_level: str, 
                                        duration: int, context: Optional[str]) -> Dict:
        """Generate a preference choice activity like the example."""
        
        prompt = f"""
        Create a complete, student-ready preference choice activity for {grade_level} grade students.
        Topic: {topic}
        Duration: {duration} minutes
        Context: {context or 'General classroom setting'}
        
        Generate exactly 2 slides of content following this structure:
        
        SLIDE 1 - Vocabulary Introduction:
        - Title: "All About Me: My Favorite [topic aspect]..."
        - Include 6-9 vocabulary items related to {topic}
        - Each item needs a clear, simple label
        - Items should be common and age-appropriate
        
        SLIDE 2 - Preference Practice:
        - Same title as Slide 1
        - Create 5 "this or that" questions using the vocabulary
        - Include clear instructions: "Look at the two choices and say each one out loud. Then say which one you prefer."
        - Provide example: "For example: [Item1] or [Item2]? I prefer [Item1]."
        - Each question should have a response line for student answers
        
        Output as JSON with this structure:
        {{
            "title": "Activity title",
            "slides": [
                {{
                    "slide_number": 1,
                    "type": "vocabulary_introduction",
                    "title": "Slide title",
                    "content": {{
                        "instructions": "Teacher instructions",
                        "vocabulary_items": ["item1", "item2", ...],
                        "activity": "What students see/do"
                    }},
                    "teacher_notes": "Private notes for teacher",
                    "timing": "X minutes"
                }},
                {{
                    "slide_number": 2,
                    "type": "guided_practice",
                    "title": "Slide title",
                    "content": {{
                        "instructions": "Student instructions with example",
                        "questions": [
                            "Question 1: [choice1] or [choice2]? _______",
                            ...
                        ]
                    }},
                    "teacher_notes": "Private notes",
                    "timing": "X minutes"
                }}
            ]
        }}
        
        Make all content student-facing and age-appropriate for {grade_level} grade.
        """
        
        response = await self.call_claude(prompt)
        return json.loads(response)
    
    async def generate_vocabulary_builder(self, topic: str, grade_level: str,
                                         duration: int, context: Optional[str]) -> Dict:
        """Generate a vocabulary building activity."""
        
        prompt = f"""
        Create a complete, student-ready vocabulary building activity for {grade_level} grade students.
        Topic: {topic}
        Duration: {duration} minutes
        
        Generate 2-3 slides that teach and practice vocabulary:
        
        SLIDE 1 - Introduction:
        - Present 6-8 key vocabulary words with visual descriptions
        - Include pronunciation guides for difficult words
        - Use simple, clear definitions
        
        SLIDE 2 - Practice:
        - Create interactive practice using the vocabulary
        - Could include: matching, fill-in-the-blank, or categorization
        - Provide clear examples
        
        SLIDE 3 (if duration > 10 min) - Production:
        - Students use vocabulary in sentences or short responses
        - Provide sentence frames for support
        
        Output as structured JSON with full student-facing content.
        All instructions should be written FOR the student, not about them.
        """
        
        response = await self.call_claude(prompt)
        return json.loads(response)
    
    async def generate_compare_contrast(self, topic: str, grade_level: str,
                                       duration: int, context: Optional[str]) -> Dict:
        """Generate a compare and contrast activity."""
        
        prompt = f"""
        Create a complete compare and contrast activity for {grade_level} grade students.
        Topic: {topic}
        Duration: {duration} minutes
        
        Structure:
        - Slide 1: Introduction to two things being compared
        - Slide 2: Finding similarities (with guided prompts)
        - Slide 3: Finding differences (with guided prompts)
        - Include sentence frames appropriate for grade level
        
        Make it visual and interactive. Output as structured JSON.
        """
        
        response = await self.call_claude(prompt)
        return json.loads(response)
    
    async def generate_sequence_builder(self, topic: str, grade_level: str,
                                       duration: int, context: Optional[str]) -> Dict:
        """Generate a sequencing activity."""
        
        prompt = f"""
        Create a step-by-step sequencing activity for {grade_level} grade students.
        Topic: {topic}
        Duration: {duration} minutes
        
        Include:
        - Clear steps to arrange in order
        - Transition words (first, next, then, finally)
        - Visual support for each step
        - Practice putting things in correct sequence
        
        Output as structured JSON with complete content.
        """
        
        response = await self.call_claude(prompt)
        return json.loads(response)
    
    async def generate_story_response(self, topic: str, grade_level: str,
                                     duration: int, context: Optional[str]) -> Dict:
        """Generate a story response activity."""
        
        prompt = f"""
        Create a story-based response activity for {grade_level} grade students.
        Topic: {topic}
        Duration: {duration} minutes
        
        Structure:
        - Slide 1: Story prompt or scenario (visual + text)
        - Slide 2: Comprehension questions with support
        - Slide 3: Personal connection/response activity
        
        Include sentence starters and word banks for support.
        Output as structured JSON.
        """
        
        response = await self.call_claude(prompt)
        return json.loads(response)
    
    async def generate_interactive_game(self, topic: str, grade_level: str,
                                       duration: int, context: Optional[str]) -> Dict:
        """Generate an interactive game activity."""
        
        prompt = f"""
        Create an interactive, game-based learning activity for {grade_level} grade students.
        Topic: {topic}
        Duration: {duration} minutes
        
        The game should:
        - Have clear, simple rules
        - Practice the topic content
        - Be playable in 1-on-1 online setting
        - Include multiple rounds or turns
        - Have a fun, engaging format
        
        Examples: Memory game, Would You Rather, 20 Questions, Simon Says with topic vocabulary
        
        Output as structured JSON with complete game content and rules.
        """
        
        response = await self.call_claude(prompt)
        return json.loads(response)
    
    async def generate_discovery_exploration(self, topic: str, grade_level: str,
                                            duration: int, context: Optional[str]) -> Dict:
        """Generate a discovery/exploration activity."""
        
        prompt = f"""
        Create a discovery and exploration activity for {grade_level} grade students.
        Topic: {topic}
        Duration: {duration} minutes
        
        Structure:
        - Slide 1: Introduction with a mystery or question to explore
        - Slide 2-3: Guided exploration with clues or information
        - Slide 4: Discovery synthesis and sharing findings
        
        Make it inquiry-based and student-driven.
        Output as structured JSON.
        """
        
        response = await self.call_claude(prompt)
        return json.loads(response)
    
    async def generate_custom_activity(self, topic: str, grade_level: str,
                                      duration: int, activity_type: str,
                                      context: Optional[str]) -> Dict:
        """Generate a custom activity based on specific type request."""
        
        prompt = f"""
        Create a complete, student-ready {activity_type} activity for {grade_level} grade students.
        Topic: {topic}
        Duration: {duration} minutes
        Context: {context or 'General classroom setting'}
        
        Generate appropriate number of slides (typically 2-4) with:
        - Clear student-facing instructions
        - Engaging content appropriate for age level
        - Interactive elements
        - Support materials (word banks, sentence frames, examples)
        
        Output as structured JSON with full content for each slide.
        Remember: This is for 1-on-1 online teaching.
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
    """Save activity to DynamoDB for reuse."""
    activity_id = f"act_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
    
    item = {
        'activity_id': activity_id,
        'created_at': datetime.now().isoformat(),
        'activity_data': activity,
        'usage_count': 0,
        'rating': None,
        'topic': activity['metadata']['topic'],
        'grade_level': activity['metadata']['grade_level'],
        'activity_type': activity['metadata']['activity_type'],
        'duration': activity['metadata']['duration']
    }
    
    table.put_item(Item=item)
    return activity_id

async def handler(event, context):
    """Lambda handler for activity generation."""
    
    # Parse request
    body = json.loads(event.get('body', '{}'))
    
    topic = body.get('topic')
    grade_level = body.get('grade_level')
    duration = body.get('duration', 15)  # Default 15 minutes
    activity_type = body.get('activity_type')
    context_info = body.get('context')
    
    if not topic or not grade_level:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing required parameters: topic and grade_level'})
        }
    
    try:
        # Generate activity
        generator = ActivityGenerator()
        activity = await generator.generate_activity(
            topic=topic,
            grade_level=grade_level,
            duration=duration,
            activity_type=activity_type,
            context=context_info
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
            'grade_level': '3',
            'duration': 15,
            'activity_type': 'preference_choice'
        })
    }
    
    result = asyncio.run(handler(test_event, None))
    print(json.dumps(json.loads(result['body']), indent=2))