"""
Celery tasks for video analysis pipeline.

Provides async task execution for the video analysis pipeline
with progress tracking and result storage.

Requirements covered:
- 7.8: Use async task queue (Celery) for long tasks
- 10.8: Provide real-time progress updates
"""
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from celery import Celery, Task
from celery.result import AsyncResult

from configs.settings import settings


logger = logging.getLogger(__name__)


# Initialize Celery app
celery_app = Celery(
    "video_assistant",
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend,
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.celery.task_serializer,
    result_serializer=settings.celery.result_serializer,
    accept_content=settings.celery.accept_content,
    timezone=settings.celery.timezone,
    enable_utc=settings.celery.enable_utc,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max
    task_soft_time_limit=540,  # 9 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    task_acks_late=True,  # Acknowledge after task completion
)


class AnalysisTask(Task):
    """
    Base task class for analysis tasks.
    
    Provides common functionality for progress tracking and error handling.
    """
    
    abstract = True
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.info(f"Task {task_id} completed successfully")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        logger.error(f"Task {task_id} failed: {exc}")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning(f"Task {task_id} retrying: {exc}")


def update_task_progress(
    task: Task,
    stage: str,
    progress_pct: float,
    message: str
) -> None:
    """
    Update task progress state.
    
    Args:
        task: The Celery task instance
        stage: Current pipeline stage
        progress_pct: Progress percentage (0-100)
        message: Progress message
    """
    task.update_state(
        state="PROGRESS",
        meta={
            "stage": stage,
            "progress": progress_pct,
            "message": message,
            "updated_at": datetime.utcnow().isoformat(),
        }
    )


@celery_app.task(
    bind=True,
    base=AnalysisTask,
    name="tasks.run_video_analysis",
    max_retries=3,
    default_retry_delay=60,
)
def run_video_analysis(
    self,
    video_path: str,
    video_id: str,
    config_dict: Optional[dict] = None
) -> dict[str, Any]:
    """
    Run the complete video analysis pipeline as a Celery task.
    
    This task executes the full pipeline:
    Uploader → Feature_Extractor → Heuristic_Analyzer → 
    Metadata_Synthesizer → Instruction_Generator
    
    Args:
        video_path: Path to the video file
        video_id: Unique video identifier
        config_dict: Optional pipeline configuration as dict
        
    Returns:
        Dictionary with pipeline results
    """
    import asyncio
    from src.services.orchestrator import Orchestrator, PipelineConfig, PipelineProgress
    
    logger.info(f"Starting video analysis task for video_id={video_id}")
    
    # Create config from dict if provided
    config = None
    if config_dict:
        config = PipelineConfig(**config_dict)
    
    # Create orchestrator
    orchestrator = Orchestrator(config=config)
    
    # Set up progress callback
    def progress_callback(progress: PipelineProgress):
        update_task_progress(
            self,
            progress.stage.value,
            progress.progress_pct,
            progress.message
        )
    
    orchestrator.set_progress_callback(progress_callback)
    
    try:
        # Run pipeline
        result = asyncio.run(
            orchestrator.run_pipeline(video_path, video_id)
        )
        
        # Convert result to dict for serialization
        result_dict = result.to_dict()
        
        # Store in database
        _store_analysis_result(video_id, result_dict)
        
        logger.info(f"Video analysis completed for video_id={video_id}")
        return result_dict
        
    except Exception as e:
        logger.error(f"Video analysis failed for video_id={video_id}: {e}")
        
        # Store error in database
        _store_analysis_error(video_id, str(e))
        
        # Retry on certain errors
        if _is_retryable_error(e):
            raise self.retry(exc=e)
        
        raise


@celery_app.task(
    bind=True,
    base=AnalysisTask,
    name="tasks.run_single_stage",
)
def run_single_stage(
    self,
    stage: str,
    input_data: dict,
    video_id: str,
    **kwargs
) -> dict[str, Any]:
    """
    Run a single pipeline stage as a Celery task.
    
    Useful for re-running specific stages or debugging.
    
    Args:
        stage: Pipeline stage name
        input_data: Input data for the stage
        video_id: Video identifier
        **kwargs: Additional arguments for the stage
        
    Returns:
        Dictionary with stage output
    """
    import asyncio
    from src.services.orchestrator import Orchestrator, PipelineStage
    
    logger.info(f"Running stage {stage} for video_id={video_id}")
    
    orchestrator = Orchestrator()
    
    try:
        pipeline_stage = PipelineStage(stage)
        result = asyncio.run(
            orchestrator.run_stage(pipeline_stage, input_data, **kwargs)
        )
        
        # Convert to dict if possible
        if hasattr(result, "to_dict"):
            return result.to_dict()
        return result
        
    except Exception as e:
        logger.error(f"Stage {stage} failed for video_id={video_id}: {e}")
        raise


