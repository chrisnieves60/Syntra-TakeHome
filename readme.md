## Setup Instructions

### 1. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

### 2. Install Required Packages
```bash
pip3 install python-dotenv openai pandas langchain langchain-openai langchain-anthropic langchain-core
```

### 3. Set Up Environment Variables in .env
```env
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

### 4. Run the Programs
```bash
python3 main.py (this is for the chatgpt4.1 wrapper)
```

```bash
python3 agentic_cpt_system.py (this is for the agentic system that uses Clade + OpenAI web search)
```
