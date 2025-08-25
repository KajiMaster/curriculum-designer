"""
Canva API Integration for Curriculum Designer
Converts lesson plans into Canva presentations
"""

import os
import httpx
from typing import Dict, Any, List, Optional
import json
from datetime import datetime


class CanvaDesignGenerator:
    def __init__(self):
        # Load credentials from Parameter Store
        self.canva_client_id = self._get_parameter("/global/curriculum-designer/canva-client-id")
        self.canva_client_secret = self._get_parameter("/global/curriculum-designer/canva-client-secret")
        self.base_url = "https://api.canva.com/rest/v1"
        
        # Load tokens from Parameter Store
        self.canva_access_token = self._get_parameter("/global/curriculum-designer/canva-access-token")
        self.canva_refresh_token = self._get_parameter("/global/curriculum-designer/canva-refresh-token")
        
        # Template IDs for different types of educational content
        self.templates = {
            "lesson_plan": os.getenv("CANVA_LESSON_TEMPLATE_ID"),
            "activity_card": os.getenv("CANVA_ACTIVITY_TEMPLATE_ID"),
            "worksheet": os.getenv("CANVA_WORKSHEET_TEMPLATE_ID")
        }
    
    def _get_parameter(self, parameter_name: str) -> Optional[str]:
        """Get parameter from AWS Parameter Store"""
        try:
            import boto3
            ssm = boto3.client('ssm')
            response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
            value = response['Parameter']['Value']
            print(f"✅ Successfully loaded parameter {parameter_name}")
            return value
        except Exception as e:
            print(f"❌ Could not load parameter {parameter_name}: {e}")
            return None
    
    async def create_lesson_presentation(self, lesson_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a complete Canva presentation from a lesson plan
        """
        slides_data = self._prepare_slides_data(lesson_plan)
        
        # Create the design using Canva API
        design = await self._create_design(
            title=f"Lesson: {lesson_plan.get('title', 'Untitled')}",
            design_type="presentation",
            slides_data=slides_data
        )
        
        return design
    
    def _prepare_slides_data(self, lesson_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert lesson plan into structured slide data
        """
        slides = []
        
        # Slide 1: Title slide
        slides.append({
            "type": "title",
            "elements": {
                "title": lesson_plan.get("title", "Lesson Plan"),
                "subtitle": f"Level: {lesson_plan.get('level', 'Intermediate')}",
                "duration": f"Duration: {lesson_plan.get('total_duration', 90)} minutes",
                "date": datetime.now().strftime("%B %d, %Y")
            }
        })
        
        # Slide 2: Objectives
        objectives = lesson_plan.get("objectives", [])
        if not objectives and lesson_plan.get("focus_area"):
            objectives = [f"Master {lesson_plan['focus_area']} concepts"]
        
        slides.append({
            "type": "objectives",
            "elements": {
                "heading": "Learning Objectives",
                "bullet_points": objectives[:5]  # Max 5 objectives per slide
            }
        })
        
        # Slide 3: Materials Needed
        materials = lesson_plan.get("materials_needed", [])
        if materials:
            slides.append({
                "type": "materials",
                "elements": {
                    "heading": "Materials Needed",
                    "items": materials
                }
            })
        
        # Slides 4+: Activities
        structure = lesson_plan.get("structure", {})
        
        # Warm-up slide
        if structure.get("warmup"):
            warmup = structure["warmup"]
            slides.append({
                "type": "activity",
                "elements": {
                    "heading": "Warm-Up Activity",
                    "title": warmup.get("name", "Warm-up"),
                    "duration": f"{warmup.get('duration', 10)} minutes",
                    "description": warmup.get("description", ""),
                    "instructions": warmup.get("instructions", [])
                }
            })
        
        # Main activities
        main_activities = structure.get("main_activities", [])
        for i, activity in enumerate(main_activities, 1):
            slides.append({
                "type": "activity",
                "elements": {
                    "heading": f"Activity {i}",
                    "title": activity.get("name", f"Activity {i}"),
                    "duration": f"{activity.get('duration', 15)} minutes",
                    "description": activity.get("description", ""),
                    "category": activity.get("category", ""),
                    "level": activity.get("level", ""),
                    "materials": activity.get("materials", "")
                }
            })
        
        # Cool-down slide if exists
        if structure.get("cooldown"):
            cooldown = structure["cooldown"]
            slides.append({
                "type": "activity",
                "elements": {
                    "heading": "Cool-Down & Review",
                    "title": cooldown.get("name", "Cool-down"),
                    "duration": f"{cooldown.get('duration', 10)} minutes",
                    "description": cooldown.get("description", "")
                }
            })
        
        # Final slide: Summary/Homework
        slides.append({
            "type": "summary",
            "elements": {
                "heading": "Lesson Summary",
                "key_points": self._extract_key_points(lesson_plan),
                "homework": lesson_plan.get("homework", "Review today's materials"),
                "next_lesson": lesson_plan.get("next_lesson", "To be announced")
            }
        })
        
        return slides
    
    def _extract_key_points(self, lesson_plan: Dict[str, Any]) -> List[str]:
        """Extract key learning points from the lesson plan"""
        points = []
        
        # Add focus area
        if lesson_plan.get("focus_area"):
            points.append(f"Focused on {lesson_plan['focus_area']}")
        
        # Add activity count
        activities = lesson_plan.get("structure", {}).get("main_activities", [])
        if activities:
            points.append(f"Completed {len(activities)} main activities")
        
        # Add skills practiced
        if lesson_plan.get("skills"):
            points.append(f"Practiced: {', '.join(lesson_plan['skills'][:3])}")
        
        return points or ["Great work today!", "Keep practicing!"]
    
    async def _refresh_access_token(self) -> bool:
        """Refresh the Canva access token using refresh token"""
        if not self.canva_refresh_token:
            return False
        
        import base64
        credentials = base64.b64encode(f"{self.canva_client_id}:{self.canva_client_secret}".encode()).decode()
        
        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.canva_refresh_token
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.base_url}/oauth/token", headers=headers, data=data)
                if response.status_code == 200:
                    tokens = response.json()
                    self.canva_access_token = tokens.get("access_token")
                    new_refresh_token = tokens.get("refresh_token")
                    
                    # Store the new tokens in Parameter Store for future use
                    try:
                        import boto3
                        ssm = boto3.client('ssm')
                        ssm.put_parameter(
                            Name="/global/curriculum-designer/canva-access-token",
                            Value=self.canva_access_token,
                            Type="SecureString",
                            Overwrite=True
                        )
                        if new_refresh_token:
                            ssm.put_parameter(
                                Name="/global/curriculum-designer/canva-refresh-token",
                                Value=new_refresh_token,
                                Type="SecureString",
                                Overwrite=True
                            )
                            self.canva_refresh_token = new_refresh_token
                        print("✅ Successfully refreshed and stored new Canva tokens")
                    except Exception as store_error:
                        print(f"Warning: Could not store new tokens: {store_error}")
                    
                    return True
                else:
                    print(f"Failed to refresh token: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Error refreshing Canva token: {e}")
        
        return False
    
    async def _create_design(self, title: str, design_type: str, slides_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a design in Canva using the API
        """
        print(f"🎨 Creating Canva design: {title}")
        print(f"📊 Access token available: {bool(self.canva_access_token)}")
        
        if not self.canva_access_token:
            print("❌ No access token available")
            return {
                "error": "Canva access token not configured",
                "note": "Token not loaded from Parameter Store",
                "slides_data": slides_data,
                "status": "ready_for_manual_creation"
            }
        
        headers = {
            "Authorization": f"Bearer {self.canva_access_token}",
            "Content-Type": "application/json"
        }
        
        # Create the design - correct format for Canva API
        design_data = {
            "design_type": {
                "type": "preset",
                "name": design_type
            },
            "title": title
        }
        
        async with httpx.AsyncClient() as client:
            try:
                print(f"🚀 Making API call to Canva with data: {design_data}")
                # Create the design using Canva API
                response = await client.post(
                    f"{self.base_url}/designs",
                    headers=headers,
                    json=design_data
                )
                print(f"📡 API Response Status: {response.status_code}")
                print(f"📝 API Response: {response.text[:200]}...")
                
                # If token expired, try to refresh and retry once
                if response.status_code == 401:
                    print("🔄 Access token expired, attempting to refresh...")
                    if await self._refresh_access_token():
                        headers["Authorization"] = f"Bearer {self.canva_access_token}"
                        response = await client.post(
                            f"{self.base_url}/designs",
                            headers=headers,
                            json=design_data
                        )
                    else:
                        return {
                            "error": "Failed to refresh Canva access token",
                            "note": "Please re-authorize the Canva integration"
                        }
                
                response.raise_for_status()
                
                response_data = response.json()
                design = response_data.get("design", {})
                design_id = design.get("id")
                
                print(f"🎉 Successfully created Canva design: {design_id}")
                
                # Add slides content (this would use the Design Editing API)
                # For now, return the created design info
                return {
                    "design_id": design_id,
                    "edit_url": design.get("urls", {}).get("edit_url"),
                    "view_url": design.get("urls", {}).get("view_url"),
                    "title": title,
                    "slides_count": len(slides_data),
                    "slides_data": slides_data,
                    "status": "created",
                    "note": "Design created successfully in Canva! Click edit_url to view and customize.",
                    "canva_design_created": True
                }
                
            except httpx.HTTPStatusError as e:
                return {
                    "error": f"Canva API error: {e.response.status_code}",
                    "details": e.response.text
                }
            except Exception as e:
                return {
                    "error": f"Failed to create design: {str(e)}"
                }
    
    async def create_activity_card(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a single activity card design in Canva
        """
        card_data = {
            "title": activity.get("name", "Activity"),
            "duration": f"{activity.get('duration', 15)} minutes",
            "level": activity.get("level", "Intermediate"),
            "category": activity.get("category", "General"),
            "description": activity.get("description", ""),
            "materials": activity.get("materials", ""),
            "instructions": activity.get("instructions", [])
        }
        
        # Create a custom design for the card
        design = await self._create_design(
            title=f"Activity: {card_data['title']}",
            design_type="presentation",  # Using presentation type for cards too
            slides_data=[{"type": "activity_card", "elements": card_data}]
        )
        
        return design
    
    async def export_design(self, design_id: str, format: str = "pdf") -> Dict[str, Any]:
        """
        Export a Canva design to a specific format
        """
        if not self.canva_access_token:
            return {"error": "Canva access token not configured"}
        
        headers = {
            "Authorization": f"Bearer {self.canva_access_token}",
            "Content-Type": "application/json"
        }
        
        export_data = {
            "format": format,  # pdf, png, jpg
            "quality": "print"  # print, standard, low
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/designs/{design_id}/exports",
                    headers=headers,
                    json=export_data
                )
                response.raise_for_status()
                
                export_info = response.json()
                return {
                    "export_id": export_info.get("id"),
                    "status": export_info.get("status"),
                    "download_url": export_info.get("urls", {}).get("download_url"),
                    "format": format
                }
                
            except Exception as e:
                return {"error": f"Failed to export design: {str(e)}"}