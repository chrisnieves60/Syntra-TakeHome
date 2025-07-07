1. Create a Virtual Environment

python3 -m venv venv
source venv/bin/activate

# (On Windows: venv\Scripts\activate)

2. Install Required Packages

pip3 install python-dotenv openai pandas langchain langchain-openai langchain-anthropic langchain-core

3. Set Up Environment Variables in .env

OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

4. Run the Programs

python3 main.py (this is for the chatgpt4 wrapper)

python3 agentic_cpt_system.py (this is for the agentic system)
