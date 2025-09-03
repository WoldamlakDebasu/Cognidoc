# CogniDocs Deployment Guide

This guide covers multiple deployment options for the CogniDocs RAG system, from development to production environments.

## 🎯 Deployment Options Overview

| Option | Frontend | Backend | Complexity | Cost | Best For |
|--------|----------|---------|------------|------|----------|
| **Local Development** | localhost:3000 | localhost:8000 | Low | Free | Testing & Demo |
| **Vercel + Railway** | Vercel | Railway | Medium | $5-20/month | Production |
| **AWS/GCP** | S3/CloudFront | EC2/Compute Engine | High | $20-100/month | Enterprise |
| **Docker Compose** | Container | Container | Medium | VPS cost | Self-hosted |

## 🚀 Option 1: Vercel + Railway (Recommended)

This is the fastest way to get CogniDocs live on the internet with minimal configuration.

### Frontend Deployment (Vercel)

1. **Prepare the Frontend**
   ```bash
   cd frontend
   npm run build
   npm run export  # For static export
   ```

2. **Deploy to Vercel**
   ```bash
   # Install Vercel CLI
   npm i -g vercel
   
   # Deploy
   vercel --prod
   ```

3. **Configure Environment Variables**
   - In Vercel dashboard, add environment variable:
   - `NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app`

### Backend Deployment (Railway)

1. **Prepare Railway**
   - Sign up at railway.app
   - Connect your GitHub repository
   - Select the `backend` folder as root

2. **Configure Environment Variables**
   ```
   OPENAI_API_KEY=your_key_here
   PINECONE_API_KEY=your_key_here
   PINECONE_ENVIRONMENT=us-west1-gcp-free
   PINECONE_INDEX_NAME=cognidocs
   PORT=8000
   ```

3. **Deploy**
   - Railway will automatically detect FastAPI and deploy
   - Your API will be available at `https://your-app.railway.app`

## 🐳 Option 2: Docker Deployment

Perfect for VPS deployment or local containerized development.

### Create Docker Files

**Frontend Dockerfile** (`frontend/Dockerfile`):
```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

**Backend Dockerfile** (`backend/Dockerfile`):
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Docker Compose** (`docker-compose.yml`):
```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - PINECONE_ENVIRONMENT=${PINECONE_ENVIRONMENT}
      - PINECONE_INDEX_NAME=${PINECONE_INDEX_NAME}
    volumes:
      - ./backend:/app
```

### Deploy with Docker

```bash
# Create .env file with your API keys
echo "OPENAI_API_KEY=your_key" > .env
echo "PINECONE_API_KEY=your_key" >> .env

# Build and run
docker-compose up --build -d

# Check status
docker-compose ps
```

## ☁️ Option 3: AWS Deployment

Enterprise-grade deployment with auto-scaling and high availability.

### Architecture Overview

```
Internet → CloudFront → S3 (Frontend)
Internet → ALB → ECS (Backend) → RDS/Pinecone
```

### Frontend (S3 + CloudFront)

1. **Build and Upload**
   ```bash
   cd frontend
   npm run build
   npm run export
   
   # Upload to S3
   aws s3 sync out/ s3://your-bucket-name --delete
   ```

2. **Configure CloudFront**
   - Create CloudFront distribution
   - Point to S3 bucket
   - Configure custom domain (optional)

### Backend (ECS Fargate)

1. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name cognidocs-backend
   ```

2. **Build and Push Docker Image**
   ```bash
   cd backend
   
   # Build
   docker build -t cognidocs-backend .
   
   # Tag and push
   docker tag cognidocs-backend:latest 123456789.dkr.ecr.region.amazonaws.com/cognidocs-backend:latest
   docker push 123456789.dkr.ecr.region.amazonaws.com/cognidocs-backend:latest
   ```

3. **Create ECS Service**
   - Use AWS Console or Terraform
   - Configure environment variables
   - Set up Application Load Balancer
   - Configure auto-scaling

## 🔧 Environment Configuration

### Production Environment Variables

**Frontend (.env.local)**:
```env
NEXT_PUBLIC_API_URL=https://your-backend-domain.com
NEXT_PUBLIC_ENVIRONMENT=production
```

**Backend (.env)**:
```env
# Required
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-west1-gcp-free
PINECONE_INDEX_NAME=cognidocs-prod

# Optional
CORS_ORIGINS=https://your-frontend-domain.com
MAX_FILE_SIZE=10485760  # 10MB
LOG_LEVEL=INFO
```

## 🔒 Security Considerations

### SSL/TLS Configuration

1. **Frontend**: Automatic with Vercel/CloudFront
2. **Backend**: Configure SSL certificate in load balancer
3. **Custom Domains**: Use Let's Encrypt or AWS Certificate Manager

### CORS Configuration

Update `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Specific domain
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### API Rate Limiting

Add rate limiting middleware:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/query/")
@limiter.limit("10/minute")
async def query_documents(request: Request, query_request: QueryRequest):
    # ... existing code
```

## 📊 Monitoring and Logging

### Health Checks

The `/health` endpoint provides system status:
```json
{
  "status": "healthy",
  "documents_count": 42,
  "timestamp": "2025-01-09T10:30:00Z"
}
```

### Logging Configuration

Add structured logging:
```python
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Log queries for analytics
@app.post("/query/")
async def query_documents(request: QueryRequest):
    logger.info(f"Query received: {request.query[:100]}...")
    # ... process query
    logger.info(f"Query processed successfully")
```

### Performance Monitoring

Consider adding:
- **Application Performance Monitoring**: New Relic, DataDog
- **Error Tracking**: Sentry
- **Uptime Monitoring**: Pingdom, UptimeRobot

## 🚨 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Check `allow_origins` in FastAPI CORS middleware
   - Verify frontend API URL configuration

2. **File Upload Failures**
   - Check file size limits
   - Verify PDF format
   - Check backend logs for processing errors

3. **Slow Query Responses**
   - Monitor OpenAI API rate limits
   - Check Pinecone index performance
   - Consider caching frequent queries

4. **Memory Issues**
   - Increase container memory limits
   - Implement document chunking optimization
   - Add garbage collection for large uploads

### Debug Commands

```bash
# Check backend logs
docker-compose logs backend

# Test API endpoints
curl -X GET http://localhost:8000/health

# Check frontend build
cd frontend && npm run build

# Verify environment variables
docker-compose exec backend env | grep OPENAI
```

## 📈 Scaling Considerations

### Horizontal Scaling

1. **Load Balancing**: Use ALB/nginx for multiple backend instances
2. **Database**: Migrate to managed Pinecone or vector database cluster
3. **Caching**: Add Redis for frequent queries
4. **CDN**: Use CloudFront/CloudFlare for global distribution

### Performance Optimization

1. **Chunking Strategy**: Optimize document splitting parameters
2. **Embedding Caching**: Cache embeddings for repeated documents
3. **Query Optimization**: Implement semantic caching
4. **Async Processing**: Use background tasks for large document uploads

## 💰 Cost Optimization

### Development
- Use demo mode (no Pinecone costs)
- Vercel free tier for frontend
- Railway free tier for backend

### Production
- Monitor OpenAI API usage
- Optimize Pinecone index size
- Use reserved instances for predictable workloads
- Implement query caching to reduce API calls

---

**Need help with deployment? Contact woldamlak@yourcompany.com for professional deployment services.**

