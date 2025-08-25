#!/usr/bin/env python3
"""
OAuth helper for Canva integration
Generates authorization URLs and handles token exchange
"""

import base64
import hashlib
import secrets
import urllib.parse
import httpx
import asyncio
import json

class CanvaOAuthHelper:
    def __init__(self):
        # Get client ID from Parameter Store
        try:
            ssm = boto3.client('ssm', region_name='us-east-1')
            response = ssm.get_parameter(Name='/global/curriculum-designer/canva-client-id', WithDecryption=True)
            self.client_id = response['Parameter']['Value']
        except Exception as e:
            print(f"Error getting client ID from Parameter Store: {e}")
            self.client_id = None
        # Get client secret from Parameter Store
        try:
            response = ssm.get_parameter(Name='/global/curriculum-designer/canva-client-secret', WithDecryption=True)
            self.client_secret = response['Parameter']['Value']
        except Exception as e:
            print(f"Error getting client secret from Parameter Store: {e}")
            self.client_secret = None
        self.redirect_uri = "https://89npxchg5j.execute-api.us-east-1.amazonaws.com/dev/canva-callback"
        self.auth_url = "https://www.canva.com/api/oauth/authorize"
        self.token_url = "https://api.canva.com/rest/v1/oauth/token"
        
    def generate_pkce_challenge(self):
        """Generate PKCE code verifier and challenge"""
        # Generate a random 43-128 character string
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Create SHA256 hash of code verifier
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    def get_authorization_url(self, code_challenge):
        """Generate authorization URL"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': 'design:content:read design:content:write asset:read asset:write',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        query_string = urllib.parse.urlencode(params)
        return f"{self.auth_url}?{query_string}"
    
    async def exchange_code_for_tokens(self, auth_code, code_verifier):
        """Exchange authorization code for access and refresh tokens"""
        
        # Prepare Basic Auth header
        credentials = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': self.redirect_uri,
            'code_verifier': code_verifier
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_url, headers=headers, data=data)
            
            if response.status_code == 200:
                tokens = response.json()
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
                    'error': f"HTTP {response.status_code}",
                    'details': response.text
                }

async def main():
    """Interactive OAuth flow"""
    helper = CanvaOAuthHelper()
    
    print("🎨 Canva OAuth Flow")
    print("==================")
    
    # Generate PKCE challenge
    code_verifier, code_challenge = helper.generate_pkce_challenge()
    print(f"Code verifier: {code_verifier}")
    print(f"Code challenge: {code_challenge}")
    
    # Generate authorization URL
    auth_url = helper.get_authorization_url(code_challenge)
    print(f"\n📋 Authorization URL:")
    print(auth_url)
    
    print(f"\n🌐 Open this URL in your browser to authorize:")
    print(f"   {auth_url}")
    
    # Wait for user to provide authorization code
    auth_code = input("\n✍️  Enter the authorization code from the callback: ").strip()
    
    if auth_code:
        print(f"\n🔄 Exchanging code for tokens...")
        result = await helper.exchange_code_for_tokens(auth_code, code_verifier)
        
        if result['success']:
            print("✅ Token exchange successful!")
            print(f"Access token: {result['access_token'][:50]}...")
            print(f"Refresh token: {result['refresh_token'][:50]}...")
            print(f"Expires in: {result['expires_in']} seconds")
            
            # Store in AWS Parameter Store
            import boto3
            ssm = boto3.client('ssm', region_name='us-east-1')
            
            try:
                # Store access token
                ssm.put_parameter(
                    Name="/global/curriculum-designer/canva-access-token",
                    Value=result['access_token'],
                    Type="SecureString",
                    Overwrite=True
                )
                
                # Store refresh token
                ssm.put_parameter(
                    Name="/global/curriculum-designer/canva-refresh-token", 
                    Value=result['refresh_token'],
                    Type="SecureString",
                    Overwrite=True
                )
                
                print("✅ Tokens stored in AWS Parameter Store!")
                
            except Exception as e:
                print(f"❌ Failed to store tokens: {e}")
                print("Tokens:")
                print(json.dumps(result, indent=2))
        else:
            print("❌ Token exchange failed:")
            print(json.dumps(result, indent=2))
    else:
        print("❌ No authorization code provided")

if __name__ == "__main__":
    asyncio.run(main())