import re

def parse_markdown_questions(filepath):
    """
    Parses a markdown file to extract questions and answers.
    Expected format from question-3d.md.
    Contains Multiple Choice and Fill the Blanks.
    """
    questions = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return questions

    current_question = None
    question_type = "multiple_choice" # Default
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Detect section change
        if "ส่วนที่ 2: ข้อสอบประเภทเติมคำ" in line:
            question_type = "fill_blank"
            continue
        
        # Skip headers / labels
        if line.startswith("ส่วนที่") or line.startswith("หมวด:") or line.startswith("(คำแนะนำ"):
            continue
            
        # --- Multiple Choice Parsing ---
        if question_type == "multiple_choice":
            # If it's not an a/b/c/d option, it's a new question text
            # Options start with ก., ข., ค., ง.
            opt_match = re.match(r'^[กขคง]\.', line)
            
            if not opt_match:
                # Save previous question
                if current_question:
                    questions.append(current_question)
                
                # Start new question
                # Remove leading numbers like "11. "
                q_text = re.sub(r'^\d+\.\s*', '', line)
                current_question = {
                    'type': 'multiple_choice',
                    'text': q_text,
                    'options': [],
                    'correct_index': 0 # Needs manual setting or assume random later, 
                                       # since this file doesn't specify correct answers!
                 }
            elif current_question:
                # Add option
                current_question['options'].append(line)
        
        # --- Fill in the Blank Parsing ---
        elif question_type == "fill_blank":
            # Questions usually end with ......
            # Answers are in the next line like (เฉลย: Klipper)
            if "(เฉลย:" in line:
                if current_question:
                    ans = re.search(r'เฉลย:\s*(.*)\)', line)
                    if ans:
                        current_question['answer'] = ans.group(1).strip()
                        questions.append(current_question)
                        current_question = None
            else:
                # It's a question text
                if current_question:
                   questions.append(current_question) # Should not happen if correctly formatted
                
                current_question = {
                    'type': 'fill_blank',
                    'text': line,
                    'answer': ''
                }
                
    if current_question and 'answer' in current_question:
        questions.append(current_question)
    elif current_question and current_question['type'] == 'multiple_choice':
        questions.append(current_question)
        
    return questions

if __name__ == "__main__":
    qs = parse_markdown_questions("question-3d.md")
    for q in qs:
        print(q)
