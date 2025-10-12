"""
FastAPI application for the Reddit Sentiment Analyzer.

This module provides the main FastAPI application with all endpoints,
middleware, and configuration for the sentiment analysis service.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..core.analyzer import RedditSentimentAnalyzer
from ..data.models import (
    BrandData, AnalysisResult, BatchAnalysisRequest, BatchAnalysisResponse,
    APIResponse, SearchQuery, ScrapingConfig, ProcessingConfig
)
from ..utils.logging import get_logger, CorrelationContext, generate_correlation_id
from ..config.settings import get_settings, get_cors_settings, get_api_settings

logger = get_logger(__name__)

# Global analyzer instance
analyzer: RedditSentimentAnalyzer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global analyzer
    
    # Startup
    logger.info("Starting Reddit Sentiment Analyzer API")
    
    try:
        # Initialize analyzer
        analyzer = RedditSentimentAnalyzer()
        await analyzer.initialize()
        
        logger.info("API startup completed successfully")
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down Reddit Sentiment Analyzer API")
        
        if analyzer:
            await analyzer.close()
        
        logger.info("API shutdown completed")


# Create FastAPI application
app = FastAPI(
    title="Reddit Sentiment Analyzer",
    description="Professional-grade brand sentiment analysis from Reddit discussions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Get settings
settings = get_settings()
cors_settings = get_cors_settings()
api_settings = get_api_settings()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_settings.origins,
    allow_credentials=cors_settings.credentials,
    allow_methods=cors_settings.methods,
    allow_headers=cors_settings.headers,
)

# Add trusted host middleware
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure with actual hosts in production
    )


# Dependency to get analyzer instance
async def get_analyzer() -> RedditSentimentAnalyzer:
    """Get the analyzer instance."""
    if analyzer is None:
        raise HTTPException(status_code=503, detail="Analyzer not initialized")
    return analyzer


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse(
            success=False,
            message=exc.detail,
            error=f"HTTP {exc.status_code}"
        ).dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation exceptions."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content=APIResponse(
            success=False,
            message="Validation error",
            error=str(exc.errors())
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=APIResponse(
            success=False,
            message="Internal server error",
            error="An unexpected error occurred"
        ).dict()
    )


# Health check endpoint
@app.get("/health", response_model=APIResponse)
async def health_check():
    """Health check endpoint."""
    return APIResponse(
        success=True,
        message="Service is healthy",
        data={"status": "healthy", "version": "1.0.0"}
    )


# Root endpoint
@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint with API information."""
    return APIResponse(
        success=True,
        message="Reddit Sentiment Analyzer API",
        data={
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health"
        }
    )


# Single brand analysis endpoint
@app.post("/analyze/single", response_model=APIResponse)
async def analyze_single_brand(
    brand_data: BrandData,
    background_tasks: BackgroundTasks,
    analyzer_instance: RedditSentimentAnalyzer = Depends(get_analyzer)
):
    """
    Analyze sentiment for a single brand.
    
    Args:
        brand_data: Brand information
        background_tasks: Background tasks for async processing
        analyzer_instance: Analyzer instance
        
    Returns:
        Analysis result
    """
    correlation_id = generate_correlation_id()
    
    with CorrelationContext(correlation_id):
        logger.info(f"Starting single brand analysis", brand=brand_data.name)
        
        try:
            # Perform analysis
            result = await analyzer_instance.analyze_brand(brand_data)
            
            logger.info(f"Single brand analysis completed", brand=brand_data.name)
            
            return APIResponse(
                success=True,
                message="Analysis completed successfully",
                data=result.dict()
            )
            
        except Exception as e:
            logger.error(f"Error in single brand analysis: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Analysis failed: {str(e)}"
            )


# Batch analysis endpoint
@app.post("/analyze/batch", response_model=APIResponse)
async def analyze_batch_brands(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    analyzer_instance: RedditSentimentAnalyzer = Depends(get_analyzer)
):
    """
    Analyze sentiment for multiple brands in batch.
    
    Args:
        request: Batch analysis request
        background_tasks: Background tasks for async processing
        analyzer_instance: Analyzer instance
        
    Returns:
        Batch analysis results
    """
    correlation_id = generate_correlation_id()
    
    with CorrelationContext(correlation_id):
        logger.info(f"Starting batch analysis", brand_count=len(request.brands))
        
        try:
            import time
            start_time = time.time()
            
            # Perform batch analysis
            results = await analyzer_instance.analyze_brands_batch(request.brands)
            
            processing_time = time.time() - start_time
            
            # Create response
            response = BatchAnalysisResponse(
                total_brands=len(request.brands),
                successful_analyses=len(results),
                failed_analyses=len(request.brands) - len(results),
                results=results,
                errors=[],  # TODO: Track individual errors
                processing_time=processing_time
            )
            
            logger.info(f"Batch analysis completed", 
                       total=len(request.brands),
                       successful=len(results),
                       processing_time=processing_time)
            
            return APIResponse(
                success=True,
                message="Batch analysis completed",
                data=response.dict()
            )
            
        except Exception as e:
            logger.error(f"Error in batch analysis: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Batch analysis failed: {str(e)}"
            )


