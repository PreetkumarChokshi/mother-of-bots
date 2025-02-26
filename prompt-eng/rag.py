from typing import List, Optional
from pathlib import Path
import hashlib
from document import Document
from vector_store import VectorStore
from models import AIModel, ModelOptions
from base import ChatbotClient

# Use string literal for forward reference to avoid circular import
class RAGPipeline:
    def __init__(self, client: ChatbotClient, model: AIModel):
        self.client = client
        self.model = model
    
        self.vector_store = VectorStore()
        self.base_prompt = """You are a helpful document assistant. Answer questions based ONLY on the following context:
        {context}
        
        If the answer isn't in the context, say 'I don't know based on the documents provided'."""
        self._init_system_prompt()
    
    def _init_system_prompt(self):
        self.client.set_system_prompt(self.base_prompt)

    async def ingest_documents(self, file_paths: List[str]):
        """Process and store documents"""
        for path in file_paths:
            content = self._load_document(path)
            chunks = self._chunk_content(content)
            self.vector_store.add_documents(chunks)

    def _load_document(self, path: str) -> str:
        # Implement PDF, DOCX, TXT, CSV parsing
        # Use existing libraries like PyPDF2, docx2txt, etc.
        pass

    def _chunk_content(self, content: str) -> List[Document]:
        # Implement text chunking with overlap
        pass

    def query(self, question: str, options: Optional[ModelOptions] = None) -> str:
        # Remove async
        try:
            # Retrieve relevant context
            context = self.vector_store.search(question, top_k=3)
            
            if not context:
                return "No relevant information found in the uploaded documents."
            
            # Update system prompt with current context
            formatted_context = "\n".join([doc.content for doc in context])
            self.client.set_system_prompt(self.base_prompt.format(context=formatted_context))
            
            # Use existing chat completion flow
            _, response = self.client.chat_completion(question, self.model, options)
            return response
        except Exception as e:
            return f"Error processing query: {str(e)}" 