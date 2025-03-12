from platforms.instagram.automation import InstagramAutoPoster
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Test Instagram automation functionality"""
    try:
        logger.info("Starting Instagram automation test...")
        
        # Create automation instance
        poster = InstagramAutoPoster()
        
        # Test login (non-headless for visual verification)
        success = poster.test_instagram_login(headless=False)
        
        if success:
            logger.info("Instagram automation test completed successfully!")
        else:
            logger.error("Instagram automation test failed!")
            
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")

if __name__ == "__main__":
    main() 