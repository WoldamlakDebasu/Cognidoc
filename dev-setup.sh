#!/bin/bash

# CogniDocs Development Setup Script
# This script helps you get CogniDocs running quickly

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

# Banner
echo -e "${BLUE}"
cat << "EOF"
   ____                  _ ____                
  / ___|___   __ _ _ __ (_)  _ \  ___   ___ ___ 
 | |   / _ \ / _` | '_ \| | | | |/ _ \ / __/ __|
 | |__| (_) | (_| | | | | | |_| | (_) | (__\__ \
  \____\___/ \__, |_| |_|_|____/ \___/ \___|___/
             |___/                             
             
Enterprise RAG Engine - Development Setup
EOF
echo -e "${NC}"

# Main menu
echo "Choose your setup option:"
echo "1. 🚀 Quick Start (Development)"
echo "2. 🐳 Docker Setup"
echo "3. 🔧 Manual Setup"
echo "4. 📊 Status Check"
echo "5. 🛑 Stop Services"
echo "6. 🧹 Clean & Reset"
echo ""
read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        log_info "Starting Quick Development Setup..."
        
        # Check prerequisites
        log_info "Checking prerequisites..."
        check_command "node"
        check_command "npm"
        check_command "python3"
        check_command "pip"
        
        # Setup backend
        log_info "Setting up backend..."
        cd backend
        
        if [ ! -f ".env" ]; then
            log_info "Creating backend .env file..."
            cp .env.example .env
            log_warning "Please edit backend/.env with your API keys if you have them"
        fi
        
        log_info "Installing Python dependencies..."
        pip install -r requirements.txt
        
        log_info "Starting backend server..."
        python main.py &
        BACKEND_PID=$!
        echo $BACKEND_PID > ../backend.pid
        
        cd ..
        
        # Setup frontend
        log_info "Setting up frontend..."
        cd frontend
        
        log_info "Installing Node.js dependencies..."
        npm install
        
        log_info "Starting frontend server..."
        npm run dev &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > ../frontend.pid
        
        cd ..
        
        log_success "Development servers started!"
        log_info "Frontend: http://localhost:3000"
        log_info "Backend API: http://localhost:8000"
        log_info "API Docs: http://localhost:8000/docs"
        log_warning "Press Ctrl+C to stop servers"
        
        # Wait for interrupt
        trap 'log_info "Stopping servers..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f backend.pid frontend.pid; exit 0' INT
        wait
        ;;
        
    2)
        log_info "Starting Docker Setup..."
        check_command "docker"
        check_command "docker-compose"
        
        log_info "Building and starting services with Docker..."
        docker-compose up --build -d
        
        log_success "Docker services started!"
        log_info "Frontend: http://localhost:3000"
        log_info "Backend API: http://localhost:8000"
        log_info "Use 'docker-compose logs -f' to view logs"
        ;;
        
    3)
        log_info "Manual Setup Instructions:"
        echo ""
        echo "Backend Setup:"
        echo "1. cd backend"
        echo "2. pip install -r requirements.txt"
        echo "3. cp .env.example .env"
        echo "4. Edit .env with your API keys"
        echo "5. python main.py"
        echo ""
        echo "Frontend Setup:"
        echo "1. cd frontend"
        echo "2. npm install"
        echo "3. npm run dev"
        echo ""
        log_info "Both servers will be available as mentioned above"
        ;;
        
    4)
        log_info "Checking service status..."
        
        # Check if running in Docker
        if docker-compose ps | grep -q "cognidocs"; then
            log_info "Docker services status:"
            docker-compose ps
        fi
        
        # Check local development servers
        if [ -f "backend.pid" ]; then
            BACKEND_PID=$(cat backend.pid)
            if ps -p $BACKEND_PID > /dev/null; then
                log_success "Backend server is running (PID: $BACKEND_PID)"
            else
                log_warning "Backend PID file exists but process is not running"
                rm -f backend.pid
            fi
        else
            log_warning "Backend server is not running (development mode)"
        fi
        
        if [ -f "frontend.pid" ]; then
            FRONTEND_PID=$(cat frontend.pid)
            if ps -p $FRONTEND_PID > /dev/null; then
                log_success "Frontend server is running (PID: $FRONTEND_PID)"
            else
                log_warning "Frontend PID file exists but process is not running"
                rm -f frontend.pid
            fi
        else
            log_warning "Frontend server is not running (development mode)"
        fi
        
        # Test endpoints
        log_info "Testing endpoints..."
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            log_success "Backend API is responding"
        else
            log_warning "Backend API is not responding"
        fi
        
        if curl -f http://localhost:3000 >/dev/null 2>&1; then
            log_success "Frontend is responding"
        else
            log_warning "Frontend is not responding"
        fi
        ;;
        
    5)
        log_info "Stopping services..."
        
        # Stop Docker services
        if docker-compose ps | grep -q "cognidocs"; then
            log_info "Stopping Docker services..."
            docker-compose down
        fi
        
        # Stop development servers
        if [ -f "backend.pid" ]; then
            BACKEND_PID=$(cat backend.pid)
            kill $BACKEND_PID 2>/dev/null || true
            rm -f backend.pid
            log_success "Backend server stopped"
        fi
        
        if [ -f "frontend.pid" ]; then
            FRONTEND_PID=$(cat frontend.pid)
            kill $FRONTEND_PID 2>/dev/null || true
            rm -f frontend.pid
            log_success "Frontend server stopped"
        fi
        
        log_success "All services stopped"
        ;;
        
    6)
        log_warning "This will clean all data and reset the application"
        read -p "Are you sure? (y/N): " confirm
        if [[ $confirm =~ ^[Yy]$ ]]; then
            log_info "Cleaning and resetting..."
            
            # Stop services first
            docker-compose down -v 2>/dev/null || true
            
            # Clean Docker
            docker system prune -f 2>/dev/null || true
            
            # Clean development files
            rm -f backend.pid frontend.pid
            rm -rf backend/__pycache__ backend/.pytest_cache
            rm -rf frontend/.next frontend/node_modules/.cache
            
            # Clean uploads
            rm -rf backend/uploads/*
            
            log_success "Cleanup completed"
        else
            log_info "Cleanup cancelled"
        fi
        ;;
        
    *)
        log_error "Invalid choice. Please select 1-6."
        exit 1
        ;;
esac
