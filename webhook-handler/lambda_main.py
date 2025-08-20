"""
Simple Lambda handler for Trello AI Webhook
Responds to Trello events with AI assistance
"""

import json
import os
import httpx
import asyncio
import boto3


def get_secret(param_name: str) -> str:
    """Get secret from Parameter Store"""
    ssm = boto3.client('ssm')
    try:
        response = ssm.get_parameter(Name=param_name, WithDecryption=True)
        return response['Parameter']['Value']
    except Exception as e:
        print(f"Error getting parameter {param_name}: {e}")
        return ""


TRELLO_API_KEY = get_secret(os.getenv("TRELLO_API_KEY_PARAM", ""))
TRELLO_TOKEN = get_secret(os.getenv("TRELLO_TOKEN_PARAM", ""))
OPENAI_API_KEY = get_secret(os.getenv("OPENAI_API_KEY_PARAM", ""))
TRELLO_WEBHOOK_SECRET = get_secret(os.getenv("TRELLO_WEBHOOK_SECRET_PARAM", ""))

print(f"Loaded credentials - Trello Key: {bool(TRELLO_API_KEY)}, Trello Token: {bool(TRELLO_TOKEN)}, OpenAI: {bool(OPENAI_API_KEY)}")

# Trello API base URL
TRELLO_BASE = "https://api.trello.com/1"


class TrelloClient:
    """Simple Trello API client"""

    def __init__(self):
        self.auth_params = {
            "key": TRELLO_API_KEY,
            "token": TRELLO_TOKEN
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
        print(f"OpenAI API Key available: {bool(OPENAI_API_KEY)}")
        print(f"OpenAI API Key length: {len(OPENAI_API_KEY) if OPENAI_API_KEY else 0}")

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

        # Extract AI request
        ai_request = comment_text.lower().replace("@ai", "").strip()
        print(f"AI request: {ai_request}")

        # Get card details for context
        try:
            card_details = await trello.get_card(card_id)
            print(f"Card details: {card_details}")
        except Exception as e:
            print(f"Error getting card details: {e}")
            card_details = {}

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


def lambda_handler(event, context):
    """AWS Lambda handler"""

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
                            "trello": bool(TRELLO_API_KEY and TRELLO_TOKEN),
                            "openai": bool(OPENAI_API_KEY)
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
