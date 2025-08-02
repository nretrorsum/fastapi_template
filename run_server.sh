#!/usr/bin/env bash

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Load environment variables from .env file (corrected version)
load_env() {
    if [ -f .env ]; then
        print_info "Loading environment variables from .env file..."

        # Method 1: Filter comments and source
        set -a
        source <(grep -v '^#' .env | grep -v '^$')
        set +a

        print_success "Environment variables loaded"
    else
        print_warning ".env file not found, using default values"
    fi
}

# Check dependencies
check_dependencies() {
    print_info "Checking dependencies..."

    if ! command_exists uv; then
        print_error "uv is not installed. Please install it first:"
        print_error "curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi

    print_success "All dependencies are available"
}

# Check if API file exists
check_api_file() {
    if [ ! -f "src/api.py" ]; then
        print_error "API file not found at src/api.py"
        print_error "Please make sure the file exists at the correct location"
        exit 1
    fi
    print_success "API file found at src/api.py"
}

# Check if virtual environment exists and sync dependencies
setup_environment() {
    print_info "Setting up Python environment..."

    if [ ! -f "uv.lock" ]; then
        print_info "uv.lock not found, installing dependencies..."
        uv sync
    else
        print_info "Syncing dependencies from uv.lock..."
        uv sync --frozen
    fi

    print_success "Python environment ready"
}

# Wait for dependencies (database, redis) when running in Docker
wait_for_dependencies() {
    if [ "$ENVIRONMENT" = "docker" ]; then
        print_info "Running in Docker environment, waiting for dependencies..."

        # Wait for database
        print_info "Waiting for database connection..."
        timeout=30
        while [ $timeout -gt 0 ]; do
            if uv run python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'meal_db'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'password')
    )
    conn.close()
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" 2>/dev/null; then
                print_success "Database is ready"
                break
            fi
            timeout=$((timeout - 1))
            sleep 1
        done

        if [ $timeout -eq 0 ]; then
            print_error "Database connection timeout"
            exit 1
        fi

        # Wait for Redis
        print_info "Waiting for Redis connection..."
        timeout=30
        while [ $timeout -gt 0 ]; do
            if uv run python -c "
import redis
import os
try:
    r = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', '6379')),
        db=int(os.getenv('REDIS_DB', '0')),
        password=os.getenv('REDIS_PASSWORD', None) if os.getenv('REDIS_PASSWORD') else None
    )
    r.ping()
    print('Redis connection successful')
except Exception as e:
    print(f'Redis connection failed: {e}')
    exit(1)
" 2>/dev/null; then
                print_success "Redis is ready"
                break
            fi
            timeout=$((timeout - 1))
            sleep 1
        done

        if [ $timeout -eq 0 ]; then
            print_error "Redis connection timeout"
            exit 1
        fi
    fi
}

# Run database migrations
run_migrations() {
    if [ -f "/app/alembic.ini" ]; then
        if [ -d "/app/alembic" ] || [ -d "/app/migrations" ]; then
            print_info "Running database migrations..."

            uv run alembic -c /app/alembic.ini upgrade head || {
                print_error "Database migration failed"
                exit 1
            }

            print_success "Database migrations completed"
        else
            print_warning "Neither 'alembic' nor 'migrations' directory found, skipping migrations"
        fi
    else
        print_warning "alembic.ini not found, skipping migrations"
    fi
}

# Create necessary directories
create_directories() {
    print_info "Creating necessary directories..."
    mkdir -p logs
    mkdir -p tmp
    print_success "Directories created"
}

# Start the FastAPI server
start_server() {
    # Set default values
    APP_HOST=${APP_HOST:-0.0.0.0}
    APP_PORT=${APP_PORT:-8000}
    DEBUG=${DEBUG:-true}

    print_info "Starting FastAPI server..."
    print_info "Host: $APP_HOST"
    print_info "Port: $APP_PORT"
    print_info "Debug: $DEBUG"
    print_info "Environment: ${ENVIRONMENT:-development}"

    # Change to the src directory to make the module path work correctly
    cd src

    if [ "$DEBUG" = "true" ]; then
        print_info "Starting in development mode with hot reload..."
        # Use uvicorn directly with the module path
        exec uv run uvicorn api:app --host "$APP_HOST" --port "$APP_PORT" --reload --reload-dir ../src
    else
        print_info "Starting in production mode..."
        # Use uvicorn for production with multiple workers
        exec uv run uvicorn api:app --host "$APP_HOST" --port "$APP_PORT" --workers 4
    fi
}

# Handle shutdown gracefully
cleanup() {
    print_info "Shutting down server..."
    # Add any cleanup logic here
    exit 0
}

# Trap SIGTERM and SIGINT
trap cleanup SIGTERM SIGINT

# Main execution
main() {
    print_info "Starting Application Management..."

    load_env
    check_dependencies
    check_api_file
    setup_environment
    create_directories
    wait_for_dependencies
    run_migrations
    start_server
}

# Help function
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help, -h          Show this help message"
    echo "  --no-migrations     Skip database migrations"
    echo "  --production        Force production mode"
    echo "  --development       Force development mode"
    echo ""
    echo "Environment Variables:"
    echo "  APP_HOST            Server host (default: 0.0.0.0)"
    echo "  APP_PORT            Server port (default: 8000)"
    echo "  DEBUG               Enable debug mode (default: true)"
    echo "  ENVIRONMENT         Environment name (development/production/docker)"
    echo ""
}

# Parse command line arguments
SKIP_MIGRATIONS=false
FORCE_PRODUCTION=false
FORCE_DEVELOPMENT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --no-migrations)
            SKIP_MIGRATIONS=true
            shift
            ;;
        --production)
            FORCE_PRODUCTION=true
            export DEBUG=false
            shift
            ;;
        --development)
            FORCE_DEVELOPMENT=true
            export DEBUG=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Override migration skip if requested
if [ "$SKIP_MIGRATIONS" = "true" ]; then
    run_migrations() {
        print_warning "Skipping database migrations as requested"
    }
fi

# Run main function
main