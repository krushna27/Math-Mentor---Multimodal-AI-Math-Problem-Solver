import easyocr
import numpy as np
from PIL import Image

# Compatibility fix for Pillow 10.0.0+ where ANTIALIAS was removed
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

class OCRProcessor:
    def __init__(self):
        self.reader = easyocr.Reader(['en'], gpu=False)
    
    def extract_text(self, image):
        if isinstance(image, Image.Image):
            image = np.array(image)
        
        results = self.reader.readtext(image)
        
        text_parts = []
        confidences = []
        
        for bbox, text, conf in results:
            text_parts.append(text)
            confidences.append(conf)
        
        full_text = ' '.join(text_parts)
        avg_confidence = np.mean(confidences) if confidences else 0.0
        
        return {
            'text': full_text,
            'confidence': avg_confidence,
            'needs_review': avg_confidence < 0.7
        }