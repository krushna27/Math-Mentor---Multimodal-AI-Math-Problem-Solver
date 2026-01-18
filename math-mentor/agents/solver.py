import os
from typing import Dict, List
import re
import ast
import operator
from google.generativeai import configure
import google.generativeai as genai

class SolverAgent:
    def __init__(self):
        configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('models/gemini-2.0-flash-lite')
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }
    
    def solve(self, parsed_problem: Dict, context: Dict, strategy: str) -> Dict:
        problem_text = parsed_problem.get('problem_text', '')
        topic = parsed_problem.get('topic', '')
        
        kb_context = context.get('knowledge_base', [])
        similar_problems = context.get('similar_problems', [])
        
        context_text = self._format_context(kb_context, similar_problems)
        
        prompt = f"""You are a math problem solver with access to a Python calculator tool.

Problem: {problem_text}
Topic: {topic}
Strategy: {strategy}

Relevant Knowledge:
{context_text}

Solve step-by-step. When you need to calculate something, write it as:
CALCULATE: <expression>
Example: CALCULATE: (2 + 3) * 4

Provide:
1. Understanding of the problem
2. Step-by-step solution (use CALCULATE for computations)
3. Final answer

Format each step clearly."""

        response = self.model.generate_content(prompt)
        solution = response.text
        
        solution_with_calcs = self._execute_calculations(solution)
        
        return {
            'solution': solution_with_calcs,
            'steps': self._extract_steps(solution_with_calcs),
            'context_used': len(kb_context) + len(similar_problems),
            'calculations_performed': solution.count('CALCULATE:')
        }
    
    def _execute_calculations(self, solution: str) -> str:
        lines = solution.split('\n')
        result_lines = []
        
        for line in lines:
            result_lines.append(line)
            if 'CALCULATE:' in line:
                expr = line.split('CALCULATE:')[1].strip()
                try:
                    result = self._safe_eval(expr)
                    result_lines.append(f"  → Result: {result}")
                except Exception as e:
                    result_lines.append(f"  → Calculation error: {str(e)}")
        
        return '\n'.join(result_lines)
    
    def _safe_eval(self, expr: str):
        try:
            expr = expr.replace('^', '**').replace('√', 'sqrt')
            
            allowed_names = {
                'sqrt': lambda x: x ** 0.5,
                'abs': abs,
                'pow': pow,
                'pi': 3.141592653589793,
                'e': 2.718281828459045
            }
            
            node = ast.parse(expr, mode='eval')
            
            def _eval(node):
                if isinstance(node, ast.Expression):
                    return _eval(node.body)
                elif isinstance(node, ast.Num):
                    return node.n
                elif isinstance(node, ast.BinOp):
                    left = _eval(node.left)
                    right = _eval(node.right)
                    return self.operators[type(node.op)](left, right)
                elif isinstance(node, ast.UnaryOp):
                    operand = _eval(node.operand)
                    return self.operators[type(node.op)](operand)
                elif isinstance(node, ast.Call):
                    func_name = node.func.id
                    args = [_eval(arg) for arg in node.args]
                    return allowed_names[func_name](*args)
                elif isinstance(node, ast.Name):
                    return allowed_names[node.id]
                else:
                    raise ValueError(f"Unsupported operation: {type(node)}")
            
            return _eval(node.body)
        except Exception as e:
            raise ValueError(f"Cannot evaluate: {expr}")
    
    def _format_context(self, kb_results: List[Dict], similar: List[Dict]) -> str:
        parts = []
        
        for i, result in enumerate(kb_results, 1):
            parts.append(f"[KB {i}] {result['content']}")
        
        for i, prob in enumerate(similar, 1):
            if 'solution' in prob:
                past_solution = prob.get('solution', '')[:200]
                parts.append(f"[Similar {i}] Previous approach: {past_solution}...")
        
        return '\n\n'.join(parts) if parts else 'No additional context available'
    
    def _extract_steps(self, solution: str) -> List[str]:
        steps = []
        for line in solution.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•') or line.startswith('Step')):
                steps.append(line)
        return steps