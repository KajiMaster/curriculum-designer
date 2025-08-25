"""
MCP Server Lambda Handler for Curriculum Designer
Provides Trello curriculum activities as context via Lambda
"""

import json
import os
import asyncio
from typing import Any, Dict, List, Optional
import base64

import httpx
from server import CurriculumMCPServer


class MCPLambdaHandler:
    def __init__(self):
        self.mcp_server = CurriculumMCPServer()
        
    async def handle_mcp_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP protocol requests"""
        try:
            # Parse MCP request from event body
            if 'body' in event:
                if event.get('isBase64Encoded'):
                    body = base64.b64decode(event['body']).decode('utf-8')
                else:
                    body = event['body']
                
                if isinstance(body, str):
                    request_data = json.loads(body)
                else:
                    request_data = body
            else:
                request_data = event
            
            # Handle different MCP methods
            method = request_data.get('method')
            params = request_data.get('params', {})
            
            if method == 'tools/list':
                tools = await self._get_tools()
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'jsonrpc': '2.0',
                        'id': request_data.get('id'),
                        'result': {'tools': tools}
                    }),
                    'headers': {'Content-Type': 'application/json'}
                }
            
            elif method == 'tools/call':
                tool_name = params.get('name')
                tool_args = params.get('arguments', {})
                
                result = await self._call_tool(tool_name, tool_args)
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'jsonrpc': '2.0',
                        'id': request_data.get('id'),
                        'result': {'content': [{'type': 'text', 'text': json.dumps(result, indent=2)}]}
                    }),
                    'headers': {'Content-Type': 'application/json'}
                }
            
            else:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': f'Unknown method: {method}'}),
                    'headers': {'Content-Type': 'application/json'}
                }
                
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)}),
                'headers': {'Content-Type': 'application/json'}
            }

    async def handle_http_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle direct HTTP API requests"""
        try:
            path = event.get('path', '')
            method = event.get('httpMethod', 'GET')
            
            if path == '/health':
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'status': 'healthy',
                        'service': 'curriculum-designer-mcp',
                        'capabilities': [
                            'get_activities', 
                            'search_activities', 
                            'suggest_lesson_plan', 
                            'get_board_structure',
                            'get_drive_resources',
                            'get_business_context',
                            'get_comprehensive_resources',
                            'save_lesson_plan',
                            'get_saved_lesson_plans',
                            'get_lesson_plan_by_id',
                            'sync_lesson_plans_to_trello',
                            'submit_feedback',
                            'get_lesson_plan_feedback',
                            'analyze_feedback_patterns',
                            'create_canva_presentation',
                            'create_canva_activity_card',
                            'export_canva_design'
                        ]
                    }),
                    'headers': {'Content-Type': 'application/json'}
                }
            
            elif path == '/activities' and method == 'GET':
                # Parse query parameters
                query_params = event.get('queryStringParameters') or {}
                activities = await self.mcp_server.get_activities(
                    category=query_params.get('category'),
                    level=query_params.get('level'),
                    duration=int(query_params['duration']) if query_params.get('duration') else None
                )
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(activities, indent=2),
                    'headers': {'Content-Type': 'application/json'}
                }
            
            elif path == '/search' and method == 'GET':
                query_params = event.get('queryStringParameters') or {}
                query = query_params.get('q', '')
                
                if not query:
                    return {
                        'statusCode': 400,
                        'body': json.dumps({'error': 'Query parameter "q" is required'}),
                        'headers': {'Content-Type': 'application/json'}
                    }
                
                results = await self.mcp_server.search_activities(query)
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(results, indent=2),
                    'headers': {'Content-Type': 'application/json'}
                }
            
            elif path == '/lesson-plan' and method == 'POST':
                # Parse request body
                if event.get('body'):
                    if event.get('isBase64Encoded'):
                        body = base64.b64decode(event['body']).decode('utf-8')
                    else:
                        body = event['body']
                    
                    params = json.loads(body) if isinstance(body, str) else body
                else:
                    return {
                        'statusCode': 400,
                        'body': json.dumps({'error': 'Request body required'}),
                        'headers': {'Content-Type': 'application/json'}
                    }
                
                lesson_plan = await self.mcp_server.suggest_lesson_plan(
                    student_level=params.get('student_level'),
                    focus_area=params.get('focus_area'),
                    total_duration=params.get('total_duration', 120)
                )
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(lesson_plan, indent=2),
                    'headers': {'Content-Type': 'application/json'}
                }
            
            elif path == '/board-structure':
                structure = await self.mcp_server.get_board_structure()
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(structure, indent=2),
                    'headers': {'Content-Type': 'application/json'}
                }
            
            elif path == '/drive-resources' and method == 'GET':
                query_params = event.get('queryStringParameters') or {}
                query = query_params.get('q')
                
                resources = await self.mcp_server.get_drive_resources(query)
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(resources, indent=2),
                    'headers': {'Content-Type': 'application/json'}
                }
            
            elif path == '/business-context' and method == 'GET':
                context = await self.mcp_server.get_business_context()
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(context, indent=2),
                    'headers': {'Content-Type': 'application/json'}
                }
            
            elif path == '/comprehensive-resources' and method == 'GET':
                query_params = event.get('queryStringParameters') or {}
                topic = query_params.get('topic')
                
                resources = await self.mcp_server.get_comprehensive_resources(topic)
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(resources, indent=2),
                    'headers': {'Content-Type': 'application/json'}
                }
            
            elif path == '/saved-lesson-plans' and method == 'GET':
                query_params = event.get('queryStringParameters') or {}
                limit = int(query_params.get('limit', 10))
                
                plans = await self.mcp_server.get_saved_lesson_plans(limit)
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(plans, indent=2),
                    'headers': {'Content-Type': 'application/json'}
                }
            
            elif path.startswith('/lesson-plan/') and method == 'GET':
                # Extract plan ID from path
                plan_id = path.split('/')[-1]
                
                plan = await self.mcp_server.get_lesson_plan_by_id(plan_id)
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(plan, indent=2),
                    'headers': {'Content-Type': 'application/json'}
                }
            
            elif path == '/save-lesson-plan' and method == 'POST':
                # Parse request body
                if event.get('body'):
                    if event.get('isBase64Encoded'):
                        body = base64.b64decode(event['body']).decode('utf-8')
                    else:
                        body = event['body']
                    
                    params = json.loads(body) if isinstance(body, str) else body
                else:
                    return {
                        'statusCode': 400,
                        'body': json.dumps({'error': 'Request body required'}),
                        'headers': {'Content-Type': 'application/json'}
                    }
                
                result = await self.mcp_server.save_lesson_plan(
                    lesson_plan=params.get('lesson_plan', {}),
                    plan_id=params.get('plan_id')
                )
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(result, indent=2),
                    'headers': {'Content-Type': 'application/json'}
                }
            
            elif path == '/sync-lesson-plans-to-trello' and method == 'POST':
                result = await self.mcp_server.sync_existing_lesson_plans_to_trello()
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(result, indent=2),
                    'headers': {'Content-Type': 'application/json'}
                }
            
            elif path == '/feedback' and method == 'POST':
                # Submit feedback for a lesson plan
                if event.get('body'):
                    if event.get('isBase64Encoded'):
                        body = base64.b64decode(event['body']).decode('utf-8')
                    else:
                        body = event['body']
                    
                    params = json.loads(body) if isinstance(body, str) else body
                else:
                    return {
                        'statusCode': 400,
                        'body': json.dumps({'error': 'Request body required'}),
                        'headers': {'Content-Type': 'application/json'}
                    }
                
                result = await self.mcp_server.submit_feedback(
                    lesson_plan_id=params.get('lesson_plan_id'),
                    feedback_type=params.get('feedback_type'),
                    feedback_text=params.get('feedback_text'),
                    rating=params.get('rating'),
                    source=params.get('source', 'api')
                )
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(result, indent=2),
                    'headers': {'Content-Type': 'application/json'}
                }
            
            elif path.startswith('/feedback/') and method == 'GET':
                # Get feedback for specific lesson plan
                lesson_plan_id = path.split('/')[-1]
                
                feedback = await self.mcp_server.get_lesson_plan_feedback(lesson_plan_id)
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(feedback, indent=2),
                    'headers': {'Content-Type': 'application/json'}
                }
            
            elif path == '/feedback-analysis' and method == 'GET':
                analysis = await self.mcp_server.analyze_feedback_patterns()
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(analysis, indent=2),
                    'headers': {'Content-Type': 'application/json'}
                }
            
            elif path == '/canva-presentation' and method == 'POST':
                # Create Canva presentation from lesson plan
                if event.get('body'):
                    if event.get('isBase64Encoded'):
                        body = base64.b64decode(event['body']).decode('utf-8')
                    else:
                        body = event['body']
                    
                    params = json.loads(body) if isinstance(body, str) else body
                else:
                    return {
                        'statusCode': 400,
                        'body': json.dumps({'error': 'Request body required'}),
                        'headers': {'Content-Type': 'application/json'}
                    }
                
                result = await self.mcp_server.create_canva_presentation(
                    lesson_plan_id=params.get('lesson_plan_id'),
                    lesson_plan_data=params.get('lesson_plan_data')
                )
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(result, indent=2),
                    'headers': {'Content-Type': 'application/json'}
                }
            
            elif path == '/canva-activity-card' and method == 'POST':
                # Create Canva activity card
                if event.get('body'):
                    if event.get('isBase64Encoded'):
                        body = base64.b64decode(event['body']).decode('utf-8')
                    else:
                        body = event['body']
                    
                    params = json.loads(body) if isinstance(body, str) else body
                else:
                    return {
                        'statusCode': 400,
                        'body': json.dumps({'error': 'Request body required'}),
                        'headers': {'Content-Type': 'application/json'}
                    }
                
                result = await self.mcp_server.create_canva_activity_card(
                    activity_data=params.get('activity_data', {})
                )
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(result, indent=2),
                    'headers': {'Content-Type': 'application/json'}
                }
            
            elif path.startswith('/canva-export/') and method == 'POST':
                # Export Canva design
                design_id = path.split('/')[-1]
                
                if event.get('body'):
                    if event.get('isBase64Encoded'):
                        body = base64.b64decode(event['body']).decode('utf-8')
                    else:
                        body = event['body']
                    
                    params = json.loads(body) if isinstance(body, str) else body
                    format = params.get('format', 'pdf')
                else:
                    format = 'pdf'
                
                result = await self.mcp_server.export_canva_design(design_id, format)
                
                return {
                    'statusCode': 200,
                    'body': json.dumps(result, indent=2),
                    'headers': {'Content-Type': 'application/json'}
                }
            
            elif path == '/webhook' and method == 'POST':
                # Handle Trello webhook for @ai comments
                if event.get('body'):
                    if event.get('isBase64Encoded'):
                        body = base64.b64decode(event['body']).decode('utf-8')
                    else:
                        body = event['body']
                    
                    webhook_data = json.loads(body) if isinstance(body, str) else body
                    
                    # Process the webhook
                    result = await self._handle_trello_webhook(webhook_data)
                    
                    return {
                        'statusCode': 200,
                        'body': json.dumps(result),
                        'headers': {'Content-Type': 'application/json'}
                    }
                else:
                    return {
                        'statusCode': 400,
                        'body': json.dumps({'error': 'Webhook body required'}),
                        'headers': {'Content-Type': 'application/json'}
                    }
            
            elif path == '/webhook' and method == 'HEAD':
                # Webhook verification endpoint
                return {
                    'statusCode': 200,
                    'body': '',
                    'headers': {'Content-Type': 'application/json'}
                }
            
            elif path == '/canva-callback' and method == 'GET':
                # Handle Canva OAuth callback
                query_params = event.get('queryStringParameters') or {}
                auth_code = query_params.get('code')
                
                if auth_code:
                    return {
                        'statusCode': 200,
                        'body': f'''<!DOCTYPE html>
<html>
<head><title>Canva Authorization Success</title></head>
<body>
<h1>✅ Authorization Successful!</h1>
<p>Your authorization code is:</p>
<p><code>{auth_code}</code></p>
<p>Copy this code and use it to complete the token exchange.</p>
<script>
console.log("Authorization code:", "{auth_code}");
</script>
</body>
</html>''',
                        'headers': {'Content-Type': 'text/html'}
                    }
                else:
                    return {
                        'statusCode': 400,
                        'body': '''<!DOCTYPE html>
<html>
<head><title>Canva Authorization Failed</title></head>
<body>
<h1>❌ Authorization Failed</h1>
<p>No authorization code received.</p>
</body>
</html>''',
                        'headers': {'Content-Type': 'text/html'}
                    }
            
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Not found'}),
                    'headers': {'Content-Type': 'application/json'}
                }
                
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)}),
                'headers': {'Content-Type': 'application/json'}
            }

    async def _get_tools(self) -> List[Dict[str, Any]]:
        """Get available MCP tools"""
        return [
            {
                "name": "get_activities",
                "description": "Get curriculum activities from Trello board",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "Filter by category"},
                        "level": {"type": "string", "description": "Filter by student level"},
                        "duration": {"type": "number", "description": "Maximum duration in minutes"}
                    }
                }
            },
            {
                "name": "search_activities",
                "description": "Search activities by keyword",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search term"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "suggest_lesson_plan",
                "description": "Generate lesson plan using available activities",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "student_level": {"type": "string", "description": "Student level"},
                        "focus_area": {"type": "string", "description": "Focus area"},
                        "total_duration": {"type": "number", "description": "Duration in minutes"}
                    },
                    "required": ["student_level"]
                }
            },
            {
                "name": "get_board_structure",
                "description": "Get Trello board structure",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_drive_resources",
                "description": "Get files from Google Drive shared folder",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search term for Drive files"}
                    }
                }
            },
            {
                "name": "get_business_context",
                "description": "Get business/organization context and website information",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_comprehensive_resources",
                "description": "Get all available resources for a topic from all sources",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Topic to search for across all sources"}
                    }
                }
            },
            {
                "name": "save_lesson_plan",
                "description": "Save a lesson plan to persistent storage",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "lesson_plan": {"type": "object", "description": "The lesson plan data to save"},
                        "plan_id": {"type": "string", "description": "Optional custom ID for the lesson plan"}
                    },
                    "required": ["lesson_plan"]
                }
            },
            {
                "name": "get_saved_lesson_plans",
                "description": "Retrieve saved lesson plans from storage",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "number", "description": "Maximum number of plans to retrieve (default: 10)"}
                    }
                }
            },
            {
                "name": "get_lesson_plan_by_id",
                "description": "Retrieve a specific lesson plan by its ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "plan_id": {"type": "string", "description": "The ID of the lesson plan to retrieve"}
                    },
                    "required": ["plan_id"]
                }
            },
            {
                "name": "sync_lesson_plans_to_trello",
                "description": "Sync all existing lesson plans from storage to Trello board",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "submit_feedback",
                "description": "Submit feedback for a lesson plan to improve future generations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "lesson_plan_id": {"type": "string", "description": "ID of the lesson plan"},
                        "feedback_type": {"type": "string", "description": "Type of feedback: like, dislike, improve, rating"},
                        "feedback_text": {"type": "string", "description": "Detailed feedback text"},
                        "rating": {"type": "number", "description": "Optional rating (1-5)"},
                        "source": {"type": "string", "description": "Source of feedback (api, trello_comment, etc.)"}
                    },
                    "required": ["lesson_plan_id", "feedback_type", "feedback_text"]
                }
            },
            {
                "name": "get_lesson_plan_feedback",
                "description": "Get all feedback for a specific lesson plan",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "lesson_plan_id": {"type": "string", "description": "ID of the lesson plan"}
                    },
                    "required": ["lesson_plan_id"]
                }
            },
            {
                "name": "analyze_feedback_patterns",
                "description": "Analyze feedback patterns to understand preferences and improvement areas",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "create_canva_presentation",
                "description": "Create a Canva presentation from a lesson plan",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "lesson_plan_id": {"type": "string", "description": "ID of saved lesson plan to convert"},
                        "lesson_plan_data": {"type": "object", "description": "Direct lesson plan data to convert"}
                    }
                }
            },
            {
                "name": "create_canva_activity_card",
                "description": "Create a Canva activity card design",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "activity_data": {"type": "object", "description": "Activity data including name, duration, description, etc."}
                    },
                    "required": ["activity_data"]
                }
            },
            {
                "name": "export_canva_design",
                "description": "Export a Canva design to PDF, PNG, or JPG",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "design_id": {"type": "string", "description": "Canva design ID to export"},
                        "format": {"type": "string", "description": "Export format: pdf, png, or jpg (default: pdf)"}
                    },
                    "required": ["design_id"]
                }
            }
        ]

    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call MCP tool"""
        if name == "get_activities":
            return await self.mcp_server.get_activities(**arguments)
        elif name == "search_activities":
            return await self.mcp_server.search_activities(**arguments)
        elif name == "suggest_lesson_plan":
            return await self.mcp_server.suggest_lesson_plan(**arguments)
        elif name == "get_board_structure":
            return await self.mcp_server.get_board_structure()
        elif name == "get_drive_resources":
            return await self.mcp_server.get_drive_resources(**arguments)
        elif name == "get_business_context":
            return await self.mcp_server.get_business_context()
        elif name == "get_comprehensive_resources":
            return await self.mcp_server.get_comprehensive_resources(**arguments)
        elif name == "save_lesson_plan":
            return await self.mcp_server.save_lesson_plan(**arguments)
        elif name == "get_saved_lesson_plans":
            return await self.mcp_server.get_saved_lesson_plans(**arguments)
        elif name == "get_lesson_plan_by_id":
            return await self.mcp_server.get_lesson_plan_by_id(**arguments)
        elif name == "sync_lesson_plans_to_trello":
            return await self.mcp_server.sync_existing_lesson_plans_to_trello()
        elif name == "submit_feedback":
            return await self.mcp_server.submit_feedback(**arguments)
        elif name == "get_lesson_plan_feedback":
            return await self.mcp_server.get_lesson_plan_feedback(**arguments)
        elif name == "analyze_feedback_patterns":
            return await self.mcp_server.analyze_feedback_patterns()
        elif name == "create_canva_presentation":
            return await self.mcp_server.create_canva_presentation(**arguments)
        elif name == "create_canva_activity_card":
            return await self.mcp_server.create_canva_activity_card(**arguments)
        elif name == "export_canva_design":
            return await self.mcp_server.export_canva_design(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _handle_trello_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Trello webhook for @ai comments"""
        try:
            action = webhook_data.get('action', {})
            action_type = action.get('type')
            
            # Quick return for non-comment actions
            if action_type != 'commentCard':
                return {
                    'status': 'ignored',
                    'action': action_type,
                    'reason': 'not a comment',
                    'processed': False
                }
            
            print(f"📨 Received Trello webhook: {action_type}")
            
            # Only process comment actions
            if action_type == 'commentCard':
                comment_text = action.get('data', {}).get('text', '').strip()
                card_data = action.get('data', {}).get('card', {})
                card_id = card_data.get('id')
                card_name = card_data.get('name')
                
                print(f"💬 Comment on card '{card_name}': {comment_text}")
                
                # Check if comment mentions @ai (must be explicit mention)
                # Ignore comments that start with bot response indicators
                bot_prefixes = ['🤖', '✅', '🎨', '❌', '🔍', '💬', '📨', '💾', '💡', '⚠️']
                is_bot_comment = any(comment_text.startswith(prefix) for prefix in bot_prefixes)
                
                if '@ai' in comment_text.lower() and not is_bot_comment:
                    print("🤖 Processing @ai request...")
                    
                    # Extract the actual request (remove @ai)
                    request_text = comment_text.lower().replace('@ai', '').strip()
                    
                    # Process based on request type
                    if any(keyword in request_text for keyword in ['lesson plan', 'lesson', 'plan']):
                        # Generate lesson plan request
                        result = await self._process_lesson_plan_request(card_id, card_name, request_text)
                    elif 'presentation' in request_text or 'canva' in request_text:
                        # Generate presentation request
                        result = await self._process_presentation_request(card_id, card_name, request_text)
                    else:
                        # General curriculum assistance
                        result = await self._process_general_request(card_id, card_name, request_text)
                    
                    # Post response back to Trello card
                    await self._post_trello_comment(card_id, result.get('response', 'Processing completed.'))
                    
                    return {
                        'status': 'processed',
                        'action': action_type,
                        'card_id': card_id,
                        'processed': True,
                        'result': result
                    }
                else:
                    print("ℹ️  Comment doesn't contain @ai, ignoring")
                    
            return {
                'status': 'ignored',
                'action': action_type,
                'processed': False
            }
            
        except Exception as e:
            print(f"❌ Error processing webhook: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'processed': False
            }

    async def _process_lesson_plan_request(self, card_id: str, card_name: str, request_text: str) -> Dict[str, Any]:
        """Process lesson plan generation request"""
        try:
            # Extract parameters from request text and card name
            # You can enhance this with more sophisticated parsing
            lesson_plan = await self.mcp_server.suggest_lesson_plan(
                student_level="intermediate",  # Default, could parse from request
                focus_area=card_name,  # Use card name as focus area
                total_duration=90  # Default duration
            )
            
            # Save the lesson plan
            save_result = await self.mcp_server.save_lesson_plan(lesson_plan=lesson_plan)
            
            response = f"✅ **Lesson Plan Generated!**\n\n"
            response += f"**Title:** {lesson_plan.get('title', 'Untitled')}\n"
            response += f"**Level:** {lesson_plan.get('level', 'N/A')}\n"
            response += f"**Duration:** {lesson_plan.get('total_duration', 'N/A')} minutes\n"
            response += f"**Activities:** {len(lesson_plan.get('structure', {}).get('main_activities', []))}\n\n"
            response += f"💾 Saved as ID: `{save_result.get('lesson_plan_id')}`\n\n"
            response += f"💡 Reply with `@ai create presentation {save_result.get('lesson_plan_id')}` to generate Canva slides!"
            
            return {
                'type': 'lesson_plan',
                'lesson_plan_id': save_result.get('lesson_plan_id'),
                'response': response
            }
            
        except Exception as e:
            return {
                'type': 'lesson_plan',
                'error': str(e),
                'response': f"❌ Error generating lesson plan: {str(e)}"
            }

    async def _process_presentation_request(self, card_id: str, card_name: str, request_text: str) -> Dict[str, Any]:
        """Process presentation generation request"""
        try:
            # Extract lesson plan ID from request if provided
            import re
            plan_id_match = re.search(r'presentation\s+([a-zA-Z0-9_-]+)', request_text)
            
            if plan_id_match:
                plan_id = plan_id_match.group(1)
                # Generate presentation from existing lesson plan
                result = await self.mcp_server.create_canva_presentation(lesson_plan_id=plan_id)
            else:
                # Generate lesson plan first, then presentation
                lesson_plan = await self.mcp_server.suggest_lesson_plan(
                    student_level="intermediate",
                    focus_area=card_name,
                    total_duration=90
                )
                result = await self.mcp_server.create_canva_presentation(lesson_plan_data=lesson_plan)
            
            if result.get('design_id'):
                response = f"🎨 **Canva Presentation Created!**\n\n"
                response += f"**Design ID:** {result.get('design_id')}\n"
                response += f"**Title:** {result.get('title')}\n"
                response += f"**Slides:** {result.get('slides_count')}\n\n"
                response += f"🎭 **Edit in Canva:** {result.get('edit_url')}\n"
                response += f"👁️ **Preview:** {result.get('view_url')}"
            else:
                response = f"⚠️ Presentation structure created but needs manual content population in Canva."
            
            return {
                'type': 'presentation',
                'design_id': result.get('design_id'),
                'response': response
            }
            
        except Exception as e:
            return {
                'type': 'presentation',
                'error': str(e),
                'response': f"❌ Error generating presentation: {str(e)}"
            }

    async def _process_general_request(self, card_id: str, card_name: str, request_text: str) -> Dict[str, Any]:
        """Process general curriculum assistance request"""
        try:
            # Search for relevant activities
            search_results = await self.mcp_server.search_activities(request_text)
            
            response = f"🔍 **Found {len(search_results)} activities:**\n\n"
            
            for i, activity in enumerate(search_results[:5], 1):  # Show top 5
                response += f"{i}. **{activity.get('name', 'Untitled')}**\n"
                response += f"   ⏱️ {activity.get('duration', 'N/A')} min | "
                response += f"📊 {activity.get('level', 'N/A')} | "
                response += f"🏷️ {activity.get('category', 'N/A')}\n"
                if activity.get('description'):
                    response += f"   📝 {activity.get('description')[:100]}...\n"
                response += "\n"
            
            response += f"💡 Try: `@ai lesson plan` or `@ai presentation` for more specific help!"
            
            return {
                'type': 'general',
                'results_count': len(search_results),
                'response': response
            }
            
        except Exception as e:
            return {
                'type': 'general',
                'error': str(e),
                'response': f"❌ Error processing request: {str(e)}"
            }

    async def _post_trello_comment(self, card_id: str, comment_text: str) -> None:
        """Post a comment back to the Trello card"""
        try:
            trello_api_key = os.getenv('TRELLO_API_KEY')
            trello_token = os.getenv('TRELLO_TOKEN')
            
            url = f"https://api.trello.com/1/cards/{card_id}/actions/comments"
            
            data = {
                'text': comment_text,
                'key': trello_api_key,
                'token': trello_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data)
                response.raise_for_status()
                print(f"✅ Posted comment to Trello card {card_id}")
                
        except Exception as e:
            print(f"❌ Error posting Trello comment: {str(e)}")


# Lambda handler function
def lambda_handler(event, context):
    """AWS Lambda handler for MCP server"""
    
    async def async_handler():
        handler = MCPLambdaHandler()
        
        # Determine if this is an MCP request or HTTP request
        if 'httpMethod' in event:
            # HTTP API Gateway request
            return await handler.handle_http_request(event)
        else:
            # MCP protocol request
            return await handler.handle_mcp_request(event)
    
    # Run async handler
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(async_handler())
    finally:
        loop.close()


# Alias for consistency
handler = lambda_handler