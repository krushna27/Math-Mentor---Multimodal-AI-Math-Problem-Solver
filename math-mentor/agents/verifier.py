
import os
from typing import Dict
import json
from google.generativeai import configure
import google.generativeai as genai

class VerifierAgent:
    def __init__(self):
        configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('models/gemini-2.0-flash-lite')
    
    def verify(self, parsed_problem: Dict, solution: Dict) -> Dict:
        problem_text = parsed_problem.get('problem_text', '')
        solution_text = solution.get('solution', '')
        
        prompt = f"""You are a math solution verifier. Check the correctness of this solution.

Problem: {problem_text}

Solution:
{solution_text}

Verify:
1. Mathematical correctness
2. Logical flow
3. Units and domains
4. Edge cases handled

Respond with JSON:
{{
  "is_correct": true/false,
  "confidence": 0.0-1.0,
  "issues": ["list of issues if any"],
  "needs_review": true/false,
  "feedback": "brief feedback"
}}

Respond with ONLY valid JSON."""

        response = self.model.generate_content(prompt)
        response_text = response.text.strip()

        try:
            if response_text.startswith('```json'):
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif response_text.startswith('```'):
                response_text = response_text.split('```')[1].split('```')[0].strip()

            verification = json.loads(response_text)

            if verification.get('confidence', 0) < 0.7:
                verification['needs_review'] = True

            return verification
        except json.JSONDecodeError:
            return {
                'is_correct': False,
                'confidence': 0.5,
                'issues': ['Unable to verify solution'],
                'needs_review': True,
                'feedback': 'Verification inconclusive'
            }