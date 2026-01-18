
import os
import json
from typing import Dict
# from google.generativeai import configure
import google.generativeai as genai

class ParserAgent:
    def __init__(self):
        # configure(api_key=os.getenv('GEMINI_API_KEY'))
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('models/gemini-2.0-flash-lite')

    def parse(self, raw_text: str, input_type: str = 'text') -> Dict:
        prompt = f"""You are a math problem parser. Convert the following {input_type} input into a structured format.

Input: {raw_text}

Analyze and provide a JSON response with:
- problem_text: cleaned problem statement
- topic: one of [algebra, probability, calculus, linear_algebra]
- variables: list of variables mentioned
- constraints: list of constraints or conditions
- needs_clarification: true/false if anything is ambiguous

Respond with ONLY valid JSON, no other text."""

        response = self.model.generate_content(prompt)
        response_text = response.text.strip()

        try:
            if response_text.startswith('```json'):
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif response_text.startswith('```'):
                response_text = response_text.split('```')[1].split('```')[0].strip()

            parsed = json.loads(response_text)
            return parsed
        except json.JSONDecodeError:
            return {
                'problem_text': raw_text,
                'topic': 'unknown',
                'variables': [],
                'constraints': [],
                'needs_clarification': True
            }