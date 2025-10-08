#!/bin/bash
# docker-build.sh - Build script for Atomic RAG System Docker image

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TAG="atomic-rag"
PUSH=false
PLATFORM="linux/amd64"

# Help function
show_help() {
    echo "🐳 Docker Build Script for Atomic RAG System"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -g, --tag TAG         Image tag [default: atomic-rag]"
    echo "  -p, --push            Push image to registry after build"
    echo "  --platform PLATFORM  Target platform [default: linux/amd64]"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Build image"
    echo "  $0 -g atomic-rag-system              # Build with custom tag"
    echo "  $0 -p                                # Build and push"
    echo "  $0 --platform linux/arm64            # Build for ARM64"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--tag)
            TAG="$2"
            shift 2
            ;;
        -p|--push)
            PUSH=true
            shift
            ;;
        --platform)
            PLATFORM="$2"
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

echo -e "${BLUE}🐳 Building Atomic RAG System Docker Image${NC}"
echo -e "${BLUE}===========================================${NC}"
echo -e "Tag: ${YELLOW}$TAG${NC}"
echo -e "Platform: ${YELLOW}$PLATFORM${NC}"
echo -e "Push: ${YELLOW}$PUSH${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if .env file exists or MISTRAL_API_KEY is set
if [ ! -f ".env" ] && [ -z "$MISTRAL_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found and MISTRAL_API_KEY not set.${NC}"
    echo -e "${YELLOW}   Make sure to set MISTRAL_API_KEY environment variable or create .env file.${NC}"
    echo -e "${YELLOW}   Example: echo 'MISTRAL_API_KEY=your_key_here' > .env${NC}"
elif [ -f ".env" ]; then
    echo -e "${GREEN}✅ Found .env file${NC}"
elif [ -n "$MISTRAL_API_KEY" ]; then
    echo -e "${GREEN}✅ MISTRAL_API_KEY environment variable is set${NC}"
fi

# Build the image
echo -e "${BLUE}🔨 Building Docker image...${NC}"
if docker build --platform "$PLATFORM" -t "$TAG:latest" .; then
    echo -e "${GREEN}✅ Docker image built successfully!${NC}"
    echo -e "${GREEN}   Image: $TAG:latest${NC}"
else
    echo -e "${RED}❌ Docker build failed!${NC}"
    exit 1
fi

# Show image size
echo ""
echo -e "${BLUE}📊 Image Information:${NC}"
docker images "$TAG:latest" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# Push if requested
if [ "$PUSH" = true ]; then
    echo ""
    echo -e "${BLUE}🚀 Pushing image to registry...${NC}"
    if docker push "$TAG:latest"; then
        echo -e "${GREEN}✅ Image pushed successfully!${NC}"
    else
        echo -e "${RED}❌ Failed to push image!${NC}"
        exit 1
    fi
fi

# Show run commands
echo ""
echo -e "${BLUE}🚀 Run Commands:${NC}"
echo -e "${GREEN}Easy Run Script (Recommended):${NC}"
echo "  ./docker-run.sh                    # Basic run"
echo "  ./docker-run.sh -s                # With persistent storage"
echo "  ./docker-run.sh -s -d              # With storage and data"
echo ""
echo -e "${GREEN}Manual Docker Commands:${NC}"
echo "  docker run -p 8501:8501 -e MISTRAL_API_KEY=\$MISTRAL_API_KEY $TAG:latest"
echo "  docker run -p 8501:8501 -v \$(pwd)/storage:/app/storage -e MISTRAL_API_KEY=\$MISTRAL_API_KEY $TAG:latest"
echo "  docker run -p 8501:8501 -v \$(pwd)/data:/app/data:ro -v \$(pwd)/storage:/app/storage -e MISTRAL_API_KEY=\$MISTRAL_API_KEY $TAG:latest"
echo ""
echo -e "${GREEN}CLI Commands (override default):${NC}"
echo "  docker run -e MISTRAL_API_KEY=\$MISTRAL_API_KEY $TAG:latest poetry run python main.py --help"
echo "  docker run -e MISTRAL_API_KEY=\$MISTRAL_API_KEY $TAG:latest poetry run python main.py load --limit 10"

echo ""
echo -e "${GREEN}🎉 Build completed successfully!${NC}"
