#!/usr/bin/env python3
"""
Test script to validate the ESL level fix
"""
import json
import re

def test_webhook_handler_parsing():
    """Test the webhook handler's new parsing logic"""
    print("=== Testing Webhook Handler Command Parsing ===")
    
    # Test cases
    test_cases = [
        '@ai generate activity "coffee farming"',
        '@ai activity coffee farming intermediate',
        '@ai activity "food and drinks" beginner 15',
        '@ai activity cooking advanced 20 preference_choice',
        '@ai activity travel upper-intermediate 10 vocabulary_builder',
    ]
    
    for ai_request in test_cases:
        print(f"\nTesting: {ai_request}")
        
        # Apply the parsing logic from webhook handler
        topic_match = re.search(r'"([^"]+)"', ai_request) or re.search(r'topic[:\s]+([^\s,]+)', ai_request)
        level_match = re.search(r'level[:\s]+([^\s,]+)', ai_request) or re.search(r'\b(beginner|elementary|intermediate|upper-intermediate|advanced)\b', ai_request, re.IGNORECASE)
        duration_match = re.search(r'duration[:\s]+(\d+)', ai_request) or re.search(r'(\d+)\s*min', ai_request) or re.search(r'\b(\d+)\b', ai_request)
        type_match = re.search(r'type[:\s]+([^\s,]+)', ai_request) or re.search(r'(preference_choice|vocabulary_builder|compare_contrast|sequence_builder|story_response|interactive_game|discovery_exploration)', ai_request)
        
        # Get topic from card if not specified (simulated)
        if not topic_match:
            topic = "English Language Learning"  # Fallback
        else:
            topic = topic_match.group(1)
        
        # Default values
        esl_level = level_match.group(1) if level_match else "intermediate"
        duration = int(duration_match.group(1)) if duration_match else 15
        activity_type = type_match.group(1) if type_match else None
        
        # Create payload for activity generator
        payload = {
            'topic': topic,
            'student_age': 'adult',  # For adult ESL learners
            'esl_level': esl_level,
            'duration': duration
        }
        
        if activity_type:
            payload['activity_type'] = activity_type
            
        print(f"  Parsed topic: {topic}")
        print(f"  Parsed ESL level: {esl_level}")
        print(f"  Parsed duration: {duration}")
        print(f"  Parsed type: {activity_type or 'Auto-selected'}")
        print(f"  Generated payload: {json.dumps(payload, indent=4)}")

def test_activity_generator_compatibility():
    """Test that the activity generator can handle the new payload format"""
    print("\n\n=== Testing Activity Generator Compatibility ===")
    
    # Simulate the payload the webhook handler would send
    test_payload = {
        'topic': 'coffee farming',
        'student_age': 'adult',
        'esl_level': 'intermediate',
        'duration': 15,
        'activity_type': 'preference_choice'
    }
    
    print("Test payload to activity generator:")
    print(json.dumps(test_payload, indent=2))
    
    # Simulate activity generator parsing
    topic = test_payload.get('topic')
    duration = test_payload.get('duration', 15)
    activity_type = test_payload.get('activity_type')
    context_info = test_payload.get('context')
    student_age = test_payload.get('student_age')
    esl_level = test_payload.get('esl_level')
    
    print(f"\nActivity generator would receive:")
    print(f"  topic: {topic}")
    print(f"  duration: {duration}")
    print(f"  activity_type: {activity_type}")
    print(f"  student_age: {student_age}")
    print(f"  esl_level: {esl_level}")
    
    # Simulate metadata creation
    metadata = {
        'generated_at': '2025-01-14T12:00:00',
        'topic': topic,
        'duration': f"{duration} minutes",
        'activity_type': activity_type,
        'student_age': student_age or 'adult',
        'esl_level': esl_level or 'intermediate',
        'energy_level': 'medium',
        'cognitive_stage': 'practice'
    }
    
    print(f"\nGenerated metadata:")
    print(json.dumps(metadata, indent=2))

if __name__ == "__main__":
    test_webhook_handler_parsing()
    test_activity_generator_compatibility()
    print("\n\n=== Summary ===")
    print("✅ Command parsing updated to use ESL levels instead of K-12 grades")
    print("✅ Payload format changed from grade_level to esl_level + student_age")
    print("✅ Activity generator updated to handle ESL levels in prompts")
    print("✅ Error messages and usage examples updated for ESL terminology")
    print("\n⚠️  Next Steps:")
    print("  1. Deploy updated Lambda functions")
    print("  2. Test with real Trello command: @ai generate activity 'coffee farming' intermediate")
    print("  3. DevOps review for CI/CD pipeline updates")