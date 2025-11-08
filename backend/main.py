from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import tempfile
import os
import asyncio
from pathlib import Path
import logging


# Import your existing modules
from app import (
    FAISSRAGSystem, 
    PromptManager, 
    extract_text_from_pdf, 
    extract_text_from_pptx,
    analyze_pitch_deck_with_rag
)

# Load environment variables from .env file


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Pitch Deck Analyzer API",
    description="RAG-powered pitch deck analysis for investment managers",
    version="1.0.0"
)

# CORS middleware for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class AnalysisRequest(BaseModel):
    content: str
    openai_api_key: Optional[str] = None

class AnalysisResponse(BaseModel):
    success: bool
    analysis: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[dict] = None

class HealthResponse(BaseModel):
    status: str
    message: str
    components: dict

# Global instances (initialized on startup)
rag_system: Optional[FAISSRAGSystem] = None
prompt_manager: Optional[PromptManager] = None

@app.on_event("startup")
async def startup_event():
    """Initialize RAG system and prompt manager on startup"""
    global rag_system, prompt_manager
    
    try:
        logger.info("Initializing RAG system...")
        rag_system = FAISSRAGSystem()
        
        logger.info("Initializing prompt manager...")
        prompt_manager = PromptManager()
        
        logger.info("Backend initialization complete")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

def get_openai_key(api_key: Optional[str] = None) -> str:
    """Get OpenAI API key from request or environment"""
    if api_key:
        return api_key
    
    env_key = os.getenv('OPENAI_API_KEY')
    if env_key:
        return env_key
        
    raise HTTPException(
        status_code=400,
        detail="OpenAI API key required. Provide in request or set OPENAI_API_KEY environment variable."
    )

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Pitch Deck Analyzer API is running",
        components={
            "rag_system": "initialized" if rag_system else "not_initialized",
            "prompt_manager": "initialized" if prompt_manager else "not_initialized"
        }
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check"""
    components = {}
    
    # Check RAG system
    try:
        if rag_system and rag_system.index is not None:
            components["rag_system"] = "healthy"
        else:
            components["rag_system"] = "not_initialized"
    except Exception as e:
        components["rag_system"] = f"error: {str(e)}"
    
    # Check prompt manager
    try:
        if prompt_manager and prompt_manager.prompts:
            components["prompt_manager"] = "healthy"
        else:
            components["prompt_manager"] = "not_initialized"
    except Exception as e:
        components["prompt_manager"] = f"error: {str(e)}"
    
    # Check if prompts.json exists
    components["prompts_config"] = "exists" if Path("prompts.json").exists() else "missing"
    
    status = "healthy" if all("error" not in v for v in components.values()) else "unhealthy"
    
    return HealthResponse(
        status=status,
        message="System health check complete",
        components=components
    )

@app.post("/analyze/upload", response_model=AnalysisResponse)
async def analyze_uploaded_file(
    file: UploadFile = File(...),
    openai_api_key: Optional[str] = None
):
    """Analyze uploaded pitch deck file (PDF or PPTX)"""
    
    # Validate file type
    allowed_extensions = {'.pdf', '.pptx'}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Get OpenAI API key
    try:
        api_key = get_openai_key(openai_api_key)
    except HTTPException as e:
        return AnalysisResponse(success=False, error=str(e.detail))
    
    # Process file
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Extract text based on file type
            if file_extension == '.pdf':
                extracted_text = extract_text_from_pdf(tmp_file_path)
            elif file_extension == '.pptx':
                extracted_text = extract_text_from_pptx(tmp_file_path)
            
            # Validate extracted content
            if len(extracted_text.strip()) < 50:
                return AnalysisResponse(
                    success=False,
                    error="Insufficient content extracted from file. Please check if the file contains readable text."
                )
            
            # Run analysis
            analysis = await run_analysis_async(extracted_text, api_key)
            
            return AnalysisResponse(
                success=True,
                analysis=analysis,
                metadata={
                    "filename": file.filename,
                    "file_size": len(content),
                    "extracted_text_length": len(extracted_text),
                    "file_type": file_extension
                }
            )
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return AnalysisResponse(
            success=False,
            error=f"Analysis failed: {str(e)}"
        )

@app.post("/analyze/text", response_model=AnalysisResponse)
async def analyze_text_content(
    request: AnalysisRequest
):
    """Analyze pitch deck from raw text content"""
    
    # Validate input
    if not request.content or len(request.content.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Content too short. Please provide substantial pitch deck content."
        )
    
    # Get OpenAI API key
    try:
        api_key = get_openai_key(request.openai_api_key)
    except HTTPException as e:
        return AnalysisResponse(success=False, error=str(e.detail))
    
    try:
        # Run analysis
        analysis = await run_analysis_async(request.content, api_key)
        
        return AnalysisResponse(
            success=True,
            analysis=analysis,
            metadata={
                "content_length": len(request.content),
                "input_type": "text"
            }
        )
        
    except Exception as e:
        logger.error(f"Text analysis error: {e}")
        return AnalysisResponse(
            success=False,
            error=f"Analysis failed: {str(e)}"
        )

async def run_analysis_async(content: str, api_key: str) -> str:
    """Run analysis in async context"""
    loop = asyncio.get_event_loop()
    
    # Run the blocking analysis function in thread pool
    analysis = await loop.run_in_executor(
        None,
        analyze_pitch_deck_with_rag,
        content,
        api_key,
        prompt_manager,
        rag_system
    )
    
    return analysis

@app.get("/knowledge/topics")
async def get_knowledge_topics():
    """Get available knowledge base topics"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    topics = []
    for item in rag_system.knowledge_base:
        topics.append({
            "id": item["id"],
            "topic": item["topic"],
            "category": item["category"],
            "tags": item["tags"]
        })
    
    return {"topics": topics}

@app.post("/knowledge/search")
async def search_knowledge(query: str, top_k: int = 5):
    """Search knowledge base directly"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        results = rag_system.retrieve_knowledge(query, top_k=top_k)
        return {
            "query": query,
            "results": results,
            "total_found": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/config/prompts")
async def get_prompt_config():
    """Get current prompt configuration"""
    if not prompt_manager:
        raise HTTPException(status_code=503, detail="Prompt manager not initialized")
    
    return prompt_manager.prompts

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "detail": "The requested endpoint does not exist"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "An unexpected error occurred"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )