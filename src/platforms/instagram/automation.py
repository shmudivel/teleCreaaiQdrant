from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyvirtualdisplay import Display
import os
import time
import logging
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstagramAutoPoster:
    """Test implementation of Instagram automation"""
    
    def __init__(self):
        self.driver = None
        self.display = None
        self.logger = logger
        
        # Get credentials from environment
        self.instagram_username = os.getenv("INSTAGRAM_USERNAME")
        self.instagram_password = os.getenv("INSTAGRAM_PASSWORD")
        
        # Configure browser options
        self.browser_options = webdriver.ChromeOptions()
        
    def _init_browser(self, headless=True):
        """Initialize browser with appropriate options"""
        try:
            if headless:
                # Start virtual display for headless mode
                self.display = Display(visible=0, size=(1920, 1080))
                self.display.start()
                
                # Configure headless Chrome
                self.browser_options.add_argument("--headless=new")
                self.browser_options.add_argument("--no-sandbox")
                self.browser_options.add_argument("--disable-gpu")
                self.browser_options.add_argument("--disable-dev-shm-usage")
                self.browser_options.add_argument("--window-size=1920,1080")
            
            # Anti-detection measures
            self.browser_options.add_argument("--disable-blink-features=AutomationControlled")
            self.browser_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            self.browser_options.add_experimental_option("useAutomationExtension", False)
            
            self.driver = webdriver.Chrome(options=self.browser_options)
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Browser initialization failed: {str(e)}")
            return False
            
    def _human_like_delay(self):
        """Add random delay between actions"""
        time.sleep(random.uniform(0.5, 2.5))
    
    def test_instagram_login(self, headless=False):
        """Test Instagram login functionality"""
        if not self.instagram_username or not self.instagram_password:
            self.logger.error("Instagram credentials not found in environment variables")
            return False
            
        try:
            if not self._init_browser(headless=headless):
                return False
                
            self.logger.info("Navigating to Instagram login page...")
            self.driver.get("https://www.instagram.com/accounts/login/")
            self._human_like_delay()
            
            # Wait for and accept cookies if present
            try:
                cookie_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Allow all cookies']"))
                )
                cookie_button.click()
                self._human_like_delay()
            except Exception as e:
                self.logger.info("No cookie banner found or already accepted")
            
            # Fill login form
            self.logger.info("Filling login form...")
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.send_keys(self.instagram_username)
            
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.send_keys(self.instagram_password)
            
            self._human_like_delay()
            
            # Submit form
            self.logger.info("Submitting login form...")
            submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            submit_button.click()
            
            # Wait for successful login
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[text()='Create']"))
                )
                self.logger.info("Successfully logged in!")
                return True
            except Exception as e:
                self.logger.error("Login verification failed. Please check for 2FA or other security prompts.")
                return False
                
        except Exception as e:
            self.logger.error(f"Login test failed: {str(e)}")
            return False
            
        finally:
            if self.driver:
                self.driver.quit()
            if self.display:
                self.display.stop()

def test_automation():
    """Run a basic test of the Instagram automation"""
    poster = InstagramAutoPoster()
    success = poster.test_instagram_login(headless=False)
    return "Test completed successfully" if success else "Test failed"

if __name__ == "__main__":
    print(test_automation()) 