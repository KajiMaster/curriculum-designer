#!/usr/bin/env python3
"""
Create DynamoDB table for curriculum frameworks
"""

import boto3
from botocore.exceptions import ClientError

def create_frameworks_table():
    dynamodb = boto3.client('dynamodb')
    
    table_name = 'curriculum-frameworks'
    
    try:
        # Check if table exists
        dynamodb.describe_table(TableName=table_name)
        print(f"Table {table_name} already exists")
        return
    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceNotFoundException':
            raise
    
    # Create table
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'framework_id',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'framework_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'board_id',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'board-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'board_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            Tags=[
                {'Key': 'Environment', 'Value': 'dev'},
                {'Key': 'Purpose', 'Value': 'FrameworkStorage'}
            ]
        )
        
        print(f"Created table: {table_name}")
        print(f"Status: {response['TableDescription']['TableStatus']}")
        
        # Wait for table to be active
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        print(f"Table {table_name} is now active")
        
    except Exception as e:
        print(f"Error creating table: {e}")

if __name__ == "__main__":
    create_frameworks_table()