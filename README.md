# AI Resume Reviewer

A Flask-based web application that analyzes resumes using OpenAI's GPT-4o-mini and provides an interactive chat interface for personalized resume coaching.

## Features

### 📄 Resume Analysis
- **File Upload**: Supports PDF, DOCX, and TXT formats
- **AI-Powered Analysis**: Uses OpenAI GPT-4o-mini for detailed resume feedback
- **Instant Results**: Get comprehensive analysis with strengths, weaknesses, and improvement suggestions

### 💬 Interactive Chat
- **Resume-Specific Coaching**: AI coach with full context of your uploaded resume
- **Session-Based**: Chat history persists throughout your session
- **Real-Time**: Instant responses with typing indicators
- **Styled Interface**: User and AI messages clearly differentiated

## Tech Stack

- **Backend**: Python Flask
- **AI**: OpenAI GPT-4o-mini API
- **File Processing**: PyPDF2, python-docx
- **Storage**: In-memory session storage (no database required)
- **Frontend**: Vanilla HTML/CSS/JavaScript

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**
   Ensure your `.env` file contains:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Run the Application**
   ```bash
   python app.py
   ```

4. **Access the App**
   Open http://localhost:5000 in your browser

## API Endpoints

### POST /upload
Upload and analyze a resume file.

**Request**: Multipart form data with 'file' field
**Response**: 
```json
{
  "success": true,
  "session_id": "uuid",
  "resume_text": "extracted text",
  "analysis": "AI analysis results"
}
```

### POST /chat
Chat with AI resume coach about your uploaded resume.

**Request**:
```json
{
  "session_id": "uuid",
  "resume_text": "resume content",
  "chat_history": [{"type": "user|ai", "message": "text"}],
  "user_message": "your question"
}
```

**Response**:
```json
{
  "success": true,
  "ai_reply": "AI response",
  "updated_chat_history": [...]
}
```

## Usage

1. **Upload Resume**: Select a PDF, DOCX, or TXT file and click "Analyze Resume"
2. **Review Analysis**: Read the detailed AI-generated feedback
3. **Ask Questions**: Use the chat interface to get specific advice about your resume
4. **Interactive Coaching**: Continue the conversation for personalized improvements

## System Prompts

- **Analysis**: Professional resume reviewer providing detailed feedback
- **Chat**: Professional resume coach giving concise, actionable advice with resume context

## Security Notes

- Session data is stored in memory (cleared on server restart)
- File uploads are validated for allowed extensions
- API keys are loaded from environment variables
- No persistent data storage (database-free)

## Future Enhancements

- Database integration for persistent storage
- User authentication and profiles
- Resume comparison features
- Export analysis reports
- Multiple AI model support
