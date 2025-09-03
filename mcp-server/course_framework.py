"""
Course Framework Management Module
Handles storage and retrieval of course frameworks in DynamoDB
Generates variants based on stored frameworks
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import boto3
from botocore.exceptions import ClientError


class CourseFrameworkManager:
    """Manages course frameworks with persistent storage in DynamoDB"""
    
    def __init__(self, table_name: str = "curriculum-frameworks"):
        """Initialize the framework manager with DynamoDB connection"""
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = table_name
        self.table = self.dynamodb.Table(table_name)
        
    def store_framework(self, 
                       board_id: str,
                       framework_name: str,
                       framework_data: Dict[str, Any],
                       metadata: Optional[Dict] = None) -> str:
        """
        Store a course framework in DynamoDB
        
        Args:
            board_id: Trello board ID
            framework_name: Name of the framework
            framework_data: The framework structure and content
            metadata: Additional metadata (tags, description, etc.)
            
        Returns:
            framework_id: Unique ID for the stored framework
        """
        framework_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            'framework_id': framework_id,
            'board_id': board_id,
            'framework_name': framework_name,
            'framework_data': framework_data,
            'metadata': metadata or {},
            'created_at': timestamp,
            'updated_at': timestamp,
            'version': 1,
            'is_active': True
        }
        
        try:
            self.table.put_item(Item=item)
            return framework_id
        except ClientError as e:
            print(f"Error storing framework: {e}")
            raise
            
    def get_framework(self, framework_id: str) -> Optional[Dict]:
        """
        Retrieve a framework by ID
        
        Args:
            framework_id: The unique framework ID
            
        Returns:
            Framework data or None if not found
        """
        try:
            response = self.table.get_item(Key={'framework_id': framework_id})
            return response.get('Item')
        except ClientError as e:
            print(f"Error retrieving framework: {e}")
            return None
            
    def list_frameworks(self, board_id: str) -> List[Dict]:
        """
        List all frameworks for a specific board
        
        Args:
            board_id: Trello board ID
            
        Returns:
            List of frameworks
        """
        try:
            response = self.table.query(
                IndexName='board-index',  # Assumes GSI on board_id
                KeyConditionExpression='board_id = :bid',
                ExpressionAttributeValues={':bid': board_id}
            )
            return response.get('Items', [])
        except ClientError as e:
            # If index doesn't exist, scan instead (less efficient)
            try:
                response = self.table.scan(
                    FilterExpression='board_id = :bid',
                    ExpressionAttributeValues={':bid': board_id}
                )
                return response.get('Items', [])
            except ClientError as scan_error:
                print(f"Error listing frameworks: {scan_error}")
                return []
                
    def update_framework(self, 
                        framework_id: str,
                        framework_data: Dict[str, Any],
                        increment_version: bool = True) -> bool:
        """
        Update an existing framework
        
        Args:
            framework_id: The framework to update
            framework_data: New framework data
            increment_version: Whether to increment the version number
            
        Returns:
            Success status
        """
        try:
            update_expr = "SET framework_data = :data, updated_at = :ts"
            expr_values = {
                ':data': framework_data,
                ':ts': datetime.utcnow().isoformat()
            }
            
            if increment_version:
                update_expr += ", version = version + :inc"
                expr_values[':inc'] = 1
                
            self.table.update_item(
                Key={'framework_id': framework_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values
            )
            return True
        except ClientError as e:
            print(f"Error updating framework: {e}")
            return False


class FrameworkVariantGenerator:
    """Generates variants of course frameworks based on different parameters"""
    
    def __init__(self, openai_client):
        """Initialize with OpenAI client for AI-powered variant generation"""
        self.openai_client = openai_client
        
    def generate_variants(self, 
                         framework: Dict,
                         variant_params: Dict,
                         num_variants: int = 3) -> List[Dict]:
        """
        Generate framework variants based on parameters
        
        Args:
            framework: Base framework structure
            variant_params: Parameters for variation (level, focus, duration, etc.)
            num_variants: Number of variants to generate
            
        Returns:
            List of framework variants
        """
        variants = []
        
        # Extract base structure
        base_structure = framework.get('framework_data', {})
        framework_name = framework.get('framework_name', 'Course')
        
        # Define variation dimensions
        variation_dimensions = {
            'proficiency_levels': variant_params.get('levels', ['B1', 'B2', 'C1']),
            'focus_areas': variant_params.get('focus', ['speaking', 'business', 'academic']),
            'durations': variant_params.get('durations', ['4-week', '8-week', '12-week']),
            'intensities': variant_params.get('intensities', ['standard', 'intensive'])
        }
        
        for i in range(num_variants):
            variant = self._create_variant(
                base_structure,
                framework_name,
                variation_dimensions,
                i
            )
            variants.append(variant)
            
        return variants
        
    def _create_variant(self,
                       base_structure: Dict,
                       base_name: str,
                       dimensions: Dict,
                       variant_index: int) -> Dict:
        """
        Create a single variant of the framework
        
        Args:
            base_structure: Base framework structure
            base_name: Base framework name
            dimensions: Variation dimensions
            variant_index: Index of this variant
            
        Returns:
            Framework variant
        """
        # Select variation parameters
        level = dimensions['proficiency_levels'][variant_index % len(dimensions['proficiency_levels'])]
        focus = dimensions['focus_areas'][variant_index % len(dimensions['focus_areas'])]
        duration = dimensions['durations'][variant_index % len(dimensions['durations'])]
        intensity = dimensions['intensities'][variant_index % len(dimensions['intensities'])]
        
        # Create variant name
        variant_name = f"{base_name} - {level} {focus.capitalize()} ({duration}, {intensity})"
        
        # Generate variant structure using AI
        variant_structure = self._generate_variant_structure(
            base_structure,
            level,
            focus,
            duration,
            intensity
        )
        
        return {
            'name': variant_name,
            'base_framework': base_name,
            'parameters': {
                'level': level,
                'focus': focus,
                'duration': duration,
                'intensity': intensity
            },
            'structure': variant_structure,
            'created_at': datetime.utcnow().isoformat()
        }
        
    def _generate_variant_structure(self,
                                   base: Dict,
                                   level: str,
                                   focus: str,
                                   duration: str,
                                   intensity: str) -> Dict:
        """
        Use AI to generate variant structure based on parameters
        
        Args:
            base: Base framework structure
            level: Proficiency level
            focus: Focus area
            duration: Course duration
            intensity: Course intensity
            
        Returns:
            Variant structure
        """
        prompt = f"""
        Based on this course framework structure:
        {json.dumps(base, indent=2)}
        
        Create a variant with these parameters:
        - Proficiency Level: {level}
        - Focus Area: {focus}
        - Duration: {duration}
        - Intensity: {intensity}
        
        Adjust the following:
        1. Module topics to match the level and focus
        2. Activity complexity and types
        3. Pacing based on duration and intensity
        4. Assessment methods appropriate for the level
        
        Return a JSON structure maintaining the original format but adapted for these parameters.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a curriculum design expert specializing in English language teaching."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error generating variant structure: {e}")
            # Return modified base as fallback
            variant = base.copy()
            variant['level'] = level
            variant['focus'] = focus
            variant['duration'] = duration
            variant['intensity'] = intensity
            return variant


