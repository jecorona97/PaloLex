import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from typing import List, Dict, Optional
import re
import logging
from models import FormField, FormInfo, FieldType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FormParser:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        
    def _setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def _cleanup_driver(self):
        """Clean up WebDriver resources"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def parse_form(self, url: str) -> FormInfo:
        """Parse a form from the given URL"""
        try:
            self._setup_driver()
            logger.info(f"Parsing form from URL: {url}")
            
            # Load the page
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find all forms on the page
            forms = soup.find_all('form')
            
            if not forms:
                raise Exception("No forms found on the page")
            
            # Use the first form (or the most complex one)
            form = self._select_best_form(forms)
            
            # Extract form information
            form_info = self._extract_form_info(form, url)
            
            return form_info
            
        except Exception as e:
            logger.error(f"Error parsing form: {str(e)}")
            raise
        finally:
            self._cleanup_driver()
    
    def _select_best_form(self, forms: List) -> BeautifulSoup:
        """Select the best form from a list of forms"""
        # Prefer forms with more fields
        best_form = forms[0]
        max_fields = len(best_form.find_all(['input', 'select', 'textarea']))
        
        for form in forms[1:]:
            field_count = len(form.find_all(['input', 'select', 'textarea']))
            if field_count > max_fields:
                best_form = form
                max_fields = field_count
                
        return best_form
    
    def _extract_form_info(self, form: BeautifulSoup, url: str) -> FormInfo:
        """Extract form information and fields"""
        # Get form attributes
        action = str(form.get('action', ''))
        method = str(form.get('method', 'POST')).upper()
        
        # Make action URL absolute if relative
        if action and not action.startswith('http'):
            if action.startswith('/'):
                base_url = '/'.join(url.split('/')[:3])
                action = base_url + action
            else:
                action = url.rsplit('/', 1)[0] + '/' + action
        
        # Get form title (try different methods)
        title = self._extract_form_title(form)
        
        # Extract fields
        fields = []
        
        # Process input fields
        for input_elem in form.find_all('input'):
            field = self._parse_input_field(input_elem)
            if field:
                fields.append(field)
        
        # Process select fields
        for select_elem in form.find_all('select'):
            field = self._parse_select_field(select_elem)
            if field:
                fields.append(field)
        
        # Process textarea fields
        for textarea_elem in form.find_all('textarea'):
            field = self._parse_textarea_field(textarea_elem)
            if field:
                fields.append(field)
        
        return FormInfo(
            url=url,
            title=title,
            fields=fields,
            action=action,
            method=method
        )
    
    def _extract_form_title(self, form: BeautifulSoup) -> str:
        """Extract form title using various methods"""
        # Try to find title in various ways
        
        # 1. Look for h1-h6 before the form
        parent = form.parent
        if parent:
            for header in parent.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                if header.get_text(strip=True):
                    return header.get_text(strip=True)
        
        # 2. Look for legend inside fieldset
        legend = form.find('legend')
        if legend:
            return legend.get_text(strip=True)
        
        # 3. Look for title attribute
        if form.get('title'):
            return form.get('title')
        
        # 4. Look for nearby text
        if form.previous_sibling:
            text = form.previous_sibling.get_text(strip=True) if hasattr(form.previous_sibling, 'get_text') else str(form.previous_sibling).strip()
            if text and len(text) < 100:
                return text
        
        return "Form"
    
    def _parse_input_field(self, input_elem: BeautifulSoup) -> Optional[FormField]:
        """Parse an input field"""
        input_type = input_elem.get('type', 'text').lower()
        name = input_elem.get('name', '')
        
        # Skip certain input types
        if input_type in ['hidden', 'submit', 'button', 'reset']:
            return None
        
        if not name:
            return None
        
        # Get label
        label = self._find_field_label(input_elem)
        
        # Map input type to FieldType
        field_type = self._map_input_type(input_type)
        
        # Check if required
        required = input_elem.get('required') is not None
        
        # Get placeholder
        placeholder = input_elem.get('placeholder')
        
        return FormField(
            name=name,
            type=field_type,
            label=label,
            required=required,
            placeholder=placeholder,
            confidence=0.8
        )
    
    def _parse_select_field(self, select_elem: BeautifulSoup) -> Optional[FormField]:
        """Parse a select field"""
        name = select_elem.get('name', '')
        if not name:
            return None
        
        # Get label
        label = self._find_field_label(select_elem)
        
        # Get options
        options = []
        for option in select_elem.find_all('option'):
            option_text = option.get_text(strip=True)
            if option_text and option_text.lower() not in ['select', 'choose', '']:
                options.append(option_text)
        
        # Check if required
        required = select_elem.get('required') is not None
        
        return FormField(
            name=name,
            type=FieldType.SELECT,
            label=label,
            required=required,
            options=options,
            confidence=0.9
        )
    
    def _parse_textarea_field(self, textarea_elem: BeautifulSoup) -> Optional[FormField]:
        """Parse a textarea field"""
        name = textarea_elem.get('name', '')
        if not name:
            return None
        
        # Get label
        label = self._find_field_label(textarea_elem)
        
        # Get placeholder
        placeholder = textarea_elem.get('placeholder')
        
        # Check if required
        required = textarea_elem.get('required') is not None
        
        return FormField(
            name=name,
            type=FieldType.TEXTAREA,
            label=label,
            required=required,
            placeholder=placeholder,
            confidence=0.8
        )
    
    def _find_field_label(self, field_elem: BeautifulSoup) -> str:
        """Find label for a field element"""
        # Try to find label by for attribute
        field_id = field_elem.get('id')
        if field_id:
            label = field_elem.find_parent().find('label', {'for': field_id})
            if label:
                return label.get_text(strip=True)
        
        # Try to find label as previous sibling
        prev_sibling = field_elem.previous_sibling
        if prev_sibling and hasattr(prev_sibling, 'get_text'):
            text = prev_sibling.get_text(strip=True)
            if text and len(text) < 100:
                return text
        
        # Try to find label as parent text
        parent = field_elem.parent
        if parent and parent.name in ['label', 'div', 'span']:
            # Get text content excluding the input itself
            text = parent.get_text(strip=True)
            if text and len(text) < 100:
                return text
        
        # Use name as fallback
        return field_elem.get('name', 'Field').replace('_', ' ').title()
    
    def _map_input_type(self, input_type: str) -> FieldType:
        """Map HTML input type to FieldType"""
        mapping = {
            'text': FieldType.TEXT,
            'email': FieldType.EMAIL,
            'tel': FieldType.PHONE,
            'phone': FieldType.PHONE,
            'date': FieldType.DATE,
            'number': FieldType.NUMBER,
            'checkbox': FieldType.CHECKBOX,
            'radio': FieldType.RADIO,
            'file': FieldType.FILE,
            'password': FieldType.TEXT,  # Treat as text for now
        }
        return mapping.get(input_type, FieldType.TEXT)