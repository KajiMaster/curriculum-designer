#!/usr/bin/env python3
"""
Canva OAuth Setup Helper
Helps you complete the OAuth flow to get your access token
"""

import base64
import hashlib
import secrets
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import requests

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle the OAuth callback"""
    
    def do_GET(self):
        # Parse the callback URL
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if 'code' in params:
            self.server.auth_code = params['code'][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Authorization successful! You can close this window.")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authorization failed. Please try again.")
    
    def log_message(self, format, *args):
        pass  # Suppress log messages

def generate_pkce():
    """Generate PKCE parameters"""
    # Generate code verifier
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    # Generate code challenge
    challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(challenge).decode('utf-8').rstrip('=')
    
    return code_verifier, code_challenge

def main():
    print("=== Canva OAuth Setup ===\n")
    
    # Get credentials
    client_id = input("Enter your Canva Client ID: ").strip()
    client_secret = input("Enter your Canva Client Secret (starts with cnvca.): ").strip()
    
    if not client_id or not client_secret:
        print("Error: Client ID and Secret are required")
        return
    
    # Generate PKCE
    code_verifier, code_challenge = generate_pkce()
    print(f"\nGenerated PKCE parameters")
    print(f"Code verifier: {code_verifier[:20]}...")
    print(f"Code challenge: {code_challenge[:20]}...")
    
    # Build authorization URL
    auth_params = {
        'client_id': client_id,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
        'response_type': 'code',
        'scope': 'design:content:read design:content:write asset:read asset:write',
        'redirect_uri': 'http://localhost:8080/callback'
    }
    
    auth_url = f"https://www.canva.com/api/oauth/authorize?{urllib.parse.urlencode(auth_params)}"
    
    print(f"\nOpening browser for authorization...")
    print(f"If browser doesn't open, visit this URL:\n{auth_url}\n")
    
    # Start local server to handle callback
    server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
    server.auth_code = None
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Wait for callback
    print("Waiting for authorization callback...")
    while server.auth_code is None:
        server.handle_request()
    
    print(f"\nReceived authorization code: {server.auth_code[:20]}...")
    
    # Exchange code for token
    print("\nExchanging authorization code for access token...")
    
    token_url = "https://api.canva.com/rest/v1/oauth/token"
    
    # Prepare basic auth
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "authorization_code",
        "code": server.auth_code,
        "code_verifier": code_verifier,
        "redirect_uri": "http://localhost:8080/callback"
    }
    
    response = requests.post(token_url, headers=headers, data=data)
    
    if response.status_code == 200:
        tokens = response.json()
        print("\n✅ Success! Here are your tokens:\n")
        print(f"Access Token: {tokens.get('access_token', 'N/A')[:50]}...")
        print(f"Refresh Token: {tokens.get('refresh_token', 'N/A')[:50]}...")
        print(f"Expires in: {tokens.get('expires_in', 'N/A')} seconds")
        
        # Save to file
        with open('canva_tokens.json', 'w') as f:
            json.dump(tokens, f, indent=2)
        print("\n📁 Tokens saved to canva_tokens.json")
        
        print("\n📝 Next steps:")
        print("1. Store the access token in AWS Parameter Store:")
        print("   aws ssm put-parameter --name '/global/curriculum-designer/canva-access-token' \\")
        print("     --value 'YOUR_ACCESS_TOKEN' --type SecureString --overwrite")
        print("\n2. Store the refresh token for long-term use:")
        print("   aws ssm put-parameter --name '/global/curriculum-designer/canva-refresh-token' \\")
        print("     --value 'YOUR_REFRESH_TOKEN' --type SecureString --overwrite")
        
    else:
        print(f"\n❌ Error exchanging code for token: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()