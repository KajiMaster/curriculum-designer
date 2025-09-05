"""
Simple Lambda handler for Trello AI Webhook
Responds to Trello events with AI assistance
"""

import json
import os
import httpx
import asyncio
import boto3
import uuid
from datetime import datetime


class SecretsManager:
    """Lazy-load secrets from Parameter Store or environment variables"""
    _instance = None
    _secrets = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_secret(self, param_env: str, fallback_env: str = None) -> str:
        """Get secret from Parameter Store or environment variable"""
        # Check cache first
        if param_env in self._secrets:
            return self._secrets[param_env]

        # Try to get from Parameter Store if in Lambda
        if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
            param_name = os.getenv(param_env, "")
            if param_name:
                try:
                    ssm = boto3.client('ssm', region_name=os.getenv('AWS_REGION', 'us-east-1'))
                    response = ssm.get_parameter(Name=param_name, WithDecryption=True)
                    value = response['Parameter']['Value']
                    self._secrets[param_env] = value
                    return value
                except Exception as e:
                    print(f"Error getting parameter {param_name}: {e}")

        # Fall back to environment variable
        if fallback_env:
            value = os.getenv(fallback_env, "")
            self._secrets[param_env] = value
            return value

        return ""


# Create singleton instance
secrets = SecretsManager()


def get_trello_api_key():
    return secrets.get_secret("TRELLO_API_KEY_PARAM", "TRELLO_API_KEY")


def get_trello_token():
    return secrets.get_secret("TRELLO_TOKEN_PARAM", "TRELLO_TOKEN")


def get_openai_api_key():
    return secrets.get_secret("OPENAI_API_KEY_PARAM", "OPENAI_API_KEY")


def get_webhook_secret():
    return secrets.get_secret("TRELLO_WEBHOOK_SECRET_PARAM", "TRELLO_WEBHOOK_SECRET")


# Trello API base URL
TRELLO_BASE = "https://api.trello.com/1"


class TrelloClient:
    """Simple Trello API client"""

    def __init__(self):
        self.auth_params = {
            "key": get_trello_api_key(),
            "token": get_trello_token()
        }

    async def add_comment(self, card_id: str, text: str):
        """Add comment to a card"""
        url = f"{TRELLO_BASE}/cards/{card_id}/actions/comments"
        data = {"text": text, **self.auth_params}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            return response.json()

    async def get_card(self, card_id: str):
        """Get card details"""
        url = f"{TRELLO_BASE}/cards/{card_id}"
        params = {"fields": "name,desc,labels,list,idBoard", **self.auth_params}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                print(f"Error getting card {card_id}: {response.status_code} - {response.text}")
                return {}
            return response.json()


class AIAssistant:
    """Simple AI assistant for curriculum help"""

    async def get_openai_response(self, prompt: str, max_tokens: int = 500):
        """Get response from OpenAI"""
        openai_key = get_openai_api_key()
        print(f"OpenAI API Key available: {bool(openai_key)}")
        print(f"OpenAI API Key length: {len(openai_key) if openai_key else 0}")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {openai_key}",
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

        print(f"Making OpenAI request to: {url}")

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            print(f"OpenAI response status: {response.status_code}")
            
            if response.status_code != 200:
                error_text = response.text
                print(f"OpenAI API error: {error_text}")
                return f"OpenAI API error ({response.status_code}): {error_text}"
            
            result = response.json()
            print(f"OpenAI response: {result}")

            if "choices" in result and result["choices"]:
                return result["choices"][0]["message"]["content"]
            return "Sorry, I couldn't generate a response."


trello = TrelloClient()
ai = AIAssistant()


