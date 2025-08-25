#!/usr/bin/env python3
"""
Simple OAuth helper for Canva integration using standard library
"""

import base64
import hashlib
import secrets
import urllib.parse

def generate_pkce_challenge():
    """Generate PKCE code verifier and challenge"""
    # Generate a random 43-128 character string
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    # Create SHA256 hash of code verifier
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    
    return code_verifier, code_challenge

def get_authorization_url(code_challenge):
    """Generate authorization URL"""
    import boto3
    ssm = boto3.client('ssm', region_name='us-east-1')
    try:
        response = ssm.get_parameter(Name='/global/curriculum-designer/canva-client-id', WithDecryption=True)
        client_id = response['Parameter']['Value']
    except Exception as e:
        print(f"Error getting client ID from Parameter Store: {e}")
        client_id = None
    redirect_uri = "https://89npxchg5j.execute-api.us-east-1.amazonaws.com/dev/canva-callback"
    auth_url = "https://www.canva.com/api/oauth/authorize"
    
    params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope': 'design:content:read design:content:write design:meta:read folder:read folder:write asset:read asset:write brandtemplate:meta:read brandtemplate:content:read',
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    
    query_string = urllib.parse.urlencode(params)
    return f"{auth_url}?{query_string}"

def main():
    """Generate OAuth URL"""
    print("🎨 Canva OAuth Flow")
    print("==================")
    
    # Generate PKCE challenge
    code_verifier, code_challenge = generate_pkce_challenge()
    print(f"Code verifier: {code_verifier}")
    print(f"Code challenge: {code_challenge}")
    
    # Generate authorization URL
    auth_url = get_authorization_url(code_challenge)
    print(f"\n📋 Authorization URL:")
    print(auth_url)
    
    print(f"\n🌐 Copy this URL and open it in your browser:")
    print(f"   {auth_url}")
    
    print(f"\n📝 Save the code verifier for token exchange:")
    print(f"   {code_verifier}")

if __name__ == "__main__":
    main()