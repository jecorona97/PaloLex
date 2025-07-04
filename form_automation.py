from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from typing import Dict, List, Optional, Tuple
import logging
import time
from models import FormInfo, FormField, FieldType

logger = logging.getLogger(__name__)

class FormAutomator:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.wait = None
        
    def _setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 10)
        
    def _cleanup_driver(self):
        """Clean up WebDriver resources"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None
    
    def fill_form(self, form_info: FormInfo, field_values: Dict[str, str]) -> Tuple[bool, str, List[str]]:
        """
        Fill out a form with provided values
        Returns: (success, message, failed_fields)
        """
        failed_fields = []
        
        try:
            self._setup_driver()
            logger.info(f"Starting form automation for: {form_info.url}")
            
            # Navigate to the form
            self.driver.get(form_info.url)
            
            # Wait for page to load
            time.sleep(2)
            
            # Fill each field
            for field in form_info.fields:
                if field.name in field_values:
                    success = self._fill_field(field, field_values[field.name])
                    if not success:
                        failed_fields.append(field.name)
                        logger.warning(f"Failed to fill field: {field.name}")
                elif field.required:
                    failed_fields.append(field.name)
                    logger.warning(f"Required field not provided: {field.name}")
            
            if failed_fields:
                return False, f"Failed to fill {len(failed_fields)} fields", failed_fields
            
            # Take screenshot for verification
            screenshot_path = f"form_filled_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Form filled successfully. Screenshot saved: {screenshot_path}")
            
            return True, "Form filled successfully", []
            
        except Exception as e:
            logger.error(f"Error filling form: {str(e)}")
            return False, f"Error filling form: {str(e)}", failed_fields
        finally:
            self._cleanup_driver()
    
    def submit_form(self, form_info: FormInfo, field_values: Dict[str, str]) -> Tuple[bool, str]:
        """
        Fill and submit a form
        Returns: (success, message)
        """
        try:
            self._setup_driver()
            logger.info(f"Starting form submission for: {form_info.url}")
            
            # Navigate to the form
            self.driver.get(form_info.url)
            time.sleep(2)
            
            # Fill all fields
            failed_fields = []
            for field in form_info.fields:
                if field.name in field_values:
                    success = self._fill_field(field, field_values[field.name])
                    if not success:
                        failed_fields.append(field.name)
                elif field.required:
                    failed_fields.append(field.name)
            
            if failed_fields:
                return False, f"Cannot submit: missing required fields {failed_fields}"
            
            # Find and click submit button
            submit_success = self._submit_form()
            if not submit_success:
                return False, "Could not find or click submit button"
            
            # Wait for submission to complete
            time.sleep(3)
            
            # Check for success indicators
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            success_indicators = [
                "thank you", "success", "submitted", "confirmation",
                "complete", "received", "processed"
            ]
            
            error_indicators = [
                "error", "failed", "invalid", "required", "missing"
            ]
            
            # Check for success
            if any(indicator in page_source for indicator in success_indicators):
                logger.info("Form submission appears successful")
                return True, "Form submitted successfully"
            
            # Check for errors
            if any(indicator in page_source for indicator in error_indicators):
                logger.warning("Form submission may have failed")
                return False, "Form submission failed - error detected on page"
            
            # If URL changed, likely successful
            if current_url != form_info.url:
                logger.info("Form submission successful - redirected to new page")
                return True, "Form submitted successfully"
            
            return True, "Form submitted (status unclear)"
            
        except Exception as e:
            logger.error(f"Error submitting form: {str(e)}")
            return False, f"Error submitting form: {str(e)}"
        finally:
            self._cleanup_driver()
    
    def _fill_field(self, field: FormField, value: str) -> bool:
        """Fill a specific field with a value"""
        try:
            if field.type == FieldType.TEXT or field.type == FieldType.EMAIL:
                return self._fill_text_field(field.name, value)
            elif field.type == FieldType.TEXTAREA:
                return self._fill_textarea_field(field.name, value)
            elif field.type == FieldType.SELECT:
                return self._fill_select_field(field.name, value)
            elif field.type == FieldType.CHECKBOX:
                return self._fill_checkbox_field(field.name, value)
            elif field.type == FieldType.RADIO:
                return self._fill_radio_field(field.name, value)
            elif field.type == FieldType.DATE:
                return self._fill_date_field(field.name, value)
            elif field.type == FieldType.NUMBER:
                return self._fill_number_field(field.name, value)
            elif field.type == FieldType.PHONE:
                return self._fill_phone_field(field.name, value)
            else:
                logger.warning(f"Unknown field type: {field.type}")
                return False
        except Exception as e:
            logger.error(f"Error filling field {field.name}: {str(e)}")
            return False
    
    def _fill_text_field(self, field_name: str, value: str) -> bool:
        """Fill a text input field"""
        try:
            # Try multiple selectors
            selectors = [
                f"input[name='{field_name}']",
                f"input[id='{field_name}']",
                f"input[name*='{field_name}']",
                f"input[id*='{field_name}']"
            ]
            
            element = None
            for selector in selectors:
                try:
                    element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not element:
                logger.warning(f"Could not find text field: {field_name}")
                return False
            
            # Clear and fill
            element.clear()
            element.send_keys(value)
            return True
            
        except Exception as e:
            logger.error(f"Error filling text field {field_name}: {str(e)}")
            return False
    
    def _fill_textarea_field(self, field_name: str, value: str) -> bool:
        """Fill a textarea field"""
        try:
            selectors = [
                f"textarea[name='{field_name}']",
                f"textarea[id='{field_name}']",
                f"textarea[name*='{field_name}']",
                f"textarea[id*='{field_name}']"
            ]
            
            element = None
            for selector in selectors:
                try:
                    element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not element:
                logger.warning(f"Could not find textarea field: {field_name}")
                return False
            
            element.clear()
            element.send_keys(value)
            return True
            
        except Exception as e:
            logger.error(f"Error filling textarea field {field_name}: {str(e)}")
            return False
    
    def _fill_select_field(self, field_name: str, value: str) -> bool:
        """Fill a select dropdown field"""
        try:
            selectors = [
                f"select[name='{field_name}']",
                f"select[id='{field_name}']",
                f"select[name*='{field_name}']",
                f"select[id*='{field_name}']"
            ]
            
            element = None
            for selector in selectors:
                try:
                    element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not element:
                logger.warning(f"Could not find select field: {field_name}")
                return False
            
            select = Select(element)
            
            # Try to select by visible text
            try:
                select.select_by_visible_text(value)
                return True
            except NoSuchElementException:
                pass
            
            # Try to select by value
            try:
                select.select_by_value(value)
                return True
            except NoSuchElementException:
                pass
            
            # Try partial text match
            for option in select.options:
                if value.lower() in option.text.lower():
                    select.select_by_visible_text(option.text)
                    return True
            
            logger.warning(f"Could not find matching option for {field_name}: {value}")
            return False
            
        except Exception as e:
            logger.error(f"Error filling select field {field_name}: {str(e)}")
            return False
    
    def _fill_checkbox_field(self, field_name: str, value: str) -> bool:
        """Fill a checkbox field"""
        try:
            selectors = [
                f"input[type='checkbox'][name='{field_name}']",
                f"input[type='checkbox'][id='{field_name}']",
                f"input[type='checkbox'][name*='{field_name}']",
                f"input[type='checkbox'][id*='{field_name}']"
            ]
            
            element = None
            for selector in selectors:
                try:
                    element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not element:
                logger.warning(f"Could not find checkbox field: {field_name}")
                return False
            
            should_check = value.lower() in ['true', '1', 'yes', 'on', 'checked']
            is_checked = element.is_selected()
            
            if should_check and not is_checked:
                element.click()
            elif not should_check and is_checked:
                element.click()
            
            return True
            
        except Exception as e:
            logger.error(f"Error filling checkbox field {field_name}: {str(e)}")
            return False
    
    def _fill_radio_field(self, field_name: str, value: str) -> bool:
        """Fill a radio button field"""
        try:
            # Find all radio buttons with the same name
            radios = self.driver.find_elements(By.CSS_SELECTOR, f"input[type='radio'][name='{field_name}']")
            
            for radio in radios:
                # Check by value
                if radio.get_attribute('value') == value:
                    radio.click()
                    return True
                
                # Check by nearby label text
                try:
                    label = radio.find_element(By.XPATH, "following-sibling::label")
                    if value.lower() in label.text.lower():
                        radio.click()
                        return True
                except NoSuchElementException:
                    pass
            
            logger.warning(f"Could not find matching radio option for {field_name}: {value}")
            return False
            
        except Exception as e:
            logger.error(f"Error filling radio field {field_name}: {str(e)}")
            return False
    
    def _fill_date_field(self, field_name: str, value: str) -> bool:
        """Fill a date field"""
        try:
            selectors = [
                f"input[type='date'][name='{field_name}']",
                f"input[type='date'][id='{field_name}']",
                f"input[name='{field_name}']",
                f"input[id='{field_name}']"
            ]
            
            element = None
            for selector in selectors:
                try:
                    element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not element:
                logger.warning(f"Could not find date field: {field_name}")
                return False
            
            element.clear()
            element.send_keys(value)
            return True
            
        except Exception as e:
            logger.error(f"Error filling date field {field_name}: {str(e)}")
            return False
    
    def _fill_number_field(self, field_name: str, value: str) -> bool:
        """Fill a number field"""
        return self._fill_text_field(field_name, value)
    
    def _fill_phone_field(self, field_name: str, value: str) -> bool:
        """Fill a phone field"""
        return self._fill_text_field(field_name, value)
    
    def _submit_form(self) -> bool:
        """Find and click the submit button"""
        try:
            # Try different submit button selectors
            submit_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                "button:contains('Submit')",
                "input[value*='Submit']",
                "button:contains('Send')",
                "input[value*='Send']",
                "button:contains('Continue')",
                "input[value*='Continue']",
                "button:contains('Next')",
                "input[value*='Next']"
            ]
            
            for selector in submit_selectors:
                try:
                    if ":contains" in selector:
                        # Use XPath for text content
                        text = selector.split(":contains('")[1].split("')")[0]
                        xpath = f"//button[contains(text(), '{text}')]"
                        submit_button = self.driver.find_element(By.XPATH, xpath)
                    else:
                        submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if submit_button.is_displayed() and submit_button.is_enabled():
                        submit_button.click()
                        return True
                except NoSuchElementException:
                    continue
            
            logger.warning("Could not find submit button")
            return False
            
        except Exception as e:
            logger.error(f"Error submitting form: {str(e)}")
            return False