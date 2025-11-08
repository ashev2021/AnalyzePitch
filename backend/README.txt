# AnalyzePitch Backend

A FastAPI-based backend service for pitch analysis using AI-powered embeddings and semantic search.

## Features

- **FastAPI Framework**: High-performance async API
- **Sentence Transformers**: Generate embeddings for semantic search
- **FAISS Vector Database**: Efficient similarity search
- **OpenAI Integration**: AI-powered analysis
- **Docker Support**: Containerized deployment

## Prerequisites

- Python 3.12.10
- pip (Python package manager)
- Virtual environment (recommended)

## Installation

### 1. Clone the Repository

```bash
cd AnalyzePitch/backend
```

### 2. Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration

### Setting Environment Variables in Terminal
**PowerShell:**
```powershell
$env:OPENAI_API_KEY = "your_api_key_here"
```

**Bash:**
```bash
export OPENAI_API_KEY="your_api_key_here"
```

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Log Level
LOG_LEVEL=INFO
```






## Running the Application

### Development Server

```bash
# Using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Or using Python
python main.py
```

The API will be available at `http://localhost:8000`

### API Documentation

Once running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc




## Project Structure

```
backend/
├── main.py                 # Application entry point
├── app.py                  # Core application logic
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├                
├── .env.example          # Example environment file
├── faiss_indexes/        # FAISS vector database storage
└── README.md             # This file
```

## API Endpoints

### Health Check
```
GET /health
```
Returns the health status of the API.

### Additional Endpoints
See `/docs` for complete API documentation.

## Dependencies

Key dependencies:
- `fastapi==0.104.1` - Web framework
- `uvicorn==0.24.0` - ASGI server
- `sentence-transformers>=2.7.0` - Embeddings generation
- `faiss-cpu` - Vector similarity search
- `openai==1.3.0` - OpenAI API client
- `numpy>=1.26.0` - Numerical computing
- `python-multipart==0.0.6` - File upload support

## Troubleshooting

### ImportError with sentence-transformers

If you see `cannot import name 'cached_download'`:
```bash
pip install --upgrade sentence-transformers>=2.7.0
```

### NumPy compatibility issues

For Python 3.12, ensure numpy >= 1.26.0:
```bash
pip install "numpy>=1.26.0"
```



## Development

### Installing Development Dependencies

```bash
pip install pytest pytest-asyncio httpx
```

### Running Tests

```bash
cd AnalyzePitch/backend/Tests
pytest test_app.py

```


## LLM as a  judge evals
```bash
python test_llm_judge.py SamplePitch.pdf SamplePitch-analysis.md

## Production Considerations

1. **Security**: Never expose API keys in code or commits
2. **HTTPS**: Use reverse proxy (nginx) with SSL in production
3. **Rate Limiting**: Implement rate limiting for API endpoints
4. **Monitoring**: Add logging and monitoring solutions
5. **Scaling**: Use multiple workers with uvicorn or gunicorn

## Support

For issues and questions, please open an issue in the repository.

## License

[Your License Here]