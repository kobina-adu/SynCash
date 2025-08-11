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
        
        # Initialize Redis
        await init_redis()
        logger.info("Redis initialized")
        
        # Initialize metrics
        from src.monitoring.metrics import metrics
        metrics.init_metrics()
        logger.info("Metrics initialized")
        
        # Start database health monitoring
        from src.services.db_monitor import db_health_monitor
        import asyncio
        asyncio.create_task(db_health_monitor.start_monitoring(check_interval=30))
        logger.info("Database health monitoring started")
        
        logger.info("SyncCash Orchestrator started successfully")
        
    except Exception as e:
        logger.error("Failed to start application", exc_info=e)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down SyncCash Orchestrator...")
    
    try:
        # Stop database monitoring
        await db_health_monitor.stop_monitoring()
        logger.info("Database monitoring stopped")
        
        await close_redis()
        logger.info("Redis connections closed")
        
        await close_db()
        logger.info("Database connections closed")
        
        logger.info("SyncCash Orchestrator shutdown complete")
        
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
from src.api.v1 import health, payments, metrics as metrics_api
from src.monitoring.middleware import MetricsMiddleware, HealthCheckMiddleware
from src.monitoring.metrics import metrics
from src.services.db_monitor import db_health_monitor

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(payments.router, prefix="/api/v1", tags=["payments"])
app.include_router(metrics_api.router, tags=["monitoring"])

# Add monitoring middleware
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
