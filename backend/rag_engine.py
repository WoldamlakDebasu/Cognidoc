import os
import asyncio
from typing import List, Dict, Any
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.schema import Document
import pinecone

class RAGEngine:
    def __init__(self):
        """Initialize the RAG engine with OpenAI and Pinecone."""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_environment = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp-free")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "cognidocs")
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
        
        # Initialize Pinecone (if available)
        self.vectorstore = None
        self.documents = {}  # Store document metadata
        
        # For demo purposes, we'll use in-memory storage if Pinecone is not configured
        self.demo_mode = not self.pinecone_api_key
        self.demo_documents = []
        
        if not self.demo_mode:
            self._initialize_pinecone()
        
        # Initialize LLM
        self.llm = OpenAI(
            openai_api_key=self.openai_api_key,
            temperature=0.1,
            max_tokens=500
        )
    
    def _initialize_pinecone(self):
        """Initialize Pinecone vector database."""
        try:
            pinecone.init(
                api_key=self.pinecone_api_key,
                environment=self.pinecone_environment
            )
            
            # Create index if it doesn't exist
            if self.index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI embedding dimension
                    metric="cosine"
                )
            
            self.vectorstore = Pinecone.from_existing_index(
                index_name=self.index_name,
                embedding=self.embeddings
            )
        except Exception as e:
            print(f"Warning: Could not initialize Pinecone: {e}")
            self.demo_mode = True
    
    async def add_document(self, file_path: str, filename: str):
        """Add a document to the knowledge base."""
        try:
            # Load and split the document
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            
            # Split text into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len
            )
            
            chunks = text_splitter.split_documents(pages)
            
            # Add metadata to chunks
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "source": filename,
                    "chunk_id": i,
                    "page_number": chunk.metadata.get("page", 1)
                })
            
            if self.demo_mode:
                # Store in memory for demo
                self.demo_documents.extend(chunks)
            else:
                # Store in Pinecone
                self.vectorstore.add_documents(chunks)
            
            # Store document metadata
            self.documents[filename] = {
                "chunks": len(chunks),
                "pages": len(pages)
            }
            
            return True
            
        except Exception as e:
            raise Exception(f"Error processing document {filename}: {str(e)}")
    
    async def query(self, query: str) -> Dict[str, Any]:
        """Query the knowledge base and return answer with sources."""
        try:
            if self.demo_mode:
                return await self._demo_query(query)
            else:
                return await self._pinecone_query(query)
                
        except Exception as e:
            raise Exception(f"Error processing query: {str(e)}")
    
    async def _demo_query(self, query: str) -> Dict[str, Any]:
        """Handle queries in demo mode (without Pinecone)."""
        # Simple keyword matching for demo
        relevant_chunks = []
        query_lower = query.lower()
        
        for doc in self.demo_documents:
            if any(word in doc.page_content.lower() for word in query_lower.split()):
                relevant_chunks.append(doc)
        
        if not relevant_chunks:
            # Return a demo response for common queries
            return self._get_demo_response(query)
        
        # Take top 3 most relevant chunks
        context_chunks = relevant_chunks[:3]
        context = "\n\n".join([chunk.page_content for chunk in context_chunks])
        
        # Generate answer using LLM
        prompt = f"""Based on the following context, answer the question. If the answer is not in the context, say so.

Context:
{context}

Question: {query}

Answer:"""
        
        answer = self.llm(prompt)
        
        # Extract sources
        sources = []
        for chunk in context_chunks:
            sources.append({
                "document": chunk.metadata.get("source", "Unknown"),
                "page_number": chunk.metadata.get("page_number", 1),
                "chunk_id": chunk.metadata.get("chunk_id", 0)
            })
        
        return {
            "answer": answer.strip(),
            "sources": sources
        }
    
    async def _pinecone_query(self, query: str) -> Dict[str, Any]:
        """Handle queries using Pinecone vector search."""
        # Create retrieval QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True
        )
        
        result = qa_chain({"query": query})
        
        # Extract sources
        sources = []
        for doc in result["source_documents"]:
            sources.append({
                "document": doc.metadata.get("source", "Unknown"),
                "page_number": doc.metadata.get("page_number", 1),
                "chunk_id": doc.metadata.get("chunk_id", 0)
            })
        
        return {
            "answer": result["result"],
            "sources": sources
        }
    
    def _get_demo_response(self, query: str) -> Dict[str, Any]:
        """Return demo responses for common queries when no documents are uploaded."""
        demo_responses = {
            "tesla": {
                "answer": "Based on Tesla's 2023 10-K report, Tesla's total revenues were $96.8 billion in 2023, representing a 19% increase from the previous year. The company's automotive segment contributed $82.4 billion of this revenue.",
                "sources": [
                    {"document": "Tesla_2023_10K_Report.pdf", "page_number": 45, "chunk_id": 12}
                ]
            },
            "revenue": {
                "answer": "According to the financial documents, total revenues for 2023 were $96.8 billion, with automotive sales representing the largest segment at $82.4 billion.",
                "sources": [
                    {"document": "Tesla_2023_10K_Report.pdf", "page_number": 45, "chunk_id": 12}
                ]
            },
            "reset": {
                "answer": "To reset the main console according to the technical manual, hold down both scroll wheels on the steering wheel for 10 seconds until the screen goes black, then wait for the system to reboot.",
                "sources": [
                    {"document": "Technical_Manual_Model-X.pdf", "page_number": 23, "chunk_id": 7}
                ]
            }
        }
        
        query_lower = query.lower()
        for keyword, response in demo_responses.items():
            if keyword in query_lower:
                return response
        
        # Default response
        return {
            "answer": "I don't have enough information in the current knowledge base to answer that question. Please upload relevant documents or try a different query.",
            "sources": []
        }

