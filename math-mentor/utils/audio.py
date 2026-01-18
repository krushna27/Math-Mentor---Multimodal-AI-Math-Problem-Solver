# import whisper
# import tempfile
# import os

# class AudioProcessor:
#     def __init__(self):
#         self.model = whisper.load_model("base")
    
#     def transcribe(self, audio_file):
#         with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
#             tmp.write(audio_file.read())
#             tmp_path = tmp.name
        
#         try:
#             result = self.model.transcribe(tmp_path)
            
#             text = result['text']
#             segments = result.get('segments', [])
            
#             avg_confidence = 0.0
#             if segments:
#                 confidences = [s.get('no_speech_prob', 0) for s in segments]
#                 avg_confidence = 1 - (sum(confidences) / len(confidences))
#             else:
#                 avg_confidence = 0.8
            
#             return {
#                 'text': text,
#                 'confidence': avg_confidence,
#                 'needs_review': avg_confidence < 0.6
#             }
#         finally:
#             os.unlink(tmp_path)




# import whisper
# import tempfile
# import os
# import soundfile as sf
# import numpy as np

# class AudioProcessor:
#     def __init__(self):
#         self.model = whisper.load_model("base")
    
#     def transcribe(self, audio_file):
#         # Save uploaded file
#         with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
#             tmp.write(audio_file.read())
#             tmp_path = tmp.name
        
#         try:
#             # Transcribe directly
#             result = self.model.transcribe(tmp_path, fp16=False)
            
#             text = result['text']
#             segments = result.get('segments', [])
            
#             avg_confidence = 0.8
#             if segments:
#                 confidences = [1 - s.get('no_speech_prob', 0) for s in segments]
#                 avg_confidence = sum(confidences) / len(confidences)
            
#             return {
#                 'text': text,
#                 'confidence': avg_confidence,
#                 'needs_review': avg_confidence < 0.6
#             }
#         except Exception as e:
#             # Fallback
#             return {
#                 'text': "Error transcribing audio. Please try again.",
#                 'confidence': 0.0,
#                 'needs_review': True
#             }
#         finally:
#             if os.path.exists(tmp_path):
#                 os.unlink(tmp_path)



import whisper
import os

class AudioProcessor:
    def __init__(self):
        try:
            self.model = whisper.load_model("tiny")  # Smaller, faster
        except:
            self.model = None
    
    def transcribe(self, audio_file):
        if self.model is None:
            return {
                'text': "",
                'confidence': 0.0,
                'needs_review': True
            }
        
        # Save to temp file
        temp_path = "temp_audio.wav"
        
        try:
            with open(temp_path, "wb") as f:
                f.write(audio_file.getvalue())
            
            # Transcribe
            result = self.model.transcribe(temp_path, language="en", fp16=False)
            
            text = result.get('text', '').strip()
            
            return {
                'text': text,
                'confidence': 0.8,
                'needs_review': len(text) < 5
            }
            
        except Exception as e:
            print(f"Transcription error: {e}")
            return {
                'text': "",
                'confidence': 0.0,
                'needs_review': True
            }
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass