#!/usr/bin/env python3
"""
Token exchange script for Canva OAuth
"""

import urllib.request
import urllib.parse
import base64
import json
import sys
import boto3

def exchange_code_for_tokens(auth_code, code_verifier):
    """Exchange authorization code for access and refresh tokens"""
    # Get client ID from Parameter Store
    ssm = boto3.client('ssm', region_name='us-east-1')
    try:
        response = ssm.get_parameter(Name='/global/curriculum-designer/canva-client-id', WithDecryption=True)
        client_id = response['Parameter']['Value']
    except Exception as e:
        print(f"Error getting client ID from Parameter Store: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": "Configuration error"})}
    
    # Get client secret from Parameter Store
    try:
        response = ssm.get_parameter(Name='/global/curriculum-designer/canva-client-secret', WithDecryption=True)
        client_secret = response['Parameter']['Value']
    except Exception as e:
        print(f"Error getting client secret from Parameter Store: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": "Configuration error"})}
    
    redirect_uri = "https://89npxchg5j.execute-api.us-east-1.amazonaws.com/dev/canva-callback"
    token_url = "https://api.canva.com/rest/v1/oauth/token"
    
    # Prepare Basic Auth header
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': redirect_uri,
        'code_verifier': code_verifier
    }
    
    # Encode data
    data_encoded = urllib.parse.urlencode(data).encode('utf-8')
    
    # Create request
    req = urllib.request.Request(token_url, data=data_encoded, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                tokens = json.loads(response.read().decode('utf-8'))
                return {
                    'success': True,
                    'access_token': tokens.get('access_token'),
                    'refresh_token': tokens.get('refresh_token'),
                    'expires_in': tokens.get('expires_in'),
                    'token_type': tokens.get('token_type')
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status}",
                    'details': response.read().decode('utf-8')
                }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def store_tokens(access_token, refresh_token):
    """Store tokens in AWS Parameter Store"""
    try:
        ssm = boto3.client('ssm', region_name='us-east-1')
        
        # Store access token
        ssm.put_parameter(
            Name="/global/curriculum-designer/canva-access-token",
            Value=access_token,
            Type="SecureString",
            Overwrite=True
        )
        
        # Store refresh token
        ssm.put_parameter(
            Name="/global/curriculum-designer/canva-refresh-token", 
            Value=refresh_token,
            Type="SecureString",
            Overwrite=True
        )
        
        return True
    except Exception as e:
        print(f"❌ Failed to store tokens: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python token_exchange.py <auth_code> <code_verifier>")
        print("Example: python token_exchange.py abc123 dUBsaPEK2LITCQnHGmjjHtm2v6HzhdhNY-cF3LKhaA0")
        sys.exit(1)
    
    auth_code = sys.argv[1]
    code_verifier = sys.argv[2]
    
    print("🔄 Exchanging authorization code for tokens...")
    print(f"Auth code: {auth_code[:20]}...")
    print(f"Code verifier: {code_verifier}")
    
    result = exchange_code_for_tokens(auth_code, code_verifier)
    
    if result['success']:
        print("✅ Token exchange successful!")
        print(f"Access token: {result['access_token'][:50]}...")
        if result['refresh_token']:
            print(f"Refresh token: {result['refresh_token'][:50]}...")
        print(f"Expires in: {result['expires_in']} seconds")
        
        # Store tokens
        if store_tokens(result['access_token'], result['refresh_token']):
            print("✅ Tokens stored in AWS Parameter Store!")
        
        # Test the access token
        print("\n🧪 Testing access token...")
        test_url = "https://89npxchg5j.execute-api.us-east-1.amazonaws.com/dev/canva-presentation"
        test_data = '{"lesson_plan_id": "advanced_presentations_001"}'
        
        print(f"curl -X POST \"{test_url}\" -H \"Content-Type: application/json\" -d '{test_data}'")
        
    else:
        print("❌ Token exchange failed:")
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()