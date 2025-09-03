#!/usr/bin/env python3
"""
Test script for Course Framework functionality
Demonstrates saving frameworks and generating variants
"""

import asyncio
import json
import os
from datetime import datetime
from server import CurriculumMCPServer

# Sample course framework
SAMPLE_FRAMEWORK = {
    "framework_name": "Business English Mastery",
    "framework_data": {
        "description": "Comprehensive business English course for professionals",
        "modules": [
            {
                "id": 1,
                "name": "Professional Communication",
                "objectives": [
                    "Master email etiquette",
                    "Conduct effective meetings",
                    "Present ideas clearly"
                ],
                "duration": "2 weeks",
                "activities": [
                    "Email writing workshop",
                    "Meeting simulation",
                    "Presentation practice"
                ]
            },
            {
                "id": 2,
                "name": "Negotiation Skills",
                "objectives": [
                    "Learn negotiation vocabulary",
                    "Practice persuasion techniques",
                    "Handle objections professionally"
                ],
                "duration": "2 weeks",
                "activities": [
                    "Role-play negotiations",
                    "Case study analysis",
                    "Conflict resolution exercises"
                ]
            },
            {
                "id": 3,
                "name": "Industry-Specific Language",
                "objectives": [
                    "Master technical vocabulary",
                    "Understand industry reports",
                    "Participate in technical discussions"
                ],
                "duration": "2 weeks",
                "activities": [
                    "Industry article analysis",
                    "Technical presentation",
                    "Vocabulary building exercises"
                ]
            },
            {
                "id": 4,
                "name": "Cross-Cultural Communication",
                "objectives": [
                    "Understand cultural differences",
                    "Adapt communication style",
                    "Build international relationships"
                ],
                "duration": "2 weeks",
                "activities": [
                    "Cultural awareness workshop",
                    "International team simulation",
                    "Case studies from different cultures"
                ]
            }
        ],
        "assessment_methods": [
            "Weekly progress checks",
            "Module-end presentations",
            "Final business project"
        ],
        "target_level": "B2-C1",
        "total_duration": "8 weeks"
    }
}

async def test_framework_workflow():
    """Test the complete framework workflow"""
    
    print("=== Course Framework Test Suite ===\n")
    
    # Initialize server
    print("1. Initializing MCP Server...")
    server = CurriculumMCPServer()
    print("   ✓ Server initialized\n")
    
    # Test 1: Store a framework
    print("2. Storing course framework...")
    framework_id = await server.store_course_framework(
        framework_name=SAMPLE_FRAMEWORK["framework_name"],
        framework_data=SAMPLE_FRAMEWORK["framework_data"],
        metadata={
            "author": "Test Suite",
            "created_date": datetime.now().isoformat(),
            "tags": ["business", "professional", "8-week"]
        }
    )
    print(f"   ✓ Framework stored with ID: {framework_id}\n")
    
    # Test 2: List frameworks
    print("3. Listing stored frameworks...")
    frameworks = await server.list_stored_frameworks()
    print(f"   ✓ Found {len(frameworks)} framework(s)")
    for fw in frameworks:
        print(f"      - {fw['name']} (ID: {fw['id']})")
    print()
    
    # Test 3: Generate variants
    print("4. Generating framework variants...")
    variant_params = {
        'levels': ['B1', 'B2', 'C1'],
        'focus': ['sales', 'marketing', 'finance'],
        'durations': ['4-week', '8-week', '12-week'],
        'intensities': ['standard', 'intensive']
    }
    
    result = await server.generate_framework_variants(
        framework_id=framework_id,
        variant_params=variant_params,
        num_variants=5,
        create_cards=False  # Don't create Trello cards in test
    )
    
    if 'error' not in result:
        print(f"   ✓ Generated {result['variants_created']} variants")
        print("\n   Variants created:")
        for i, variant in enumerate(result['variants'], 1):
            print(f"      {i}. {variant['name']}")
            print(f"         - Level: {variant['parameters']['level']}")
            print(f"         - Focus: {variant['parameters']['focus']}")
            print(f"         - Duration: {variant['parameters']['duration']}")
            print(f"         - Intensity: {variant['parameters']['intensity']}")
    else:
        print(f"   ✗ Error: {result['error']}")
    print()
    
    # Test 4: Simulate @ai commands
    print("5. Testing @ai command handling...")
    
    # Test save framework command
    card_context = {
        "name": "Test Framework Card",
        "description": json.dumps(SAMPLE_FRAMEWORK["framework_data"])
    }
    
    response = await server.handle_ai_command("save framework", card_context)
    print(f"   Command: '@ai save framework'")
    print(f"   Response: {response['message']}")
    print()
    
    # Test list frameworks command
    response = await server.handle_ai_command("list frameworks")
    print(f"   Command: '@ai list frameworks'")
    print(f"   Response: {response['message'][:100]}...")
    print()
    
    # Test generate variants command
    response = await server.handle_ai_command(
        f"generate variants framework_id={framework_id} num=3 list=Test Variants"
    )
    print(f"   Command: '@ai generate variants framework_id={framework_id} num=3'")
    print(f"   Response: {response['message']}")
    print()
    
    print("=== Test Suite Complete ===")

def main():
    """Run the test suite"""
    
    # Check for required environment variables
    required_vars = [
        "TRELLO_API_KEY",
        "TRELLO_TOKEN",
        "TRELLO_BOARD_ID"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these variables in your .env file or environment")
        return
    
    # Run tests
    asyncio.run(test_framework_workflow())

if __name__ == "__main__":
    main()