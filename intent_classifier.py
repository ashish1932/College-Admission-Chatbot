import re

def classify_intent(question):
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['fee', 'cost', 'payment', 'money']):
        return 'fees'
    elif any(word in question_lower for word in ['date', 'deadline', 'when', 'time']):
        return 'dates'
    elif any(word in question_lower for word in ['eligibility', 'criteria', 'requirement']):
        return 'eligibility'
    elif any(word in question_lower for word in ['course', 'program', 'degree']):
        return 'courses'
    else:
        return 'general'