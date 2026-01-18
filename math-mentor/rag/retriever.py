from typing import List, Dict
from rag.knowledge_base import KnowledgeBase
from utils.memory import MemorySystem

class Retriever:
    def __init__(self):
        self.kb = KnowledgeBase()
        self.memory = MemorySystem()
    
    def retrieve_context(self, problem: Dict, k: int = 3) -> Dict:
        problem_text = problem.get('problem_text', '')
        topic = problem.get('topic', '')
        
        kb_results = self.kb.search(problem_text, topic, k=k)
        
        similar_problems = self.memory.search_similar(problem_text, topic, limit=2)
        
        context = {
            'knowledge_base': kb_results,
            'similar_problems': similar_problems,
            'sources': [r['metadata'] for r in kb_results]
        }
        
        return context