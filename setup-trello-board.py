#!/usr/bin/env python3
"""
Script to create the Trello board structure for AI curriculum management
"""

import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv('.env')

TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
TRELLO_BASE = "https://api.trello.com/1"

class TrelloBoardSetup:
    def __init__(self):
        self.client = httpx.Client()
        self.auth_params = {
            "key": TRELLO_API_KEY,
            "token": TRELLO_TOKEN
        }
    
    def create_board(self):
        """Create the main curriculum board"""
        url = f"{TRELLO_BASE}/boards"
        data = {
            "name": "English Curriculum AI Assistant",
            "desc": "AI-powered curriculum management for English teaching",
            "defaultLists": False,  # We'll create custom lists
            "powerUps": ["calendar"],  # Enable calendar view
            **self.auth_params
        }
        
        response = self.client.post(url, data=data)
        board = response.json()
        print(f"✅ Created board: {board['name']}")
        print(f"   URL: {board['url']}")
        return board
    
    def create_lists(self, board_id):
        """Create the workflow lists"""
        lists_to_create = [
            "📚 Activity Bank",
            "🤖 AI Requests", 
            "📋 AI Suggestions",
            "📅 This Week",
            "⏰ Today",
            "✅ Completed",
            "🔄 Needs Revision",
            "🗂️ Templates"
        ]
        
        created_lists = {}
        for i, list_name in enumerate(lists_to_create):
            url = f"{TRELLO_BASE}/lists"
            data = {
                "name": list_name,
                "idBoard": board_id,
                "pos": i + 1,
                **self.auth_params
            }
            
            response = self.client.post(url, data=data)
            list_obj = response.json()
            created_lists[list_name] = list_obj
            print(f"   📋 Created list: {list_name}")
        
        return created_lists
    
    def create_labels(self, board_id):
        """Create category and level labels"""
        labels_to_create = [
            ("Beginner", "green"),
            ("Intermediate", "yellow"), 
            ("Advanced", "red"),
            ("Grammar", "blue"),
            ("Speaking", "purple"),
            ("Writing", "black"),
            ("Business English", "orange"),
            ("Listening", "sky"),
            ("Warmup", "lime"),
            ("Assessment", "pink")
        ]
        
        created_labels = {}
        for label_name, color in labels_to_create:
            url = f"{TRELLO_BASE}/labels"
            data = {
                "name": label_name,
                "color": color,
                "idBoard": board_id,
                **self.auth_params
            }
            
            response = self.client.post(url, data=data)
            label_obj = response.json()
            created_labels[label_name] = label_obj
            print(f"   🏷️  Created label: {label_name} ({color})")
        
        return created_labels
    
    def create_sample_activities(self, lists, labels):
        """Create sample activity cards"""
        
        activity_bank_id = lists["📚 Activity Bank"]["id"]
        
        sample_activities = [
            {
                "name": "[20m] Present Perfect Practice | Intermediate | Grammar",
                "desc": """📊 METADATA:
Level: Intermediate
Duration: 20 minutes
Energy: Medium
Skills: Grammar, Speaking
Interaction: Pairs then Individual
Materials: Worksheet, Timer

🎯 OBJECTIVES:
- Master present perfect vs past simple
- Use time expressions (for/since)
- Practice in conversation context

📝 INSTRUCTIONS:
1. Warm-up (3m): Timeline on board
2. Explanation (5m): Key differences  
3. Practice (8m): Worksheet completion
4. Speaking (4m): Interview partner

💡 NOTES:
Best after past tense lesson
Students struggle with "since" vs "for"

🏷️ TAGS: #tested #popular #grammar-sequence""",
                "labels": ["Intermediate", "Grammar"]
            },
            {
                "name": "[30m] Business Meeting Roleplay | Advanced | Speaking",
                "desc": """📊 METADATA:
Level: Advanced
Duration: 30 minutes
Energy: High
Skills: Speaking, Business Communication
Interaction: Groups of 4
Materials: Meeting scenario cards, Agenda template

🎯 OBJECTIVES:
- Practice formal meeting language
- Learn to chair meetings effectively
- Master negotiation phrases

📝 INSTRUCTIONS:
1. Review meeting language (5m)
2. Assign roles (boardchair, participants) (3m)
3. Conduct mock meeting (20m)
4. Debrief and feedback (2m)

💡 NOTES:
Great for business English students
Record for later analysis if possible

🏷️ TAGS: #business #roleplay #advanced""",
                "labels": ["Advanced", "Speaking", "Business English"]
            },
            {
                "name": "🤖 AI: Build Lesson - Sample Request",
                "desc": """🤖 AI REQUEST:
Type: Lesson Builder
Student: Sample Student
Level: Intermediate  
Duration: 120 minutes
Focus: Business presentations

📋 REQUIREMENTS:
- Include warmup (10m)
- 2-3 main activities
- Interactive elements
- Materials list

⏰ DEADLINE: Sample request

🎯 CONTEXT:
This is a sample AI request card.
Move this to "AI Requests" list to see AI processing in action!""",
                "labels": []
            }
        ]
        
        for activity in sample_activities:
            # Get label IDs
            label_ids = []
            for label_name in activity["labels"]:
                if label_name in labels:
                    label_ids.append(labels[label_name]["id"])
            
            # Choose appropriate list
            if "🤖 AI:" in activity["name"]:
                list_id = lists["🤖 AI Requests"]["id"]
            else:
                list_id = activity_bank_id
            
            url = f"{TRELLO_BASE}/cards"
            data = {
                "name": activity["name"],
                "desc": activity["desc"],
                "idList": list_id,
                "idLabels": ",".join(label_ids),
                **self.auth_params
            }
            
            response = self.client.post(url, data=data)
            card = response.json()
            print(f"   📄 Created card: {activity['name'][:50]}...")
    
    def setup_webhook(self, board_id, webhook_url):
        """Set up webhook for the board"""
        url = f"{TRELLO_BASE}/webhooks"
        data = {
            "callbackURL": webhook_url,
            "idModel": board_id,
            "description": "Curriculum AI Assistant Webhook",
            **self.auth_params
        }
        
        response = self.client.post(url, data=data)
        if response.status_code == 200:
            webhook = response.json()
            print(f"✅ Created webhook: {webhook['id']}")
            return webhook
        else:
            print(f"❌ Failed to create webhook: {response.text}")
            return None
    
    def setup_complete_board(self, webhook_url=None):
        """Set up the complete board structure"""
        print("🚀 Setting up Trello board for AI curriculum management...")
        
        # Create board
        board = self.create_board()
        board_id = board["id"]
        
        # Create lists  
        print("\n📋 Creating lists...")
        lists = self.create_lists(board_id)
        
        # Create labels
        print("\n🏷️  Creating labels...")
        labels = self.create_labels(board_id)
        
        # Create sample activities
        print("\n📄 Creating sample activities...")
        self.create_sample_activities(lists, labels)
        
        # Set up webhook if URL provided
        if webhook_url:
            print(f"\n🔗 Setting up webhook...")
            self.setup_webhook(board_id, webhook_url)
        
        print(f"\n🎉 Board setup complete!")
        print(f"📋 Board URL: {board['url']}")
        print(f"🆔 Board ID: {board_id}")
        
        if not webhook_url:
            print(f"\n⚠️  To enable AI features, set up webhook manually:")
            print(f"   Webhook URL: http://localhost:8000/webhook")
            print(f"   Board ID: {board_id}")
        
        return board

def main():
    if not TRELLO_API_KEY or not TRELLO_TOKEN:
        print("❌ Error: Missing Trello credentials!")
        print("Make sure TRELLO_API_KEY and TRELLO_TOKEN are set in webhook-handler/.env")
        return
    
    setup = TrelloBoardSetup()
    
    # For local testing, don't set up webhook yet
    board = setup.setup_complete_board()
    
    print(f"\n✨ Next steps:")
    print(f"1. Visit your board: {board['url']}")
    print(f"2. Try moving the AI request card to 'AI Requests' list")
    print(f"3. Add a comment with '@ai hello' to test AI responses")

if __name__ == "__main__":
    main()