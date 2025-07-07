import re
import os 
from dotenv import load_dotenv 
from openai import OpenAI 

load_dotenv() 

client = OpenAI() 


def parse_questions(text):
    
    raw_questions = re.split(r'\n?\s*(\d+)\.\s+', text) #split based off, number period and space. to indicate new question. 

    questions = []
    for i in range(1, len(raw_questions), 2): #step thru by 2, [i] will always be number of question, i+1 will always be content 
        number = raw_questions[i]
        content = raw_questions[i + 1]
        questions.append((number, content.strip())) #append as tuple, remove trailiing/leading whitespace. 
    
    return questions

# load the .txt file (converted from PDF)
with open('Test.txt', 'r', encoding='utf-8') as f:
    text = f.read()

parsed_questions = parse_questions(text)



batch_size = 5 #how many questions are parsed and answered at once 
current_model = "gpt-4.1"

with open(f"{current_model}_wrapper_responses.txt", "w", encoding="utf-8") as file: 
    for i in range(0, len(parsed_questions), batch_size): 
        batch = parsed_questions[i:i + batch_size] 

        prompt = "\n\n".join( #use \n\n as seperator, join array of 5 questions saved as(num, content) into one single prompt. give this prompt to gpt 
            [f"Question {num}:\n{q}" for num, q in batch]
        )

        response = client.responses.create(
            model=current_model,
            instructions="You are a highly knowledgeable medical coding assistant. You will be given multiple-choice questions related to CPT, ICD-10, and HCPCS medical coding. Your job is to select the most accurate and appropriate code based on the question context. Answer ONLY with the number of the question, followed by a period, followed by the correct letter (A, B, C, or D) then a new line.",
            temperature=0, 
            input=prompt 
        )
        file.write(response.output_text + "\n" + "-" * 80 + "\n") # each batch of answered questions will be seperated by dashes. 



