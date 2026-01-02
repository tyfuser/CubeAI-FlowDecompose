# Services module
"""
Service modules for the Video Shooting Assistant.

Provides external service integrations and business logic.
"""

from src.services.llm_client import (
    LLMClient,
    LLMConfig,
    LLMProvider,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMResponseError,
    MockLLMClient,
    create_llm_client,
)

from src.services.orchestrator import (
    Orchestrator,
    PipelineConfig,
    PipelineStage,
    PipelineProgress,
    ConfidenceAction,
    ValidationResult,
    RetryableError,
    create_orchestrator,
)

from src.services.vector_db import (
    VectorDB,
    VectorDBConfig,
    VideoMetadata,
    SearchResult,
    RetrievalFilters,
    VectorDBError,
    FAISSNotAvailableError,
    IndexNotInitializedError,
    create_vector_db,
)

__all__ = [
    # LLM Client
    "LLMClient",
    "LLMConfig",
    "LLMProvider",
    "LLMError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "LLMResponseError",
    "MockLLMClient",
    "create_llm_client",
    # Orchestrator
    "Orchestrator",
    "PipelineConfig",
    "PipelineStage",
    "PipelineProgress",
    "ConfidenceAction",
    "ValidationResult",
    "RetryableError",
    "create_orchestrator",
    # Vector DB
    "VectorDB",
    "VectorDBConfig",
    "VideoMetadata",
    "SearchResult",
    "RetrievalFilters",
    "VectorDBError",
    "FAISSNotAvailableError",
    "IndexNotInitializedError",
    "create_vector_db",
]