# Google Sheets analysis endpoint
@app.post("/analyze/sheets", response_model=APIResponse)
async def analyze_from_google_sheets(
    sheet_id: str,
    output_sheet_id: str = None,
    background_tasks: BackgroundTasks = None,
    analyzer_instance: RedditSentimentAnalyzer = Depends(get_analyzer)
):
    """
    Analyze brands from a Google Sheet.
    
    Args:
        sheet_id: Google Sheet ID containing brand data
        output_sheet_id: Optional output sheet ID for results
        background_tasks: Background tasks for async processing
        analyzer_instance: Analyzer instance
        
    Returns:
        Analysis results
    """
    correlation_id = generate_correlation_id()
    
    with CorrelationContext(correlation_id):
        logger.info(f"Starting Google Sheets analysis", sheet_id=sheet_id)
        
        try:
            # Perform analysis from Google Sheets
            results = await analyzer_instance.analyze_from_google_sheets(
                sheet_id=sheet_id,
                output_sheet_id=output_sheet_id
            )
            
            logger.info(f"Google Sheets analysis completed", 
                       sheet_id=sheet_id,
                       result_count=len(results))
            
            return APIResponse(
                success=True,
                message="Google Sheets analysis completed",
                data={
                    "sheet_id": sheet_id,
                    "output_sheet_id": output_sheet_id,
                    "results": [result.dict() for result in results]
                }
            )
            
        except Exception as e:
            logger.error(f"Error in Google Sheets analysis: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Google Sheets analysis failed: {str(e)}"
            )


# Search endpoint
@app.post("/search", response_model=APIResponse)
async def search_reddit_content(
    query: SearchQuery,
    analyzer_instance: RedditSentimentAnalyzer = Depends(get_analyzer)
):
    """
    Search for Reddit content using Google Search.
    
    Args:
        query: Search query parameters
        analyzer_instance: Analyzer instance
        
    Returns:
        Search results
    """
    correlation_id = generate_correlation_id()
    
    with CorrelationContext(correlation_id):
        logger.info(f"Starting Reddit search", query=query.query)
        
        try:
            # Generate search query
            search_query = f"site:reddit.com {query.query}"
            
            # Search for Reddit URLs
            reddit_urls = await analyzer_instance._search_reddit_urls(search_query)
            
            logger.info(f"Reddit search completed", 
                       query=query.query,
                       url_count=len(reddit_urls))
            
            return APIResponse(
                success=True,
                message="Search completed successfully",
                data={
                    "query": query.query,
                    "reddit_urls": reddit_urls,
                    "url_count": len(reddit_urls)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in Reddit search: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Search failed: {str(e)}"
            )


# Configuration endpoint
@app.get("/config", response_model=APIResponse)
async def get_configuration():
    """
    Get current configuration (without sensitive data).
    
    Returns:
        Configuration information
    """
    return APIResponse(
        success=True,
        message="Configuration retrieved",
        data={
            "environment": settings.environment,
            "debug": settings.debug,
            "features": settings.features.dict(),
            "api": {
                "host": api_settings.host,
                "port": api_settings.port,
                "workers": api_settings.workers
            }
        }
    )


# Metrics endpoint
@app.get("/metrics", response_model=APIResponse)
async def get_metrics():
    """
    Get application metrics.
    
    Returns:
        Application metrics
    """
    # TODO: Implement actual metrics collection
    return APIResponse(
        success=True,
        message="Metrics retrieved",
        data={
            "uptime": "N/A",  # TODO: Calculate actual uptime
            "requests_total": 0,  # TODO: Track request count
            "analysis_count": 0,  # TODO: Track analysis count
            "error_count": 0  # TODO: Track error count
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=api_settings.host,
        port=api_settings.port,
        reload=api_settings.reload,
        workers=1 if api_settings.reload else api_settings.workers
    )