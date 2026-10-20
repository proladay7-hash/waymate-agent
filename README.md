# BigBikeBlitz AI Agent

A Python-based AI agent that integrates with your BigBikeBlitz motorcycle e-commerce website to provide real-time chat support using Mistral 7B via Ollama.

## 🚀 Features

- **Real-time AI Chat**: WebSocket-based chat interface with Mistral 7B
- **Website Knowledge Base**: Automatically scrapes and indexes your website content
- **Product Information**: Access to motorcycle details, pricing, and specifications
- **Conversation History**: Persistent chat sessions and analytics
- **Multi-language Support**: Built-in internationalization
- **Analytics Dashboard**: Track user interactions and popular queries

## 📋 Prerequisites

1. **Python 3.8+**
2. **Ollama** installed and running locally
3. **Mistral 7B model** downloaded in Ollama
4. **BigBikeBlitz website** running (frontend + backend)

## 🛠️ Installation

### 1. Install Ollama

```bash
# Download and install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve
```

### 2. Download Mistral 7B Model

```bash
# Pull the Mistral 7B model
ollama pull mistral:7b

# Verify installation
ollama list
```

### 3. Setup Python Environment

```bash
# Navigate to AI agent directory
cd ai_agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the `ai_agent` directory:

```env
# Application settings
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Ollama settings
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral:7b

# Website settings
WEBSITE_BASE_URL=http://localhost:5173
BACKEND_API_URL=http://localhost:8080

# Database settings
DATABASE_PATH=./ai_agent.db

# Knowledge base settings
KNOWLEDGE_BASE_PATH=./knowledge_base
```

## 🚀 Running the AI Agent

### 1. Start the AI Agent

```bash
# From the ai_agent directory
python main.py
```

The AI agent will start on `http://localhost:8000`

### 2. Initial Website Scraping

On first run, the AI agent will automatically scrape your website to build the knowledge base. You can also trigger manual scraping:

```bash
curl -X POST http://localhost:8000/api/scrape-website
```

### 3. Test the AI Agent

```bash
# Health check
curl http://localhost:8000/api/health

# Test chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about BigBikeBlitz",
    "user_id": "test_user",
    "session_id": "test_session"
  }'
```

## 🔧 Frontend Integration

### 1. Update LiveChat Component

Replace your existing `LiveChat.tsx` with the new `AIChat.tsx` component that connects to the AI agent.

### 2. Update App.tsx

```typescript
// Import the new AI chat component
import AIChat from './components/AIChat';

// Replace LiveChat with AIChat in your App component
<AIChat 
  isOpen={showLiveChat}
  onClose={() => setShowLiveChat(false)}
/>
```

## 📊 API Endpoints

### WebSocket Chat
- **URL**: `ws://localhost:8000/ws/chat/{session_id}`
- **Purpose**: Real-time chat interface

### REST API
- **POST** `/api/chat` - Send chat message
- **POST** `/api/scrape-website` - Trigger website scraping
- **GET** `/api/knowledge-base/stats` - Get knowledge base statistics
- **GET** `/api/health` - Health check

## 🗄️ Database Schema

### Conversations Table
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT,
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    sources TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Analytics Table
```sql
CREATE TABLE analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    session_id TEXT,
    user_id TEXT,
    data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔍 Knowledge Base

The AI agent uses ChromaDB to store and search website content:

- **Automatic Scraping**: Scrapes your website on startup
- **Product Information**: Indexes motorcycle details and specifications
- **Semantic Search**: Finds relevant information for user queries
- **Source Attribution**: Provides sources for AI responses

## 📈 Analytics

Track user interactions and AI performance:

- **Conversation Logs**: All chat interactions
- **Popular Queries**: Most asked questions
- **User Sessions**: Session duration and engagement
- **AI Performance**: Response quality and accuracy

## 🛡️ Security

- **CORS Configuration**: Restricted to your domain
- **Session Management**: Secure session handling
- **Input Validation**: Sanitized user inputs
- **Rate Limiting**: Built-in request throttling

## 🔧 Configuration

### Ollama Settings
```python
# config.py
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "mistral:7b"
OLLAMA_TIMEOUT = 30
```

### Knowledge Base Settings
```python
KNOWLEDGE_BASE_PATH = "./knowledge_base"
MAX_SEARCH_RESULTS = 5
```

### Chat Settings
```python
MAX_CONVERSATION_HISTORY = 20
SESSION_TIMEOUT_HOURS = 24
```

## 🚀 Deployment

### Development
```bash
python main.py
```

### Production
```bash
# Using uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Using gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker (Optional)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

## 🐛 Troubleshooting

### Common Issues

1. **Ollama Connection Error**
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   
   # Start Ollama if not running
   ollama serve
   ```

2. **Model Not Found**
   ```bash
   # List available models
   ollama list
   
   # Pull Mistral 7B if not available
   ollama pull mistral:7b
   ```

3. **WebSocket Connection Issues**
   - Check if the AI agent is running on port 8000
   - Verify CORS settings
   - Check browser console for errors

4. **Knowledge Base Issues**
   ```bash
   # Check knowledge base stats
   curl http://localhost:8000/api/knowledge-base/stats
   
   # Re-scrape website
   curl -X POST http://localhost:8000/api/scrape-website
   ```

## 📝 Logs

The AI agent logs to console by default. For production, configure logging:

```python
# config.py
LOG_LEVEL = "INFO"
LOG_FILE = "./ai_agent.log"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the troubleshooting section
- Review the logs for error messages
- Open an issue on GitHub

---

**BigBikeBlitz AI Agent** - Powered by Llama 3.2 1B and Ollama 