async def handle_comment(action):
    """Process comments for AI requests"""

    print(f"Processing comment action: {action}")

    comment_text = action["data"]["text"]
    card = action["data"]["card"]
    card_id = card["id"]
    
    # Get member who created the comment
    member_creator = action.get("memberCreator", {})
    member_username = member_creator.get("username", "")

    print(f"Comment text: {comment_text}")
    print(f"Card ID: {card_id}")
    print(f"Comment creator: {member_username}")

    # Prevent infinite loops: Skip comments that look like bot responses
    if any(marker in comment_text for marker in ["🤖 **AI Assistant:**", "✅ **Framework Saved Successfully!**", "📚 **Stored Frameworks", "❌", "🚧", "🔄 Starting", "✅ Found", "✅ Using", "✅ Created"]):
        print("Skipping bot-generated comment to prevent infinite loop")
        return

    # Check if comment mentions AI
    if "@ai" in comment_text.lower():
        print("Found @ai mention, processing AI request")

        # Get card details for context
        try:
            card_details = await trello.get_card(card_id)
            print(f"Card details: {card_details}")
        except Exception as e:
            print(f"Error getting card details: {e}")
            card_details = {}

        # Check if this is a lesson plan card (from lesson plans board)
        lesson_plans_board_id = "68a646dba9f202dbd275b7e8"
        card_board_id = card_details.get("idBoard")

        if card_board_id == lesson_plans_board_id:
            print("This is a lesson plan card, checking for feedback")

            # Try to parse feedback from comment
            feedback_result = await handle_lesson_plan_feedback(comment_text, card_id, card_details)

            if feedback_result:
                print(f"Feedback processed: {feedback_result}")
                # Post acknowledgment comment
                ack_comment = f"✅ **Feedback Received**\n\nThanks for the feedback! I've recorded your {feedback_result.get('feedback_type', 'comment')} and will use it to improve future lesson plans."
                await trello.add_comment(card_id, ack_comment)
                return  # Don't process as general AI request if it's feedback
            else:
                print("No feedback detected, will process as general AI request")

        # Extract AI request for general assistance
        ai_request = comment_text.lower().replace("@ai", "").strip()
        print(f"AI request: {ai_request}")

        # Check for activity command
        if "activity" in ai_request and not "framework" in ai_request:
            print(f"Detected activity command: {ai_request}")
            await handle_activity_command(ai_request, card_details, card_id)
            return

        # Check for framework commands
        if any(cmd in ai_request for cmd in ["save framework", "generate variants", "list frameworks"]):
            print(f"Detected framework command: {ai_request}")
            await handle_framework_command(ai_request, card_details, card_id)
            return

        # General AI assistance
        context = f"Card: {card_details.get('name', '')}\\nDescription: {card_details.get('desc', '')}"
        prompt = f"Teacher asks: {ai_request}\\nContext: {context}"
        print(f"AI prompt: {prompt}")

        try:
            response = await ai.get_openai_response(prompt)
            print(f"AI response: {response}")

            # Post AI response as comment
            ai_comment = f"🤖 **AI Assistant:**\\n\\n{response}"
            await trello.add_comment(card_id, ai_comment)
            print("Comment posted successfully")
        except Exception as e:
            print(f"Error in AI processing: {e}")
    else:
        print("No @ai mention found in comment")


