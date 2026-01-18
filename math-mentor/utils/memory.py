


import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from collections import Counter

class MemorySystem:
    def __init__(self, memory_file='data/memory.json'):
        self.memory_file = memory_file
        os.makedirs(os.path.dirname(memory_file), exist_ok=True)
        self.memories = self._load_memory()
        self.correction_patterns = self._load_correction_patterns()
    
    def _load_memory(self) -> List[Dict]:
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_memory(self):
        with open(self.memory_file, 'w') as f:
            json.dump(self.memories, f, indent=2)
    
    def _load_correction_patterns(self) -> Dict:
        patterns = {
            'ocr_corrections': {},
            'audio_corrections': {},
            'common_mistakes': Counter(),
            'successful_strategies': Counter()
        }
        
        for memory in self.memories:
            if memory.get('user_feedback') == 'incorrect' and memory.get('user_comment'):
                topic = memory.get('parsed_question', {}).get('topic', 'unknown')
                patterns['common_mistakes'][topic] += 1
            
            if memory.get('user_feedback') == 'correct':
                strategy = memory.get('routing', {}).get('strategy', 'unknown')
                patterns['successful_strategies'][strategy] += 1
        
        return patterns
    
    def store(self, entry: Dict):
        entry['timestamp'] = datetime.now().isoformat()
        entry['id'] = len(self.memories)
        self.memories.append(entry)
        self._save_memory()
        
        self.correction_patterns = self._load_correction_patterns()
    
    def search_similar(self, problem_text: str, topic: str = None, limit: int = 3) -> List[Dict]:
        results = []
        problem_lower = problem_text.lower()
        problem_words = set(problem_lower.split())
        
        for memory in reversed(self.memories):
            if topic and memory.get('parsed_question', {}).get('topic', '').lower() != topic.lower():
                continue
            
            memory_text = memory.get('parsed_question', {}).get('problem_text', '').lower()
            memory_words = set(memory_text.split())
            
            common_words = problem_words & memory_words
            similarity = len(common_words) / max(len(problem_words), 1)
            
            if similarity > 0.3:
                results.append({
                    **memory,
                    'similarity': similarity
                })
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]
    
    def get_corrections(self) -> List[Dict]:
        return [m for m in self.memories if m.get('user_feedback') == 'incorrect']
    
    def get_learning_insights(self) -> Dict:
        total = len(self.memories)
        if total == 0:
            return {
                'total_problems': 0,
                'accuracy': 0,
                'topics_distribution': {},
                'most_successful_strategy': None,
                'common_error_topics': []
            }
        
        correct = sum(1 for m in self.memories if m.get('user_feedback') == 'correct')
        
        topics = Counter()
        for m in self.memories:
            topic = m.get('parsed_question', {}).get('topic', 'unknown')
            topics[topic] += 1
        
        return {
            'total_problems': total,
            'accuracy': (correct / total * 100) if total > 0 else 0,
            'topics_distribution': dict(topics),
            'most_successful_strategy': self.correction_patterns['successful_strategies'].most_common(1)[0][0] if self.correction_patterns['successful_strategies'] else None,
            'common_error_topics': [topic for topic, count in self.correction_patterns['common_mistakes'].most_common(3)]
        }
    
    def apply_learned_corrections(self, text: str, input_type: str) -> str:
        corrections_key = f'{input_type}_corrections'
        if corrections_key in self.correction_patterns:
            for wrong, correct in self.correction_patterns[corrections_key].items():
                text = text.replace(wrong, correct)
        
        return text
    
    def get_reusable_solution_pattern(self, topic: str) -> Optional[Dict]:
        successful_solutions = [
            m for m in self.memories 
            if m.get('user_feedback') == 'correct' 
            and m.get('parsed_question', {}).get('topic') == topic
        ]
        
        if successful_solutions:
            return successful_solutions[-1]
        return None