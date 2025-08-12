"""
SyncCash Orchestrator Service - Main Application
Handles payment workflow orchestration across multiple mobile money providers
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
from contextlib import asynccontextmanager

from src.config.settings import get_settings
from src.core.database import init_db
from src.core.redis_client import init_redis

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting SyncCash Orchestrator...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")
        
        # Start database health monitoring
        from src.services.db_monitor import db_health_monitor
        await db_health_monitor.start_monitoring()
        logger.info("Database health monitoring started")
        
        # Initialize Redis connection
        await redis_client.initialize()
        logger.info("Redis connection initialized")
        
        # Test database connection
        await test_connection()
        logger.info("Database connection verified")
        
        # Initialize payment providers
        settings = get_settings()
        provider_configs = settings.get_provider_configs()
        
        from src.providers import initialize_provider_manager
        provider_manager = initialize_provider_manager(provider_configs)
        logger.info("Payment providers initialized")
        
        # Authenticate all providers
        auth_results = await provider_manager.authenticate_all()
        successful_auths = sum(1 for success in auth_results.values() if success)
        logger.info(f"Provider authentication completed: {successful_auths}/{len(auth_results)} successful")
        
        # Initialize BetterAuth service
        from src.services.betterauth import get_betterauth_service
        betterauth_service = get_betterauth_service()
        
        # Test BetterAuth connection
        health_check = await betterauth_service.health_check()
        if health_check["status"] == "healthy":
            logger.info("BetterAuth service connection verified")
        else:
            logger.warning("BetterAuth service health check failed", 
                          error=health_check.get("error"))
        
        logger.info("SyncCash Orchestrator started successfully")
        
    except Exception as e:
        logger.error("Failed to start application", exc_info=e)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down SyncCash Orchestrator...")
    
    try:
        # Close provider connections
        from src.providers import get_provider_manager
        try:
            provider_manager = get_provider_manager()
            await provider_manager.close_all()
            logger.info("Provider connections closed")
        except RuntimeError:
            # Provider manager not initialized
            pass
        
        # Stop database health monitoring
        await db_health_monitor.stop_monitoring()
        logger.info("Database health monitoring stopped")
        
        # Close BetterAuth service
        try:
            from src.services.betterauth import get_betterauth_service
            betterauth_service = get_betterauth_service()
            await betterauth_service.close()
            logger.info("BetterAuth service closed")
        except Exception as e:
            logger.warning("Error closing BetterAuth service", error=str(e))
        
        # Close Redis connection
        await redis_client.close()
        logger.info("Redis connection closed")
        
        # Close database connections
        await close_db()
        logger.info("Database connections closed")
        
        logger.info("SyncCash Orchestrator shut down successfully")
        
    except Exception as e:
        logger.error("Error during shutdown", exc_info=e)

# Create FastAPI application
app = FastAPI(
    title="SyncCash Orchestrator",
    description="Payment orchestration service for unified multi-wallet transactions",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Global exception handler",
        exc_info=exc,
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": time.time()
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "synccash-orchestrator",
        "timestamp": time.time(),
        "version": "1.0.0"
    }

# Include API routers
from src.api.v1 import health, payments, metrics as metrics_api, resilience, webhooks
from src.monitoring.middleware import MetricsMiddleware, HealthCheckMiddleware
from src.monitoring.metrics import metrics
from src.services.db_monitor import db_health_monitor
from src.middleware.resilience import ResilienceMiddleware
from src.providers import initialize_provider_manager

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(payments.router, prefix="/api/v1", tags=["payments"])
app.include_router(resilience.router, prefix="/api/v1", tags=["resilience"])
app.include_router(webhooks.router, prefix="/api/v1", tags=["webhooks"])
app.include_router(metrics_api.router, tags=["monitoring"])

# Add resilience and monitoring middleware (order matters - resilience first)
app.add_middleware(ResilienceMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(HealthCheckMiddleware)

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "SyncCash Orchestrator",
        "version": "1.0.0",
        "status": "running",
        "timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
