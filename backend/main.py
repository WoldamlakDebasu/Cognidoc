from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import tempfile
import shutil
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our RAG components
from backend.rag_engine import RAGEngine

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CogniDocs Enterprise RAG API",
    description="Advanced Retrieval-Augmented Generation system for enterprise knowledge management",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enhanced CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "https://*.vercel.app",
        "https://*.app.github.dev",
        "https://*.github.dev",
        "https://musical-broccoli-px75xv4jxxr27w7p-3000.app.github.dev"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG engine
rag_engine = RAGEngine()

# Pydantic models
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="The question to ask the AI")
    include_sources: bool = Field(True, description="Whether to include source citations")
    max_sources: int = Field(5, ge=1, le=10, description="Maximum number of sources to return")

class Source(BaseModel):
    document: str
    page_number: int
    chunk_id: int
    relevance: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    context_used: Optional[int] = None
    processing_time: Optional[float] = None
    timestamp: datetime
    suggestion: Optional[str] = None

class UploadResponse(BaseModel):
    message: str
    uploaded_files: List[str]
    processing_details: Dict[str, Any]
    total_files: int

class HealthResponse(BaseModel):
    status: str
    mode: str
    documents_count: int
    gemini_configured: bool
    pinecone_configured: bool
    timestamp: str
    demo_chunks: Optional[int] = None

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None
    timestamp: str
    request_id: Optional[str] = None

# Dependency functions
async def get_rag_engine() -> RAGEngine:
    """Dependency to get RAG engine instance."""
    return rag_engine

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            timestamp=datetime.utcnow().isoformat() + "Z"
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            details=str(exc) if os.getenv("DEBUG") == "true" else None,
            timestamp=datetime.utcnow()
        ).dict()
    )

# API Routes
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "CogniDocs Enterprise RAG API",
        "version": "2.0.0",
        "status": "operational",
        "documentation": "/docs",
        "timestamp": datetime.utcnow()
    }

@app.post("/upload/", response_model=UploadResponse, tags=["Document Management"])
async def upload_documents(
    files: List[UploadFile] = File(...),
    engine: RAGEngine = Depends(get_rag_engine)
):
    """
    Upload and process PDF documents for the knowledge base.
    
    - **files**: List of PDF files to upload and process
    - Returns processing details and success confirmation
    """
    start_time = datetime.utcnow()
    
    try:
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files provided"
            )
        
        uploaded_files = []
        processing_details = {}
        
        for file in files:
            # Validate file type
            if not file.filename or not file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only PDF files are supported. Received: {file.filename}"
                )
            
            # Check file size (limit to 50MB)
            file_size = 0
            content = await file.read()
            file_size = len(content)
            
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File {file.filename} is too large. Maximum size is 50MB."
                )
            
            # Reset file pointer
            await file.seek(0)
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                shutil.copyfileobj(file.file, tmp_file)
                tmp_path = tmp_file.name
            
            try:
                # Process the document with RAG engine
                file_start = datetime.utcnow()
                await engine.add_document(tmp_path, file.filename)
                processing_time = (datetime.utcnow() - file_start).total_seconds()
                
                uploaded_files.append(file.filename)
                processing_details[file.filename] = {
                    "size_mb": round(file_size / (1024 * 1024), 2),
                    "processing_time_seconds": round(processing_time, 2),
                    "status": "success"
                }
                
                logger.info(f"Successfully processed {file.filename}")
                
            except Exception as e:
                logger.error(f"Error processing {file.filename}: {str(e)}")
                processing_details[file.filename] = {
                    "size_mb": round(file_size / (1024 * 1024), 2),
                    "status": "failed",
                    "error": str(e)
                }
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error processing {file.filename}: {str(e)}"
                )
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        
        total_time = (datetime.utcnow() - start_time).total_seconds()
        processing_details["total_processing_time"] = round(total_time, 2)
        
        return UploadResponse(
            message=f"Successfully uploaded and processed {len(uploaded_files)} document(s)",
            uploaded_files=uploaded_files,
            processing_details=processing_details,
            total_files=len(uploaded_files)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during upload process: {str(e)}"
        )

@app.post("/query/", response_model=QueryResponse, tags=["AI Query"])
async def query_documents(
    request: QueryRequest,
    engine: RAGEngine = Depends(get_rag_engine)
):
    """
    Query the knowledge base and receive AI-generated answers with source citations.
    
    - **query**: The question to ask (1-1000 characters)
    - **include_sources**: Whether to include source citations (default: true)
    - **max_sources**: Maximum number of sources to return (1-10, default: 5)
    """
    start_time = datetime.utcnow()
    
    try:
        if not request.query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query cannot be empty"
            )
        
        logger.info(f"Processing query: {request.query[:100]}...")
        
        # Process the query
        result = await engine.query(request.query)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Limit sources if requested
        sources = result.get("sources", [])[:request.max_sources] if request.include_sources else []
        
        response = QueryResponse(
            answer=result["answer"],
            sources=[Source(**source) for source in sources],
            context_used=result.get("context_used"),
            processing_time=round(processing_time, 2),
            timestamp=datetime.utcnow(),
            suggestion=result.get("suggestion")
        )
        
        logger.info(f"Query processed successfully in {processing_time:.2f}s")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(engine: RAGEngine = Depends(get_rag_engine)):
    """
    Comprehensive health check endpoint.
    
    Returns system status, configuration, and document count.
    """
    try:
        status_info = engine.get_status()
        
        return HealthResponse(
            status="healthy",
            mode=status_info["mode"],
            documents_count=status_info["documents_count"],
            gemini_configured=status_info["gemini_configured"],
            pinecone_configured=status_info["pinecone_configured"],
            demo_chunks=status_info.get("demo_chunks"),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )

@app.get("/documents/", tags=["Document Management"])
async def list_documents(engine: RAGEngine = Depends(get_rag_engine)):
    """List all uploaded documents with metadata."""
    try:
        return {
            "documents": engine.documents,
            "total_count": len(engine.documents),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Document listing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing documents: {str(e)}"
        )

@app.get("/status", tags=["Health"])
async def get_system_status():
    """Get detailed system status and configuration."""
    return {
        "system": "CogniDocs Enterprise RAG",
        "version": "2.0.0",
        "environment": {
            "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
            "pinecone_configured": bool(os.getenv("PINECONE_API_KEY")),
            "debug_mode": os.getenv("DEBUG", "false").lower() == "true"
        },
        "timestamp": datetime.utcnow(),
        "uptime": "operational"
    }

if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting CogniDocs API server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

