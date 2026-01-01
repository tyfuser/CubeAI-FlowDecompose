"""FastAPI主应用"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path

from .api import routes_jobs, routes_virtual_motion, routes_terminology
from .db.session import init_db
from .core.config import settings
from .core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("初始化数据库...")
    init_db()
    logger.info("应用启动完成")
    
    yield
    
    # 关闭时
    logger.info("应用关闭")


# 创建FastAPI应用
app = FastAPI(
    title="Video AI Demo API",
    description="视频分析与对比API - Learn模式和Compare模式",
    version="0.1.0",
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(routes_jobs.router)
app.include_router(routes_virtual_motion.router)
app.include_router(routes_terminology.router)

# 挂载静态文件
frontend_dir = Path(__file__).parent.parent / "frontend"
data_dir = Path(__file__).parent.parent / "data"

# 挂载 data 目录用于访问视频文件
if data_dir.exists():
    app.mount("/data", StaticFiles(directory=str(data_dir)), name="data")
    logger.info(f"已挂载 data 目录: {data_dir}")

if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")
    
    @app.get("/")
    async def root():
        """前端页面"""
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Frontend not found"}
else:
    @app.get("/")
    async def root():
        """根路径"""
        return {
            "name": "Video AI Demo API",
            "version": "0.1.0",
            "status": "running",
            "endpoints": {
                "docs": "/docs",
                "frontend": "/",
                "create_job": "POST /v1/video-analysis/jobs",
                "get_job": "GET /v1/video-analysis/jobs/{job_id}",
                "virtual_motion": "POST /v1/video-analysis/virtual-motion/jobs"
            }
        }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

