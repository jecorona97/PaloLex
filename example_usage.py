#!/usr/bin/env python3
"""
Example usage script for the Form Filling Agent

This script demonstrates how to use the form filling agent to:
1. Parse a form
2. Fill it with user data
3. Handle missing information
4. Submit the form
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test_user_123"

def make_request(method: str, endpoint: str, data: Dict[Any, Any] = None) -> Dict[Any, Any]:
    """Make HTTP request to the API"""
    url = f"{API_BASE_URL}{endpoint}"
    
    if method.upper() == "GET":
        response = requests.get(url)
    elif method.upper() == "POST":
        response = requests.post(url, json=data if data is not None else {})
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return {}
    
    return response.json()

def test_api_connection():
    """Test if the API server is running"""
    try:
        response = make_request("GET", "/")
        print(f"✓ API server is running: {response.get('message', 'OK')}")
        return True
    except Exception as e:
        print(f"✗ Could not connect to API server: {e}")
        print("Please make sure the API server is running with: python api_server.py")
        return False

def example_form_filling():
    """Example of filling a form with the agent"""
    print("\n=== Form Filling Example ===")
    
    # Example form URL (you can replace this with any form URL)
    form_url = input("Enter a form URL to test (or press Enter for demo): ").strip()
    if not form_url:
        print("Using demo mode - no actual form will be filled")
        return
    
    # Step 1: Start form filling process
    print(f"\n1. Starting form filling process for: {form_url}")
    
    fill_request = {
        "user_id": TEST_USER_ID,
        "form_url": form_url,
        "chat_platform": "demo"
    }
    
    response = make_request("POST", "/fill_form", fill_request)
    
    if not response:
        print("✗ Failed to start form filling process")
        return
    
    session_id = response.get("session_id")
    success = response.get("success", False)
    message = response.get("message", "")
    missing_fields = response.get("missing_fields", [])
    questions = response.get("questions", [])
    
    print(f"Session ID: {session_id}")
    print(f"Success: {success}")
    print(f"Message: {message}")
    
    # Step 2: Handle missing information
    if not success and missing_fields:
        print(f"\n2. Missing information needed for fields: {missing_fields}")
        print("Questions from the agent:")
        for i, question in enumerate(questions, 1):
            print(f"   {i}. {question}")
        
        # Collect user responses
        print("\nProvide answers (or press Enter to skip):")
        user_responses = []
        for question in questions:
            answer = input(f"   {question}: ").strip()
            if answer:
                user_responses.append(answer)
        
        if user_responses:
            # Send responses to the agent
            user_message = " | ".join(user_responses)
            chat_request = {
                "session_id": session_id,
                "message": user_message,
                "user_id": TEST_USER_ID
            }
            
            response = make_request("POST", "/chat", chat_request)
            
            if response:
                print(f"\nAgent response: {response.get('message', 'No response')}")
                success = response.get("success", False)
                
                if not success and response.get("questions"):
                    print("Still need more information:")
                    for question in response.get("questions", []):
                        print(f"   - {question}")
    
    # Step 3: Check session status
    print(f"\n3. Checking session status...")
    status_response = make_request("GET", f"/session/{session_id}")
    
    if status_response:
        print(f"Status: {status_response.get('status', 'unknown')}")
        print(f"Collected data fields: {status_response.get('collected_data_count', 0)}")
        print(f"Missing fields: {status_response.get('missing_fields', [])}")
    
    # Step 4: Submit form (if ready)
    if success:
        print(f"\n4. Submitting form...")
        submit_request = {
            "session_id": session_id,
            "user_id": TEST_USER_ID
        }
        
        submit_response = make_request("POST", "/submit", submit_request)
        
        if submit_response:
            print(f"Submission result: {submit_response.get('message', 'No message')}")
            print(f"Success: {submit_response.get('success', False)}")
    else:
        print(f"\n4. Form not ready for submission - missing information")

def example_user_stats():
    """Example of getting user statistics"""
    print("\n=== User Statistics Example ===")
    
    response = make_request("GET", f"/user/{TEST_USER_ID}/stats")
    
    if response:
        print(f"Forms filled: {response.get('forms_filled', 0)}")
        print(f"Fields learned: {response.get('fields_learned', 0)}")
        print(f"Last activity: {response.get('last_activity', 'Never')}")
    else:
        print("No statistics available")

def demo_chat_integration():
    """Demo of chat integration"""
    print("\n=== Chat Integration Demo ===")
    
    # Simulate a chat message with a form URL
    chat_message = input("Enter a chat message with a form URL (or press Enter to skip): ").strip()
    
    if not chat_message:
        print("Skipping chat integration demo")
        return
    
    webhook_request = {
        "user_id": TEST_USER_ID,
        "message": chat_message,
        "chat_platform": "demo"
    }
    
    response = make_request("POST", "/webhook", webhook_request)
    
    if response:
        print(f"Bot response: {response.get('message', 'No response')}")

def interactive_menu():
    """Interactive menu for testing different features"""
    while True:
        print("\n" + "="*50)
        print("Form Filling Agent - Interactive Demo")
        print("="*50)
        print("1. Test form filling")
        print("2. View user statistics")
        print("3. Test chat integration")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            example_form_filling()
        elif choice == "2":
            example_user_stats()
        elif choice == "3":
            demo_chat_integration()
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

def main():
    """Main function"""
    print("Form Filling Agent - Example Usage")
    print("="*40)
    
    # Test API connection
    if not test_api_connection():
        return
    
    # Show interactive menu
    interactive_menu()

if __name__ == "__main__":
    main()