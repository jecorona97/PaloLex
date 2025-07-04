# Form Filling Agent

An intelligent agent that automatically fills out web forms for users. This agent can be integrated with chat applications like WhatsApp, Telegram, and iMessage to provide form automation services.

## Features

- **Automatic Form Parsing**: Analyzes web forms to understand field types and requirements
- **Smart Field Mapping**: Matches form fields with stored user data using AI-powered matching
- **Learning System**: Remembers user preferences and information for future use
- **Chat Integration**: Works with popular chat platforms (WhatsApp, Telegram, iMessage)
- **Multi-step Forms**: Handles complex forms with multiple pages and dependencies
- **User Data Storage**: Securely stores user information for reuse across forms
- **Form Validation**: Validates form data before submission
- **Error Handling**: Graceful error handling with user-friendly messages

## Architecture

The system consists of several key components:

1. **Form Parser** (`form_parser.py`): Analyzes web forms using Selenium and BeautifulSoup
2. **User Storage** (`user_storage.py`): SQLite-based storage for user data and preferences
3. **Form Automation** (`form_automation.py`): Selenium-based form filling automation
4. **Form Agent** (`form_agent.py`): Main orchestrator that coordinates all components
5. **API Server** (`api_server.py`): FastAPI-based web server for chat integration

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd form-filling-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Chrome WebDriver:
The system will automatically download ChromeDriver using `webdriver-manager`.

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Usage

### Running the API Server

Start the FastAPI server:
```bash
python api_server.py
```

The server will run on `http://localhost:8000` by default.

### API Endpoints

#### 1. Fill Form
```bash
POST /fill_form
```
Start the form filling process for a given URL.

**Request:**
```json
{
  "user_id": "user123",
  "form_url": "https://example.com/form",
  "chat_platform": "whatsapp"
}
```

**Response:**
```json
{
  "session_id": "abc-123-def",
  "success": false,
  "message": "Need additional information to fill the form",
  "missing_fields": ["email", "phone"],
  "questions": [
    "What is your email address?",
    "What is your phone number?"
  ]
}
```

#### 2. Chat Message
```bash
POST /chat
```
Handle user responses with missing information.

**Request:**
```json
{
  "session_id": "abc-123-def",
  "message": "john@example.com and +1234567890",
  "user_id": "user123"
}
```

#### 3. Submit Form
```bash
POST /submit
```
Submit the filled form.

**Request:**
```json
{
  "session_id": "abc-123-def",
  "user_id": "user123"
}
```

#### 4. Session Status
```bash
GET /session/{session_id}
```
Get the current status of a form filling session.

#### 5. User Statistics
```bash
GET /user/{user_id}/stats
```
Get user statistics (forms filled, fields learned, etc.).

### Chat Platform Integration

#### WhatsApp
```bash
POST /whatsapp
```
Webhook endpoint for WhatsApp Business API.

#### Telegram
```bash
POST /telegram
```
Webhook endpoint for Telegram Bot API.

#### Generic Webhook
```bash
POST /webhook
```
Generic webhook endpoint for any chat platform.

## Usage Examples

### Example 1: Simple Form Filling

```python
import requests

# Start form filling
response = requests.post("http://localhost:8000/fill_form", json={
    "user_id": "user123",
    "form_url": "https://example.com/contact-form",
    "chat_platform": "whatsapp"
})

session_id = response.json()["session_id"]

# If missing information is needed
if not response.json()["success"]:
    # Provide missing information
    requests.post("http://localhost:8000/chat", json={
        "session_id": session_id,
        "message": "Email: john@example.com, Phone: +1234567890",
        "user_id": "user123"
    })

# Submit the form
requests.post("http://localhost:8000/submit", json={
    "session_id": session_id,
    "user_id": "user123"
})
```

### Example 2: Chat Integration

The agent can be integrated with chat platforms by setting up webhooks:

1. **WhatsApp**: Configure WhatsApp Business API webhook to point to `/whatsapp`
2. **Telegram**: Set up Telegram bot webhook to point to `/telegram`
3. **Custom**: Use the generic `/webhook` endpoint for other platforms

## Configuration

### Environment Variables

Create a `.env` file with:

```bash
# Database
DATABASE_URL=sqlite:///user_data.db

# API Configuration
PORT=8000
HOST=0.0.0.0

# Chrome WebDriver
CHROME_HEADLESS=true

# Logging
LOG_LEVEL=INFO
```

### Form Parser Configuration

The form parser can be customized by modifying `form_parser.py`:

- **Timeout settings**: Adjust WebDriver wait times
- **Field mapping**: Customize how form fields are identified
- **Browser options**: Add or remove Chrome options

### Storage Configuration

The user storage system uses SQLite by default but can be configured to use other databases by modifying `user_storage.py`.

## Data Storage

The system stores:

- **User Profiles**: Personal information and preferences
- **Form Sessions**: Active form filling sessions
- **Field Mappings**: Learned associations between form fields and user data
- **Usage Statistics**: Form completion history and success rates

## Security Considerations

1. **Data Encryption**: Consider encrypting sensitive user data
2. **Access Control**: Implement proper authentication for API endpoints
3. **Rate Limiting**: Add rate limiting to prevent abuse
4. **Input Validation**: Validate all user inputs
5. **HTTPS**: Use HTTPS in production

## Troubleshooting

### Common Issues

1. **ChromeDriver Issues**: Ensure Chrome browser is installed
2. **Form Parsing Failures**: Check if the website blocks automation
3. **Database Errors**: Verify database permissions and file paths
4. **Network Issues**: Check firewall and proxy settings

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue on GitHub or contact the development team.

## Roadmap

- [ ] Machine learning for better field mapping
- [ ] Support for more form types (file uploads, complex validations)
- [ ] Multi-language support
- [ ] Form preview before submission
- [ ] Integration with password managers
- [ ] OCR for image-based forms
- [ ] Voice input support
- [ ] Advanced analytics and reporting