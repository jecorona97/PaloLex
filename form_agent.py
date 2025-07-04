import uuid
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from models import (
    FormFillRequest, FormFillResponse, ChatSession, FormInfo, 
    FormField, FieldType, UserProfile
)
from form_parser import FormParser
from user_storage import UserStorage
from form_automation import FormAutomator

logger = logging.getLogger(__name__)

class FormFillingAgent:
    def __init__(self, db_path: str = "user_data.db"):
        self.storage = UserStorage(db_path)
        self.parser = FormParser()
        self.automator = FormAutomator()
        
    def process_form_request(self, request: FormFillRequest) -> FormFillResponse:
        """Process a form filling request from a chat app"""
        try:
            # Generate session ID
            session_id = str(uuid.uuid4())
            
            logger.info(f"Processing form request for user {request.user_id}: {request.form_url}")
            
            # Parse the form
            try:
                form_info = self.parser.parse_form(request.form_url)
                logger.info(f"Parsed form with {len(form_info.fields)} fields")
            except Exception as e:
                logger.error(f"Error parsing form: {str(e)}")
                return FormFillResponse(
                    session_id=session_id,
                    success=False,
                    message=f"Could not parse form: {str(e)}"
                )
            
            # Create session
            session = ChatSession(
                session_id=session_id,
                user_id=request.user_id,
                form_url=request.form_url,
                form_info=form_info,
                status="pending"
            )
            
            # Try to fill fields with known user data
            field_values, missing_fields = self._match_user_data(request.user_id, form_info)
            
            session.collected_data = field_values
            session.missing_fields = missing_fields
            
            # Save session
            self.storage.save_session(session)
            
            if missing_fields:
                # Need to ask user for missing information
                questions = self._generate_questions(missing_fields, form_info)
                session.status = "collecting"
                self.storage.save_session(session)
                
                return FormFillResponse(
                    session_id=session_id,
                    success=False,
                    message="Need additional information to fill the form",
                    missing_fields=missing_fields,
                    questions=questions
                )
            else:
                # Can fill the form immediately
                return self._attempt_form_filling(session)
                
        except Exception as e:
            logger.error(f"Error processing form request: {str(e)}")
            return FormFillResponse(
                session_id=session_id,
                success=False,
                message=f"Error processing request: {str(e)}"
            )
    
    def handle_user_response(self, session_id: str, user_message: str) -> FormFillResponse:
        """Handle user response with missing information"""
        try:
            session = self.storage.get_session(session_id)
            if not session:
                return FormFillResponse(
                    session_id=session_id,
                    success=False,
                    message="Session not found"
                )
            
            # Parse user response
            self._parse_user_response(session, user_message)
            
            # Check if we still have missing fields
            remaining_missing = []
            for field_name in session.missing_fields:
                if field_name not in session.collected_data:
                    remaining_missing.append(field_name)
            
            session.missing_fields = remaining_missing
            
            if remaining_missing:
                # Still need more information
                if session.form_info:
                    questions = self._generate_questions(remaining_missing, session.form_info)
                    session.status = "collecting"
                    self.storage.save_session(session)
                else:
                    return FormFillResponse(
                        session_id=session_id,
                        success=False,
                        message="Session form info not available"
                    )
                
                return FormFillResponse(
                    session_id=session_id,
                    success=False,
                    message="Need more information",
                    missing_fields=remaining_missing,
                    questions=questions
                )
            else:
                # Ready to fill form
                return self._attempt_form_filling(session)
                
        except Exception as e:
            logger.error(f"Error handling user response: {str(e)}")
            return FormFillResponse(
                session_id=session_id,
                success=False,
                message=f"Error processing response: {str(e)}"
            )
    
    def _match_user_data(self, user_id: str, form_info: FormInfo) -> Tuple[Dict[str, str], List[str]]:
        """Match form fields with known user data"""
        field_values = {}
        missing_fields = []
        
        for field in form_info.fields:
            # Try to get value from user storage
            value = self.storage.get_user_field_value(user_id, field.label, field.type.value)
            
            if value:
                field_values[field.name] = value
                logger.info(f"Found value for field {field.name}: {value}")
            elif field.required:
                missing_fields.append(field.name)
                logger.info(f"Missing required field: {field.name}")
        
        return field_values, missing_fields
    
    def _generate_questions(self, missing_fields: List[str], form_info: FormInfo) -> List[str]:
        """Generate questions for missing fields"""
        questions = []
        field_map = {field.name: field for field in form_info.fields}
        
        for field_name in missing_fields:
            if field_name in field_map:
                field = field_map[field_name]
                question = self._create_question_for_field(field)
                questions.append(question)
        
        return questions
    
    def _create_question_for_field(self, field: FormField) -> str:
        """Create a natural language question for a field"""
        if field.type == FieldType.EMAIL:
            return f"What is your email address? (for {field.label})"
        elif field.type == FieldType.PHONE:
            return f"What is your phone number? (for {field.label})"
        elif field.type == FieldType.DATE:
            return f"What date should I enter for {field.label}? (format: YYYY-MM-DD)"
        elif field.type == FieldType.SELECT and field.options:
            options_text = ", ".join(field.options)
            return f"What should I select for {field.label}? Options: {options_text}"
        elif field.type == FieldType.CHECKBOX:
            return f"Should I check the box for {field.label}? (yes/no)"
        elif field.type == FieldType.RADIO and field.options:
            options_text = ", ".join(field.options)
            return f"Which option should I select for {field.label}? Options: {options_text}"
        else:
            placeholder_text = f" (example: {field.placeholder})" if field.placeholder else ""
            return f"What should I enter for {field.label}?{placeholder_text}"
    
    def _parse_user_response(self, session: ChatSession, user_message: str) -> None:
        """Parse user response and extract field values"""
        # This is a simplified parser - in production, you'd want more sophisticated NLP
        
        # For now, we'll assume the user provides answers in order of missing fields
        # or in a key-value format
        
        missing_fields = session.missing_fields
        if not session.form_info:
            return
        field_map = {field.name: field for field in session.form_info.fields}
        
        # Try to parse key-value pairs
        lines = user_message.strip().split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                # Find matching field
                for field_name in missing_fields:
                    field = field_map.get(field_name)
                    if field and (key in field.label.lower() or key in field.name.lower()):
                        session.collected_data[field_name] = value
                        # Save to user storage for future use
                        self.storage.save_field_value(
                            session.user_id, field.label, field.type.value, value
                        )
                        break
        
        # If no key-value pairs found, try to map to first missing field
        if not any(':' in line for line in lines) and missing_fields:
            first_missing = missing_fields[0]
            value = user_message.strip()
            if value:
                session.collected_data[first_missing] = value
                field = field_map.get(first_missing)
                if field:
                    self.storage.save_field_value(
                        session.user_id, field.label, field.type.value, value
                    )
    
    def _attempt_form_filling(self, session: ChatSession) -> FormFillResponse:
        """Attempt to fill the form with collected data"""
        try:
            session.status = "filling"
            self.storage.save_session(session)
            
            # Fill the form
            if not session.form_info:
                return FormFillResponse(
                    session_id=session.session_id,
                    success=False,
                    message="Session form info not available"
                )
            
            success, message, failed_fields = self.automator.fill_form(
                session.form_info, session.collected_data
            )
            
            if success:
                session.status = "completed"
                self.storage.save_session(session)
                
                return FormFillResponse(
                    session_id=session.session_id,
                    success=True,
                    message="Form filled successfully! You can now review and submit it."
                )
            else:
                session.status = "error"
                self.storage.save_session(session)
                
                return FormFillResponse(
                    session_id=session.session_id,
                    success=False,
                    message=f"Error filling form: {message}"
                )
                
        except Exception as e:
            session.status = "error"
            self.storage.save_session(session)
            logger.error(f"Error filling form: {str(e)}")
            
            return FormFillResponse(
                session_id=session.session_id,
                success=False,
                message=f"Error filling form: {str(e)}"
            )
    
    def submit_form(self, session_id: str) -> FormFillResponse:
        """Submit a filled form"""
        try:
            session = self.storage.get_session(session_id)
            if not session:
                return FormFillResponse(
                    session_id=session_id,
                    success=False,
                    message="Session not found"
                )
            
            if session.status != "completed":
                return FormFillResponse(
                    session_id=session_id,
                    success=False,
                    message="Form must be filled before submission"
                )
            
            # Submit the form
            if not session.form_info:
                return FormFillResponse(
                    session_id=session_id,
                    success=False,
                    message="Session form info not available"
                )
            
            success, message = self.automator.submit_form(
                session.form_info, session.collected_data
            )
            
            if success:
                session.status = "submitted"
                self.storage.save_session(session)
                
                return FormFillResponse(
                    session_id=session_id,
                    success=True,
                    message="Form submitted successfully!"
                )
            else:
                return FormFillResponse(
                    session_id=session_id,
                    success=False,
                    message=f"Error submitting form: {message}"
                )
                
        except Exception as e:
            logger.error(f"Error submitting form: {str(e)}")
            return FormFillResponse(
                session_id=session_id,
                success=False,
                message=f"Error submitting form: {str(e)}"
            )
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get statistics for a user"""
        return self.storage.get_user_stats(user_id)
    
    def get_session_status(self, session_id: str) -> Optional[ChatSession]:
        """Get current session status"""
        return self.storage.get_session(session_id)