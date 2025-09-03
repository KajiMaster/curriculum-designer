#!/usr/bin/env python3
"""Test OpenAI API quota and billing status"""

import boto3
import httpx
import json
import asyncio

def get_openai_api_key():
    """Get OpenAI API key from Parameter Store"""
    try:
        ssm = boto3.client('ssm', region_name='us-east-1')
        response = ssm.get_parameter(
            Name="/global/curriculum-designer/openai-api-key",
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except Exception as e:
        print(f"Error getting OpenAI API key: {e}")
        return None

async def test_openai_api():
    """Test OpenAI API with a simple request"""
    api_key = get_openai_api_key()
    if not api_key:
        print("❌ No OpenAI API key found")
        return
    
    print(f"✅ Found OpenAI API key (length: {len(api_key)})")
    
    # Test with a minimal request
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 10
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data, timeout=30.0)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ OpenAI API working!")
                print(f"Response: {result.get('choices', [{}])[0].get('message', {}).get('content', 'No content')}")
            else:
                print(f"❌ OpenAI API Error: {response.status_code}")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception calling OpenAI: {e}")

if __name__ == "__main__":
    asyncio.run(test_openai_api())