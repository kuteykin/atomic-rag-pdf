# Docker Deployment Guide

## 🐳 Docker Deployment for Atomic RAG System

This guide covers deploying the Atomic RAG System using a single optimized Docker container with both backend and Streamlit frontend.

## 📋 Prerequisites

- Docker Engine 20.10+
- MISTRAL_API_KEY environment variable

## 🚀 Quick Start

### 1. Environment Setup

Set the `MISTRAL_API_KEY` environment variable:
```bash
export MISTRAL_API_KEY=your_mistral_api_key_here
```

### 2. Build and Run

**Option A: Using Run Script (Recommended)**
```bash
# Build image first
./docker-build.sh

# Easy run with automatic MISTRAL_API_KEY handling
./docker-run.sh                    # Basic run
./docker-run.sh -s                # With persistent storage
./docker-run.sh -s -d              # With storage and data
./docker-run.sh -p 8502            # Different port
```

**Option B: Using Build Script**
```bash
# Build image
./docker-build.sh

# Build with custom tag
./docker-build.sh -g atomic-rag-system

# Build and push to registry
./docker-build.sh -p
```

**Option C: Direct Docker**
```bash
# Build image
docker build -t atomic-rag:latest .

# Run web interface (backend + frontend)
docker run -p 8501:8501 -e MISTRAL_API_KEY=$MISTRAL_API_KEY atomic-rag:latest

# Run with persistent storage
docker run -p 8501:8501 -v $(pwd)/storage:/app/storage -e MISTRAL_API_KEY=$MISTRAL_API_KEY atomic-rag:latest
```

## 🏗️ Single Container Architecture

### Features
- **Backend**: Complete RAG pipeline with 3 agents
- **Frontend**: Streamlit web interface
- **Database**: SQLite + Qdrant initialization
- **Size**: ~800MB optimized image
- **Security**: Non-root user, minimal attack surface

### Container Startup Process
1. Initialize SQLite and Qdrant databases
2. Start Streamlit web interface
3. Ready for PDF processing and search

## 🔧 Configuration

### Environment Variables

```bash
# Required
MISTRAL_API_KEY=your_api_key

# Optional
PYTHONUNBUFFERED=1
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Volume Mounts

```bash
# Persistent storage (recommended)
-v $(pwd)/storage:/app/storage

# PDF data (read-only)
-v $(pwd)/data:/app/data:ro

# Optional: Use environment file (if you have one)
# -v $(pwd)/.env:/app/.env:ro
```

## 🌐 Access Points

- **Web Interface**: http://localhost:8501
- **Health Check**: http://localhost:8501/_stcore/health

## 🛠️ Common Commands

### Build and Run
```bash
# Build image
./docker-build.sh

# Easy run (automatically handles MISTRAL_API_KEY)
./docker-run.sh                    # Basic run
./docker-run.sh -s                # With persistent storage
./docker-run.sh -s -d              # With storage and data
./docker-run.sh -p 8502            # Different port

# Manual run (requires MISTRAL_API_KEY)
docker run -p 8501:8501 -e MISTRAL_API_KEY=$MISTRAL_API_KEY atomic-rag:latest
docker run -p 8501:8501 -v $(pwd)/storage:/app/storage -e MISTRAL_API_KEY=$MISTRAL_API_KEY atomic-rag:latest
docker run -p 8501:8501 -v $(pwd)/data:/app/data:ro -v $(pwd)/storage:/app/storage -e MISTRAL_API_KEY=$MISTRAL_API_KEY atomic-rag:latest
```

### CLI Operations
```bash
# Override default command for CLI operations
docker run -e MISTRAL_API_KEY=$MISTRAL_API_KEY atomic-rag:latest poetry run python main.py --help

# Batch processing
docker run -e MISTRAL_API_KEY=$MISTRAL_API_KEY atomic-rag:latest poetry run python main.py load --limit 50

# Search queries
docker run -e MISTRAL_API_KEY=$MISTRAL_API_KEY atomic-rag:latest poetry run python main.py search "your query"

# Run tests
docker run -e MISTRAL_API_KEY=$MISTRAL_API_KEY atomic-rag:latest poetry run python test_basic.py
```

## 🔍 Monitoring & Logs

```bash
# View container logs
docker logs -f <container_id>

# Check container status
docker ps

# Monitor resources
docker stats <container_id>
```

## 🚨 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Use different port
   docker run -p 8502:8501 -e MISTRAL_API_KEY=$MISTRAL_API_KEY atomic-rag:latest
   ```

2. **Permission Issues**
   ```bash
   # Fix storage permissions
   sudo chown -R $USER:$USER ./storage
   ```

3. **API Key Not Set**
   ```bash
   # Set environment variable and run
   export MISTRAL_API_KEY=your_key_here
   docker run -e MISTRAL_API_KEY=$MISTRAL_API_KEY atomic-rag:latest
   ```

### Debug Mode

```bash
# Run with debug shell
docker run -it --entrypoint bash atomic-rag:latest

# Check Python environment
docker run atomic-rag:latest poetry run python --version
```

## 📈 Performance Optimization

### Resource Limits
```bash
# Run with memory limit
docker run -p 8501:8501 --memory=2g -e MISTRAL_API_KEY=$MISTRAL_API_KEY atomic-rag:latest

# Run with CPU limit
docker run -p 8501:8501 --cpus=1.0 -e MISTRAL_API_KEY=$MISTRAL_API_KEY atomic-rag:latest
```

### Multi-Architecture Builds
```bash
# Build for multiple architectures
./docker-build.sh --platform linux/amd64,linux/arm64
```

## 🔒 Security Considerations

- Non-root user (`appuser`)
- Read-only volume mounts where possible
- No unnecessary packages
- Health checks enabled
- Resource limits configurable

## 📝 Production Deployment

### Kubernetes Example
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: atomic-rag
spec:
  replicas: 2
  selector:
    matchLabels:
      app: atomic-rag
  template:
    metadata:
      labels:
        app: atomic-rag
    spec:
      containers:
      - name: atomic-rag
        image: atomic-rag:latest
        ports:
        - containerPort: 8501
        env:
        - name: MISTRAL_API_KEY
          valueFrom:
            secretKeyRef:
              name: mistral-secret
              key: api-key
        volumeMounts:
        - name: storage
          mountPath: /app/storage
      volumes:
      - name: storage
        persistentVolumeClaim:
          claimName: atomic-rag-storage
```

## 🎯 Best Practices

1. **Use specific tags** instead of `latest`
2. **Mount volumes** for persistent data
3. **Set resource limits** in production
4. **Use health checks** for monitoring
5. **Keep images updated** regularly
6. **Scan images** for vulnerabilities
7. **Use single container** for simplicity

## 📚 Additional Resources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Streamlit Deployment](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app)
- [Poetry Docker Integration](https://python-poetry.org/docs/#docker)