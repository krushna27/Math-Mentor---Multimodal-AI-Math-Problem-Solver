
import os
from typing import Dict
from google.generativeai import configure
import google.generativeai as genai

class ExplainerAgent:
    def __init__(self):
        configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('models/gemini-2.0-flash-lite')

    def explain(self, parsed_problem: Dict, solution: Dict, verification: Dict) -> Dict:
        problem_text = parsed_problem.get('problem_text', '')
        solution_text = solution.get('solution', '')
        is_correct = verification.get('is_correct', False)

        prompt = f"""You are a friendly math tutor. Explain this solution in a student-friendly way.

Problem: {problem_text}

Solution:
{solution_text}

Create a clear, step-by-step explanation that:
1. Breaks down the approach
2. Explains why each step works
3. Highlights key concepts
4. Points out common mistakes to avoid

Make it conversational and encouraging.

"""

        response = self.model.generate_content(prompt)
        explanation = response.text

        if not is_correct:
            explanation += "\n\n⚠️ Note: The verifier has some concerns about this solution. Please review carefully."

        return {
            'explanation': explanation,
            'tone': 'friendly',
            'includes_warnings': not is_correct
        }