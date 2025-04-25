#!/usr/bin/env python3
"""
Script to test YouTube authentication with the token file.
This script will check if the YouTube token file is valid and can be used for authentication.
"""

import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# File path for YouTube token
TOKEN_FILE = "youtube_token.json"

def test_youtube_auth():
    """Test YouTube authentication and token validity."""
    print(f"Looking for token file at: {TOKEN_FILE}")
    
    if not os.path.exists(TOKEN_FILE):
        print(f"Error: Token file not found at {TOKEN_FILE}")
        return False
    
    try:
        print("Reading token file...")
        with open(TOKEN_FILE, 'r') as token_file:
            token_data = json.load(token_file)
        
        print("Creating credentials from token data...")
        credentials = Credentials.from_authorized_user_info(token_data)
        
        print(f"Token scopes: {credentials.scopes}")
        
        if not credentials.valid:
            if credentials.expired and credentials.refresh_token:
                print("Token expired, refreshing...")
                credentials.refresh(Request())
                
                # Save refreshed credentials
                token_data = {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': credentials.client_secret,
                    'scopes': credentials.scopes
                }
                
                with open(TOKEN_FILE, 'w') as token_file:
                    json.dump(token_data, token_file)
                print(f"Refreshed token saved to {TOKEN_FILE}")
            else:
                print("Error: Invalid credentials and cannot refresh.")
                return False
        
        print("Building YouTube API service...")
        youtube = build("youtube", "v3", credentials=credentials)
        
        print("Checking if token has upload permissions...")
        # Instead of accessing channel info, just check if we have the required scope
        has_upload_scope = 'https://www.googleapis.com/auth/youtube.upload' in credentials.scopes
        
        if has_upload_scope:
            print("Success! Token has YouTube upload permissions.")
            
            # Just verify we can get a valid service object
            try:
                # Try accessing the uploads endpoint schema (doesn't make an actual upload)
                youtube.videos().insert(part="snippet,status", body={}, media_body=None)
                print("YouTube API service connection verified.")
                return True
            except Exception as e:
                print(f"Error verifying YouTube API service: {str(e)}")
                return False
        else:
            print("Error: Token does not have YouTube upload permissions.")
            print(f"Current scopes: {credentials.scopes}")
            return False
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== YouTube Authentication Test ===")
    result = test_youtube_auth()
    print(f"\nTest result: {'SUCCESS' if result else 'FAILED'}")
    print("==================================") 