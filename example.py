from screen_recorder import ScreenRecord
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
#pip install webdriver-manager
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

def main():
    output_file = f"C:\\Users\\{os.getlogin()}\\Desktop\\test_output.mp4"
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    screen_recorder = ScreenRecord(driver=driver, file_name=output_file)
    try:
        screen_recorder.record_screen()
        driver.get("https://phptravels.com/demo")
        wait = WebDriverWait(driver, 20)
        first_name_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='first_name']")))
        last_name_field = wait.until(
          EC.presence_of_element_located((By.XPATH, "//input[@name='last_name']")))
        business_field = wait.until(
          EC.presence_of_element_located((By.XPATH, "//input[@name='business_name']")))
        email_field = wait.until(
          EC.presence_of_element_located((By.XPATH, "//input[@name='email']")))
        ac = ActionChains(driver)
        ac.send_keys_to_element(first_name_field, "John") \
            .send_keys_to_element(last_name_field, "Doe") \
            .send_keys_to_element(business_field, "My Business") \
            .send_keys_to_element(email_field, "john@doe.com") \
            .perform()
        time.sleep(3)
    finally:
        driver.close()
        screen_recorder.stop_recording()


if __name__ == "__main__":
    main()
