import os
from dotenv import load_dotenv 
import pandas as pd
from typing import Dict, List, Optional
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate
from langchain.schema import AgentAction, AgentFinish
import re
import time
from hcpcs_lookup import HCPCSLookup 
from openai import OpenAI

load_dotenv() 
client = OpenAI() #side load OpenAI Client for web search 

class AgenticCPTSystem:
    def __init__(self, lookup, anthropic_api_key):
        self.lookup = lookup  
        
        self.llm = ChatAnthropic (
            model="claude-sonnet-4-20250514",  
            temperature=0,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def enrich_llm_codes_with_descriptions(self, extracted_codes_text, lookup):

        lines = extracted_codes_text.strip().split('\n')
        enriched = []
        for line in lines:
            code = line.strip()
            #if we find a code, 
            if re.match(r'^([A-Z]\d{4}|\d{5})$', code): # match 5 digits (CPT) or 1 letter + 4 digits (HCPCS)
                desc = lookup.lookup(code)
                enriched.append(f"{code} - {desc}")

        return "\n".join(enriched)
        
    def web_search_missing_code_descriptions(self, codes): 
        
        response = client.responses.create(
            model="gpt-4.1",
            tools=[{"type": "web_search_preview"}],
            input=f"""I have these medical codes with descriptions from a local lookup table:
        {codes}
        Some descriptions may be incomplete, generic, missing, or unclear. Please:
        1. Review each code-description pair
        2. For any codes that need better/more detailed descriptions, search for the official medical descriptions. 
        3. If all of the codes are too similar, find detailed descriptions for each code 
        4. Return ALL codes in the exact same format, but with improved descriptions where needed
        5. If codes are deleted, or dont exist, just return description as DOES NOT EXIST 

        Return format:
        [CODE] - [DESCRIPTION]

        Example: 

        23454 - excision of a cyst 

        ONLY RETURN THE CODES IN THAT FORMAT. 
        
        Keep good descriptions as-is, only improve the ones that need it.
        """
            )
    
        return response.output_text

    def _create_tools(self) -> List[Tool]:
        #create tools for the agent
        
        def lookup_codes_local(codes_text: str) -> str:
            try:
                return self.enrich_llm_codes_with_descriptions(codes_text, self.lookup)
            except Exception as e:
                return f"Error in local lookup: {str(e)}"
        
        def web_search_missing_codes(codes_text: str) -> str: 
            #web search for codes not found locally 
            try: 
                return self.web_search_missing_code_descriptions(codes_text)
            except Exception as e:
                return f"Error in web search: {str(e)}"

        
        return [
            Tool(
                name="lookup_codes_local", #use csv lookup table to find descriptions 
                func=lookup_codes_local,
                description="Look up code descriptions using the local lookup table"
            ), 
            Tool(
                name="web_search_missing_codes", 
                func=web_search_missing_codes, 
                description="Search the web for medical codes not found in csv file" 
            )
        ]
    
    def _create_agent(self) -> AgentExecutor:
        """Create the ReAct agent"""
    
        template = """You are an expert medical coding assistant. Select the correct CPT/HCPCS/ICD-10 code from multiple choice options.

        AVAILABLE TOOLS: 
        - lookup_codes_local: looks up medical code descriptions in local lookup table
        - web_search_missing_codes: searches web for codes with poor/missing descriptions

        CRITICAL WORKFLOW:
        1. ICD-10 codes (contain dots like M17.0): Skip local lookup, use web_search immediately
        2. CPT/HCPCS codes (5 digits or letter+4 digits): Always try lookup_codes_local first
        3. Use web_search ONLY when:
        - Local Lookup codes have identical descriptions or all are too similar
        - Do NOT web search if only 1-2 codes are missing descriptions
        4. DO NOT web search just because descriptions are abbreviated or unclear - work with what you have
        5. If there is only 1-2 descriptions out of the 4 codes, assume the answer is in one of the codes WITH descriptions


        Format:
        Question: [the question to answer]
        Thought: [analysis]
        Action: [tool_name from: {tool_names}]
        Action Input: [input for the tool]
        Observation: [tool results]
        [...repeat Thought/Action/Observation cycle as needed...]
        Thought: I now know the final answer
        Final Answer: [SINGLE LETTER: A, B, C, or D - NOTHING ELSE]


        You have access to these tools:
        {tools}
        IMPORTANT: 
        If no code matches the procedure, state this clearly before making your best guess

        Example:
        Thought: The question asks for percutaneous nephrostolithotomy. None of the codes (renal exploration, abscess drainage, biopsy, partial nephrectomy) describe stone removal. However, I must select the closest option.

        Examples of CORRECT format:
        Final Answer: A
        Final Answer: B

        Examples of WRONG format:
        Final Answer: A - because code 41110 is for tongue lesion
        Final Answer: The answer is A
        Final Answer: A (code 41110)

        IMPORTANT:
        1. ALWAYS use lookup_codes_local first for CPT and HCPCS Codes 
        2. IF CODES ARE ICD10, USE WEB SEARCH. 
        Example: M17.0, M17.1 → These have dots → Action: web_search_missing_codes
        3. If you see identical descriptions for ALL codes, use web_search_missing_codes
        4. Pass the COMPLETE output from lookup_codes_local to web_search_missing_codes (include both found and missing descriptions)
        
        Example workflow:
        Action: lookup_codes_local
        Action Input: 41110
        41105
        41113
        40800
        Observation: 41110 - Description not found
        41105 - Tongue lesion excision
        41113 - Description not found  
        40800 - Oral lesion removal

        Action: web_search_missing_codes
        Action Input: 41110 - Description not found
        41105 - Tongue lesion excision
        41113 - Description not found
        40800 - Oral lesion removal

        Question: {input}
        Thought: {agent_scratchpad}"""
        
        prompt = PromptTemplate.from_template(template)
        
        agent = create_react_agent(self.llm, self.tools, prompt)
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=6,
            handle_parsing_errors=True
        )
    
    def process_single_question(self, question: str) -> Dict:

        formatted_question = question.strip()
        start_time = time.time()

        try:
            response = self.agent.invoke({"input": formatted_question})

            full_output = response.get('output', '')

            # look for "Final Answer:" and grab what comes after
            if "Final Answer:" in full_output:
                after_final = full_output.split("Final Answer:")[-1].strip()
                # Get just the first character that's A, B, C, or D
                for char in after_final:
                    if char in ['A', 'B', 'C', 'D']:
                        selected_letter = char
                        break
                else:
                    selected_letter = 'AN ERROR HAS OCCURED.'  # Fallback
            else:
                # fallback: find any A, B, C, or D in output
                matches = re.findall(r'\b([A-D])\b', full_output)
                selected_letter = matches[-1] if matches else 'AN ERROR HAS OCCURED '

            result = {
                'selected_letter': selected_letter,
                'full_reasoning': full_output,
                'processing_time': time.time() - start_time,
                'status': 'success'
            }

        except Exception as e:
            result = {
                'selected_letter': 'ERROROCCURED',
                'full_reasoning': f'Error: {str(e)}',
                'processing_time': time.time() - start_time,
                'status': 'error'
            }

        return result
    
    def parse_questions(self, text):
    
        raw_questions = re.split(r'\n?\s*(\d+)\.\s+', text) #split based off, number period and space. to indicate new question. 

        questions = []
        for i in range(1, len(raw_questions), 2): #step thru by 2. i will always be number of question, i+1 will always be content 
            number = raw_questions[i]
            content = raw_questions[i + 1]
            questions.append((number, content.strip())) #append as tuple, remove trailiing/leading whitespace. 

        return questions

    def process_batch(self, questions_batch): 
        batch_results = []
        for num, q in questions_batch:
            formatted_q = f"Question {num}:\n{q}" 
            result = self.process_single_question(formatted_q)
            batch_results.append(f"{num}. {result['selected_letter']}")
            
            #delay to avoid rate limiting
            time.sleep(1)
        
        return "\n".join(batch_results)
    
    def run_full_test(self, parsed_questions, batch_size=1, output_file="agent_responses.txt"):
        
        with open(output_file, "w", encoding="utf-8") as file:
            for i in range(0, len(parsed_questions), batch_size):
                batch = parsed_questions[i:i + batch_size]
                
                print(f"Processing batch {i//batch_size + 1}: questions {[q[0] for q in batch]}")
                
                batch_output = self.process_batch(batch)
                
                file.write(batch_output + "\n" + "-" * 80 + "\n")
                file.flush()  # writes immediately
                
                print(f"Completed batch: {batch_output.replace(chr(10), ', ')}")

if __name__ == "__main__":
    # use the existing HCPCSLookup instance
    lookup = HCPCSLookup()
    lookup.load_from_csv('PPRRVU23_JAN.csv')  
    
    system = AgenticCPTSystem(lookup, anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    with open('Test.txt', 'r', encoding='utf-8') as f: #read in test
        text = f.read()

    
    # Run the full test
    system.run_full_test(system.parse_questions(text), batch_size=1, output_file="agent_responses.txt")
    
    print("Test completed! Check agent_responses.txt for results.")