#!/usr/bin/env python3
"""
Create a Trello card with the framework JSON
"""

import requests
import json
import boto3

def get_trello_token():
    """Get Trello token from Parameter Store"""
    ssm = boto3.client('ssm')
    response = ssm.get_parameter(Name="/global/curriculum-designer/trello-token", WithDecryption=True)
    return response['Parameter']['Value']

def create_framework_card():
    """Create Trello card with framework JSON"""
    
    # Credentials
    api_key = "c1fb91381f329cadc1f95a301163bc9a"
    token = get_trello_token()
    board_id = "68a5fba51647caf78fc40866"
    
    # Get lists
    lists_url = f"https://api.trello.com/1/boards/{board_id}/lists"
    params = {"key": api_key, "token": token}
    
    response = requests.get(lists_url, params=params)
    lists = response.json()
    
    # Find Templates list
    templates_list = None
    for lst in lists:
        if "template" in lst['name'].lower():
            templates_list = lst
            break
    
    if not templates_list:
        print("Templates list not found. Available lists:")
        for lst in lists:
            print(f"  - {lst['name']}")
        return
    
    print(f"Found Templates list: {templates_list['name']} (ID: {templates_list['id']})")
    
    # Read framework JSON
    with open('/home/kaji/curriculum-designer/framework_template.json', 'r') as f:
        framework_json = f.read()
    
    # Create card
    card_url = "https://api.trello.com/1/cards"
    card_data = {
        "key": api_key,
        "token": token,
        "idList": templates_list['id'],
        "name": "Preferences Introduction Framework Template",
        "desc": framework_json,
        "pos": "top"
    }
    
    response = requests.post(card_url, data=card_data)
    
    if response.status_code == 200:
        card = response.json()
        print(f"✅ Card created successfully!")
        print(f"   Name: {card['name']}")
        print(f"   ID: {card['id']}")
        print(f"   URL: {card['url']}")
        print(f"\nNow you can comment '@ai save framework' on this card!")
    else:
        print(f"❌ Error creating card: {response.status_code}")
        print(f"   Response: {response.text}")

if __name__ == "__main__":
    create_framework_card()