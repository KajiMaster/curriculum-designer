#!/usr/bin/env python3
"""
Script to register Trello webhook for the curriculum designer
"""

import requests
import os
import sys

# Configuration
TRELLO_API_KEY = os.getenv("TRELLO_API_KEY", "c1fb91381f329cadc1f95a301163bc9a")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")  # You'll need to provide this
BOARD_ID = "68a5fba51647caf78fc40866"  # Main curriculum board
WEBHOOK_URL = "https://r5sj8iny39.execute-api.us-east-1.amazonaws.com/dev/webhook"

def list_webhooks():
    """List existing webhooks"""
    if not TRELLO_TOKEN:
        print("Error: TRELLO_TOKEN environment variable required")
        return []
    
    url = "https://api.trello.com/1/tokens/{}/webhooks".format(TRELLO_TOKEN)
    params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        webhooks = response.json()
        print(f"Found {len(webhooks)} existing webhooks:")
        for webhook in webhooks:
            print(f"  ID: {webhook['id']}")
            print(f"  URL: {webhook['callbackURL']}")
            print(f"  Model ID: {webhook['idModel']}")
            print(f"  Active: {webhook['active']}")
            print()
        return webhooks
    else:
        print(f"Error listing webhooks: {response.status_code} - {response.text}")
        return []

def delete_webhook(webhook_id):
    """Delete a webhook"""
    if not TRELLO_TOKEN:
        print("Error: TRELLO_TOKEN environment variable required")
        return False
    
    url = f"https://api.trello.com/1/webhooks/{webhook_id}"
    params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN
    }
    
    response = requests.delete(url, params=params)
    if response.status_code == 200:
        print(f"Successfully deleted webhook {webhook_id}")
        return True
    else:
        print(f"Error deleting webhook: {response.status_code} - {response.text}")
        return False

def register_webhook():
    """Register new webhook for the board"""
    if not TRELLO_TOKEN:
        print("Error: TRELLO_TOKEN environment variable required")
        return False
    
    url = "https://api.trello.com/1/webhooks/"
    data = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN,
        "callbackURL": WEBHOOK_URL,
        "idModel": BOARD_ID,
        "description": "Curriculum Designer AI Webhook"
    }
    
    response = requests.post(url, data=data)
    if response.status_code == 200:
        webhook = response.json()
        print("Successfully registered webhook:")
        print(f"  ID: {webhook['id']}")
        print(f"  URL: {webhook['callbackURL']}")
        print(f"  Model ID: {webhook['idModel']}")
        print(f"  Active: {webhook['active']}")
        return True
    else:
        print(f"Error registering webhook: {response.status_code} - {response.text}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python register_webhook.py [list|register|delete <webhook_id>]")
        print()
        print("Examples:")
        print("  python register_webhook.py list")
        print("  python register_webhook.py register")
        print("  python register_webhook.py delete 5f4b2c1a...")
        return
    
    command = sys.argv[1]
    
    if command == "list":
        list_webhooks()
    elif command == "register":
        register_webhook()
    elif command == "delete" and len(sys.argv) == 3:
        webhook_id = sys.argv[2]
        delete_webhook(webhook_id)
    else:
        print("Unknown command or missing webhook ID for delete")

if __name__ == "__main__":
    main()