#!/usr/bin/env python3

"""
MCP Server for Curriculum Designer
Provides Trello curriculum activities as context to Claude
"""

import asyncio
import json
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qs

import httpx
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal
from canva_integration import CanvaDesignGenerator


def decimal_to_int(obj):
    """Convert DynamoDB Decimal objects to int/float for JSON serialization"""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    elif isinstance(obj, dict):
        return {key: decimal_to_int(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_int(item) for item in obj]
    return obj


class CurriculumMCPServer:
    def __init__(self):
        self.trello_key = os.getenv("TRELLO_API_KEY")
        self.trello_token = os.getenv("TRELLO_TOKEN") 
        self.board_id = os.getenv("TRELLO_BOARD_ID")
        
        # Google Drive integration
        self.google_drive_folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        self.google_drive_api_key = os.getenv("GOOGLE_DRIVE_API_KEY")
        
        # Business website reference
        self.business_website = os.getenv("BUSINESS_WEBSITE", "https://example.com")
        self.business_name = os.getenv("BUSINESS_NAME", "Curriculum Design Organization")
        
        # DynamoDB integration
        self.dynamodb_table_name = os.getenv("DYNAMODB_TABLE_NAME")
        self.dynamodb_feedback_table_name = os.getenv("DYNAMODB_FEEDBACK_TABLE_NAME")
        self.dynamodb = boto3.resource('dynamodb') if self.dynamodb_table_name else None
        self.table = self.dynamodb.Table(self.dynamodb_table_name) if self.dynamodb else None
        self.feedback_table = self.dynamodb.Table(self.dynamodb_feedback_table_name) if self.dynamodb and self.dynamodb_feedback_table_name else None
        
        # Lesson Plans Trello Board integration
        self.lesson_plans_board_id = os.getenv("TRELLO_LESSON_PLANS_BOARD_ID")
        self.active_list_id = os.getenv("TRELLO_ACTIVE_LIST_ID")
        
        # Canva integration
        self.canva_generator = CanvaDesignGenerator()
        
        if not all([self.trello_key, self.trello_token, self.board_id]):
            raise ValueError("Missing required environment variables: TRELLO_API_KEY, TRELLO_TOKEN, TRELLO_BOARD_ID")

    async def get_activities(self, category: Optional[str] = None, 
                           level: Optional[str] = None, 
                           duration: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch and filter curriculum activities from Trello"""
        
        async with httpx.AsyncClient() as client:
            # Fetch all cards from the board
            url = f"https://api.trello.com/1/boards/{self.board_id}/cards"
            params = {
                "key": self.trello_key,
                "token": self.trello_token,
                "fields": "name,desc,labels,list,url",
                "list": "true",
                "labels": "true"
            }
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            cards = response.json()
        
        activities = []
        for card in cards:
            # Parse activity data from card
            activity_data = self.parse_card_data(card)
            
            # Apply filters
            if category and activity_data.get("category", "").lower() != category.lower():
                continue
            if level and activity_data.get("level", "").lower() != level.lower():
                continue  
            if duration and activity_data.get("duration", 0) > duration:
                continue
                
            activities.append(activity_data)
        
        return activities

    async def search_activities(self, query: str) -> List[Dict[str, Any]]:
        """Search activities by keyword"""
        all_activities = await self.get_activities()
        
        query_lower = query.lower()
        filtered = []
        
        for activity in all_activities:
            # Search in name, description, and tags
            searchable_text = " ".join([
                activity.get("name", ""),
                activity.get("description", ""),
                " ".join(activity.get("tags", []))
            ]).lower()
            
            if query_lower in searchable_text:
                filtered.append(activity)
        
        return filtered

    async def suggest_lesson_plan(self, student_level: str, 
                                focus_area: Optional[str] = None,
                                total_duration: int = 120) -> Dict[str, Any]:
        """Generate a lesson plan using available activities"""
        
        # Get activities matching the level
        activities = await self.get_activities(level=student_level)
        
        if focus_area:
            activities = [a for a in activities if a.get("category", "").lower() == focus_area.lower()]
        
        if not activities:
            return {"error": f"No activities found for level '{student_level}'" + (f" and category '{focus_area}'" if focus_area else "")}
        
        # Simple lesson plan structure
        lesson_plan = {
            "level": student_level,
            "focus_area": focus_area or "general",
            "total_duration": total_duration,
            "structure": {
                "warmup": None,
                "main_activities": [],
                "cooldown": None
            },
            "materials_needed": set(),
            "estimated_duration": 0
        }
        
        # Find warmup activity (5-15 minutes)
        warmup_activities = [a for a in activities if a.get("duration", 0) <= 15]
        if warmup_activities:
            lesson_plan["structure"]["warmup"] = warmup_activities[0]
            lesson_plan["estimated_duration"] += warmup_activities[0].get("duration", 10)
            if warmup_activities[0].get("materials"):
                lesson_plan["materials_needed"].add(warmup_activities[0]["materials"])
        
        # Find main activities
        remaining_time = total_duration - lesson_plan["estimated_duration"] - 10  # Reserve 10 min for cooldown
        for activity in sorted(activities, key=lambda x: x.get("duration", 20)):
            if (lesson_plan["estimated_duration"] + activity.get("duration", 20) <= remaining_time and 
                activity not in [lesson_plan["structure"]["warmup"]]):
                lesson_plan["structure"]["main_activities"].append(activity)
                lesson_plan["estimated_duration"] += activity.get("duration", 20)
                if activity.get("materials"):
                    lesson_plan["materials_needed"].add(activity["materials"])
        
        # Convert materials set to list
        lesson_plan["materials_needed"] = list(lesson_plan["materials_needed"])
        
        return lesson_plan

    async def get_board_structure(self) -> Dict[str, Any]:
        """Get board structure (lists, labels, etc)"""
        
        async with httpx.AsyncClient() as client:
            # Get board info
            board_url = f"https://api.trello.com/1/boards/{self.board_id}"
            params = {
                "key": self.trello_key,
                "token": self.trello_token,
                "fields": "name,desc,url",
                "lists": "all",
                "labels": "all"
            }
            
            response = await client.get(board_url, params=params)
            response.raise_for_status()
            board_data = response.json()
        
        return {
            "board_name": board_data.get("name"),
            "board_description": board_data.get("desc"),
            "board_url": board_data.get("url"),
            "lists": [{"name": lst["name"], "id": lst["id"]} for lst in board_data.get("lists", [])],
            "labels": [{"name": lbl["name"], "color": lbl["color"]} for lbl in board_data.get("labels", [])]
        }

    def parse_card_data(self, card: Dict[str, Any]) -> Dict[str, Any]:
        """Parse structured data from Trello card"""
        
        # Extract structured data from card description using [key: value] format
        description = card.get("desc", "")
        parsed_data = {}
        
        # Look for [key: value] patterns
        pattern = r'\[(\w+):\s*([^\]]+)\]'
        matches = re.findall(pattern, description)
        
        for key, value in matches:
            parsed_data[key.lower()] = value.strip()
        
        # Extract labels as tags/categories
        labels = [label["name"] for label in card.get("labels", [])]
        
        return {
            "id": card.get("id"),
            "name": card.get("name"),
            "description": description,
            "url": card.get("url"),
            "list_name": card.get("list", {}).get("name", "Unknown"),
            "level": parsed_data.get("level", "intermediate"),
            "duration": int(parsed_data.get("duration", "20").split()[0]) if parsed_data.get("duration") else 20,
            "category": parsed_data.get("category", labels[0] if labels else "general"),
            "materials": parsed_data.get("materials", ""),
            "tags": labels,
            "parsed_fields": parsed_data
        }

    async def get_drive_resources(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get files from Google Drive shared folder"""
        
        if not self.google_drive_api_key or not self.google_drive_folder_id:
            return [{"error": "Google Drive not configured", "note": "Set GOOGLE_DRIVE_API_KEY and GOOGLE_DRIVE_FOLDER_ID"}]
        
        async with httpx.AsyncClient() as client:
            # Search files in the shared folder
            url = "https://www.googleapis.com/drive/v3/files"
            params = {
                "key": self.google_drive_api_key,
                "q": f"'{self.google_drive_folder_id}' in parents and trashed=false",
                "fields": "files(id,name,mimeType,size,modifiedTime,webViewLink,parents)",
                "orderBy": "modifiedTime desc"
            }
            
            # Add search query if provided
            if query:
                params["q"] += f" and name contains '{query}'"
            
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                files = []
                for file in data.get("files", []):
                    files.append({
                        "id": file["id"],
                        "name": file["name"],
                        "type": file["mimeType"],
                        "size": file.get("size", "N/A"),
                        "modified": file["modifiedTime"],
                        "url": file["webViewLink"],
                        "is_document": "document" in file["mimeType"],
                        "is_spreadsheet": "spreadsheet" in file["mimeType"],
                        "is_presentation": "presentation" in file["mimeType"],
                        "is_pdf": "pdf" in file["mimeType"]
                    })
                
                return files
                
            except Exception as e:
                return [{"error": f"Google Drive API error: {str(e)}"}]

    async def get_business_context(self) -> Dict[str, Any]:
        """Get business/organization context and website information"""
        
        context = {
            "business_name": self.business_name,
            "website": self.business_website,
            "description": "Curriculum design and educational content creation",
            "services": [
                "English language curriculum development",
                "Activity and lesson plan creation", 
                "Educational content organization",
                "AI-assisted curriculum design"
            ]
        }
        
        # Try to fetch website information if possible
        if self.business_website and self.business_website != "https://example.com":
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(self.business_website, timeout=10)
                    if response.status_code == 200:
                        # Basic website info - could be enhanced with more parsing
                        context["website_status"] = "accessible"
                        context["website_title"] = "Retrieved successfully"
                    else:
                        context["website_status"] = f"HTTP {response.status_code}"
            except Exception as e:
                context["website_status"] = f"Error: {str(e)}"
        
        return context

    async def create_trello_card_for_lesson_plan(self, lesson_plan: Dict[str, Any], plan_id: str) -> Optional[str]:
        """Create a Trello card for a saved lesson plan"""
        
        if not self.lesson_plans_board_id or not self.active_list_id:
            return None
        
        # Generate card title and description
        title = lesson_plan.get('title') or f"Lesson Plan: {lesson_plan.get('focus_area', 'General')}"
        level = lesson_plan.get('level', 'Unknown')
        duration = lesson_plan.get('duration') or lesson_plan.get('total_duration', 'N/A')
        
        # Create rich description
        description = f"""# 📚 {title}
        
**Level:** {level}
**Duration:** {duration} minutes
**Plan ID:** {plan_id}

## 📋 Structure:
"""
        
        # Add structure details
        structure = lesson_plan.get('structure', {})
        if structure.get('warmup'):
            description += f"\n**Warm-up:** {structure['warmup'].get('name', 'Warm-up activity')}"
        
        main_activities = structure.get('main_activities', [])
        if main_activities:
            description += "\n\n**Main Activities:**"
            for i, activity in enumerate(main_activities, 1):
                activity_name = activity.get('name', f'Activity {i}')
                activity_duration = activity.get('duration', '')
                description += f"\n{i}. {activity_name}"
                if activity_duration:
                    description += f" ({activity_duration}m)"
        
        # Add activities if different format
        activities = lesson_plan.get('activities', [])
        if activities and not main_activities:
            description += "\n\n**Activities:**"
            for i, activity in enumerate(activities, 1):
                activity_name = activity.get('name', f'Activity {i}')
                activity_duration = activity.get('duration', '')
                description += f"\n{i}. {activity_name}"
                if activity_duration:
                    description += f" ({activity_duration}m)"
        
        # Add materials
        materials = lesson_plan.get('materials_needed', [])
        if materials:
            description += f"\n\n**Materials:** {', '.join(materials)}"
        
        description += f"\n\n---\n*Generated by Curriculum Designer MCP*\n*Stored in DynamoDB as: {plan_id}*"
        
        try:
            async with httpx.AsyncClient() as client:
                url = "https://api.trello.com/1/cards"
                params = {
                    "key": self.trello_key,
                    "token": self.trello_token,
                    "idList": self.active_list_id,
                    "name": title,
                    "desc": description
                }
                
                response = await client.post(url, params=params)
                response.raise_for_status()
                card_data = response.json()
                
                return card_data.get('id')
                
        except Exception as e:
            print(f"Error creating Trello card: {str(e)}")
            return None

    async def save_lesson_plan(self, lesson_plan: Dict[str, Any], plan_id: Optional[str] = None) -> Dict[str, Any]:
        """Save a generated lesson plan for future reference"""
        
        if not plan_id:
            plan_id = f"lesson_{int(time.time())}"
        
        created_at = datetime.now().isoformat()
        
        # Prepare item for DynamoDB
        item = {
            "id": plan_id,
            "type": "lesson_plan",
            "created_at": created_at,
            "lesson_plan": lesson_plan,
            "status": "active"
        }
        
        if self.table:
            try:
                # Save to DynamoDB
                self.table.put_item(Item=item)
                
                # Create Trello card
                trello_card_id = await self.create_trello_card_for_lesson_plan(lesson_plan, plan_id)
                
                result = {
                    "id": plan_id,
                    "created_at": created_at,
                    "status": "saved_to_dynamodb",
                    "table_name": self.dynamodb_table_name,
                    "lesson_plan": lesson_plan
                }
                
                if trello_card_id:
                    result["trello_card_id"] = trello_card_id
                    result["trello_url"] = f"https://trello.com/c/{trello_card_id}"
                    result["status"] = "saved_to_dynamodb_and_trello"
                
                return result
                
            except ClientError as e:
                return {
                    "id": plan_id,
                    "created_at": created_at,
                    "status": "error",
                    "error": str(e),
                    "lesson_plan": lesson_plan
                }
        else:
            # Fallback if DynamoDB not configured
            return {
                "id": plan_id,
                "created_at": created_at,
                "status": "saved_locally",
                "note": "DynamoDB not configured",
                "lesson_plan": lesson_plan
            }

    async def get_saved_lesson_plans(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve saved lesson plans from DynamoDB"""
        
        if not self.table:
            return [{"error": "DynamoDB not configured"}]
        
        try:
            # Query by type using GSI
            response = self.table.query(
                IndexName='type-created_at-index',
                KeyConditionExpression='#type = :type',
                ExpressionAttributeNames={'#type': 'type'},
                ExpressionAttributeValues={':type': 'lesson_plan'},
                ScanIndexForward=False,  # Newest first
                Limit=limit
            )
            
            plans = []
            for item in response.get('Items', []):
                plan = {
                    "id": item["id"],
                    "created_at": item["created_at"],
                    "status": item.get("status", "unknown"),
                    "lesson_plan": item.get("lesson_plan", {})
                }
                # Convert Decimal objects to JSON-serializable types
                plans.append(decimal_to_int(plan))
            
            return plans
            
        except ClientError as e:
            return [{"error": f"DynamoDB query error: {str(e)}"}]

    async def get_lesson_plan_by_id(self, plan_id: str) -> Dict[str, Any]:
        """Retrieve a specific lesson plan by ID"""
        
        if not self.table:
            return {"error": "DynamoDB not configured"}
        
        try:
            response = self.table.get_item(
                Key={
                    'id': plan_id,
                    'type': 'lesson_plan'
                }
            )
            
            if 'Item' in response:
                item = response['Item']
                plan = {
                    "id": item["id"],
                    "created_at": item["created_at"],
                    "status": item.get("status", "unknown"),
                    "lesson_plan": item.get("lesson_plan", {})
                }
                # Convert Decimal objects to JSON-serializable types
                return decimal_to_int(plan)
            else:
                return {"error": f"Lesson plan with ID '{plan_id}' not found"}
                
        except ClientError as e:
            return {"error": f"DynamoDB error: {str(e)}"}

    async def sync_existing_lesson_plans_to_trello(self) -> Dict[str, Any]:
        """Sync all existing lesson plans from DynamoDB to Trello board"""
        
        if not self.lesson_plans_board_id:
            return {"error": "Trello lesson plans board not configured"}
        
        # Get all saved lesson plans
        existing_plans = await self.get_saved_lesson_plans(limit=50)
        
        if not existing_plans or (len(existing_plans) == 1 and existing_plans[0].get('error')):
            return {"message": "No lesson plans to sync"}
        
        results = {"synced": [], "errors": []}
        
        for plan in existing_plans:
            if plan.get('error'):
                continue
                
            plan_id = plan.get('id')
            lesson_plan = plan.get('lesson_plan', {})
            
            try:
                card_id = await self.create_trello_card_for_lesson_plan(lesson_plan, plan_id)
                if card_id:
                    results["synced"].append({
                        "plan_id": plan_id,
                        "card_id": card_id,
                        "card_url": f"https://trello.com/c/{card_id}"
                    })
                else:
                    results["errors"].append(f"Failed to create card for {plan_id}")
            except Exception as e:
                results["errors"].append(f"Error syncing {plan_id}: {str(e)}")
        
        return {
            "total_plans": len(existing_plans),
            "synced_count": len(results["synced"]),
            "error_count": len(results["errors"]),
            "details": results
        }

    async def submit_feedback(self, 
                            lesson_plan_id: str, 
                            feedback_type: str, 
                            feedback_text: str,
                            rating: Optional[int] = None,
                            source: str = "api") -> Dict[str, Any]:
        """Submit feedback for a lesson plan to improve future generations"""
        
        if not self.feedback_table:
            return {"error": "Feedback storage not configured"}
        
        import uuid
        feedback_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        # Prepare feedback item
        feedback_item = {
            "feedback_id": feedback_id,
            "created_at": created_at,
            "lesson_plan_id": lesson_plan_id,
            "feedback_type": feedback_type.lower(),  # like, dislike, improve, rating
            "feedback_text": feedback_text,
            "source": source,  # api, trello_comment, etc.
            "processed": False
        }
        
        if rating is not None:
            feedback_item["rating"] = rating
        
        try:
            # Save feedback to DynamoDB
            self.feedback_table.put_item(Item=feedback_item)
            
            return {
                "feedback_id": feedback_id,
                "status": "feedback_saved",
                "lesson_plan_id": lesson_plan_id,
                "feedback_type": feedback_type,
                "created_at": created_at
            }
            
        except ClientError as e:
            return {
                "error": f"Failed to save feedback: {str(e)}",
                "feedback_type": feedback_type,
                "lesson_plan_id": lesson_plan_id
            }

    async def get_lesson_plan_feedback(self, lesson_plan_id: str) -> List[Dict[str, Any]]:
        """Get all feedback for a specific lesson plan"""
        
        if not self.feedback_table:
            return [{"error": "Feedback storage not configured"}]
        
        try:
            # Query feedback by lesson plan ID using GSI
            response = self.feedback_table.query(
                IndexName='lesson-plan-feedback-index',
                KeyConditionExpression='lesson_plan_id = :lesson_plan_id',
                ExpressionAttributeValues={':lesson_plan_id': lesson_plan_id},
                ScanIndexForward=False  # Newest first
            )
            
            feedback_list = []
            for item in response.get('Items', []):
                feedback = {
                    "feedback_id": item["feedback_id"],
                    "created_at": item["created_at"],
                    "feedback_type": item["feedback_type"],
                    "feedback_text": item["feedback_text"],
                    "source": item.get("source", "unknown"),
                    "rating": item.get("rating")
                }
                # Convert any Decimal objects
                feedback_list.append(decimal_to_int(feedback))
            
            return feedback_list
            
        except ClientError as e:
            return [{"error": f"DynamoDB error: {str(e)}"}]

    async def analyze_feedback_patterns(self) -> Dict[str, Any]:
        """Analyze feedback patterns to improve lesson plan generation"""
        
        if not self.feedback_table:
            return {"error": "Feedback storage not configured"}
        
        try:
            # Get all feedback
            response = self.feedback_table.scan()
            feedback_items = response.get('Items', [])
            
            analysis = {
                "total_feedback": len(feedback_items),
                "feedback_breakdown": {"like": 0, "dislike": 0, "improve": 0, "rating": 0},
                "average_rating": 0,
                "common_likes": [],
                "common_dislikes": [],
                "improvement_suggestions": [],
                "lessons_with_feedback": len(set(item.get("lesson_plan_id") for item in feedback_items))
            }
            
            ratings = []
            likes = []
            dislikes = []
            improvements = []
            
            for item in feedback_items:
                feedback_type = item.get("feedback_type", "")
                feedback_text = item.get("feedback_text", "")
                
                if feedback_type in analysis["feedback_breakdown"]:
                    analysis["feedback_breakdown"][feedback_type] += 1
                
                if feedback_type == "like":
                    likes.append(feedback_text)
                elif feedback_type == "dislike":
                    dislikes.append(feedback_text)
                elif feedback_type == "improve":
                    improvements.append(feedback_text)
                elif feedback_type == "rating" and item.get("rating"):
                    ratings.append(float(item["rating"]))
            
            # Calculate average rating
            if ratings:
                analysis["average_rating"] = round(sum(ratings) / len(ratings), 2)
            
            # Store feedback samples (simplified - could use NLP for better analysis)
            analysis["common_likes"] = likes[:5]
            analysis["common_dislikes"] = dislikes[:5]
            analysis["improvement_suggestions"] = improvements[:5]
            
            return decimal_to_int(analysis)
            
        except ClientError as e:
            return {"error": f"DynamoDB error: {str(e)}"}

    async def parse_trello_comment_feedback(self, comment_text: str, lesson_plan_id: str, card_id: str) -> Optional[Dict[str, Any]]:
        """Parse @ai feedback from Trello comments"""
        
        comment_lower = comment_text.lower()
        
        # Look for @ai mentions
        if "@ai" not in comment_lower:
            return None
        
        # Extract feedback type and text
        feedback_data = None
        
        if "like:" in comment_lower or "@ai like" in comment_lower:
            # Extract text after "like:"
            if "like:" in comment_text:
                feedback_text = comment_text.split("like:", 1)[1].strip()
            else:
                feedback_text = comment_text.replace("@ai like", "").strip()
            
            feedback_data = {
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
                "feedback_type": "improve",
                "feedback_text": feedback_text,
                "source": f"trello_comment:{card_id}"
            }
        
        elif "rating:" in comment_lower:
            # Extract rating (e.g., "@ai rating: 4/5" or "@ai rating: 3")
            import re
            rating_match = re.search(r'rating:\s*(\d+)(?:/\d+)?', comment_text, re.IGNORECASE)
            if rating_match:
                rating = int(rating_match.group(1))
                feedback_text = comment_text
                
                feedback_data = {
                    "feedback_type": "rating",
                    "feedback_text": feedback_text,
                    "rating": rating,
                    "source": f"trello_comment:{card_id}"
                }
        
        # Submit feedback if parsed successfully
        if feedback_data:
            return await self.submit_feedback(
                lesson_plan_id=lesson_plan_id,
                feedback_type=feedback_data["feedback_type"],
                feedback_text=feedback_data["feedback_text"],
                rating=feedback_data.get("rating"),
                source=feedback_data["source"]
            )
        
        return None

    async def create_canva_presentation(self, lesson_plan_id: Optional[str] = None, lesson_plan_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a Canva presentation from a lesson plan"""
        
        # Get lesson plan data if ID provided
        if lesson_plan_id and not lesson_plan_data:
            lesson_plan_result = await self.get_lesson_plan_by_id(lesson_plan_id)
            if lesson_plan_result.get("error"):
                return lesson_plan_result
            lesson_plan_data = lesson_plan_result.get("lesson_plan", {})
        
        if not lesson_plan_data:
            return {"error": "No lesson plan data provided"}
        
        # Create Canva presentation
        design = await self.canva_generator.create_lesson_presentation(lesson_plan_data)
        
        # If successful, save the design reference
        if design.get("design_id") and lesson_plan_id:
            # Update the lesson plan in DynamoDB with Canva design info
            if self.table:
                try:
                    self.table.update_item(
                        Key={"id": lesson_plan_id, "type": "lesson_plan"},
                        UpdateExpression="SET canva_design = :design",
                        ExpressionAttributeValues={
                            ":design": {
                                "design_id": design["design_id"],
                                "edit_url": design.get("edit_url", ""),
                                "view_url": design.get("view_url", ""),
                                "created_at": datetime.now().isoformat()
                            }
                        }
                    )
                except Exception as e:
                    print(f"Error updating lesson plan with Canva design: {e}")
        
        return design
    
    async def create_canva_activity_card(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Canva activity card from activity data"""
        
        if not activity_data:
            return {"error": "No activity data provided"}
        
        # Create Canva activity card
        card = await self.canva_generator.create_activity_card(activity_data)
        
        return card
    
    async def export_canva_design(self, design_id: str, format: str = "pdf") -> Dict[str, Any]:
        """Export a Canva design to a specific format"""
        
        if not design_id:
            return {"error": "Design ID required"}
        
        # Export the design
        export_result = await self.canva_generator.export_design(design_id, format)
        
        return export_result
    
    async def get_comprehensive_resources(self, topic: Optional[str] = None) -> Dict[str, Any]:
        """Get all available resources for a topic from all sources"""
        
        resources = {
            "topic": topic or "all",
            "sources": {},
            "summary": {}
        }
        
        # Get Trello activities
        if topic:
            trello_activities = await self.search_activities(topic)
        else:
            trello_activities = await self.get_activities()
        
        resources["sources"]["trello"] = {
            "count": len(trello_activities),
            "activities": trello_activities[:5]  # Limit to first 5 for summary
        }
        
        # Get Google Drive resources
        drive_files = await self.get_drive_resources(topic)
        resources["sources"]["google_drive"] = {
            "count": len([f for f in drive_files if not f.get("error")]),
            "files": drive_files[:5] if not any(f.get("error") for f in drive_files) else drive_files
        }
        
        # Get business context
        business_context = await self.get_business_context()
        resources["sources"]["business_context"] = business_context
        
        # Create summary
        resources["summary"] = {
            "total_trello_activities": len(trello_activities),
            "total_drive_files": len([f for f in drive_files if not f.get("error")]),
            "business_name": business_context["business_name"],
            "last_updated": datetime.now().isoformat()
        }
        
        return resources