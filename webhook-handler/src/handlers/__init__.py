"""Request handlers for webhook processing with ESL support for adult learners."""

import logging
import json
from typing import Dict, Any, Optional

from ..config import get_config
from ..models import WebhookPayload, LambdaResponse, ActionType
from ..clients import get_trello_client, cleanup_clients
from ..services import get_ai_service, get_feedback_service, get_framework_service, get_activity_service
from ..utils import ErrorBoundary, get_trello_api_key, get_trello_token, get_openai_api_key

logger = logging.getLogger(__name__)
config = get_config()


class CommentHandler:
    """Handler for comment card actions."""
    
    def __init__(self):
        self.trello_client = get_trello_client()
        self.ai_service = get_ai_service()
        self.feedback_service = get_feedback_service()
        self.framework_service = get_framework_service()
        self.activity_service = get_activity_service()
    
    async def handle(self, action: Dict[str, Any]) -> None:
        """Process comment actions."""
        with ErrorBoundary("handle_comment", logger):
            comment_text = action["data"]["text"]
            card = action["data"]["card"]
            card_id = card["id"]
            
            # Get member who created the comment
            member_creator = action.get("memberCreator", {})
            member_username = member_creator.get("username", "")
            
            logger.info(f"Processing comment from {member_username} on card {card_id}")
            
            # Prevent infinite loops: Skip bot responses
            bot_markers = [
                "🤖 **AI Assistant:**", "✅ **Framework Saved Successfully!**",
                "📚 **Stored Frameworks", "❌", "🚧", "🔄 Starting",
                "✅ Found", "✅ Using", "✅ Created", "✅ **Activity Generated Successfully!**"
            ]
            
            if any(marker in comment_text for marker in bot_markers):
                logger.debug("Skipping bot-generated comment to prevent infinite loop")
                return
            
            # Check if comment mentions AI
            if "@ai" not in comment_text.lower():
                logger.debug("No @ai mention found in comment")
                return
            
            logger.info("Found @ai mention, processing AI request")
            
            # Get card details for context
            card_details = await self.trello_client.get_card(card_id)
            
            # Check if this is a lesson plan card (from lesson plans board)
            card_board_id = card_details.get("idBoard")
            
            if card_board_id == config.LESSON_PLANS_BOARD_ID:
                logger.info("This is a lesson plan card, checking for feedback")
                await self._handle_lesson_plan_feedback(comment_text, card_id, card_details)
                return
            
            # Process different types of AI requests
            ai_request = comment_text.lower().replace("@ai", "").strip()
            
            if "activity" in ai_request and "framework" not in ai_request:
                await self._handle_activity_command(ai_request, card_details, card_id)
            elif any(cmd in ai_request for cmd in ["save framework", "generate variants", "list frameworks"]):
                await self._handle_framework_command(ai_request, card_details, card_id)
            else:
                await self._handle_general_ai_request(ai_request, card_details, card_id)
    
    async def _handle_lesson_plan_feedback(self, comment_text: str, card_id: str, card_details: Dict[str, Any]) -> None:
        """Handle feedback for lesson plan cards."""
        feedback = self.feedback_service.parse_feedback_from_comment(comment_text, card_details)
        
        if feedback:
            logger.info(f"Parsed feedback: {feedback.feedback_type}")
            result = await self.feedback_service.submit_feedback(feedback)
            
            if result:
                ack_comment = f"✅ **Feedback Received**\n\nThanks for the feedback! I've recorded your {feedback.feedback_type} and will use it to improve future lesson plans."
                await self.trello_client.add_comment(card_id, ack_comment)
            else:
                logger.error("Failed to submit feedback")
        else:
            logger.info("No feedback detected, processing as general AI request")
            ai_request = comment_text.lower().replace("@ai", "").strip()
            await self._handle_general_ai_request(ai_request, card_details, card_id)
    
    async def _handle_activity_command(self, ai_request: str, card_details: Dict[str, Any], card_id: str) -> None:
        """Handle activity generation commands."""
        try:
            # Parse the activity request
            request = self.activity_service.parse_activity_request(ai_request, card_details)
            
            await self.trello_client.add_comment(
                card_id,
                f"🎯 **Generating Activity**\n\n📚 Topic: {request.topic}\n📊 ESL Level: {request.esl_level}\n⏱️ Duration: {request.duration} minutes\n🎨 Type: {request.activity_type or 'Auto-selected'}"
            )
            
            # Generate the activity
            activity = await self.activity_service.generate_activity(request)
            
            # Format the response
            comment = self._format_activity_response(activity)
            await self.trello_client.add_comment(card_id, comment)
            
            # Create a separate card with full details if needed
            if activity.get('activity_id'):
                await self._create_activity_card(activity, card_details)
                
        except Exception as e:
            logger.error(f"Error in activity generation: {e}")
            error_comment = f"❌ **Error generating activity:** {str(e)}\n\nPlease check your parameters and try again.\n\n**Usage:** `@ai activity \"topic\" esl_level duration [type]`\n\n**Example:** `@ai activity \"coffee farming\" intermediate 15 discussion`"
            await self.trello_client.add_comment(card_id, error_comment)
    
    async def _handle_framework_command(self, ai_request: str, card_details: Dict[str, Any], card_id: str) -> None:
        """Handle framework-specific AI commands."""
        try:
            if "save framework" in ai_request:
                await self._save_framework(card_details, card_id)
            elif "list frameworks" in ai_request:
                await self._list_frameworks(card_details, card_id)
            elif "generate variants" in ai_request:
                await self._generate_framework_variants(ai_request, card_id)
                
        except Exception as e:
            logger.error(f"Error in framework command: {e}")
            await self.trello_client.add_comment(card_id, f"❌ Error processing framework command: {str(e)}")
    
    async def _handle_general_ai_request(self, ai_request: str, card_details: Dict[str, Any], card_id: str) -> None:
        """Handle general AI assistance requests."""
        try:
            context = f"Card: {card_details.get('name', '')}\nDescription: {card_details.get('desc', '')}"
            prompt = f"Teacher asks: {ai_request}\nContext: {context}"
            
            response = await self.ai_service.get_response(prompt)
            ai_comment = f"🤖 **AI Assistant:**\n\n{response}"
            await self.trello_client.add_comment(card_id, ai_comment)
            
        except Exception as e:
            logger.error(f"Error in general AI request: {e}")
            await self.trello_client.add_comment(card_id, f"❌ Error processing AI request: {str(e)}")
    
    async def _save_framework(self, card_details: Dict[str, Any], card_id: str) -> None:
        """Save framework from card description."""
        framework_data_str = card_details.get('desc', '')
        framework_name = card_details.get('name', 'Unnamed Framework')
        
        if not framework_data_str:
            await self.trello_client.add_comment(
                card_id, 
                "❌ No framework data found in card description. Please add your framework structure in JSON format to the card description."
            )
            return
        
        try:
            framework_data = json.loads(framework_data_str)
            board_id = card_details.get('idBoard', config.DEFAULT_BOARD_ID)
            
            framework_id = await self.framework_service.save_framework(
                framework_data, framework_name, board_id
            )
            
            response_msg = f"✅ **Framework Saved Successfully!**\n\n"
            response_msg += f"Framework: **{framework_name}**\n"
            response_msg += f"ID: `{framework_id}`\n\n"
            response_msg += f"You can now generate variants with:\n"
            response_msg += f"`@ai generate variants framework_id={framework_id} num=5`"
            
            await self.trello_client.add_comment(card_id, response_msg)
            
        except json.JSONDecodeError:
            await self.trello_client.add_comment(
                card_id, 
                "❌ Invalid JSON in card description. Please ensure your framework is properly formatted JSON."
            )
    
    async def _list_frameworks(self, card_details: Dict[str, Any], card_id: str) -> None:
        """List stored frameworks for the board."""
        board_id = card_details.get('idBoard', config.DEFAULT_BOARD_ID)
        frameworks = self.framework_service.list_frameworks(board_id)
        
        if not frameworks:
            await self.trello_client.add_comment(card_id, "📚 No stored frameworks found for this board.")
            return
        
        msg = f"📚 **Stored Frameworks ({len(frameworks)} found):**\n\n"
        for fw in frameworks:
            msg += f"• **{fw.get('framework_name', 'Unnamed')}**\n"
            msg += f"  ID: `{fw.get('framework_id')}`\n"
            msg += f"  Created: {fw.get('created_at', '')[:10]}\n\n"
        
        msg += "💡 Generate variants with: `@ai generate variants framework_id=<id>`"
        await self.trello_client.add_comment(card_id, msg)
    
    async def _generate_framework_variants(self, ai_request: str, card_id: str) -> None:
        """Generate framework variants."""
        import re
        
        framework_id_match = re.search(r'framework_id=([a-f0-9-]+)', ai_request)
        num_match = re.search(r'num=(\d+)', ai_request)
        
        if not framework_id_match:
            await self.trello_client.add_comment(
                card_id, 
                "❌ Please specify framework_id. Usage: `@ai generate variants framework_id=<id> num=<number>`"
            )
            return
        
        framework_id = framework_id_match.group(1)
        num_variants = int(num_match.group(1)) if num_match else 3
        
        framework = self.framework_service.get_framework(framework_id)
        if not framework:
            await self.trello_client.add_comment(card_id, f"❌ Framework not found: {framework_id}")
            return
        
        await self.trello_client.add_comment(card_id, f"🔄 Starting variant generation for {framework_id}...")
        
        created_cards = await self.framework_service.generate_framework_variants(
            framework_id, framework['framework_data'], num_variants, framework['board_id']
        )
        
        if created_cards:
            await self.trello_client.add_comment(
                card_id, 
                f"✅ Created {len(created_cards)} framework variants!"
            )
        else:
            await self.trello_client.add_comment(card_id, "❌ Failed to create framework variants")
    
    def _format_activity_response(self, activity: Dict[str, Any]) -> str:
        """Format activity response for Trello comment."""
        comment = f"✅ **Activity Generated Successfully!**\n\n"
        comment += f"**{activity.get('title', 'Activity')}**\n\n"
        
        if activity.get('activity_id'):
            comment += f"📌 Activity ID: `{activity['activity_id']}`\n\n"
        
        # Format slides for display
        slides = activity.get('slides', [])
        for slide in slides[:3]:  # Show first 3 slides
            comment += f"**Slide {slide.get('slide_number', '')} - {slide.get('type', '')}**\n"
            comment += f"*Title:* {slide.get('title', '')}\n\n"
            
            if slide.get('teacher_notes'):
                comment += f"👩‍🏫 *Teacher Notes:* {slide['teacher_notes'][:100]}...\n"
            if slide.get('timing'):
                comment += f"⏱️ *Timing:* {slide['timing']}\n"
            comment += "\n---\n\n"
        
        if len(slides) > 3:
            comment += f"...(and {len(slides) - 3} more slides)\n\n"
        
        # Add metadata
        metadata = activity.get('metadata', {})
        if metadata:
            comment += f"**Activity Details:**\n"
            comment += f"• Energy Level: {metadata.get('energy_level', 'medium')}\n"
            comment += f"• Duration: {metadata.get('duration', '15 minutes')}\n"
        
        # Truncate if too long for Trello
        if len(comment) > 16000:
            comment = comment[:15900] + "\n\n...[Content truncated for display]"
        
        return comment
    
    async def _create_activity_card(self, activity: Dict[str, Any], card_details: Dict[str, Any]) -> None:
        """Create a separate card with full activity details."""
        activities_list_id = await self.trello_client.get_or_create_list(
            card_details.get('idBoard'), 
            "Generated Activities"
        )
        
        if activities_list_id:
            card_id = await self.trello_client.create_card(
                activities_list_id,
                activity.get('title', f"Activity: {activity.get('topic', 'Unknown')}"),
                json.dumps(activity, indent=2)
            )
            
            if card_id:
                logger.info(f"Created detailed activity card: {card_id}")


