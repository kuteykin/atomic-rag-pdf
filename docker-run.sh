#!/bin/bash
# docker-run.sh - Easy run script for Atomic RAG System Docker container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TAG="atomic-rag"
PORT="8501"
STORAGE_MOUNT=false
DATA_MOUNT=false
ENV_FILE=""

# Help function
show_help() {
    echo "🐳 Docker Run Script for Atomic RAG System"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --tag TAG         Image tag [default: atomic-rag]"
    echo "  -p, --port PORT       Host port [default: 8501]"
    echo "  -s, --storage         Mount persistent storage"
    echo "  -d, --data            Mount PDF data directory"
    echo "  -e, --env-file FILE   Use environment file [default: .env]"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Basic run"
    echo "  $0 -s                                # With persistent storage"
    echo "  $0 -s -d                             # With storage and data"
    echo "  $0 -p 8502                          # Different port"
    echo "  $0 -e custom.env                    # Custom env file"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -s|--storage)
            STORAGE_MOUNT=true
            shift
            ;;
        -d|--data)
            DATA_MOUNT=true
            shift
            ;;
        -e|--env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Set default env file if not specified
if [ -z "$ENV_FILE" ]; then
    ENV_FILE=".env"
fi

echo -e "${BLUE}🐳 Running Atomic RAG System Docker Container${NC}"
echo -e "${BLUE}==============================================${NC}"
echo -e "Image: ${YELLOW}$TAG:latest${NC}"
echo -e "Port: ${YELLOW}$PORT:8501${NC}"
echo -e "Storage Mount: ${YELLOW}$STORAGE_MOUNT${NC}"
echo -e "Data Mount: ${YELLOW}$DATA_MOUNT${NC}"
echo -e "Env File: ${YELLOW}$ENV_FILE${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if image exists
if ! docker image inspect "$TAG:latest" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Image $TAG:latest not found. Building it first...${NC}"
    ./docker-build.sh -g "$TAG"
fi

# Check if MISTRAL_API_KEY is set
if [ -z "$MISTRAL_API_KEY" ] && [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ MISTRAL_API_KEY not set and $ENV_FILE not found!${NC}"
    echo -e "${YELLOW}   Please set MISTRAL_API_KEY environment variable or create $ENV_FILE file.${NC}"
    exit 1
fi

# Build docker run command
DOCKER_CMD="docker run -p $PORT:8501"

# Add environment variables
if [ -f "$ENV_FILE" ]; then
    echo -e "${GREEN}✅ Using environment file: $ENV_FILE${NC}"
    DOCKER_CMD="$DOCKER_CMD --env-file $ENV_FILE"
else
    echo -e "${GREEN}✅ Using MISTRAL_API_KEY from environment${NC}"
    DOCKER_CMD="$DOCKER_CMD -e MISTRAL_API_KEY=\$MISTRAL_API_KEY"
fi

# Add volume mounts
if [ "$STORAGE_MOUNT" = true ]; then
    echo -e "${GREEN}✅ Mounting persistent storage${NC}"
    DOCKER_CMD="$DOCKER_CMD -v \$(pwd)/storage:/app/storage"
fi

if [ "$DATA_MOUNT" = true ]; then
    echo -e "${GREEN}✅ Mounting PDF data directory${NC}"
    DOCKER_CMD="$DOCKER_CMD -v \$(pwd)/data:/app/data:ro"
fi

# Add image name
DOCKER_CMD="$DOCKER_CMD $TAG:latest"

echo ""
echo -e "${BLUE}🚀 Starting container...${NC}"
echo -e "${BLUE}Command: $DOCKER_CMD${NC}"
echo ""

# Execute the command
eval $DOCKER_CMD
