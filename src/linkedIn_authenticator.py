import time
from typing import Optional
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class LinkedInAuthenticator:

    def __init__(self, driver: Optional[WebDriver] = None) -> None:
        self.driver: Optional[WebDriver] = driver
        self.email = ""
        self.password = ""

    def set_secrets(self, email: str, password: str) -> None:
        """Set the email and password for LinkedIn login."""
        self.email = email
        self.password = password

    def start(self) -> None:
        """Start the LinkedIn login process using the Chrome browser."""
        print("Starting Chrome browser to log in to LinkedIn.")
        if self.driver is None:
            raise ValueError("Driver must be initialized before starting the login process.")
        if self.driver:
            self.driver.get("https://www.linkedin.com")
        self.wait_for_page_load()
        if not self.is_logged_in():
            self.handle_login()

    def handle_login(self) -> None:
        """Handle the login process for LinkedIn."""
        print("Navigating to the LinkedIn login page...")
        if self.driver:
            self.driver.get("https://www.linkedin.com/login")
        if "feed" in self.driver.current_url:
            print("User is already logged in.")
            return
        try:
            self.enter_credentials()
            self.submit_login_form()
        except NoSuchElementException:
            print("Could not log in to LinkedIn. Please check your credentials.")
        time.sleep(35) #TODO fix better
        self.handle_security_check()

    def enter_credentials(self) -> None:
        """Enter the user's email and password into the LinkedIn login form."""
        try:
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.send_keys(self.email)
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(self.password)
        except TimeoutException:
            print("Login form not found. Aborting login.")

    def submit_login_form(self) -> None:
        """Submit the LinkedIn login form."""
        try:
            login_button = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
            login_button.click()
        except NoSuchElementException:
            print("Login button not found. Please verify the page structure.")

    def handle_security_check(self) -> None:
        """Handle any security checks that occur after login."""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.url_contains("https://www.linkedin.com/checkpoint/challengesV2/")
            )
            print("Security checkpoint detected. Please complete the challenge.")
            WebDriverWait(self.driver, 300).until(
                EC.url_contains("https://www.linkedin.com/feed/")
            )
            print("Security check completed")
        except TimeoutException:
            print("Security check not completed. Please try again later.")

    def is_logged_in(self) -> bool:
        """Check if the user is already logged into LinkedIn."""
        if self.driver:
            self.driver.get("https://www.linkedin.com/")
            return self.driver.current_url == "https://www.linkedin.com/feed/"
        return False

    def wait_for_page_load(self, timeout: int = 10) -> None:
        """Wait for the LinkedIn page to fully load."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            print("Page load timed out.")
