import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
import json
from pathlib import Path
import hashlib
from clients import bootstrap_client_and_model
from document import Document
from vector_store import VectorStore

@dataclass
class ProcessedDocument:
    id: str
    content: str
    summary: str
    key_points: List[str]
    metadata: Dict
    embeddings: Optional[List[float]] = None

@dataclass
class KnowledgeBase:
    documents: List[ProcessedDocument]
    vector_store: VectorStore
    last_updated: str
    
    def __post_init__(self):
        self.documents = self.documents or []

class LearningEngineAgent:
    def __init__(self):
        # Initialize client with LLaMA-2 (or fallback to available model)
        self.client, self.model = bootstrap_client_and_model(
            preferred_model="llama2"
        )
        self.vector_store = VectorStore()
        self.knowledge_base = KnowledgeBase(
            documents=[],
            vector_store=self.vector_store,
            last_updated=""
        )
    
    async def process_documents(self, file_paths: List[str]) -> List[ProcessedDocument]:
        """Process and analyze documents using LLaMA-2"""
        processed_docs = []
        
        for file_path in file_paths:
            # Read document content
            content = await self._read_document(file_path)
            
            # Generate document ID
            doc_id = self._generate_doc_id(file_path, content)
            
            # Process document using LLaMA-2
            system_prompt = """You are a document analysis expert. Extract key information, 
            create a summary, and identify main points from the document. 
            Respond in JSON format with 'summary' and 'key_points' fields."""
            
            self.client.set_system_prompt(system_prompt)
            
            _, analysis_json = self.client.chat_completion(content, self.model, None)
            
            try:
                analysis = json.loads(analysis_json)
                processed_doc = ProcessedDocument(
                    id=doc_id,
                    content=content,
                    summary=analysis.get("summary", ""),
                    key_points=analysis.get("key_points", []),
                    metadata={
                        "source": file_path,
                        "type": Path(file_path).suffix,
                        "size": len(content)
                    }
                )
                processed_docs.append(processed_doc)
                
            except json.JSONDecodeError:
                print(f"Error processing document: {file_path}")
                continue
        
        return processed_docs

    async def build_knowledge_base(self, processed_docs: List[ProcessedDocument]):
        """Build knowledge base using vector embeddings"""
        for doc in processed_docs:
            # Generate embeddings using LLaMA-2
            system_prompt = """Generate a semantic embedding for the following text.
            Focus on key concepts and relationships."""
            
            self.client.set_system_prompt(system_prompt)
            
            # Combine summary and key points for embedding
            embedding_text = f"{doc.summary}\n" + "\n".join(doc.key_points)
            
            # Get embedding from model
            _, embedding_response = self.client.chat_completion(
                embedding_text,
                self.model,
                None
            )
            
            # Store document in vector store
            document = Document(
                content=doc.content,
                metadata={
                    "id": doc.id,
                    "summary": doc.summary,
                    "key_points": doc.key_points,
                    **doc.metadata
                }
            )
            
            self.vector_store.add_documents([document])
            self.knowledge_base.documents.append(doc)
    
    async def query_knowledge_base(self, query: str) -> Dict:
        """Query knowledge base using RAG"""
        system_prompt = """You are a knowledge base assistant. Use the provided context 
        to answer the question. If unsure, say so."""
        
        self.client.set_system_prompt(system_prompt)
        
        # Find relevant documents
        relevant_docs = self.vector_store.search(query, top_k=3)
        
        # Build context from relevant documents
        context = []
        for doc in relevant_docs:
            metadata = doc.metadata
            context.append(f"Summary: {metadata.get('summary', '')}")
            context.extend(f"- {point}" for point in metadata.get('key_points', []))
        
        context_str = "\n".join(context)
        
        # Generate response using RAG
        _, response = self.client.chat_completion(
            f"Context:\n{context_str}\n\nQuestion: {query}",
            self.model,
            None
        )
        
        return {
            "response": response,
            "sources": [doc.metadata.get("source") for doc in relevant_docs]
        }

    async def _read_document(self, file_path: str) -> str:
        """Read document content based on file type"""
        path = Path(file_path)
        
        if path.suffix.lower() == '.txt':
            async with open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        
        elif path.suffix.lower() == '.pdf':
            # TODO: Implement PDF reading
            raise NotImplementedError("PDF reading not yet implemented")
        
        elif path.suffix.lower() in ['.doc', '.docx']:
            # TODO: Implement DOCX reading
            raise NotImplementedError("DOCX reading not yet implemented")
        
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")

    def _generate_doc_id(self, file_path: str, content: str) -> str:
        """Generate unique document ID"""
        unique_string = f"{file_path}:{content[:100]}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]

# Example usage:
if __name__ == "__main__":
    async def main():
        agent = LearningEngineAgent()
        
        # Example documents
        documents = [
            "example_docs/doc1.txt",
            "example_docs/doc2.txt"
        ]
        
        # Process documents
        processed_docs = await agent.process_documents(documents)
        print(f"Processed {len(processed_docs)} documents")
        
        # Build knowledge base
        await agent.build_knowledge_base(processed_docs)
        print("Knowledge base built")
        
        # Example query
        query = "What are the main points about weather patterns?"
        result = await agent.query_knowledge_base(query)
        print("\nQuery Result:")
        print(f"Response: {result['response']}")
        print(f"Sources: {result['sources']}")
    
    asyncio.run(main()) 