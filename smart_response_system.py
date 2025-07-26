import re
from typing import List, Dict, Tuple
import json
from datetime import datetime

class SmartResponseSystem:
    def __init__(self, faq_data):
        self.faq_data = faq_data
        self.context_memory = {}
        self.response_cache = {}
        
    def get_smart_answer(self, question: str, user_id: str, conversation_history: List[Dict]) -> Tuple[str, str, float]:
        """Get answer with context awareness and confidence scoring"""
        
        # Check cache first
        cache_key = self._generate_cache_key(question)
        if cache_key in self.response_cache:
            cached = self.response_cache[cache_key]
            return cached['answer'], cached['intent'], cached['confidence']
        
        # Analyze context from conversation history
        context = self._analyze_context(conversation_history)
        
        # Find best match with context
        best_match, confidence = self._find_best_match_with_context(question, context)
        
        if best_match:
            answer = best_match['response']
            intent = self._classify_intent_advanced(question, context)
            
            # Personalize response based on context
            answer = self._personalize_response(answer, context, conversation_history)
            
            # Cache the response
            self.response_cache[cache_key] = {
                'answer': answer,
                'intent': intent,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat()
            }
            
            return answer, intent, confidence
        
        # Fallback to contextual help
        return self._generate_contextual_fallback(question, context), 'general', 0.3
    
    def _analyze_context(self, conversation_history: List[Dict]) -> Dict:
        """Analyze conversation context"""
        context = {
            'previous_intents': [],
            'mentioned_courses': [],
            'mentioned_topics': [],
            'user_interests': [],
            'conversation_stage': 'initial'
        }
        
        if not conversation_history:
            return context
        
        # Analyze last 5 interactions
        recent_history = conversation_history[-5:]
        
        for qa in recent_history:
            question = qa['question'].lower()
            
            # Extract mentioned courses
            courses = re.findall(r'\b(b\.?tech|mba|bca|mca|b\.?com|m\.?com)\b', question)
            context['mentioned_courses'].extend(courses)
            
            # Extract topics
            if 'fee' in question or 'cost' in question:
                context['mentioned_topics'].append('fees')
            if 'eligibility' in question or 'criteria' in question:
                context['mentioned_topics'].append('eligibility')
            if 'date' in question or 'deadline' in question:
                context['mentioned_topics'].append('dates')
        
        # Determine conversation stage
        if len(conversation_history) > 5:
            context['conversation_stage'] = 'detailed'
        elif len(conversation_history) > 2:
            context['conversation_stage'] = 'exploring'
        
        return context
    
    def _find_best_match_with_context(self, question: str, context: Dict) -> Tuple[Dict, float]:
        """Find best match considering context"""
        question_lower = question.lower()
        best_match = None
        max_score = 0
        
        for item in self.faq_data:
            score = self._calculate_relevance_score(question_lower, item, context)
            
            if score > max_score:
                max_score = score
                best_match = item
        
        return best_match, max_score
    
    def _calculate_relevance_score(self, question: str, faq_item: Dict, context: Dict) -> float:
        """Calculate relevance score with context"""
        prompt_lower = faq_item['prompt'].lower()
        
        # Base similarity score
        question_words = set(question.split())
        prompt_words = set(prompt_lower.split())
        
        if not question_words or not prompt_words:
            return 0
        
        base_score = len(question_words.intersection(prompt_words)) / len(question_words.union(prompt_words))
        
        # Context boost
        context_boost = 0
        
        # Boost if related to previous topics
        for topic in context['mentioned_topics']:
            if topic in prompt_lower:
                context_boost += 0.2
        
        # Boost if related to mentioned courses
        for course in context['mentioned_courses']:
            if course in prompt_lower:
                context_boost += 0.3
        
        # Stage-based boost
        if context['conversation_stage'] == 'detailed' and len(prompt_lower) > 50:
            context_boost += 0.1
        
        return min(base_score + context_boost, 1.0)
    
    def _personalize_response(self, answer: str, context: Dict, history: List[Dict]) -> str:
        """Personalize response based on context"""
        
        # Add contextual references
        if context['mentioned_courses']:
            course = context['mentioned_courses'][-1].upper()
            if course not in answer:
                answer = f"For {course} specifically: {answer}"
        
        # Add follow-up suggestions based on conversation stage
        if context['conversation_stage'] == 'initial':
            answer += "\n\n💡 You might also want to know about eligibility criteria, fees, or application deadlines."
        elif context['conversation_stage'] == 'exploring':
            answer += "\n\n🎯 Based on your questions, you might be interested in our placement statistics or campus facilities."
        
        # Add related questions
        related_questions = self._get_related_questions(context)
        if related_questions:
            answer += f"\n\n❓ Related questions you might have:\n" + "\n".join([f"• {q}" for q in related_questions[:3]])
        
        return answer
    
    def _get_related_questions(self, context: Dict) -> List[str]:
        """Get related questions based on context"""
        related = []
        
        if 'fees' in context['mentioned_topics']:
            related.extend([
                "Are there any scholarships available?",
                "What is the fee payment schedule?",
                "Are there any additional charges?"
            ])
        
        if 'eligibility' in context['mentioned_topics']:
            related.extend([
                "What is the admission process?",
                "When is the entrance exam?",
                "What documents are required?"
            ])
        
        return related[:5]  # Return max 5 related questions