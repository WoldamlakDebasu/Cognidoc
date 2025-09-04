#!/bin/bash

# CogniDocs Development Script
# Usage: ./scripts/dev.sh [command]

set -e

PROJECT_NAME="CogniDocs"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists node; then
        print_error "Node.js is not installed. Please install Node.js 18+ and try again."
        exit 1
    fi
    
    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install Python 3.8+ and try again."
        exit 1
    fi
    
    if ! command_exists pip3; then
        print_error "pip3 is not installed. Please install pip3 and try again."
        exit 1
    fi
    
    print_success "All prerequisites are installed."
}

# Install dependencies
install_deps() {
    print_status "Installing dependencies..."
    
    # Backend dependencies
    print_status "Installing Python dependencies..."
    cd "$PROJECT_DIR/backend"
    pip3 install -r requirements.txt
    
    # Frontend dependencies
    print_status "Installing Node.js dependencies..."
    cd "$PROJECT_DIR/frontend"
    npm install
    
    print_success "All dependencies installed successfully."
}

# Start development servers
start_dev() {
    print_status "Starting development servers..."
    
    # Create logs directory
    mkdir -p "$PROJECT_DIR/logs"
    
    # Start backend
    print_status "Starting backend server..."
    cd "$PROJECT_DIR/backend"
    python3 main.py > "../logs/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "../logs/backend.pid"
    
    # Wait for backend to start
    sleep 5
    
    # Check if backend is running
    if ! curl -s http://localhost:8000/health > /dev/null; then
        print_error "Backend failed to start. Check logs/backend.log for details."
        exit 1
    fi
    
    print_success "Backend started on http://localhost:8000"
    
    # Start frontend
    print_status "Starting frontend server..."
    cd "$PROJECT_DIR/frontend"
    npm run dev > "../logs/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "../logs/frontend.pid"
    
    # Wait for frontend to start
    sleep 10
    
    # Check if frontend is running
    if ! curl -s http://localhost:3000 > /dev/null; then
        print_error "Frontend failed to start. Check logs/frontend.log for details."
        exit 1
    fi
    
    print_success "Frontend started on http://localhost:3000"
    print_success "Development servers are running!"
    print_status "Press Ctrl+C to stop both servers"
    
    # Wait for user interrupt
    trap 'stop_dev' INT
    while true; do
        sleep 1
    done
}

# Stop development servers
stop_dev() {
    print_status "Stopping development servers..."
    
    # Stop backend
    if [ -f "$PROJECT_DIR/logs/backend.pid" ]; then
        BACKEND_PID=$(cat "$PROJECT_DIR/logs/backend.pid")
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            print_success "Backend stopped"
        fi
        rm -f "$PROJECT_DIR/logs/backend.pid"
    fi
    
    # Stop frontend
    if [ -f "$PROJECT_DIR/logs/frontend.pid" ]; then
        FRONTEND_PID=$(cat "$PROJECT_DIR/logs/frontend.pid")
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            print_success "Frontend stopped"
        fi
        rm -f "$PROJECT_DIR/logs/frontend.pid"
    fi
    
    print_success "All servers stopped"
}

# Build for production
build_prod() {
    print_status "Building for production..."
    
    # Build frontend
    print_status "Building frontend..."
    cd "$PROJECT_DIR/frontend"
    npm run build
    
    print_success "Production build completed"
}

# Run with Docker
run_docker() {
    print_status "Starting with Docker..."
    
    cd "$PROJECT_DIR"
    docker-compose up --build
}

# Show status
show_status() {
    print_status "Checking service status..."
    
    # Check backend
    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "Backend is running on http://localhost:8000"
    else
        print_warning "Backend is not running"
    fi
    
    # Check frontend
    if curl -s http://localhost:3000 > /dev/null; then
        print_success "Frontend is running on http://localhost:3000"
    else
        print_warning "Frontend is not running"
    fi
}

# Clean up
clean() {
    print_status "Cleaning up..."
    
    # Stop any running servers
    stop_dev
    
    # Clean Python cache
    find "$PROJECT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # Clean Node.js cache
    cd "$PROJECT_DIR/frontend"
    rm -rf .next node_modules/.cache 2>/dev/null || true
    
    # Clean logs
    rm -rf "$PROJECT_DIR/logs" 2>/dev/null || true
    
    print_success "Cleanup completed"
}

# Show help
show_help() {
    echo "CogniDocs Development Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  install     Install all dependencies"
    echo "  dev         Start development servers"
    echo "  stop        Stop development servers"
    echo "  build       Build for production"
    echo "  docker      Run with Docker"
    echo "  status      Show service status"
    echo "  clean       Clean up cache and temporary files"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 install     # Install dependencies"
    echo "  $0 dev         # Start development"
    echo "  $0 docker      # Run with Docker"
}

# Main script logic
main() {
    case "${1:-dev}" in
        "check")
            check_prerequisites
            ;;
        "install")
            check_prerequisites
            install_deps
            ;;
        "dev")
            check_prerequisites
            start_dev
            ;;
        "stop")
            stop_dev
            ;;
        "build")
            check_prerequisites
            build_prod
            ;;
        "docker")
            run_docker
            ;;
        "status")
            show_status
            ;;
        "clean")
            clean
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
