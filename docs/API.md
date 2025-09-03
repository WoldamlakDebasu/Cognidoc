# CogniDocs API Documentation

This document provides comprehensive API documentation for the CogniDocs backend service.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication

Currently, the API does not require authentication. For production deployments, consider implementing:
- API key authentication
- JWT tokens
- OAuth 2.0

## Content Type

All requests should use `Content-Type: application/json` unless specified otherwise.

## Error Handling

The API returns standard HTTP status codes and JSON error responses:

```json
{
  "detail": "Error message description"
}
```

### Common Status Codes

- `200` - Success
- `400` - Bad Request (invalid input)
- `422` - Validation Error
- `500` - Internal Server Error

## Endpoints

### 1. Health Check

**GET** `/`

Basic health check endpoint.

**Response:**
```json
{
  "message": "CogniDocs API is running"
}
```

### 2. System Health

**GET** `/health`

Detailed system health and statistics.

**Response:**
```json
{
  "status": "healthy",
  "documents_count": 5,
  "timestamp": "2025-01-09T10:30:00Z"
}
```

### 3. Upload Documents

**POST** `/upload/`

Upload PDF documents to the knowledge base.

**Content-Type:** `multipart/form-data`

**Parameters:**
- `files` (required): One or more PDF files

**Example Request:**
```bash
curl -X POST "http://localhost:8000/upload/" \
  -F "files=@document1.pdf" \
  -F "files=@document2.pdf"
```

**Response:**
```json
{
  "message": "Documents uploaded successfully",
  "uploaded_files": [
    "document1.pdf",
    "document2.pdf"
  ]
}
```

**Error Responses:**

*Invalid file type:*
```json
{
  "detail": "Only PDF files are supported. Got: document.txt"
}
```

*Processing error:*
```json
{
  "detail": "Error processing documents: [specific error message]"
}
```

### 4. Query Knowledge Base

**POST** `/query/`

Query the knowledge base and receive AI-generated answers with source citations.

**Request Body:**
```json
{
  "query": "What were the total revenues in 2023?"
}
```

**Response:**
```json
{
  "answer": "Based on the financial documents, total revenues for 2023 were $96.8 billion, with automotive sales representing the largest segment at $82.4 billion.",
  "sources": [
    {
      "document": "Tesla_2023_10K_Report.pdf",
      "page_number": 45,
      "chunk_id": 12
    }
  ]
}
```

**Error Responses:**

*Empty query:*
```json
{
  "detail": "Query cannot be empty"
}
```

*Processing error:*
```json
{
  "detail": "Error processing query: [specific error message]"
}
```

## Request/Response Examples

### Complete Upload and Query Flow

1. **Upload a document:**
```bash
curl -X POST "http://localhost:8000/upload/" \
  -F "files=@company_report.pdf"
```

2. **Query the document:**
```bash
curl -X POST "http://localhost:8000/query/" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the key financial highlights?"}'
```

### JavaScript/Frontend Integration

```javascript
// Upload documents
const uploadDocuments = async (files) => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  
  const response = await fetch('http://localhost:8000/upload/', {
    method: 'POST',
    body: formData,
  });
  
  return await response.json();
};

// Query knowledge base
const queryKnowledgeBase = async (query) => {
  const response = await fetch('http://localhost:8000/query/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query }),
  });
  
  return await response.json();
};
```

### Python Client Example

```python
import requests

# Upload documents
def upload_documents(file_paths):
    files = [('files', open(path, 'rb')) for path in file_paths]
    response = requests.post('http://localhost:8000/upload/', files=files)
    return response.json()

# Query knowledge base
def query_knowledge_base(query):
    response = requests.post(
        'http://localhost:8000/query/',
        json={'query': query}
    )
    return response.json()

# Example usage
upload_result = upload_documents(['report.pdf'])
query_result = query_knowledge_base('What are the main findings?')
print(query_result['answer'])
```

## Rate Limiting

Currently, no rate limiting is implemented. For production use, consider:

- **Per-IP limits**: 100 requests per minute
- **Upload limits**: 10 files per hour
- **Query limits**: 50 queries per minute

## File Constraints

### Upload Limits

- **File types**: PDF only
- **File size**: 10MB per file (configurable)
- **Batch size**: 10 files per request
- **Total storage**: Depends on vector database limits

### Supported Document Features

- **Text extraction**: Full text from PDFs
- **Page numbers**: Preserved for source citation
- **Metadata**: Document name, page count, upload timestamp
- **Languages**: Primarily English (OpenAI model dependent)

## Response Time Expectations

| Operation | Typical Response Time | Factors |
|-----------|----------------------|---------|
| Health check | < 100ms | Server load |
| Document upload | 2-10 seconds | File size, processing complexity |
| Simple query | 1-3 seconds | Vector search + LLM generation |
| Complex query | 3-8 seconds | Context size, reasoning complexity |

## Error Codes Reference

### 400 Bad Request
- Empty query string
- Invalid file format
- Missing required parameters

### 422 Validation Error
- Malformed JSON request
- Invalid parameter types
- Request body validation failures

### 500 Internal Server Error
- OpenAI API failures
- Vector database connection issues
- Document processing errors
- Unexpected system errors

## Integration Patterns

### Webhook Integration

For asynchronous processing, consider implementing webhooks:

```python
# Pseudo-code for webhook support
@app.post("/upload-async/")
async def upload_async(files: List[UploadFile], webhook_url: str):
    # Process files in background
    # Send results to webhook_url when complete
    pass
```

### Batch Processing

For large document collections:

```python
# Pseudo-code for batch processing
@app.post("/batch-upload/")
async def batch_upload(document_urls: List[str]):
    # Download and process multiple documents
    # Return batch processing job ID
    pass
```

### Streaming Responses

For real-time query responses:

```python
# Pseudo-code for streaming
@app.post("/query-stream/")
async def query_stream(query: str):
    # Return streaming response as AI generates answer
    pass
```

## Security Considerations

### Input Validation

- File type verification
- Content scanning for malicious files
- Query length limits
- SQL injection prevention (if using SQL databases)

### Data Privacy

- Document content is processed by OpenAI
- Consider on-premise deployment for sensitive data
- Implement data retention policies
- Add audit logging for compliance

### API Security

```python
# Example security middleware
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/query/")
async def query_documents(
    request: QueryRequest,
    token: str = Security(security)
):
    # Validate token
    if not validate_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    # ... rest of endpoint
```

## Monitoring and Analytics

### Metrics to Track

- Request volume and response times
- Error rates by endpoint
- Document processing success rates
- Query complexity and accuracy
- User engagement patterns

### Logging Format

```json
{
  "timestamp": "2025-01-09T10:30:00Z",
  "level": "INFO",
  "endpoint": "/query/",
  "method": "POST",
  "status_code": 200,
  "response_time_ms": 2340,
  "query_length": 45,
  "sources_returned": 3,
  "user_id": "anonymous"
}
```

## OpenAPI/Swagger Documentation

The API automatically generates interactive documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

These interfaces allow you to:
- Test endpoints directly
- View request/response schemas
- Generate client SDKs
- Export API specifications

---

**For additional API support or custom integrations, contact woldamlak@yourcompany.com**