class TrelloVariantCreator:
    """Creates Trello cards for framework variants"""
    
    def __init__(self, trello_key: str, trello_token: str):
        """Initialize with Trello credentials"""
        self.trello_key = trello_key
        self.trello_token = trello_token
        self.base_url = "https://api.trello.com/1"
        
    def create_variant_cards(self,
                            board_id: str,
                            list_name: str,
                            variants: List[Dict]) -> List[str]:
        """
        Create Trello cards for each variant
        
        Args:
            board_id: Trello board ID
            list_name: Name of the list to create cards in
            variants: List of framework variants
            
        Returns:
            List of created card IDs
        """
        import requests
        
        # First, get or create the list
        list_id = self._get_or_create_list(board_id, list_name)
        if not list_id:
            return []
            
        created_cards = []
        
        for variant in variants:
            # Create card content
            card_name = variant['name']
            card_desc = self._format_variant_description(variant)
            
            # Create the card
            url = f"{self.base_url}/cards"
            params = {
                'key': self.trello_key,
                'token': self.trello_token,
                'idList': list_id,
                'name': card_name,
                'desc': card_desc,
                'pos': 'bottom'
            }
            
            # Add labels based on parameters
            labels = self._get_variant_labels(variant['parameters'])
            if labels:
                params['idLabels'] = ','.join(labels)
                
            try:
                response = requests.post(url, params=params)
                if response.status_code == 200:
                    card_data = response.json()
                    created_cards.append(card_data['id'])
                    
                    # Add framework structure as attachment or comment
                    self._add_framework_details(card_data['id'], variant)
            except Exception as e:
                print(f"Error creating card for variant {card_name}: {e}")
                
        return created_cards
        
    def _get_or_create_list(self, board_id: str, list_name: str) -> Optional[str]:
        """Get existing list or create new one"""
        import requests
        
        # Get board lists
        url = f"{self.base_url}/boards/{board_id}/lists"
        params = {
            'key': self.trello_key,
            'token': self.trello_token
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                lists = response.json()
                
                # Check if list exists
                for lst in lists:
                    if lst['name'] == list_name:
                        return lst['id']
                        
                # Create new list
                create_url = f"{self.base_url}/lists"
                create_params = {
                    'key': self.trello_key,
                    'token': self.trello_token,
                    'name': list_name,
                    'idBoard': board_id,
                    'pos': 'bottom'
                }
                
                create_response = requests.post(create_url, params=create_params)
                if create_response.status_code == 200:
                    return create_response.json()['id']
        except Exception as e:
            print(f"Error managing list: {e}")
            
        return None
        
    def _format_variant_description(self, variant: Dict) -> str:
        """Format variant information for card description"""
        params = variant['parameters']
        desc = f"""
## Framework Variant

**Base Framework:** {variant.get('base_framework', 'Unknown')}

### Parameters:
- **Level:** {params.get('level', 'N/A')}
- **Focus:** {params.get('focus', 'N/A')}
- **Duration:** {params.get('duration', 'N/A')}
- **Intensity:** {params.get('intensity', 'N/A')}

### Key Features:
"""
        
        # Add structure highlights
        structure = variant.get('structure', {})
        if 'modules' in structure:
            desc += f"- {len(structure['modules'])} modules\n"
        if 'objectives' in structure:
            desc += f"- Primary objectives: {', '.join(structure['objectives'][:3])}\n"
            
        desc += f"\n*Generated: {variant.get('created_at', 'Unknown')}*"
        
        return desc
        
    def _get_variant_labels(self, parameters: Dict) -> List[str]:
        """Get label IDs based on variant parameters"""
        # This would map to actual Trello label IDs
        # For now, returning empty list
        return []
        
    def _add_framework_details(self, card_id: str, variant: Dict):
        """Add detailed framework structure as card comment"""
        import requests
        
        url = f"{self.base_url}/cards/{card_id}/actions/comments"
        params = {
            'key': self.trello_key,
            'token': self.trello_token,
            'text': f"```json\n{json.dumps(variant['structure'], indent=2)}\n```"
        }
        
        try:
            requests.post(url, params=params)
        except Exception as e:
            print(f"Error adding framework details: {e}")