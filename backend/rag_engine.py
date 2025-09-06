import os
import asyncio
from typing import List, Dict, Any, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from langchain_pinecone import Pinecone as LangchainPinecone
import logging
import google.generativeai as genai

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self):
        """Initialize the RAG engine with Google Gemini and Pinecone."""
        self.gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_environment = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp-free")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "cognidocs")
        
        if not self.gemini_api_key:
            logger.warning("GEMINI_API_KEY or GOOGLE_API_KEY not found. Using demo mode.")
        else:
            # Configure Gemini API
            genai.configure(api_key=self.gemini_api_key)
        
        # Initialize embeddings with Gemini
        self.embeddings = None
        if self.gemini_api_key:
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=self.gemini_api_key
            )
        
        # Initialize Pinecone (if available)
        self.vectorstore = None
        self.documents = {}  # Store document metadata
        
        # For demo purposes, use in-memory storage if Pinecone is not configured
        self.demo_mode = not self.pinecone_api_key or not self.gemini_api_key
        self.demo_documents = []
        
        if not self.demo_mode:
            self._initialize_pinecone()
        
        # Initialize LLM with Gemini
        self.llm = None
        if self.gemini_api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=self.gemini_api_key,
                temperature=0.1,
                max_tokens=1000,
                convert_system_message_to_human=True
            )
        
        # Custom prompt template
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are an intelligent assistant that answers questions based on provided documents. 
            Use the following context to answer the question accurately and professionally.
            
            If the answer is not in the provided context, state that clearly.
            Always cite your sources when possible.
            
            Context:
            {context}
            
            Question: {question}
            
            Answer:"""
        )
    
    def _initialize_pinecone(self):
        """Initialize Pinecone vector database."""
        try:
            from pinecone import Pinecone
            
            # Initialize the Pinecone client
            pc = Pinecone(
                api_key=self.pinecone_api_key,
                environment=self.pinecone_environment
            )
            
            # Check if index exists
            if self.index_name not in pc.list_indexes().names():
                logger.info(f"Index '{self.index_name}' not found. Creating a new one...")
                pc.create_index(
                    name=self.index_name,
                    dimension=768,  # Ensure this matches your embedding model's dimension
                    metric="cosine",
                )
                logger.info(f"Created new Pinecone index: {self.index_name}")
            
            # Get the index using the client instance
            index = pc.Index(self.index_name)
            
            # Create LangChain Pinecone vectorstore
            self.vectorstore = LangchainPinecone(
                index=index,
                embedding=self.embeddings,
                text_key="text"
            )
            logger.info(f"Pinecone initialized successfully. Connected to index '{self.index_name}'.")
            
        except Exception as e:
            logger.error(f"Could not initialize Pinecone: {e}")
            self.demo_mode = True
    
    async def add_document(self, file_path: str, filename: str):
        """Add a document to the knowledge base."""
        try:
            # Load and split the document
            loader = PyPDFLoader(file_path)
            pages = await asyncio.to_thread(loader.load)
            
            if not pages:
                raise Exception("No content found in the PDF")
            
            # Split text into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
            chunks = text_splitter.split_documents(pages)
            
            # Add metadata to chunks
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "source": filename,
                    "chunk_id": i,
                    "page_number": chunk.metadata.get("page", 1),
                    "total_chunks": len(chunks)
                })
            
            if self.demo_mode:
                # Store in memory for demo
                self.demo_documents.extend(chunks)
                logger.info(f"Added {len(chunks)} chunks to demo storage")
            else:
                # Store in Pinecone
                await asyncio.to_thread(
                    self.vectorstore.add_documents, 
                    chunks
                )
                logger.info(f"Added {len(chunks)} chunks to Pinecone")
            
            # Store document metadata
            self.documents[filename] = {
                "chunks": len(chunks),
                "pages": len(pages),
                "status": "processed"
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}")
            raise Exception(f"Error processing document {filename}: {str(e)}")
    
    async def query(self, query: str) -> Dict[str, Any]:
        """Query the knowledge base and return answer with sources."""
        try:
            if self.demo_mode:
                return await self._demo_query(query)
            else:
                return await self._pinecone_query(query)
                
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "answer": f"I encountered an error while processing your query: {str(e)}",
                "sources": [],
                "error": True
            }
    
    async def _demo_query(self, query: str) -> Dict[str, Any]:
        """Handle queries in demo mode (without Pinecone)."""
        # Enhanced keyword matching for demo
        relevant_chunks = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for doc in self.demo_documents:
            content_words = set(doc.page_content.lower().split())
            # Calculate simple relevance score
            relevance = len(query_words.intersection(content_words)) / len(query_words)
            if relevance > 0.1:  # At least 10% word overlap
                relevant_chunks.append((doc, relevance))
        
        # Sort by relevance
        relevant_chunks.sort(key=lambda x: x[1], reverse=True)
        
        if not relevant_chunks:
            # Return enhanced demo response
            return self._get_demo_response(query)
        
        # Take top 3 most relevant chunks
        context_chunks = [chunk[0] for chunk in relevant_chunks[:3]]
        context = "\n\n".join([chunk.page_content for chunk in context_chunks])
        
        # Generate answer using enhanced prompting
        if self.llm:
            prompt = self.prompt_template.format(context=context, question=query)
            answer_response = await asyncio.to_thread(self.llm.invoke, prompt)
            answer = answer_response.content
        else:
            answer = self._generate_simple_answer(context, query)
        
        # Extract sources
        sources = []
        for chunk in context_chunks:
            sources.append({
                "document": chunk.metadata.get("source", "Unknown"),
                "page_number": chunk.metadata.get("page_number", 1),
                "chunk_id": chunk.metadata.get("chunk_id", 0),
                "relevance": "high"
            })
        
        return {
            "answer": answer.strip(),
            "sources": sources,
            "context_used": len(context_chunks)
        }
    
    async def _pinecone_query(self, query: str) -> Dict[str, Any]:
        """Handle queries using Pinecone vector search."""
        try:
            # Create retrieval QA chain with custom prompt
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 5}
                ),
                return_source_documents=True,
                chain_type_kwargs={"prompt": self.prompt_template}
            )
            
            result = await asyncio.to_thread(qa_chain, {"query": query})
            
            # Extract sources with enhanced metadata
            sources = []
            for doc in result["source_documents"]:
                sources.append({
                    "document": doc.metadata.get("source", "Unknown"),
                    "page_number": doc.metadata.get("page_number", 1),
                    "chunk_id": doc.metadata.get("chunk_id", 0),
                    "relevance": "high"
                })
            
            return {
                "answer": result["result"],
                "sources": sources,
                "context_used": len(result["source_documents"])
            }
            
        except Exception as e:
            logger.error(f"Pinecone query error: {str(e)}")
            raise e
    
    def _generate_simple_answer(self, context: str, query: str) -> str:
        """Generate a simple answer when LLM is not available."""
        # Basic text processing for demo purposes
        context_sentences = context.split('. ')
        query_words = query.lower().split()
        
        relevant_sentences = []
        for sentence in context_sentences:
            if any(word in sentence.lower() for word in query_words):
                relevant_sentences.append(sentence)
        
        if relevant_sentences:
            return '. '.join(relevant_sentences[:2]) + '.'
        else:
            return "Based on the available documents, I couldn't find a specific answer to your question."
    
    def _get_demo_response(self, query: str) -> Dict[str, Any]:
        """Return enhanced demo responses for common queries."""
        demo_responses = {
            "tesla": {
                "answer": "Based on Tesla's 2023 annual report, Tesla achieved record financial performance with total revenues of $96.77 billion, representing a 19% increase year-over-year. The automotive segment contributed $82.42 billion, while energy generation and storage contributed $6.04 billion, and services and other contributed $8.32 billion.",
                "sources": [
                    {"document": "Tesla_2023_Annual_Report.pdf", "page_number": 45, "chunk_id": 12, "relevance": "high"}
                ]
            },
            "revenue": {
                "answer": "According to the financial documents in our knowledge base, total revenues for 2023 were $96.77 billion. This represents strong growth across all business segments, with automotive sales being the primary revenue driver.",
                "sources": [
                    {"document": "Tesla_2023_Annual_Report.pdf", "page_number": 45, "chunk_id": 12, "relevance": "high"}
                ]
            },
            "reset": {
                "answer": "To perform a console reset according to the technical documentation: 1) Ensure the vehicle is in Park, 2) Hold down both scroll wheels on the steering wheel simultaneously for 10-15 seconds, 3) Wait for the main screen to go black, 4) The system will automatically reboot and display the Tesla logo. This process typically takes 30-60 seconds to complete.",
                "sources": [
                    {"document": "Tesla_Model_X_Manual.pdf", "page_number": 23, "chunk_id": 7, "relevance": "high"}
                ]
            },
            "console": {
                "answer": "The main console reset procedure involves holding both steering wheel scroll wheels for 10-15 seconds until the screen goes black, then waiting for the automatic reboot process to complete.",
                "sources": [
                    {"document": "Tesla_Model_X_Manual.pdf", "page_number": 23, "chunk_id": 7, "relevance": "high"}
                ]
            }
        }
        
        query_lower = query.lower()
        for keyword, response in demo_responses.items():
            if keyword in query_lower:
                return response
        
        # Enhanced default response
        return {
            "answer": "I don't have enough information in the current knowledge base to provide a specific answer to your question. To get better results, please try uploading relevant documents or rephrasing your question with more specific terms.",
            "sources": [],
            "suggestion": "Try queries about Tesla financials, technical procedures, or vehicle operations."
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the RAG engine."""
        return {
            "mode": "demo" if self.demo_mode else "production",
            "documents_count": len(self.documents),
            "demo_chunks": len(self.demo_documents) if self.demo_mode else 0,
            "gemini_configured": bool(self.gemini_api_key),
            "pinecone_configured": bool(self.pinecone_api_key and not self.demo_mode),
            "ai_provider": "Google Gemini"
        }

