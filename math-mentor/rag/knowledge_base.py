import os
from typing import List, Dict
import openai
import chromadb
from chromadb.config import Settings
from chromadb import EmbeddingFunction

class OpenAIEmbedder(EmbeddingFunction):
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        response = openai.Embedding.create(input=input, model="text-embedding-ada-002")
        return [item['embedding'] for item in response['data']]

class KnowledgeBase:
    def __init__(self, knowledge_dir='knowledge/docs'):
        self.knowledge_dir = knowledge_dir
        self.embedder = OpenAIEmbedder()
        
        self.client = chromadb.Client(Settings(
            anonymized_telemetry=False,
            allow_reset=True
        ))
        
        # Always reset collection to ensure clean state with correct embeddings
        try:
            self.client.delete_collection('math_knowledge')
        except:
            pass
        
        self.collection = self.client.create_collection('math_knowledge', embedding_function=self.embedder)
        self._load_documents()
    
    def _load_documents(self):
        docs = []
        metadatas = []
        ids = []
        
        for filename in os.listdir(self.knowledge_dir):
            if filename.endswith('.txt'):
                filepath = os.path.join(self.knowledge_dir, filename)
                topic = filename.replace('.txt', '')
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                chunks = self._chunk_document(content)
                
                for i, chunk in enumerate(chunks):
                    docs.append(chunk)
                    metadatas.append({
                        'topic': topic,
                        'source': filename
                    })
                    ids.append(f"{topic}_{i}")
        
        if docs:
            self.collection.add(
                documents=docs,
                metadatas=metadatas,
                ids=ids
            )
    
    def _chunk_document(self, content: str, chunk_size: int = 500) -> List[str]:
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line)
            if current_size + line_size > chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def search(self, query: str, topic: str = None, k: int = 3) -> List[Dict]:
        where = {"topic": topic} if topic else None
        
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=where
        )
        
        retrieved = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                retrieved.append({
                    'content': doc,
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else 0
                })
        
        return retrieved