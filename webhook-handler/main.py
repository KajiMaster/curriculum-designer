"""
Minimal Trello AI Webhook Handler
Responds to Trello events with AI assistance
"""

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import httpx
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables for local development
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Curriculum AI Webhook", version="1.0.0")

# Function to get secrets from Parameter Store (Lambda) or environment (local)
def get_secret(param_name_env: str, local_env_var: str) -> str:
    """Get secret from Parameter Store in Lambda or environment variable locally"""
    
    # Check if running in Lambda (AWS environment)
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        import boto3
        ssm = boto3.client('ssm')
        param_name = os.getenv(param_name_env)
        if param_name:
            try:
                response = ssm.get_parameter(Name=param_name, WithDecryption=True)
                return response['Parameter']['Value']
            except Exception as e:
                print(f"Error getting parameter {param_name}: {e}")
                return ""
    
    # Local development - use environment variables
    return os.getenv(local_env_var, "")

# Get credentials
TRELLO_API_KEY = get_secret("TRELLO_API_KEY_PARAM", "TRELLO_API_KEY")
TRELLO_TOKEN = get_secret("TRELLO_TOKEN_PARAM", "TRELLO_TOKEN")
OPENAI_API_KEY = get_secret("OPENAI_API_KEY_PARAM", "OPENAI_API_KEY")
TRELLO_WEBHOOK_SECRET = get_secret("TRELLO_WEBHOOK_SECRET_PARAM", "TRELLO_WEBHOOK_SECRET")

# Trello API base URL
TRELLO_BASE = "https://api.trello.com/1"

class TrelloClient:
    """Simple Trello API client"""
    
    def __init__(self):
        self.session = httpx.AsyncClient()
        self.auth_params = {
            "key": TRELLO_API_KEY,
            "token": TRELLO_TOKEN
        }
    
    async def add_comment(self, card_id: str, text: str):
        """Add comment to a card"""
        url = f"{TRELLO_BASE}/cards/{card_id}/actions/comments"
        data = {"text": text, **self.auth_params}
        
        response = await self.session.post(url, data=data)
        return response.json()
    
    async def get_card(self, card_id: str):
        """Get card details"""
        url = f"{TRELLO_BASE}/cards/{card_id}"
        params = {"fields": "name,desc,labels,list", **self.auth_params}
        
        response = await self.session.get(url, params=params)
        return response.json()
    
    async def create_card(self, list_id: str, name: str, desc: str = ""):
        """Create a new card"""
        url = f"{TRELLO_BASE}/cards"
        data = {
            "idList": list_id,
            "name": name,
            "desc": desc,
            **self.auth_params
        }
        
        response = await self.session.post(url, data=data)
        return response.json()
    
    async def add_checklist(self, card_id: str, name: str, items: List[str]):
        """Add checklist to card"""
        # Create checklist
        url = f"{TRELLO_BASE}/checklists"
        data = {"idCard": card_id, "name": name, **self.auth_params}
        response = await self.session.post(url, data=data)
        checklist = response.json()
        
        # Add items
        for item in items:
            item_url = f"{TRELLO_BASE}/checklists/{checklist['id']}/checkItems"
            item_data = {"name": item, **self.auth_params}
            await self.session.post(item_url, data=item_data)
        
        return checklist
    
    async def move_card(self, card_id: str, list_id: str):
        """Move card to different list"""
        url = f"{TRELLO_BASE}/cards/{card_id}"
        data = {"idList": list_id, **self.auth_params}
        
        response = await self.session.put(url, data=data)
        return response.json()

class AIAssistant:
    """Simple AI assistant for curriculum help"""
    
    def __init__(self):
        self.client = httpx.AsyncClient()
    
    async def get_openai_response(self, prompt: str, max_tokens: int = 500):
        """Get response from OpenAI"""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system", 
                    "content": "You are an English teaching assistant. Help teachers with curriculum planning, activity suggestions, and lesson organization. Be practical and concise."
                },
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        response = await self.client.post(url, headers=headers, json=data)
        result = response.json()
        
        if "choices" in result and result["choices"]:
            return result["choices"][0]["message"]["content"]
        return "Sorry, I couldn't generate a response."
    
    async def suggest_activities(self, student_level: str, focus: str, duration: int):
        """Suggest activities for a lesson"""
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
        return await self.get_openai_response(prompt)
    
    async def create_lesson_plan(self, activities_text: str, duration: int):
        """Create optimized lesson plan"""
        prompt = f"""
        Create a {duration}-minute lesson plan using these activities:
        {activities_text}
        
        Organize into:
        1. Warm-up (5-10 minutes)
        2. Main activities (with timing)
        3. Wrap-up (5 minutes)
        
        Include transitions and timing for each section.
        """
        return await self.get_openai_response(prompt)
    
    async def analyze_activity(self, activity_name: str, description: str):
        """Analyze an activity and suggest improvements"""
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
        return await self.get_openai_response(prompt, max_tokens=600)

# Initialize services
trello = TrelloClient()
ai = AIAssistant()

@app.post("/webhook")
async def handle_webhook(request: Request):
    """Main webhook handler for Trello events"""
    
    try:
        # Get payload
        payload = await request.json()
        action = payload.get("action", {})
        action_type = action.get("type")
        
        print(f"Received webhook: {action_type}")
        
        # Handle different action types
        if action_type == "commentCard":
            await handle_comment(action)
        elif action_type == "updateCard":
            await handle_card_update(action)
        elif action_type == "createCard":
            await handle_card_create(action)
        
        return {"status": "ok", "processed": action_type}
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

