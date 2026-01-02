"""
Application settings and configuration.
"""
from typing import Optional
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    
    model_config = ConfigDict(extra="ignore")
    
    host: str = Field(default="localhost", alias="DB_HOST")
    port: int = Field(default=5432, alias="DB_PORT")
    name: str = Field(default="video_assistant", alias="DB_NAME")
    user: str = Field(default="postgres", alias="DB_USER")
    password: str = Field(default="postgres", alias="DB_PASSWORD")
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    @property
    def async_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisSettings(BaseSettings):
    """Redis configuration."""
    
    model_config = ConfigDict(extra="ignore")
    
    host: str = Field(default="localhost", alias="REDIS_HOST")
    port: int = Field(default=6379, alias="REDIS_PORT")
    db: int = Field(default=0, alias="REDIS_DB")
    password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    
    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class CelerySettings(BaseSettings):
    """Celery configuration."""
    
    model_config = ConfigDict(extra="ignore")
    
    broker_url: str = Field(default="redis://localhost:6379/0", alias="CELERY_BROKER_URL")
    result_backend: str = Field(default="redis://localhost:6379/1", alias="CELERY_RESULT_BACKEND")
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: list[str] = ["json"]
    timezone: str = "UTC"
    enable_utc: bool = True


class StorageSettings(BaseSettings):
    """Storage configuration for videos and frames."""
    
    model_config = ConfigDict(extra="ignore")
    
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")
    frames_dir: str = Field(default="./frames", alias="FRAMES_DIR")
    max_file_size_mb: int = Field(default=500, alias="MAX_FILE_SIZE_MB")
    allowed_formats: list[str] = ["mp4", "mov", "avi", "mkv"]
    cleanup_days: int = Field(default=7, alias="CLEANUP_DAYS")


class ProcessingSettings(BaseSettings):
    """Video processing configuration."""
    
    model_config = ConfigDict(extra="ignore")
    
    target_resolution: tuple[int, int] = (640, 480)
    frame_extraction_fps: float = Field(default=1.0, alias="FRAME_EXTRACTION_FPS")
    max_processing_time_1min: int = Field(default=120, alias="MAX_PROCESSING_TIME_1MIN")
    max_processing_time_5min: int = Field(default=300, alias="MAX_PROCESSING_TIME_5MIN")
    concurrent_requests: int = Field(default=10, alias="CONCURRENT_REQUESTS")


class LLMSettings(BaseSettings):
    """LLM API configuration."""
    
    model_config = ConfigDict(extra="ignore")

    provider: str = Field(default="sophnet", alias="LLM_PROVIDER")
    api_key: Optional[str] = Field(default="OjmhrLwGlhZE_8BWV0NDYg19PURDsjGwUNazaH7LkrbKQ5LBQPeDrqKvX8-NNyvDTXH25JHP0Wn83gt2_8OEAw", alias="LLM_API_KEY")
    base_url: Optional[str] = Field(default="https://www.sophnet.com/api/open-apis/v1", alias="LLM_BASE_URL")
    model: str = Field(default="DeepSeek-V3.2", alias="LLM_MODEL")
    max_retries: int = Field(default=3, alias="LLM_MAX_RETRIES")
    timeout: int = Field(default=60, alias="LLM_TIMEOUT")


class MMHLLMSettings(BaseSettings):
    """Multi-modal LLM API configuration."""
    
    model_config = ConfigDict(extra="ignore")

    api_key: Optional[str] = Field(default="OjmhrLwGlhZE_8BWV0NDYg19PURDsjGwUNazaH7LkrbKQ5LBQPeDrqKvX8-NNyvDTXH25JHP0Wn83gt2_8OEAw", alias="MM_LLM_API_KEY")
    base_url: str = Field(default="https://www.sophnet.com/api/open-apis/v1", alias="MM_LLM_BASE_URL")
    model: str = Field(default="Qwen2.5-VL-7B-Instruct", alias="MM_LLM_MODEL")
    max_retries: int = Field(default=3, alias="MM_LLM_MAX_RETRIES")
    timeout: int = Field(default=30, alias="MM_LLM_TIMEOUT")


class SecuritySettings(BaseSettings):
    """Security configuration."""
    
    model_config = ConfigDict(extra="ignore")
    
    secret_key: str = Field(default="your-secret-key-change-in-production", alias="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    rate_limit_per_minute: int = Field(default=100, alias="RATE_LIMIT_PER_MINUTE")


class Settings(BaseSettings):
    """Main application settings."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # 忽略 .env 文件中的额外字段（如 PORT, HOST 等）
    )
    
    app_name: str = "Video Shooting Assistant"
    debug: bool = Field(default=False, alias="DEBUG")
    api_prefix: str = "/api"
    
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    celery: CelerySettings = CelerySettings()
    storage: StorageSettings = StorageSettings()
    processing: ProcessingSettings = ProcessingSettings()
    llm: LLMSettings = LLMSettings()
    mm_llm: MMHLLMSettings = MMHLLMSettings()
    security: SecuritySettings = SecuritySettings()


# Global settings instance
settings = Settings()