async def handle_lesson_plan_feedback(comment_text, card_id, card_details):
    """Parse and submit feedback for lesson plan cards"""

    # Extract lesson plan ID from card description
    card_desc = card_details.get("desc", "")
    lesson_plan_id = None

    # Look for lesson plan ID in the card description
    import re
    plan_id_match = re.search(r'\*\*Plan ID:\*\* (\w+)', card_desc)
    if plan_id_match:
        lesson_plan_id = plan_id_match.group(1)
    else:
        # Also try alternative format
        plan_id_match = re.search(r'Plan ID:\*\* (\w+)', card_desc)
        if plan_id_match:
            lesson_plan_id = plan_id_match.group(1)
        else:
            # Also try looking for "Stored in DynamoDB as:"
            stored_match = re.search(r'Stored in DynamoDB as: (\w+)', card_desc)
            if stored_match:
                lesson_plan_id = stored_match.group(1)
            else:
                # Fallback: use card name or ID
                lesson_plan_id = card_details.get("name", card_id).replace(" ", "_").lower()

    print(f"Extracted lesson plan ID: {lesson_plan_id}")

    # Parse feedback from comment
    comment_lower = comment_text.lower()
    feedback_data = None

    if "like:" in comment_lower or "@ai like" in comment_lower:
        if "like:" in comment_text:
            feedback_text = comment_text.split("like:", 1)[1].strip()
        else:
            feedback_text = comment_text.replace("@ai like", "").strip()

        feedback_data = {
            "lesson_plan_id": lesson_plan_id,
            "feedback_type": "like",
            "feedback_text": feedback_text,
            "source": f"trello_comment:{card_id}"
        }

    elif "dislike:" in comment_lower or "@ai dislike" in comment_lower:
        if "dislike:" in comment_text:
            feedback_text = comment_text.split("dislike:", 1)[1].strip()
        else:
            feedback_text = comment_text.replace("@ai dislike", "").strip()

        feedback_data = {
            "lesson_plan_id": lesson_plan_id,
            "feedback_type": "dislike",
            "feedback_text": feedback_text,
            "source": f"trello_comment:{card_id}"
        }

    elif "improve:" in comment_lower or "@ai improve" in comment_lower:
        if "improve:" in comment_text:
            feedback_text = comment_text.split("improve:", 1)[1].strip()
        else:
            feedback_text = comment_text.replace("@ai improve", "").strip()

        feedback_data = {
            "lesson_plan_id": lesson_plan_id,
            "feedback_type": "improve",
            "feedback_text": feedback_text,
            "source": f"trello_comment:{card_id}"
        }

    elif "rating:" in comment_lower:
        # Extract rating (e.g., "@ai rating: 4/5" or "@ai rating: 3")
        rating_match = re.search(r'rating:\s*(\d+)(?:/\d+)?', comment_text, re.IGNORECASE)
        if rating_match:
            rating = int(rating_match.group(1))
            feedback_data = {
                "lesson_plan_id": lesson_plan_id,
                "feedback_type": "rating",
                "feedback_text": comment_text,
                "rating": rating,
                "source": f"trello_comment:{card_id}"
            }

    # Submit feedback to MCP API if parsed successfully
    if feedback_data:
        try:
            mcp_api_url = "https://89npxchg5j.execute-api.us-east-1.amazonaws.com/dev/feedback"

            async with httpx.AsyncClient() as client:
                response = await client.post(mcp_api_url, json=feedback_data)
                response.raise_for_status()
                result = response.json()
                print(f"Feedback submitted to MCP: {result}")
                return result

        except Exception as e:
            print(f"Error submitting feedback to MCP: {e}")
            return None

    return None


def handler(event, context):
    """AWS Lambda handler - optimized pipeline with simplified test"""

    try:
        print(f"Full event: {json.dumps(event)}")

        # Handle API Gateway event
        if event.get("httpMethod"):
            # Parse body
            body = event.get("body", "{}")
            print(f"Raw body: {body}")
            print(f"Body type: {type(body)}")

            if isinstance(body, str) and body:
                try:
                    payload = json.loads(body)
                    print(f"Parsed payload: {payload}")
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    payload = {}
            else:
                payload = body if body else {}
                print(f"Using body as payload: {payload}")

            # Handle webhook
            if event["path"] == "/webhook":
                if event["httpMethod"] in ["GET", "HEAD"]:
                    # Webhook verification - just return 200
                    return {
                        "statusCode": 200,
                        "body": json.dumps({"status": "webhook endpoint ready"}) if event["httpMethod"] == "GET" else ""
                    }
                elif event["httpMethod"] == "POST":
                    action = payload.get("action", {})
                    action_type = action.get("type")

                    print(f"Received webhook: {action_type}")

                    # Handle different action types
                    if action_type == "commentCard":
                        asyncio.run(handle_comment(action))

                    return {
                        "statusCode": 200,
                        "body": json.dumps({"status": "ok", "processed": action_type})
                    }

            # Health check
            elif event["path"] == "/health":
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "status": "healthy",
                        "services": {
                            "trello": bool(get_trello_api_key() and get_trello_token()),
                            "openai": bool(get_openai_api_key())
                        }
                    })
                }

            # Root endpoint
            elif event["path"] == "/":
                return {
                    "statusCode": 200,
                    "body": json.dumps({"message": "Curriculum AI Webhook Handler", "status": "running"})
                }

        # Default response
        return {
            "statusCode": 404,
            "body": json.dumps({"message": "Not found"})
        }

    except Exception as e:
        print(f"Lambda error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"status": "error", "message": str(e)})
        }


async def get_or_create_list(board_id: str, list_name: str):
    """Get existing list or create new one"""
    url = f"{TRELLO_BASE}/boards/{board_id}/lists"
    params = {**trello.auth_params}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        if response.status_code == 200:
            lists = response.json()
            
            # Check if list exists
            for lst in lists:
                if lst['name'] == list_name:
                    return lst['id']
                    
            # Create new list
            create_url = f"{TRELLO_BASE}/lists"
            create_params = {
                'name': list_name,
                'idBoard': board_id,
                'pos': 'bottom',
                **trello.auth_params
            }
            
            create_response = await client.post(create_url, data=create_params)
            if create_response.status_code == 200:
                return create_response.json()['id']
    return None


