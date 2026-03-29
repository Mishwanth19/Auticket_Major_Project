# IT Service Approval System - Chat Interface

A conversational AI-powered interface for requesting tool access through natural language.

## � Project Structure

```
Auticket/
├── orchestrator.py          # FastAPI backend server
├── granter_agent.py         # AI-powered policy evaluation
├── requester_agent.py       # Request processing agent
├── policies.py              # Company policies and access rules
├── streamlit_chat.py        # Chat-based Streamlit interface
├── run_chat.py              # Easy startup script
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (API keys)
└── README_CHAT.md          # This documentation
```

## �🚀 Quick Start

### 1. Start the Backend API
```bash
# Activate virtual environment
venv\Scripts\activate

# Start the FastAPI backend
python orchestrator.py
```

### 2. Start the Chat Interface
```bash
# Option 1: Using the run script
python run_chat.py

# Option 2: Direct Streamlit command
streamlit run streamlit_chat.py
```

### 3. Access the Application
- **Chat Interface**: http://localhost:8501
- **Backend API**: http://localhost:8000

## 💬 How to Use the Chat Interface

### Starting a Conversation
1. Open the chat interface in your browser
2. The assistant will greet you and ask for your email
3. Provide your work email (e.g., `john.doe@company.com`)
4. Start requesting tools in natural language

### Example Requests
Try these natural language requests:

```
I need Docker and PostgreSQL for my web development project
```

```
Can I get access to AWS CLI and Kubernetes? It's for our cloud migration
```

```
I need TensorFlow 2.8 for machine learning model training
```

```
I need Git, VS Code, and Python for my development work
```

```
Can you help me get access to Tableau for data analysis?
```

### What the Chat Interface Does

1. **Natural Language Parsing**: Extracts tool names, versions, and justifications from your message
2. **AI Evaluation**: Submits requests to the AI-powered approval system
3. **Instant Results**: Shows approval/rejection decisions with reasoning
4. **Download Approval**: Provides download button for approved tools
5. **Conversation History**: Maintains chat context throughout the session

## 🔧 Supported Tools

The system recognizes these common tools:

### Development Tools
- **Version Control**: Git
- **IDEs**: VS Code
- **Languages**: Python, Node.js, Java
- **Containers**: Docker, Kubernetes
- **CI/CD**: Jenkins

### Database Tools
- **SQL**: PostgreSQL, MySQL
- **NoSQL**: MongoDB
- **Clients**: Database access tools

### Cloud & Infrastructure
- **Cloud**: AWS CLI
- **Infrastructure**: Terraform

### Data Science
- **ML Frameworks**: TensorFlow, PyTorch
- **Notebooks**: Jupyter
- **Libraries**: NumPy, Pandas
- **Analytics**: Tableau, Excel

## 📥 Download Feature

When tools are approved:
- A **Download Approval Letter** button appears
- Click to download a text file with:
  - Request ID and timestamp
  - List of approved tools
  - Policy references
  - Approval validity period

## 🏗️ Architecture

### Chat Interface Features
- **Natural Language Processing**: Parses user messages to extract structured requests
- **Conversational Flow**: Maintains context and guides users through the process
- **Real-time Feedback**: Shows AI evaluation results immediately
- **Download Functionality**: Generates approval letters for approved requests

### Backend Integration
- **API Integration**: Communicates with FastAPI backend
- **Structured Output**: Uses existing granter agent with JSON output format
- **Error Handling**: Provides clear error messages and guidance

## 🔄 Comparison: Form vs Chat

| Feature | Form Interface | Chat Interface |
|---------|---------------|----------------|
| **Input Method** | Structured forms | Natural language |
| **User Experience** | Step-by-step fields | Conversational |
| **Tool Selection** | Dropdown/text fields | Automatic parsing |
| **Justification** | Text area | Extracted from message |
| **Speed** | Multiple clicks | Single message |
| **Accessibility** | Form navigation | Natural conversation |

## 🛠️ Technical Details

### Natural Language Processing
The chat interface uses regex patterns to identify:
- Tool names from predefined dictionary
- Version numbers (e.g., "TensorFlow 2.8")
- Justification context

### Data Flow
1. User sends message
2. Chat interface parses and extracts tool requests
3. Structured request sent to `/submit-request` API
4. AI evaluates and returns decisions
5. Results displayed in chat format
6. Download button shown for approved tools

### System Prompt
The granter agent uses this structured output format:
```json
{
  "decisions": [
    {
      "tool_name": "Docker",
      "decision": "APPROVED",
      "risk_level": "low",
      "policy_reference": "POL-DEV-004 §2.1",
      "reason": "Standard development tool, approved for role",
      "resolution_steps": ""
    }
  ]
}
```

## 📝 Example Conversation

```
Assistant: 👋 Hello! I'm your IT Service Approval Assistant...
User: john.doe@company.com
Assistant: Thanks! I've noted your email as john.doe@company.com...
User: I need Docker and PostgreSQL for my web development project
Assistant: I've identified the following tools in your request:
• Docker
• PostgreSQL

I'll now submit this request for AI evaluation...
[Shows approval results with download button]
```

## 🚨 Troubleshooting

### Common Issues

**"API server is not running"**
- Start the backend: `python orchestrator.py`
- Check port 8000 is available

**"Couldn't identify any specific tools"**
- Be specific about tool names
- Use common tool names from the supported list
- Include justification in your message

**Download button not appearing**
- Only shown for approved tools
- Check if any tools in your request were approved

### Getting Help

1. Check the sidebar for system status
2. Review example requests above
3. Use the "Track Request" page to monitor requests
4. Check "System Info" for technical details

## 🎯 Next Steps

The chat interface provides a more natural way to interact with the IT approval system. Users can simply type what they need, and the AI handles the rest - from parsing to evaluation to approval letter generation.

For production deployment, consider:
- Adding more sophisticated NLP for tool recognition
- Implementing user authentication
- Adding voice input capabilities
- Expanding the supported tool dictionary
