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
Run GPT Wrapper
```bash
python3 gpt_wrapper.py 
```
Run CPT Agent Claude + OpenAI Web serach
```bash
python3 agentic_cpt_system.py 
```

### 5. Test score against answer key 
#### Edit line 7 of test_taker.py to specify file name for output test answers. It will be agent_responses.txt OR gpt-4.1_wrapper_responses.txt (Whichever file was tested) 

```bash
python3 test_taker.py 
```
