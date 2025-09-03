from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import tempfile
import shutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our RAG components
from rag_engine import RAGEngine

app = FastAPI(title="CogniDocs API", version="1.0.0")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG engine
rag_engine = RAGEngine()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]

@app.get("/")
async def root():
    return {"message": "CogniDocs API is running"}

@app.post("/upload/")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload and process documents for the knowledge base."""
    try:
        uploaded_files = []
        
        for file in files:
            if not file.filename.endswith('.pdf'):
                raise HTTPException(status_code=400, detail=f"Only PDF files are supported. Got: {file.filename}")
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                shutil.copyfileobj(file.file, tmp_file)
                tmp_path = tmp_file.name
            
            try:
                # Process the document with RAG engine
                await rag_engine.add_document(tmp_path, file.filename)
                uploaded_files.append(file.filename)
            finally:
                # Clean up temporary file
                os.unlink(tmp_path)
        
        return {"message": "Documents uploaded successfully", "uploaded_files": uploaded_files}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing documents: {str(e)}")

@app.post("/query/", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query the knowledge base and get AI-generated answers with sources."""
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        result = await rag_engine.query(request.query)
        
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "documents_count": len(rag_engine.documents)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