def _store_analysis_result(video_id: str, result: dict) -> None:
    """
    Store analysis result in database.
    
    Args:
        video_id: Video identifier
        result: Pipeline result dictionary
    """
    try:
        from sqlalchemy.orm import Session
        from src.models.database import AnalysisTask, get_engine, get_session_factory
        
        engine = get_engine(settings.database.url)
        SessionLocal = get_session_factory(engine)
        
        with SessionLocal() as session:
            # Find or create task record
            task = session.query(AnalysisTask).filter(
                AnalysisTask.video_id == video_id
            ).first()
            
            if task:
                task.status = "completed"
                task.completed_at = datetime.utcnow()
                task.uploader_output = result.get("uploader_output")
                task.feature_output = result.get("feature_output")
                task.heuristic_output = result.get("heuristic_output")
                task.metadata_output = result.get("metadata_output")
                task.instruction_card = result.get("instruction_card")
                task.error_message = result.get("error")
                session.commit()
                
    except Exception as e:
        logger.error(f"Failed to store analysis result: {e}")


def _store_analysis_error(video_id: str, error: str) -> None:
    """
    Store analysis error in database.
    
    Args:
        video_id: Video identifier
        error: Error message
    """
    try:
        from sqlalchemy.orm import Session
        from src.models.database import AnalysisTask, get_engine, get_session_factory
        
        engine = get_engine(settings.database.url)
        SessionLocal = get_session_factory(engine)
        
        with SessionLocal() as session:
            task = session.query(AnalysisTask).filter(
                AnalysisTask.video_id == video_id
            ).first()
            
            if task:
                task.status = "failed"
                task.error_message = error
                session.commit()
                
    except Exception as e:
        logger.error(f"Failed to store analysis error: {e}")


def _is_retryable_error(error: Exception) -> bool:
    """
    Check if an error is retryable.
    
    Args:
        error: The exception
        
    Returns:
        True if the error should be retried
    """
    retryable_types = (
        ConnectionError,
        TimeoutError,
        OSError,
    )
    
    # Check error type
    if isinstance(error, retryable_types):
        return True
    
    # Check error message for common retryable patterns
    error_str = str(error).lower()
    retryable_patterns = [
        "timeout",
        "connection",
        "temporary",
        "rate limit",
        "too many requests",
    ]
    
    return any(pattern in error_str for pattern in retryable_patterns)


# =========================================================================
# Task Status and Progress Utilities
# =========================================================================

def get_task_status(task_id: str) -> dict[str, Any]:
    """
    Get the status of a Celery task.
    
    Args:
        task_id: The Celery task ID
        
    Returns:
        Dictionary with task status information
    """
    result = AsyncResult(task_id, app=celery_app)
    
    status_info = {
        "task_id": task_id,
        "status": result.status,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None,
    }
    
    # Add progress info if available
    if result.status == "PROGRESS":
        status_info["progress"] = result.info
    elif result.ready():
        if result.successful():
            status_info["result"] = result.result
        else:
            status_info["error"] = str(result.result)
    
    return status_info


def cancel_task(task_id: str) -> bool:
    """
    Cancel a running Celery task.
    
    Args:
        task_id: The Celery task ID
        
    Returns:
        True if cancellation was requested
    """
    result = AsyncResult(task_id, app=celery_app)
    result.revoke(terminate=True)
    return True


def get_queue_length() -> int:
    """
    Get the number of tasks in the queue.
    
    Returns:
        Number of pending tasks
    """
    try:
        inspect = celery_app.control.inspect()
        active = inspect.active() or {}
        reserved = inspect.reserved() or {}
        
        total = 0
        for worker_tasks in active.values():
            total += len(worker_tasks)
        for worker_tasks in reserved.values():
            total += len(worker_tasks)
        
        return total
    except Exception:
        return -1


def estimate_wait_time(queue_length: int) -> int:
    """
    Estimate wait time based on queue length.
    
    Args:
        queue_length: Number of tasks in queue
        
    Returns:
        Estimated wait time in seconds
    """
    # Assume average task takes 2 minutes
    avg_task_time = 120
    return queue_length * avg_task_time
