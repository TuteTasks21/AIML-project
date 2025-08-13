from flask import Flask, request, jsonify, session, render_template_string
import os
from dotenv import load_dotenv
import openai
import PyPDF2
import docx
import uuid
from werkzeug.utils import secure_filename
import io

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Configure OpenAI client
try:
    client = openai.OpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        timeout=30.0
    )
except Exception as e:
    print(f"OpenAI client initialization error: {e}")
    # Fallback to older API style if needed
    openai.api_key = os.getenv('OPENAI_API_KEY')
    client = None

# In-memory storage for sessions (replace with database in production)
session_data = {}

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_stream):
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(file_stream)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def extract_text_from_docx(file_stream):
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file_stream)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        return f"Error reading DOCX: {str(e)}"

def extract_text_from_file(file):
    """Extract text from uploaded file based on its type"""
    filename = file.filename.lower()
    
    if filename.endswith('.pdf'):
        return extract_text_from_pdf(file.stream)
    elif filename.endswith('.docx'):
        return extract_text_from_docx(file.stream)
    elif filename.endswith('.txt'):
        return file.read().decode('utf-8')
    else:
        return "Unsupported file format"

def analyze_resume_with_ai(resume_text):
    """Comprehensive resume analysis with mandatory features"""
    try:
        system_prompt = """You are an expert resume analyst and career coach. You must provide a comprehensive analysis covering these THREE MANDATORY sections:

## 1. AI RESUME IMPROVEMENT
Provide clear, actionable suggestions for:
- Formatting and layout improvements
- Grammar and language corrections
- Keyword optimization for the industry
- Overall presentation enhancements
- Content structure improvements

## 2. ATS SCORE SIMULATION
Analyze ATS (Applicant Tracking System) compatibility:
- Provide an ATS compatibility score (0-100)
- List specific ATS optimization issues found
- Suggest keywords to add for better ATS performance
- Comment on formatting compatibility with ATS systems

## 3. CAREER COACHING INSIGHTS
Provide strategic career advice:
- Identify career strengths and growth areas
- Suggest skill gaps to address
- Recommend experience highlights to emphasize
- Provide industry-specific guidance

Format your response with clear headers using ### for each section. Be specific, actionable, and professional."""

        if client:
            # Use new client
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": system_prompt
                    },
                    {
                        "role": "user", 
                        "content": f"Please provide a comprehensive analysis of this resume:\n\n{resume_text}"
                    }
                ],
                max_tokens=2000,
                temperature=0.7
            )
            return response.choices[0].message.content
        else:
            # Fallback to older API
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": system_prompt
                    },
                    {
                        "role": "user", 
                        "content": f"Please provide a comprehensive analysis of this resume:\n\n{resume_text}"
                    }
                ],
                max_tokens=2000,
                temperature=0.7
            )
            return response.choices[0].message.content
    except Exception as e:
        return f"Error analyzing resume: {str(e)}"

