from answer_key import answer_key 
import re 


def evaluate_model_responses(): 
    model_answers = {} 
    current_test = "agent_responses.txt"
    with open(current_test, "r", encoding="utf-8") as file: 
        for line in file: 
            match = re.match(r'(\d+)\.\s*([A-D])', line.strip()) #match on digit, period, space, and Letter (A-D)
            if match: 
                q_num = int(match.group(1)) 
                answer = match.group(2) 
                model_answers[q_num] = answer 
            
    return model_answers 

model_answers = evaluate_model_responses()

correct = 0
total = len(answer_key) 
for q_num, correct_answer in answer_key.items(): 
    model_answer = model_answers.get(q_num) 
    if model_answer == correct_answer:
        correct += 1 
        print(f"Good job. {q_num}: Is correct. Answer is {correct_answer}")
    else: 
        print(f"WRONG on question {q_num}: Agent Answered: {model_answer}, correct answer was: {correct_answer}")


print(f"Model score: {correct} out of {total}") 

