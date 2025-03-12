import os
from facebook import GraphAPI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_instagram_connection():
    """
    Test connection to Instagram account using Facebook Graph API.
    You'll need to set up these environment variables:
    - INSTAGRAM_ACCESS_TOKEN: Your Instagram access token
    - INSTAGRAM_BUSINESS_ACCOUNT_ID: Your Instagram Business Account ID
    """
    try:
        # Initialize the Graph API with your access token
        access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
        if not access_token:
            raise ValueError("INSTAGRAM_ACCESS_TOKEN not found in environment variables")

        graph = GraphAPI(access_token=access_token)

        # Get Instagram Business Account ID
        instagram_account_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
        if not instagram_account_id:
            raise ValueError("INSTAGRAM_BUSINESS_ACCOUNT_ID not found in environment variables")

        # Test connection by getting basic account info
        account_info = graph.get_object(
            instagram_account_id,
            fields='username,profile_picture_url,followers_count,media_count'
        )

        print("Successfully connected to Instagram!")
        print(f"Account Username: {account_info.get('username')}")
        print(f"Followers Count: {account_info.get('followers_count')}")
        print(f"Media Count: {account_info.get('media_count')}")

        return True, account_info

    except Exception as e:
        print(f"Error connecting to Instagram: {str(e)}")
        return False, str(e)

if __name__ == "__main__":
    success, result = test_instagram_connection()
    if not success:
        print("Please make sure you have set up the following:")
        print("1. Created a Facebook App")
        print("2. Set up Instagram Basic Display API")
        print("3. Generated an access token")
        print("4. Added the access token to your .env file") 