async def handle_comment(action):
    """Process comments for AI requests"""
    
    comment_text = action["data"]["text"]
    card = action["data"]["card"]
    card_id = card["id"]
    
    # Check if comment mentions AI
    if "@ai" in comment_text.lower():
        # Extract AI request
        ai_request = comment_text.lower().replace("@ai", "").strip()
        
        # Get card details for context
        card_details = await trello.get_card(card_id)
        
        # Process different types of AI requests
        if "suggest" in ai_request and "activity" in ai_request:
            response = await handle_activity_suggestion(ai_request, card_details)
        elif "lesson plan" in ai_request or "build lesson" in ai_request:
            response = await handle_lesson_planning(ai_request, card_details)
        elif "analyze" in ai_request:
            response = await handle_activity_analysis(card_details)
        elif "alternative" in ai_request:
            response = await handle_find_alternative(card_details)
        else:
            # General AI assistance
            context = f"Card: {card_details.get('name', '')}\nDescription: {card_details.get('desc', '')}"
            prompt = f"Teacher asks: {ai_request}\nContext: {context}"
            response = await ai.get_openai_response(prompt)
        
        # Post AI response as comment
        ai_comment = f"🤖 **AI Assistant:**\n\n{response}"
        await trello.add_comment(card_id, ai_comment)

async def handle_card_update(action):
    """Process card moves and updates"""
    
    data = action["data"]
    card = data["card"]
    
    # Check if card was moved to specific lists
    if "listAfter" in data:
        list_after = data["listAfter"]["name"]
        
        if "This Week" in list_after:
            await handle_schedule_activity(card)
        elif "AI Requests" in list_after:
            await handle_ai_request_card(card)
        elif "Needs Revision" in list_after:
            await handle_revision_request(card)

async def handle_card_create(action):
    """Process newly created cards"""
    
    card = action["data"]["card"]
    card_name = card["name"]
    
    # Check for AI command cards
    if card_name.startswith("🤖 AI:"):
        await process_ai_command_card(card)

async def handle_activity_suggestion(request: str, card_details: Dict):
    """Handle activity suggestion requests"""
    
    # Extract parameters from request
    level_match = re.search(r'(beginner|intermediate|advanced)', request, re.IGNORECASE)
    duration_match = re.search(r'(\d+)\s*min', request)
    
    level = level_match.group(1) if level_match else "intermediate"
    duration = int(duration_match.group(1)) if duration_match else 30
    
    # Get focus from card context
    focus = extract_focus_from_card(card_details)
    
    return await ai.suggest_activities(level, focus, duration)

async def handle_lesson_planning(request: str, card_details: Dict):
    """Handle lesson planning requests"""
    
    duration_match = re.search(r'(\d+)\s*min', request)
    duration = int(duration_match.group(1)) if duration_match else 120
    
    # Use card description as activities context
    activities_text = card_details.get("desc", "")
    
    return await ai.create_lesson_plan(activities_text, duration)

async def handle_activity_analysis(card_details: Dict):
    """Analyze an activity"""
    
    name = card_details.get("name", "")
    description = card_details.get("desc", "")
    
    return await ai.analyze_activity(name, description)

async def handle_find_alternative(card_details: Dict):
    """Find alternative activities"""
    
    name = card_details.get("name", "")
    description = card_details.get("desc", "")
    
    prompt = f"""
    Find 3 alternative activities similar to:
    
    Activity: {name}
    Description: {description}
    
    For each alternative, provide:
    - Activity name
    - Brief description  
    - Why it's a good alternative
    - Any differences in difficulty/focus
    """
    
    return await ai.get_openai_response(prompt, max_tokens=600)

async def handle_schedule_activity(card: Dict):
    """Handle activity scheduled for this week"""
    
    card_id = card["id"]
    
    # Create preparation checklist
    prep_items = [
        "Review activity materials",
        "Check equipment needed", 
        "Prepare handouts/worksheets",
        "Set up learning environment",
        "Review student backgrounds"
    ]
    
    await trello.add_checklist(card_id, "📋 Preparation Checklist", prep_items)
    
    # Add helpful comment
    comment = "🗓️ **Scheduled for This Week**\n\nI've added a preparation checklist. Need any help with materials or setup? Just ask @ai!"
    await trello.add_comment(card_id, comment)

async def process_ai_command_card(card: Dict):
    """Process AI command cards"""
    
    card_name = card["name"]
    card_id = card["id"]
    
    if "Build Lesson" in card_name:
        comment = "🤖 **Lesson Builder Ready**\n\nI'll help build your lesson! Please provide:\n- Student level\n- Duration\n- Focus area\n- Any specific requirements\n\nJust comment with these details!"
        await trello.add_comment(card_id, comment)

def extract_focus_from_card(card_details: Dict) -> str:
    """Extract focus area from card labels or description"""
    
    labels = card_details.get("labels", [])
    
    for label in labels:
        label_name = label.get("name", "").lower()
        if any(skill in label_name for skill in ["grammar", "speaking", "writing", "reading", "business"]):
            return label_name
    
    return "general english"

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "trello": bool(TRELLO_API_KEY and TRELLO_TOKEN),
            "openai": bool(OPENAI_API_KEY)
        }
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Curriculum AI Webhook Handler", "status": "running"}

# AWS Lambda handler
from mangum import Mangum

handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)