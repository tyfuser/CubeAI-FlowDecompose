"""
FastAPI application for the Video Shooting Assistant.

Main application entry point with middleware configuration.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from configs.settings import settings
from src.api.routes import router
from src.api.realtime_routes import router as realtime_router, router_v1 as realtime_router_v1
from src.api.auth import rate_limiter


# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Video Shooting Assistant API")
    yield
    logger.info("Shutting down Video Shooting Assistant API")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="智能视频拍摄辅助系统 API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
# 注意：allow_credentials=True 时不能使用 allow_origins=["*"]
# 需要明确指定允许的源，或者设置 allow_credentials=False
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=False,  # 改为 False 以兼容 allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    """Add rate limit headers to responses."""
    response = await call_next(request)
    
    # Add rate limit info headers
    response.headers["X-RateLimit-Limit"] = str(settings.security.rate_limit_per_minute)
    
    return response


# Include API routes
app.include_router(router)
app.include_router(realtime_router)  # /api/realtime
app.include_router(realtime_router_v1)  # /v1/realtime (兼容 rubik-ai 前端)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
    }
