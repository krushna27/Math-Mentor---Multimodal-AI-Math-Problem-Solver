from typing import Dict, Optional
from datetime import datetime

class HITLSystem:
    def __init__(self):
        self.hitl_triggers = []
    
    def should_trigger_hitl(self, 
                           ocr_confidence: float = 1.0,
                           audio_confidence: float = 1.0,
                           parser_needs_clarification: bool = False,
                           verifier_confidence: float = 1.0,
                           explicit_request: bool = False) -> Dict:
        
        triggers = []
        
        if ocr_confidence < 0.7:
            triggers.append({
                'reason': 'Low OCR confidence',
                'confidence': ocr_confidence,
                'severity': 'medium'
            })
        
        if audio_confidence < 0.6:
            triggers.append({
                'reason': 'Low audio transcription confidence',
                'confidence': audio_confidence,
                'severity': 'medium'
            })
        
        if parser_needs_clarification:
            triggers.append({
                'reason': 'Parser detected ambiguity or incomplete information',
                'confidence': 0.5,
                'severity': 'high'
            })
        
        if verifier_confidence < 0.7:
            triggers.append({
                'reason': 'Verifier not confident in solution correctness',
                'confidence': verifier_confidence,
                'severity': 'high'
            })
        
        if explicit_request:
            triggers.append({
                'reason': 'User explicitly requested review',
                'confidence': 0.0,
                'severity': 'high'
            })
        
        should_trigger = len(triggers) > 0
        
        hitl_data = {
            'should_trigger': should_trigger,
            'triggers': triggers,
            'timestamp': datetime.now().isoformat(),
            'primary_reason': triggers[0]['reason'] if triggers else None
        }
        
        if should_trigger:
            self.hitl_triggers.append(hitl_data)
        
        return hitl_data
    
    def get_hitl_instructions(self, hitl_data: Dict) -> str:
        if not hitl_data['should_trigger']:
            return ""
        
        instructions = ["⚠️ **Human Review Required**\n"]
        
        for trigger in hitl_data['triggers']:
            severity_emoji = "🔴" if trigger['severity'] == 'high' else "🟡"
            instructions.append(f"{severity_emoji} {trigger['reason']}")
            if 'confidence' in trigger:
                instructions.append(f"   Confidence: {trigger['confidence']:.2%}")
        
        instructions.append("\n**Action Required:**")
        instructions.append("1. Review the extracted/parsed content above")
        instructions.append("2. Edit if necessary")
        instructions.append("3. Click 'Solve Problem' again, or")
        instructions.append("4. Use 'Request Re-check' if solution is generated")
        
        return '\n'.join(instructions)
    
    def record_hitl_resolution(self, hitl_data: Dict, resolution: Dict):
        hitl_data['resolution'] = {
            'action': resolution.get('action'),
            'edited': resolution.get('edited', False),
            'approved': resolution.get('approved', False),
            'timestamp': datetime.now().isoformat()
        }
        return hitl_data