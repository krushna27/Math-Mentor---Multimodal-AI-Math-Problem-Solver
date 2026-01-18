
import os
from typing import Dict
from google.generativeai import configure
import google.generativeai as genai

class RouterAgent:
    def __init__(self):
        configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('models/gemini-2.0-flash-lite')
    
    def route(self, parsed_problem: Dict) -> Dict:
        topic = parsed_problem.get('topic', 'unknown')
        needs_clarification = parsed_problem.get('needs_clarification', False)
        
        if needs_clarification:
            return {
                'action': 'request_clarification',
                'requires_hitl': True,
                'reason': 'Problem statement is ambiguous or incomplete'
            }
        
        if topic == 'unknown':
            return {
                'action': 'request_clarification',
                'requires_hitl': True,
                'reason': 'Cannot determine problem topic'
            }
        
        strategy = self._determine_strategy(parsed_problem)
        
        return {
            'action': 'solve',
            'requires_hitl': False,
            'strategy': strategy,
            'topic': topic
        }
    
    def _determine_strategy(self, problem: Dict) -> str:
        topic = problem.get('topic', '')
        
        strategies = {
            'algebra': 'algebraic_manipulation',
            'probability': 'counting_and_probability',
            'calculus': 'differentiation_integration',
            'linear_algebra': 'matrix_operations'
        }

        
        return strategies.get(topic, 'general_problem_solving')