@app.route('/')
def index():
    """Main page with upload form and chat interface"""
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AIML_Project - AI Resume Reviewer</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .main-container {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .header {
                text-align: center;
                margin-bottom: 40px;
                color: white;
            }
            
            .header h1 {
                font-size: 3rem;
                font-weight: 700;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            
            .header .subtitle {
                font-size: 1.2rem;
                opacity: 0.9;
                font-weight: 300;
            }
            
            .container {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                margin-bottom: 30px;
                border: 1px solid rgba(255,255,255,0.2);
            }
            
            .upload-section {
                border: 3px dashed #667eea;
                padding: 40px;
                text-align: center;
                border-radius: 15px;
                margin-bottom: 30px;
                background: linear-gradient(45deg, #f8f9ff, #ffffff);
                transition: all 0.3s ease;
            }
            
            .upload-section:hover {
                border-color: #764ba2;
                transform: translateY(-2px);
                box-shadow: 0 10px 25px rgba(102, 126, 234, 0.15);
            }
            
            .upload-section h3 {
                color: #333;
                margin-bottom: 15px;
                font-size: 1.5rem;
                font-weight: 600;
            }
            
            .upload-section p {
                color: #666;
                margin-bottom: 25px;
                font-size: 1rem;
            }
            
            .file-input {
                margin: 20px 0;
            }
            
            .file-input input[type="file"] {
                padding: 12px;
                border: 2px solid #e1e5e9;
                border-radius: 10px;
                background: white;
                font-size: 16px;
                width: 100%;
                max-width: 400px;
                transition: border-color 0.3s ease;
            }
            
            .file-input input[type="file"]:focus {
                outline: none;
                border-color: #667eea;
            }
            
            .btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                margin: 10px;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
            }
            
            .btn:active {
                transform: translateY(0);
            }
            
            .analysis-result {
                background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
                padding: 30px;
                border-radius: 15px;
                margin: 30px 0;
                border-left: 5px solid #667eea;
                display: none;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }
            
            .analysis-result h3 {
                color: #333;
                margin-bottom: 20px;
                font-size: 1.5rem;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .chat-container {
                margin-top: 40px;
                display: none;
            }
            
            .chat-container h3 {
                color: #333;
                margin-bottom: 20px;
                font-size: 1.5rem;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .chat-history {
                height: 300px;
                overflow-y: auto;
                border: 2px solid #e1e5e9;
                padding: 15px;
                background: linear-gradient(135deg, #fafbff 0%, #ffffff 100%);
                border-radius: 12px;
                margin-bottom: 15px;
                box-shadow: inset 0 2px 10px rgba(0,0,0,0.05);
                font-size: 14px;
            }
            
            .chat-history::-webkit-scrollbar {
                width: 8px;
            }
            
            .chat-history::-webkit-scrollbar-track {
                background: #f1f1f1;
                border-radius: 10px;
            }
            
            .chat-history::-webkit-scrollbar-thumb {
                background: #667eea;
                border-radius: 10px;
            }
            
            .message {
                margin: 10px 0;
                padding: 10px 15px;
                border-radius: 12px;
                max-width: 85%;
                word-wrap: break-word;
                animation: fadeIn 0.3s ease;
                font-size: 14px;
                line-height: 1.4;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .user-message {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin-left: auto;
                text-align: right;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            
            .ai-message {
                background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
                color: #333;
                margin-right: auto;
                border: 1px solid #e1e5e9;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
            
            .chat-input-container {
                display: flex;
                gap: 10px;
                align-items: center;
            }
            
            .chat-input {
                flex: 1;
                padding: 10px 15px;
                border: 2px solid #e1e5e9;
                border-radius: 20px;
                font-size: 14px;
                background: white;
                transition: all 0.3s ease;
            }
            
            .chat-input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .chat-send-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 10px;
                border: none;
                border-radius: 50%;
                cursor: pointer;
                font-size: 14px;
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            
            .chat-send-btn:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            }
            
            .loading {
                display: none;
                text-align: center;
                color: #667eea;
                font-style: italic;
                font-size: 1.1rem;
                padding: 20px;
                background: rgba(102, 126, 234, 0.1);
                border-radius: 10px;
                margin: 20px 0;
            }
            
            .loading::before {
                content: "⏳ ";
                animation: spin 2s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .feature-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            
            .feature-card {
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 15px;
                text-align: center;
                color: white;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
            }
            
            .feature-card i {
                font-size: 2rem;
                margin-bottom: 10px;
                color: #fff;
            }
            
            .optional-features {
                background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
                padding: 25px;
                border-radius: 15px;
                margin: 25px 0;
                border-left: 5px solid #28a745;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }
            
            .optional-features h3 {
                color: #333;
                margin-bottom: 20px;
                font-size: 1.4rem;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .feature-buttons {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .feature-btn {
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                color: white;
                padding: 15px 20px;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }
            
            .feature-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(40, 167, 69, 0.4);
            }
            
            .feature-btn:disabled {
                background: #6c757d;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            
            .feature-result {
                background: rgba(255, 255, 255, 0.8);
                padding: 20px;
                border-radius: 10px;
                margin: 15px 0;
                border-left: 4px solid #28a745;
            }
            
            .feature-result h4 {
                color: #28a745;
                margin-bottom: 15px;
                font-size: 1.2rem;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .modal {
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.5);
                backdrop-filter: blur(5px);
            }
            
            .modal-content {
                background-color: white;
                margin: 15% auto;
                padding: 30px;
                border-radius: 15px;
                width: 90%;
                max-width: 500px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.2);
                position: relative;
            }
            
            .modal-content h3 {
                color: #333;
                margin-bottom: 20px;
                font-size: 1.4rem;
            }
            
            .modal-input {
                width: 100%;
                padding: 12px 15px;
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                font-size: 14px;
                margin-bottom: 20px;
                transition: border-color 0.3s ease;
            }
            
            .modal-input:focus {
                outline: none;
                border-color: #667eea;
            }
            
            .close {
                color: #aaa;
                float: right;
                font-size: 28px;
                font-weight: bold;
                position: absolute;
                right: 15px;
                top: 10px;
                cursor: pointer;
            }
            
            .close:hover {
                color: #333;
            }
            
            @media (max-width: 768px) {
                .header h1 {
                    font-size: 2rem;
                }
                
                .container {
                    padding: 20px;
                    margin: 10px;
                }
                
                .message {
                    max-width: 95%;
                }
                
                .chat-input-container {
                    flex-direction: column;
                    gap: 10px;
                }
                
                .chat-input {
                    border-radius: 10px;
                }
                
                .feature-buttons {
                    grid-template-columns: 1fr;
                }
                
                .modal-content {
                    margin: 10% auto;
                    width: 95%;
                }
            }
        </style>
    </head>
    <body>
        <div class="main-container">
            <div class="header">
                <h1><i class="fas fa-robot"></i> AIML_Project</h1>
                <p class="subtitle">AI-Powered Resume Analysis & Coaching Platform</p>
            </div>
            
            <div class="feature-grid">
                <div class="feature-card">
                    <i class="fas fa-file-alt"></i>
                    <h4>Smart Analysis</h4>
                    <p>AI-powered resume evaluation</p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-comments"></i>
                    <h4>Interactive Chat</h4>
                    <p>Personalized coaching sessions</p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-chart-line"></i>
                    <h4>Instant Feedback</h4>
                    <p>Real-time improvement suggestions</p>
                </div>
            </div>
            
            <div class="container">
            
            <div class="upload-section">
                <h3>Upload Your Resume</h3>
                <p>Supported formats: PDF, DOCX, TXT</p>
                <form id="uploadForm" enctype="multipart/form-data">
                    <div class="file-input">
                        <input type="file" id="resumeFile" name="file" accept=".pdf,.docx,.txt" required>
                    </div>
                    <button type="submit" class="btn">Analyze Resume</button>
                </form>
            </div>

            <div class="loading" id="loading">
                Analyzing your resume... Please wait.
            </div>

            <div class="analysis-result" id="analysisResult">
                <h3><i class="fas fa-chart-bar"></i> Comprehensive Resume Analysis</h3>
                <div id="analysisContent"></div>
            </div>

            <!-- Optional Features Section -->
            <div class="optional-features" id="optionalFeatures" style="display: none;">
                <h3><i class="fas fa-plus-circle"></i> Optional Features</h3>
                <div class="feature-buttons">
                    <button onclick="getJobSuggestions()" class="feature-btn" id="jobSuggestionsBtn">
                        <i class="fas fa-briefcase"></i> Job Role Suggestions
                    </button>
                    <button onclick="showCoverLetterModal()" class="feature-btn" id="coverLetterBtn">
                        <i class="fas fa-file-alt"></i> Cover Letter Generator
                    </button>
                    <button onclick="showInterviewQuestionsModal()" class="feature-btn" id="interviewBtn">
                        <i class="fas fa-question-circle"></i> Interview Questions
                    </button>
                </div>
                
                <!-- Results containers for optional features -->
                <div id="jobSuggestionsResult" class="feature-result" style="display: none;">
                    <h4><i class="fas fa-briefcase"></i> Recommended Job Roles</h4>
                    <div id="jobSuggestionsContent"></div>
                </div>
                
                <div id="coverLetterResult" class="feature-result" style="display: none;">
                    <h4><i class="fas fa-file-alt"></i> Generated Cover Letter</h4>
                    <div id="coverLetterContent"></div>
                </div>
                
                <div id="interviewQuestionsResult" class="feature-result" style="display: none;">
                    <h4><i class="fas fa-question-circle"></i> Interview Questions</h4>
                    <div id="interviewQuestionsContent"></div>
                </div>
            </div>

            <div class="chat-container" id="chatContainer">
                <h3><i class="fas fa-comments"></i> Interactive AI Coaching Chat</h3>
                <div class="chat-history" id="chatHistory"></div>
                <div class="chat-input-container">
                    <input type="text" id="chatInput" class="chat-input" placeholder="Ask questions about your resume..." maxlength="500">
                    <button onclick="sendMessage()" class="chat-send-btn"><i class="fas fa-paper-plane"></i></button>
                </div>
            </div>
            </div>
        </div>

        <!-- Modal for Cover Letter -->
        <div id="coverLetterModal" class="modal" style="display: none;">
            <div class="modal-content">
                <span class="close" onclick="closeCoverLetterModal()">&times;</span>
                <h3>Generate Cover Letter</h3>
                <input type="text" id="jobRoleInput" placeholder="Enter job role (e.g., Software Engineer)" class="modal-input">
                <button onclick="generateCoverLetter()" class="btn">Generate Cover Letter</button>
            </div>
        </div>

        <!-- Modal for Interview Questions -->
        <div id="interviewModal" class="modal" style="display: none;">
            <div class="modal-content">
                <span class="close" onclick="closeInterviewModal()">&times;</span>
                <h3>Generate Interview Questions</h3>
                <input type="text" id="interviewJobRoleInput" placeholder="Enter job role (e.g., Data Analyst)" class="modal-input">
                <button onclick="generateInterviewQuestions()" class="btn">Generate Questions</button>
            </div>
        </div>

        <script>
            let sessionId = null;
            let resumeText = '';
            let chatHistory = [];

            // Handle resume upload and analysis
            document.getElementById('uploadForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const fileInput = document.getElementById('resumeFile');
                const file = fileInput.files[0];
                
                if (!file) {
                    alert('Please select a file');
                    return;
                }

                const formData = new FormData();
                formData.append('file', file);

                // Show loading
                document.getElementById('loading').style.display = 'block';
                document.getElementById('analysisResult').style.display = 'none';
                document.getElementById('chatContainer').style.display = 'none';

                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();
                    
                    if (result.success) {
                        sessionId = result.session_id;
                        resumeText = result.resume_text;
                        
                        // Display analysis results with better formatting
                        document.getElementById('analysisContent').innerHTML = formatAnalysisText(result.analysis);
                        document.getElementById('analysisResult').style.display = 'block';
                        document.getElementById('chatContainer').style.display = 'block';
                        document.getElementById('optionalFeatures').style.display = 'block';
                        
                        // Clear previous chat and optional features
                        chatHistory = [];
                        document.getElementById('chatHistory').innerHTML = '';
                        hideAllFeatureResults();
                    } else {
                        alert('Error: ' + result.error);
                    }
                } catch (error) {
                    alert('Upload failed: ' + error.message);
                } finally {
                    document.getElementById('loading').style.display = 'none';
                }
            });

            // Handle chat input
            document.getElementById('chatInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });

            async function sendMessage() {
                const chatInput = document.getElementById('chatInput');
                const userMessage = chatInput.value.trim();
                
                if (!userMessage || !sessionId) {
                    return;
                }

                // Add user message to chat history
                chatHistory.push({type: 'user', message: userMessage});
                displayMessage(userMessage, 'user');
                
                // Clear input
                chatInput.value = '';

                // Show typing indicator
                const typingDiv = document.createElement('div');
                typingDiv.className = 'message ai-message';
                typingDiv.innerHTML = '<em>AI is typing...</em>';
                typingDiv.id = 'typing-indicator';
                document.getElementById('chatHistory').appendChild(typingDiv);
                scrollToBottom();

                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            session_id: sessionId,
                            resume_text: resumeText,
                            chat_history: chatHistory,
                            user_message: userMessage
                        })
                    });

                    const result = await response.json();
                    
                    // Remove typing indicator
                    document.getElementById('typing-indicator').remove();
                    
                    if (result.success) {
                        chatHistory = result.updated_chat_history;
                        displayMessage(result.ai_reply, 'ai');
                    } else {
                        displayMessage('Sorry, there was an error processing your message.', 'ai');
                    }
                } catch (error) {
                    document.getElementById('typing-indicator').remove();
                    displayMessage('Sorry, there was a connection error.', 'ai');
                }
            }

            function displayMessage(message, type) {
                const chatHistory = document.getElementById('chatHistory');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}-message`;
                messageDiv.innerHTML = formatChatText(message);
                chatHistory.appendChild(messageDiv);
                scrollToBottom();
            }

            function formatAnalysisText(text) {
                // Convert markdown-style formatting to clean HTML
                let formatted = text;
                
                // Headers - convert ### Title to bold headers
                formatted = formatted.replace(/### (.*?)\\n/g, '<h3 style="color: #667eea; font-weight: bold; margin: 20px 0 10px 0; font-size: 18px;">$1</h3>');
                formatted = formatted.replace(/## (.*?)\\n/g, '<h2 style="color: #667eea; font-weight: bold; margin: 25px 0 15px 0; font-size: 20px;">$1</h2>');
                formatted = formatted.replace(/# (.*?)\\n/g, '<h1 style="color: #667eea; font-weight: bold; margin: 30px 0 20px 0; font-size: 22px;">$1</h1>');
                
                // Bold text - convert **text** to <strong>
                formatted = formatted.split('**').map((part, index) => {
                    return index % 2 === 1 ? '<strong style="color: #333; font-weight: 600;">' + part + '</strong>' : part;
                }).join('');
                
                // Line breaks
                formatted = formatted.replace(/\\n\\n/g, '<br><br>');
                formatted = formatted.replace(/\\n/g, '<br>');
                
                // Bullet points
                formatted = formatted.replace(/- /g, '• ');
                
                return '<div style="line-height: 1.8; font-size: 15px; color: #333; padding: 10px;">' + formatted + '</div>';
            }

            function formatChatText(text) {
                // Convert markdown-style formatting to clean HTML for chat
                let formatted = text;
                
                // Bold text - convert **text** to <strong>
                formatted = formatted.split('**').map((part, index) => {
                    return index % 2 === 1 ? '<strong style="color: #333;">' + part + '</strong>' : part;
                }).join('');
                
                // Line breaks
                formatted = formatted.replace(/\\n/g, '<br>');
                
                // Bullet points
                formatted = formatted.replace(/- /g, '• ');
                
                return '<div style="line-height: 1.6; font-size: 14px;">' + formatted + '</div>';
            }

            function scrollToBottom() {
                const chatHistory = document.getElementById('chatHistory');
                chatHistory.scrollTop = chatHistory.scrollHeight;
            }

            // Optional Features Functions
            function hideAllFeatureResults() {
                document.getElementById('jobSuggestionsResult').style.display = 'none';
                document.getElementById('coverLetterResult').style.display = 'none';
                document.getElementById('interviewQuestionsResult').style.display = 'none';
            }

            async function getJobSuggestions() {
                if (!sessionId) return;
                
                const btn = document.getElementById('jobSuggestionsBtn');
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
                
                try {
                    const response = await fetch('/job-suggestions', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            session_id: sessionId
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        document.getElementById('jobSuggestionsContent').innerHTML = formatAnalysisText(result.suggestions);
                        document.getElementById('jobSuggestionsResult').style.display = 'block';
                    } else {
                        alert('Error: ' + result.error);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-briefcase"></i> Job Role Suggestions';
                }
            }

            function showCoverLetterModal() {
                document.getElementById('coverLetterModal').style.display = 'block';
            }

            function closeCoverLetterModal() {
                document.getElementById('coverLetterModal').style.display = 'none';
                document.getElementById('jobRoleInput').value = '';
            }

            async function generateCoverLetter() {
                const jobRole = document.getElementById('jobRoleInput').value.trim();
                if (!jobRole || !sessionId) {
                    alert('Please enter a job role');
                    return;
                }
                
                try {
                    const response = await fetch('/cover-letter', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            session_id: sessionId,
                            job_role: jobRole
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        document.getElementById('coverLetterContent').innerHTML = formatAnalysisText(result.cover_letter);
                        document.getElementById('coverLetterResult').style.display = 'block';
                        closeCoverLetterModal();
                    } else {
                        alert('Error: ' + result.error);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }

            function showInterviewQuestionsModal() {
                document.getElementById('interviewModal').style.display = 'block';
            }

            function closeInterviewModal() {
                document.getElementById('interviewModal').style.display = 'none';
                document.getElementById('interviewJobRoleInput').value = '';
            }

            async function generateInterviewQuestions() {
                const jobRole = document.getElementById('interviewJobRoleInput').value.trim();
                if (!jobRole || !sessionId) {
                    alert('Please enter a job role');
                    return;
                }
                
                try {
                    const response = await fetch('/interview-questions', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            session_id: sessionId,
                            job_role: jobRole
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        document.getElementById('interviewQuestionsContent').innerHTML = formatAnalysisText(result.questions);
                        document.getElementById('interviewQuestionsResult').style.display = 'block';
                        closeInterviewModal();
                    } else {
                        alert('Error: ' + result.error);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }

            // Close modals when clicking outside
            window.onclick = function(event) {
                const coverLetterModal = document.getElementById('coverLetterModal');
                const interviewModal = document.getElementById('interviewModal');
                
                if (event.target == coverLetterModal) {
                    closeCoverLetterModal();
                }
                if (event.target == interviewModal) {
                    closeInterviewModal();
                }
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)

@app.route('/upload', methods=['POST'])
def upload_resume():
    """Handle resume upload and analysis"""
    try:
        print("Upload route called")  # Debug
        
        # Check if file was uploaded
        if 'file' not in request.files:
            print("No file in request")  # Debug
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        file = request.files['file']
        print(f"File received: {file.filename}")  # Debug
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed'})
        
        # Extract text from file
        print("Extracting text from file...")  # Debug
        resume_text = extract_text_from_file(file)
        print(f"Extracted text length: {len(resume_text) if resume_text else 0}")  # Debug
        
        if not resume_text or resume_text.startswith('Error'):
            print(f"Text extraction error: {resume_text}")  # Debug
            return jsonify({'success': False, 'error': resume_text})
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        print(f"Generated session ID: {session_id}")  # Debug
        
        # Analyze resume with AI
        print("Starting AI analysis...")  # Debug
        analysis = analyze_resume_with_ai(resume_text)
        print(f"AI analysis completed. Length: {len(analysis) if analysis else 0}")  # Debug
        
        if analysis.startswith('Error'):
            print(f"AI analysis error: {analysis}")  # Debug
            return jsonify({'success': False, 'error': analysis})
        
        # Store session data
        session_data[session_id] = {
            'resume_text': resume_text,
            'analysis': analysis,
            'chat_history': []
        }
        
        print("Returning success response")  # Debug
        return jsonify({
            'success': True,
            'session_id': session_id,
            'resume_text': resume_text[:500] + '...' if len(resume_text) > 500 else resume_text,  # Truncate for response
            'analysis': analysis
        })
        
    except Exception as e:
        print(f"Upload route exception: {str(e)}")  # Debug
        return jsonify({'success': False, 'error': str(e)})

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages with AI resume coach"""
    try:
        data = request.json
        session_id = data.get('session_id')
        resume_text = data.get('resume_text', '')
        chat_history = data.get('chat_history', [])
        user_message = data.get('user_message', '')
        
        if not session_id or not user_message:
            return jsonify({'success': False, 'error': 'Missing required data'})
        
        # Check if session exists
        if session_id not in session_data:
            return jsonify({'success': False, 'error': 'Session not found'})
        
        # Prepare messages for OpenAI
        messages = [
            {
                "role": "system",
                "content": "You are a professional resume coach. Give concise, actionable advice tailored to the provided resume. Always reference the resume content and suggest improvements with examples."
            },
            {
                "role": "user",
                "content": f"Here is the resume I'm working on:\n\n{resume_text}\n\nPlease keep this context in mind for our conversation."
            }
        ]
        
        # Add chat history to messages
        for chat_msg in chat_history:
            if chat_msg['type'] == 'user':
                messages.append({"role": "user", "content": chat_msg['message']})
            elif chat_msg['type'] == 'ai':
                messages.append({"role": "assistant", "content": chat_msg['message']})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Get AI response
        if client:
            # Use new client
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=800,
                temperature=0.7
            )
        else:
            # Fallback to older API
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=800,
                temperature=0.7
            )
        
        ai_reply = response.choices[0].message.content
        
        # Update chat history
        updated_chat_history = chat_history + [
            {'type': 'user', 'message': user_message},
            {'type': 'ai', 'message': ai_reply}
        ]
        
        # Update session data
        session_data[session_id]['chat_history'] = updated_chat_history
        
        return jsonify({
            'success': True,
            'ai_reply': ai_reply,
            'updated_chat_history': updated_chat_history
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/job-suggestions', methods=['POST'])
def get_job_suggestions():
    """Generate job role suggestions based on resume"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if not session_id or session_id not in session_data:
            return jsonify({'success': False, 'error': 'Session not found'})
        
        resume_text = session_data[session_id]['resume_text']
        
        prompt = """Based on this resume, suggest 3-5 specific job titles that would be most suitable for this candidate. Consider their skills, experience, and background. Format as a numbered list with brief explanations for each suggestion."""
        
        if client:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Resume content:\n\n{resume_text}"}
                ],
                max_tokens=800,
                temperature=0.7
            )
            suggestions = response.choices[0].message.content
        else:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Resume content:\n\n{resume_text}"}
                ],
                max_tokens=800,
                temperature=0.7
            )
            suggestions = response.choices[0].message.content
        
        return jsonify({'success': True, 'suggestions': suggestions})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/cover-letter', methods=['POST'])
def generate_cover_letter():
    """Generate personalized cover letter"""
    try:
        data = request.json
        session_id = data.get('session_id')
        job_role = data.get('job_role', '')
        
        if not session_id or session_id not in session_data:
            return jsonify({'success': False, 'error': 'Session not found'})
        
        resume_text = session_data[session_id]['resume_text']
        
        prompt = f"""Create a professional cover letter for the job role: "{job_role}". Base it on the provided resume content. The cover letter should:
- Be personalized and specific to the role
- Highlight relevant experience and skills
- Be professional yet engaging
- Include proper structure (greeting, body paragraphs, closing)
- Be approximately 250-300 words"""
        
        if client:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Resume content:\n\n{resume_text}"}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            cover_letter = response.choices[0].message.content
        else:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Resume content:\n\n{resume_text}"}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            cover_letter = response.choices[0].message.content
        
        return jsonify({'success': True, 'cover_letter': cover_letter})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/interview-questions', methods=['POST'])
def generate_interview_questions():
    """Generate interview questions based on resume and job role"""
    try:
        data = request.json
        session_id = data.get('session_id')
        job_role = data.get('job_role', '')
        
        if not session_id or session_id not in session_data:
            return jsonify({'success': False, 'error': 'Session not found'})
        
        resume_text = session_data[session_id]['resume_text']
        
        prompt = f"""Generate 8-12 potential interview questions for the job role: "{job_role}" based on this resume. Include:
- 3-4 general questions about experience and background
- 3-4 technical/skill-based questions relevant to the role
- 2-3 behavioral questions
- 1-2 questions about specific projects or achievements mentioned in the resume

Format as a numbered list with clear, realistic interview questions."""
        
        if client:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Resume content:\n\n{resume_text}"}
                ],
                max_tokens=1200,
                temperature=0.7
            )
            questions = response.choices[0].message.content
        else:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Resume content:\n\n{resume_text}"}
                ],
                max_tokens=1200,
                temperature=0.7
            )
            questions = response.choices[0].message.content
        
        return jsonify({'success': True, 'questions': questions})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
