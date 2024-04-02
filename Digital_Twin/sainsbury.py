from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

def order_ingredients(ingredients):
    options = Options()
    options.add_argument("--incognito")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


    driver.get("https://account.sainsburys.co.uk/gol/login?login_challenge=9c1f2bd5d0d34201b913af3c8389f4e3")
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")


    email_field = driver.find_element(By.ID, "username")
    email_field.send_keys(os.getenv("email"))
    wait = WebDriverWait(driver, 10)
    time.sleep(2)

    password_field = driver.find_element(By.ID, "password")
    password_field.send_keys(os.getenv("password"))
    wait = WebDriverWait(driver, 10)

    cookies = driver.find_element(By.ID, "onetrust-reject-all-handler")
    cookies.click()

    login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='log-in']")))
    login_button.click()

    cookies = driver.find_element(By.ID, "onetrust-reject-all-handler")
    cookies.click()

    book_slot_button = driver.find_element(By.CSS_SELECTOR, 'a[href="https://www.sainsburys.co.uk/gol-ui/slot/book?slot_type=saver_slot"]')
    book_slot_button.click()

    wait.until(EC.presence_of_all_elements_located((By.ID, "username")))


    email_field = driver.find_element(By.ID, "username")
    email_field.send_keys(os.getenv("email"))
    wait = WebDriverWait(driver, 10)
    time.sleep(2) 
    password_field = driver.find_element(By.ID, "password")
    password_field.send_keys(os.getenv("password"))
    login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='log-in']")))
    login_button.click()



    wait = WebDriverWait(driver, 40) 
    available_slots = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//*[contains(@id, 'slot-price')]")))
    if available_slots:
        available_slots[0].click()
        print("Clicked the first available slot.")
    else:
        print("No available slots found.")


    # Check if there are any available slots

    reserve_slot_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-test-id='basic-modal-primary-button']")))
    reserve_slot_button.click()

    wait = WebDriverWait(driver, 10) 
    for ingredient in ingredients:
        search_bar = driver.find_element(By.ID, "search-bar-label")
        time.sleep(5)
        search_bar.send_keys(ingredient)
        search_bar.send_keys(Keys.RETURN)

        wait = WebDriverWait(driver, 10)

        first_add_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-id='add-button']")))  # Adjust the selector
        first_add_button.click()
        search_bar = driver.find_element(By.ID, "search-bar-label")
        search_bar.send_keys(Keys.CONTROL, 'a')
        search_bar.send_keys(Keys.BACK_SPACE)
