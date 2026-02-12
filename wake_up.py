from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

urls_str = os.environ.get("APP_URLS", "")

# 去除首尾空白，按行分割，并过滤掉空行
URL_LIST = [
    url.strip()
    for url in urls_str.splitlines()
    if url.strip()  # 跳过空行
]
# ==========================================

def get_driver():
    """Initializes and returns a headless Chrome driver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Suppress logging
    chrome_options.add_argument("--log-level=3")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def check_is_app_loaded(driver):
    """
    Checks if the Streamlit main container is present.
    Returns True if the app is actually running, False otherwise.
    """
    try:
        # Streamlit apps typically have a div with data-testid="stAppViewContainer" or class "stApp"
        # We check specifically for the main content area to know it's rendered.
        driver.find_element(By.TAG_NAME, "body")
        
        # Check for specific Streamlit indicators
        indicators = [
            (By.CLASS_NAME, "stApp"),
            (By.XPATH, "//div[@data-testid='stAppViewContainer']")
        ]
        
        for method, selector in indicators:
            if len(driver.find_elements(method, selector)) > 0:
                return True
        return False
    except:
        return False

def process_url_sequentially(url, driver_instance=None):
    print(f"\n🚀 [START] Processing: {url}")
    
    # If a driver wasn't passed, create one (safety fallback)
    if driver_instance:
        driver = driver_instance
    else:
        driver = get_driver()

    try:
        driver.get(url)
        
        # 1. Initial wait for page skeleton to load
        time.sleep(3) 

        # 2. Check if the "Wake Up" button exists
        wake_up_xpath = "//*[contains(text(), 'Yes, get this app back up!')]"
        wake_up_buttons = driver.find_elements(By.XPATH, wake_up_xpath)

        if wake_up_buttons:
            print(f"   💤 [STATUS] App is ASLEEP. Clicking 'Yes'...")
            
            try:
                wake_up_buttons[0].click()
            except Exception as e:
                print(f"   ⚠️ Could not click button (might be obscured): {e}")

            print(f"   ⏳ [WAITING] Polling for app to reboot (Max 3 mins)...")
            
            # Smart Waiting Loop: Check every 5 seconds for 180 seconds
            start_time = time.time()
            max_wait = 60
            app_up = False
            
            while time.time() - start_time < max_wait:
                if check_is_app_loaded(driver):
                    app_up = True
                    break
                time.sleep(5)
                print(".", end="", flush=True) # visual progress

            print("") # Newline
            
            if app_up:
                print(f"   ✅ [SUCCESS] App woke up successfully!")
            else:
                print(f"   ❌ [FAILURE] App timed out. It did not load within 3 minutes.")

        else:
            # 3. If no wake up button, verify it is actually running
            if check_is_app_loaded(driver):
                print(f"   ⚡ [ACTIVE] App is already running and validated.")
            else:
                print(f"   ⚠️ [UNKNOWN] 'Wake up' button not found, but app content also not detected. (Check URL or Server Status)")

    except Exception as e:
        print(f"   ❌ [ERROR] Exception occurred: {e}")

    # Note: We do NOT quit the driver here if we want to reuse it, 
    # but for stability, it is often better to restart driver per URL or keep one session.
    # Here we keep the session open in the main loop.

def run_all_checks_sequentially():
    print(f"--- Starting Sequential Validation for {len(URL_LIST)} apps ---")
    
    # Initialize driver ONCE to save startup time, or per URL to ensure clean slate.
    # For stability with many URLs, let's use one driver instance but handle errors gracefully.
    driver = get_driver()
    driver.set_page_load_timeout(30)

    try:
        for i, url in enumerate(URL_LIST):
            print(f"--- [{i+1}/{len(URL_LIST)}] ---")
            try:
                process_url_sequentially(url, driver)
            except Exception as e:
                print(f"Critical error processing {url}: {e}")
                # If driver crashed, restart it
                try:
                    driver.quit()
                except:
                    pass
                driver = get_driver()
            
            # Small pause between URLs
            time.sleep(1)
            
    finally:
        print("\n--- All checks finished. Closing driver. ---")
        driver.quit()

if __name__ == "__main__":
    run_all_checks_sequentially()