class WebhookHandler:
    """Main webhook handler."""
    
    def __init__(self):
        self.comment_handler = CommentHandler()
    
    async def handle(self, event: Dict[str, Any], context: Any) -> LambdaResponse:
        """Handle incoming webhook events."""
        try:
            logger.info(f"Received event: {event.get('httpMethod')} {event.get('path')}")
            
            # Handle API Gateway event
            if event.get("httpMethod"):
                return await self._handle_api_gateway_event(event)
            
            # Default response
            return LambdaResponse(
                statusCode=404,
                body=json.dumps({"message": "Not found"})
            )
            
        except Exception as e:
            logger.error(f"Lambda error: {e}", exc_info=True)
            return LambdaResponse(
                statusCode=500,
                body=json.dumps({"status": "error", "message": str(e)})
            )
        finally:
            # Clean up connections for Lambda
            await cleanup_clients()
    
    async def _handle_api_gateway_event(self, event: Dict[str, Any]) -> LambdaResponse:
        """Handle API Gateway events."""
        method = event["httpMethod"]
        path = event["path"]
        
        # Parse body
        body = event.get("body", "{}")
        if isinstance(body, str) and body:
            try:
                payload = json.loads(body)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                payload = {}
        else:
            payload = body if body else {}
        
        # Route requests
        if path == "/webhook":
            return await self._handle_webhook_endpoint(method, payload)
        elif path == "/health":
            return await self._handle_health_check()
        elif path == "/":
            return self._handle_root()
        
        return LambdaResponse(
            statusCode=404,
            body=json.dumps({"message": "Not found"})
        )
    
    async def _handle_webhook_endpoint(self, method: str, payload: Dict[str, Any]) -> LambdaResponse:
        """Handle webhook endpoint requests."""
        if method in ["GET", "HEAD"]:
            # Webhook verification
            body = json.dumps({"status": "webhook endpoint ready"}) if method == "GET" else ""
            return LambdaResponse(statusCode=200, body=body)
        
        elif method == "POST":
            try:
                webhook_payload = WebhookPayload(**payload)
                action = webhook_payload.action
                
                logger.info(f"Processing webhook action: {action.type}")
                
                if action.type == ActionType.COMMENT_CARD:
                    await self.comment_handler.handle(action.dict())
                
                return LambdaResponse(
                    statusCode=200,
                    body=json.dumps({"status": "ok", "processed": action.type})
                )
                
            except Exception as e:
                logger.error(f"Error processing webhook: {e}")
                return LambdaResponse(
                    statusCode=500,
                    body=json.dumps({"status": "error", "message": str(e)})
                )
        
        return LambdaResponse(
            statusCode=405,
            body=json.dumps({"message": "Method not allowed"})
        )
    
    async def _handle_health_check(self) -> LambdaResponse:
        """Handle health check requests."""
        return LambdaResponse(
            statusCode=200,
            body=json.dumps({
                "status": "healthy",
                "services": {
                    "trello": bool(get_trello_api_key() and get_trello_token()),
                    "openai": bool(get_openai_api_key())
                }
            })
        )
    
    def _handle_root(self) -> LambdaResponse:
        """Handle root endpoint requests."""
        return LambdaResponse(
            statusCode=200,
            body=json.dumps({"message": "Curriculum AI Webhook Handler", "status": "running"})
        )