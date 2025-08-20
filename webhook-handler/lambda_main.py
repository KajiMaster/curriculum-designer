"""
Simple Lambda handler for Trello AI Webhook
Responds to Trello events with AI assistance
"""

import json
import os
import httpx
import asyncio
import boto3


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
        params = {"fields": "name,desc,labels,list", **self.auth_params}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
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

    print(f"Comment text: {comment_text}")
    print(f"Card ID: {card_id}")

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


def lambda_handler(event, context):
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


handler = lambda_handler
