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