async def create_variant_card(board_id: str, list_id: str, variant_name: str, variant_framework: str):
    """Create a Trello card for a framework variant"""
    url = f"{TRELLO_BASE}/cards"
    data = {
        'idList': list_id,
        'name': variant_name,
        'desc': variant_framework,
        'pos': 'bottom',
        **trello.auth_params
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        if response.status_code == 200:
            return response.json()['id']
    return None


async def generate_framework_variants(framework_id: str, framework_data: dict, num_variants: int, card_id: str):
    """Generate framework variants using OpenAI and create individual Trello cards"""
    
    try:
        await trello.add_comment(card_id, f"🔄 Starting variant generation for {framework_id}...")
        
        # Get card details to find board ID
        card_details = await trello.get_card(card_id)
        board_id = card_details.get('idBoard')
        
        if not board_id:
            await trello.add_comment(card_id, "❌ Could not determine board ID for variant creation")
            return
        
        await trello.add_comment(card_id, f"✅ Found board ID: {board_id}")
        
        # Get or create "Framework Variants" list
        variants_list_id = await get_or_create_list(board_id, "Framework Variants")
        if not variants_list_id:
            await trello.add_comment(card_id, "❌ Could not create Framework Variants list")
            return
            
        await trello.add_comment(card_id, f"✅ Using variants list: {variants_list_id}")
        
        # Generate detailed variant with AI
        themes = ['Technology & Innovation', 'Travel & Culture', 'Business Communication', 'Environmental Issues', 'Health & Wellness', 'Arts & Entertainment']
        levels = ['A2', 'B1', 'B2', 'C1']
        
        theme = themes[0 % len(themes)]
        level = levels[0 % len(levels)]
        
        # Create detailed prompt based on tmp_framework.md structure
        prompt = f"""
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

Example structure:
- Question: "What technology do you use daily?"
- Options: 📱 Smartphone / 💻 Laptop
- Model: "None. I use both smartphone and laptop daily."

## Target Vocabulary (theme-specific)
🟦 **Verbs (with -ing):** [8 verbs related to {theme}]
🟩 **Adjectives of opinion:** [8 adjectives: fun, boring, exciting, challenging, etc.]
🟥 **Connectors:** because, and, but
🟨 **Theme nouns:** [6-8 nouns specific to {theme}]

## Vocabulary Activities
### Activity 1: Vocabulary Matching - My Opinion Version
**Instructions:** Match {theme} activities with opinion adjectives
**Target structure:** "In my opinion, [activity] is [adjective]"
**Materials:** Activity cards with emojis, adjective cards

### Activity 2: Guided Completion
**Format:** Complete sentences using emojis as clues
**Example:** "Maria: I like ______ [emoji] because it is ______ [emoji] and ______ [emoji]."

## Grammar Focus (20-25 minutes)
### Verbs of Preference + -ing + Connectors
**Focus:** like/love/hate/enjoy + verb + -ing + connectors

**Examples:**
- I like [theme activity] because it's [adjective]
- She loves [theme activity] because it's [adjective] and [adjective]
- I don't like [theme activity], but I enjoy [other activity]

## Communicative Practice (30-40 minutes)
### Speaking Challenge
**Prompts:**
- "Tell me 3 {theme} things you enjoy and why"
- "Tell me something about {theme} you hate and explain why"

### Role-play: [Theme-specific scenario]
**Situation:** [Detailed scenario related to {theme}]
**Required elements:**
- Personal information
- Theme-specific preferences with reasons
- Use of target grammar and vocabulary

**Model example:** [Provide complete example dialogue]

## Extension Activities
### Idiomatic Expressions: "Piece of Cake" / "Not My Cup of Tea"
**Application:** Use expressions with {theme} activities

## Mini Wrap-Up and Assessment (10-15 minutes)
**Review questions:**
1. Which verbs do we use followed by -ing when talking about likes and dislikes?
2. How would you describe {theme} activities using opinion adjectives?
3. Say something about {theme} that your family member likes/doesn't like

**Motivational closing:** [Theme-specific motivational phrase]

**Materials needed:** [Specific materials for {theme} activities]
**Assessment criteria:** [4-5 specific criteria for this {theme} class]

Make it practical, engaging, and immediately usable by teachers. Include emojis and specific examples throughout.
"""

        # Get AI response
        ai_response = await ai.get_openai_response(prompt, max_tokens=3000)
        
        # Create card name
        variant_name = f"{framework_data.get('framework_name', 'Framework')} - {theme} ({level})"
        
        # Create card with detailed framework
        card_id_new = await create_variant_card(board_id, variants_list_id, variant_name, ai_response)
        
        if card_id_new:
            await trello.add_comment(card_id, f"✅ Created variant card: {variant_name}")
        else:
            await trello.add_comment(card_id, f"❌ Failed to create card for variant: {variant_name}")
        
    except Exception as e:
        print(f"Error in generate_framework_variants: {e}")
        import traceback
        traceback.print_exc()
        await trello.add_comment(card_id, f"❌ Error generating variants: {str(e)}")


async def handle_activity_command(ai_request: str, card_details: dict, card_id: str):
    """Handle activity generation commands"""
    import re
    
    print(f"Processing activity command: {ai_request}")
    
    try:
        # Parse parameters from request
        # Format: @ai activity [topic] [grade_level] [duration] [activity_type]
        # Example: @ai activity "food and drinks" 3 15 preference_choice
        
        # Extract parameters using regex
        # Look for quoted strings first (for multi-word topics)
        topic_match = re.search(r'"([^"]+)"', ai_request) or re.search(r'topic[:\s]+([^\s,]+)', ai_request)
        grade_match = re.search(r'grade[:\s]+([^\s,]+)', ai_request) or re.search(r'\b([K1-9]|1[0-2])\b', ai_request)
        duration_match = re.search(r'duration[:\s]+(\d+)', ai_request) or re.search(r'(\d+)\s*min', ai_request)
        type_match = re.search(r'type[:\s]+([^\s,]+)', ai_request) or re.search(r'(preference_choice|vocabulary_builder|compare_contrast|sequence_builder|story_response|interactive_game|discovery_exploration)', ai_request)
        
        # Get topic from card if not specified
        if not topic_match:
            topic = card_details.get('name', 'English Language Learning')
        else:
            topic = topic_match.group(1)
        
        # Default values
        grade_level = grade_match.group(1) if grade_match else "3"
        duration = int(duration_match.group(1)) if duration_match else 15
        activity_type = type_match.group(1) if type_match else None
        
        # Get context from card description
        context = card_details.get('desc', '')[:500] if card_details.get('desc') else None
        
        await trello.add_comment(card_id, f"🎯 **Generating Activity**\n\n📚 Topic: {topic}\n📊 Grade Level: {grade_level}\n⏱️ Duration: {duration} minutes\n🎨 Type: {activity_type or 'Auto-selected'}")
        
        # Call activity generator Lambda
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        payload = {
            'topic': topic,
            'grade_level': grade_level,
            'duration': duration
        }
        
        if activity_type:
            payload['activity_type'] = activity_type
        if context:
            payload['context'] = context
        
        print(f"Invoking activity generator with payload: {payload}")
        
        # Invoke Lambda function (assuming it's deployed as curriculum-activity-generator)
        response = lambda_client.invoke(
            FunctionName='curriculum-activity-generator',
            InvocationType='RequestResponse',
            Payload=json.dumps({'body': json.dumps(payload)})
        )
        
        # Parse response
        result = json.loads(response['Payload'].read())
        print(f"Activity generator response: {result}")
        
        if result.get('statusCode') == 200:
            activity = json.loads(result.get('body', '{}'))
            
            # Format activity for Trello comment
            comment = f"✅ **Activity Generated Successfully!**\n\n"
            comment += f"**{activity.get('title', 'Activity')}**\n\n"
            
            # Add activity ID for tracking
            if activity.get('activity_id'):
                comment += f"📌 Activity ID: `{activity['activity_id']}`\n\n"
            
            # Format slides for display
            slides = activity.get('slides', [])
            for slide in slides:
                comment += f"**Slide {slide.get('slide_number', '')} - {slide.get('type', '')}**\n"
                comment += f"*Title:* {slide.get('title', '')}\n\n"
                
                content = slide.get('content', {})
                if isinstance(content, dict):
                    if content.get('instructions'):
                        comment += f"📝 *Instructions:* {content['instructions']}\n\n"
                    if content.get('vocabulary_items'):
                        comment += f"📚 *Vocabulary:* {', '.join(content['vocabulary_items'][:5])}"
                        if len(content['vocabulary_items']) > 5:
                            comment += f" (and {len(content['vocabulary_items']) - 5} more)"
                        comment += "\n\n"
                    if content.get('questions'):
                        comment += f"❓ *Practice Questions:*\n"
                        for i, q in enumerate(content['questions'][:3], 1):
                            comment += f"  {i}. {q}\n"
                        if len(content['questions']) > 3:
                            comment += f"  (and {len(content['questions']) - 3} more)\n"
                        comment += "\n"
                else:
                    comment += f"{str(content)[:200]}...\n\n"
                
                if slide.get('teacher_notes'):
                    comment += f"👩‍🏫 *Teacher Notes:* {slide['teacher_notes'][:100]}...\n"
                if slide.get('timing'):
                    comment += f"⏱️ *Timing:* {slide['timing']}\n"
                comment += "\n---\n\n"
            
            # Add metadata
            metadata = activity.get('metadata', {})
            if metadata:
                comment += f"**Activity Details:**\n"
                comment += f"• Energy Level: {metadata.get('energy_level', 'medium')}\n"
                comment += f"• Cognitive Stage: {metadata.get('cognitive_stage', 'practice')}\n"
                comment += f"• Duration: {metadata.get('duration', '15 minutes')}\n"
            
            # Truncate if too long for Trello
            if len(comment) > 16000:
                comment = comment[:15900] + "\n\n...[Content truncated for display]"
            
            await trello.add_comment(card_id, comment)
            
            # Create a separate card with full activity details
            if activity.get('activity_id'):
                # Create activity card in Activities list
                activities_list_id = await get_or_create_list(card_details.get('idBoard'), "Generated Activities")
                if activities_list_id:
                    activity_card_data = {
                        'idList': activities_list_id,
                        'name': activity.get('title', f"Activity: {topic}"),
                        'desc': json.dumps(activity, indent=2),
                        'pos': 'bottom',
                        **trello.auth_params
                    }
                    
                    async with httpx.AsyncClient() as client:
                        card_response = await client.post(
                            f"{TRELLO_BASE}/cards",
                            data=activity_card_data
                        )
                        if card_response.status_code == 200:
                            new_card = card_response.json()
                            await trello.add_comment(card_id, f"📋 Full activity details saved to card: {new_card.get('shortUrl')}")
        else:
            error_msg = json.loads(result.get('body', '{}')).get('error', 'Unknown error')
            await trello.add_comment(card_id, f"❌ **Activity Generation Failed**\n\n{error_msg}")
            
    except Exception as e:
        print(f"Error in activity generation: {e}")
        import traceback
        traceback.print_exc()
        await trello.add_comment(card_id, f"❌ **Error generating activity:** {str(e)}\n\nPlease check your parameters and try again.\n\n**Usage:** `@ai activity \"topic\" grade_level duration [type]`\n\n**Example:** `@ai activity \"food and drinks\" 3 15 preference_choice`")


async def handle_framework_command(ai_request: str, card_details: dict, card_id: str):
    """Handle framework-specific AI commands"""
    secrets = SecretsManager()
    trello = TrelloClient()
    
    print(f"Processing framework command: {ai_request}")
    
    try:
        if "save framework" in ai_request:
            # Store framework from card description
            framework_data = card_details.get('desc', '')
            framework_name = card_details.get('name', 'Unnamed Framework')
            
            if not framework_data:
                await trello.add_comment(card_id, "❌ No framework data found in card description. Please add your framework structure in JSON format to the card description.")
                return
            
            try:
                # Parse JSON from description
                parsed_framework = json.loads(framework_data)
                
                # Store in DynamoDB
                dynamodb = boto3.resource('dynamodb')
                table = dynamodb.Table('curriculum-frameworks')
                
                framework_id = str(uuid.uuid4())
                timestamp = datetime.utcnow().isoformat()
                
                item = {
                    'framework_id': framework_id,
                    'board_id': card_details.get('idBoard', '68a5fba51647caf78fc40866'),
                    'framework_name': framework_name,
                    'framework_data': parsed_framework,
                    'metadata': {'source': 'trello_card'},
                    'created_at': timestamp,
                    'updated_at': timestamp,
                    'version': 1,
                    'is_active': True
                }
                
                table.put_item(Item=item)
                
                response_msg = f"✅ **Framework Saved Successfully!**\n\n"
                response_msg += f"Framework: **{framework_name}**\n"
                response_msg += f"ID: `{framework_id}`\n\n"
                response_msg += f"You can now generate variants with:\n"
                response_msg += f"`@ai generate variants framework_id={framework_id} num=5`"
                
                await trello.add_comment(card_id, response_msg)
                
            except json.JSONDecodeError:
                await trello.add_comment(card_id, "❌ Invalid JSON in card description. Please ensure your framework is properly formatted JSON.")
            except Exception as e:
                await trello.add_comment(card_id, f"❌ Error saving framework: {str(e)}")
                
        elif "list frameworks" in ai_request:
            # List stored frameworks
            try:
                dynamodb = boto3.resource('dynamodb')
                table = dynamodb.Table('curriculum-frameworks')
                
                board_id = card_details.get('idBoard', '68a5fba51647caf78fc40866')
                
                # Scan for frameworks (could be optimized with GSI)
                response = table.scan(
                    FilterExpression='board_id = :bid',
                    ExpressionAttributeValues={':bid': board_id}
                )
                
                frameworks = response.get('Items', [])
                
                if not frameworks:
                    await trello.add_comment(card_id, "📚 No stored frameworks found for this board.")
                    return
                
                msg = f"📚 **Stored Frameworks ({len(frameworks)} found):**\n\n"
                for fw in frameworks:
                    msg += f"• **{fw.get('framework_name', 'Unnamed')}**\n"
                    msg += f"  ID: `{fw.get('framework_id')}`\n"
                    msg += f"  Created: {fw.get('created_at', '')[:10]}\n\n"
                
                msg += "💡 Generate variants with: `@ai generate variants framework_id=<id>`"
                
                await trello.add_comment(card_id, msg)
                
            except Exception as e:
                await trello.add_comment(card_id, f"❌ Error listing frameworks: {str(e)}")
                
        elif "generate variants" in ai_request:
            # Parse framework_id and num from the request
            import re
            print(f"Parsing variants request: {ai_request}")
            framework_id_match = re.search(r'framework_id=([a-f0-9-]+)', ai_request)
            num_match = re.search(r'num=(\d+)', ai_request)
            
            print(f"Framework ID match: {framework_id_match}")
            print(f"Num match: {num_match}")
            
            if not framework_id_match:
                await trello.add_comment(card_id, "❌ Please specify framework_id. Usage: `@ai generate variants framework_id=<id> num=<number>`")
                return
                
            framework_id = framework_id_match.group(1)
            num_variants = int(num_match.group(1)) if num_match else 3
            
            print(f"Extracted framework_id: {framework_id}")
            print(f"Extracted num_variants: {num_variants}")
            
            try:
                # Get framework from DynamoDB
                dynamodb = boto3.resource('dynamodb')
                table = dynamodb.Table('curriculum-frameworks')
                
                print(f"Getting framework from DynamoDB: {framework_id}")
                response = table.get_item(Key={'framework_id': framework_id})
                print(f"DynamoDB response: {response}")
                
                if 'Item' not in response:
                    await trello.add_comment(card_id, f"❌ Framework not found: {framework_id}")
                    return
                    
                framework = response['Item']
                framework_data = framework['framework_data']
                
                print(f"Found framework: {framework.get('framework_name')}")
                
                # Generate variants using OpenAI
                print(f"About to call generate_framework_variants with: {framework_id}, {num_variants}, {card_id}")
                await generate_framework_variants(framework_id, framework_data, num_variants, card_id)
                print(f"Completed generate_framework_variants call")
                
            except Exception as e:
                print(f"Exception in generate variants: {e}")
                import traceback
                traceback.print_exc()
                await trello.add_comment(card_id, f"❌ Error generating variants: {str(e)}")
            
    except Exception as e:
        print(f"Error in framework command: {e}")
        await trello.add_comment(card_id, f"❌ Error processing framework command: {str(e)}")


# Standard handler name - no alias needed
