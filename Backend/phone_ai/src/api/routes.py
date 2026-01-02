"""
FastAPI routes for the Video Shooting Assistant API.

Provides REST API endpoints for video upload, analysis, and feedback.

Requirements covered:
- 9.1: POST /api/upload - Video file upload
- 9.2: GET /api/analysis/{video_id} - Retrieve analysis results
- 9.3: GET /api/suggestions/{video_id} - Retrieve instruction cards
- 9.4: POST /api/feedback - Submit user feedback
- 9.5: GET /api/export/{video_id} - Export shot-list
- 9.6: Return appropriate HTTP status codes and error messages
- 10.4: Rate limiting (100 req/min/user)
- 10.5: JWT-based authentication
"""
import csv
import io
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from configs.settings import settings
from src.models.database import AnalysisTask, UserFeedback, get_engine, get_session_factory
from src.models.enums import FeedbackAction, TaskStatus
from src.tasks.analysis_tasks import (
    run_video_analysis,
    get_task_status,
    cancel_task,
    get_queue_length,
    estimate_wait_time,
)
from src.api.auth import (
    User,
    Token,
    get_current_user,
    require_auth,
    rate_limit_check,
    generate_token_for_user,
)


logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["Video Analysis"])


# =========================================================================
# Database Session Dependency
# =========================================================================

def get_db():
    """Get database session."""
    engine = get_engine(settings.database.url)
    SessionLocal = get_session_factory(engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================================================
# Request/Response Models
# =========================================================================

class UploadResponse(BaseModel):
    """Response model for video upload."""
    video_id: str
    task_id: str
    status: str
    message: str
    estimated_wait_time: Optional[int] = None


class AnalysisResponse(BaseModel):
    """Response model for analysis results."""
    video_id: str
    status: str
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    uploader_output: Optional[dict] = None
    feature_output: Optional[dict] = None
    heuristic_output: Optional[dict] = None
    metadata_output: Optional[dict] = None
    instruction_card: Optional[dict] = None


class SuggestionsResponse(BaseModel):
    """Response model for shooting suggestions."""
    video_id: str
    status: str
    confidence: Optional[float] = None
    confidence_action: Optional[str] = None
    confidence_message: Optional[str] = None
    instruction_card: Optional[dict] = None


class FeedbackRequest(BaseModel):
    """Request model for user feedback."""
    video_id: str
    instruction_index: Optional[int] = None
    action: str = Field(..., description="accept, modify, or ignore")
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Response model for feedback submission."""
    feedback_id: str
    message: str


class TaskStatusResponse(BaseModel):
    """Response model for task status."""
    task_id: str
    status: str
    progress: Optional[dict] = None
    result: Optional[dict] = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    error_code: str
    message: str
    details: Optional[dict] = None


# =========================================================================
# API Endpoints
# =========================================================================

@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file format"},
        413: {"model": ErrorResponse, "description": "File too large"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    dependencies=[Depends(rate_limit_check)],
)
async def upload_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """
    Upload a video file for analysis.
    
    Requirement 9.1: POST /api/upload endpoint for video file upload.
    
    The video will be queued for async processing. Use the returned
    task_id to check progress via GET /api/analysis/{video_id}.
    
    Supported formats: MP4, MOV, AVI, MKV
    Maximum file size: 500MB (configurable)
    """
    # Validate file format
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_FILENAME",
                "message": "Filename is required",
            }
        )
    
    extension = file.filename.split(".")[-1].lower()
    if extension not in settings.storage.allowed_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_VIDEO_FORMAT",
                "message": f"Unsupported format: {extension}. Supported: {settings.storage.allowed_formats}",
            }
        )
    
    # Generate video ID
    video_id = str(uuid.uuid4())
    
    # Save file to upload directory
    upload_dir = settings.storage.upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{video_id}.{extension}")
    
    try:
        # Read and save file
        content = await file.read()
        
        # Check file size
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > settings.storage.max_file_size_mb:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error_code": "FILE_TOO_LARGE",
                    "message": f"File size {file_size_mb:.1f}MB exceeds limit of {settings.storage.max_file_size_mb}MB",
                }
            )
        
        with open(file_path, "wb") as f:
            f.write(content)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "UPLOAD_FAILED",
                "message": "Failed to save uploaded file",
            }
        )
    
    # Create database record
    task_record = AnalysisTask(
        video_id=video_id,
        status=TaskStatus.PENDING.value,
    )
    db.add(task_record)
    db.commit()
    
    # Queue analysis task
    celery_task = run_video_analysis.delay(file_path, video_id)
    
    # Estimate wait time
    queue_len = get_queue_length()
    wait_time = estimate_wait_time(queue_len) if queue_len >= 0 else None
    
    return UploadResponse(
        video_id=video_id,
        task_id=celery_task.id,
        status="queued",
        message="Video uploaded successfully. Analysis in progress.",
        estimated_wait_time=wait_time,
    )


@router.get(
    "/analysis/{video_id}",
    response_model=AnalysisResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Video not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    dependencies=[Depends(rate_limit_check)],
)
async def get_analysis(
    video_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """
    Retrieve analysis results for a video.
    
    Requirement 9.2: GET /api/analysis/{video_id} endpoint.
    
    Returns the full analysis results including all intermediate outputs
    from each pipeline stage.
    """
    task = db.query(AnalysisTask).filter(
        AnalysisTask.video_id == video_id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "VIDEO_NOT_FOUND",
                "message": f"No analysis found for video_id: {video_id}",
            }
        )
    
    return AnalysisResponse(
        video_id=task.video_id,
        status=task.status,
        created_at=task.created_at,
        completed_at=task.completed_at,
        error_message=task.error_message,
        uploader_output=task.uploader_output,
        feature_output=task.feature_output,
        heuristic_output=task.heuristic_output,
        metadata_output=task.metadata_output,
        instruction_card=task.instruction_card,
    )


@router.get(
    "/suggestions/{video_id}",
    response_model=SuggestionsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Video not found"},
        202: {"model": SuggestionsResponse, "description": "Analysis in progress"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    dependencies=[Depends(rate_limit_check)],
)
async def get_suggestions(
    video_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """
    Retrieve shooting instruction cards for a video.
    
    Requirement 9.3: GET /api/suggestions/{video_id} endpoint.
    
    Returns the three-layer instruction card with confidence information.
    """
    task = db.query(AnalysisTask).filter(
        AnalysisTask.video_id == video_id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "VIDEO_NOT_FOUND",
                "message": f"No analysis found for video_id: {video_id}",
            }
        )
    
    # Check if analysis is complete
    if task.status != TaskStatus.COMPLETED.value:
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "video_id": video_id,
                "status": task.status,
                "confidence": None,
                "confidence_action": None,
                "confidence_message": "Analysis in progress",
                "instruction_card": None,
            }
        )
    
    # Get confidence info from metadata
    confidence = None
    confidence_action = None
    confidence_message = None
    
    if task.metadata_output:
        confidence = task.metadata_output.get("confidence")
        if confidence is not None:
            if confidence > 0.75:
                confidence_action = "proceed"
                confidence_message = None
            elif confidence >= 0.55:
                confidence_action = "warn"
                confidence_message = "请尝试并拍摄两条版本"
            else:
                confidence_action = "manual"
                confidence_message = "置信度较低，建议人工确认后再执行"
    
    return SuggestionsResponse(
        video_id=video_id,
        status=task.status,
        confidence=confidence,
        confidence_action=confidence_action,
        confidence_message=confidence_message,
        instruction_card=task.instruction_card,
    )


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid feedback data"},
        404: {"model": ErrorResponse, "description": "Video not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    dependencies=[Depends(rate_limit_check)],
)
async def submit_feedback(
    feedback: FeedbackRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """
    Submit user feedback on instruction cards.
    
    Requirement 9.4: POST /api/feedback endpoint.
    
    Allows users to provide feedback on generated recommendations
    to improve future analysis.
    """
    # Validate action
    try:
        action = FeedbackAction(feedback.action)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_ACTION",
                "message": f"Invalid action: {feedback.action}. Must be one of: {FeedbackAction.values()}",
            }
        )
    
    # Find the analysis task
    task = db.query(AnalysisTask).filter(
        AnalysisTask.video_id == feedback.video_id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "VIDEO_NOT_FOUND",
                "message": f"No analysis found for video_id: {feedback.video_id}",
            }
        )
    
    # Create feedback record
    feedback_record = UserFeedback(
        task_id=task.id,
        instruction_index=feedback.instruction_index,
        action=action.value,
        rating=feedback.rating,
        comment=feedback.comment,
    )
    db.add(feedback_record)
    db.commit()
    db.refresh(feedback_record)
    
    return FeedbackResponse(
        feedback_id=str(feedback_record.id),
        message="Feedback submitted successfully",
    )


@router.get(
    "/export/{video_id}",
    responses={
        200: {"description": "Shot list export"},
        404: {"model": ErrorResponse, "description": "Video not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    dependencies=[Depends(rate_limit_check)],
)
async def export_shot_list(
    video_id: str,
    format: str = Query("json", description="Export format: json or csv"),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """
    Export shot-list in JSON or CSV format.
    
    Requirement 9.5: GET /api/export/{video_id} endpoint.
    
    Exports the analysis results and instruction cards in a format
    suitable for use in production workflows.
    """
    task = db.query(AnalysisTask).filter(
        AnalysisTask.video_id == video_id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "VIDEO_NOT_FOUND",
                "message": f"No analysis found for video_id: {video_id}",
            }
        )
    
    if task.status != TaskStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "ANALYSIS_NOT_COMPLETE",
                "message": "Analysis must be completed before export",
            }
        )
    
    # Prepare export data
    export_data = {
        "video_id": video_id,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "metadata": task.metadata_output,
        "instruction_card": task.instruction_card,
    }
    
    if format.lower() == "csv":
        return _export_as_csv(export_data, video_id)
    else:
        return JSONResponse(content=export_data)


def _export_as_csv(data: dict, video_id: str) -> StreamingResponse:
    """
    Export data as CSV file.
    
    Args:
        data: Export data dictionary
        video_id: Video identifier for filename
        
    Returns:
        StreamingResponse with CSV content
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "video_id",
        "created_at",
        "completed_at",
        "motion_type",
        "speed_profile",
        "suggested_scale",
        "confidence",
        "primary_instruction_1",
        "primary_instruction_2",
        "primary_instruction_3",
        "primary_instruction_4",
        "explain",
    ])
    
    # Extract values
    metadata = data.get("metadata", {}) or {}
    instruction_card = data.get("instruction_card", {}) or {}
    card_data = instruction_card.get("instruction_card", {}) or {}
    
    motion = metadata.get("motion", {}) or {}
    framing = metadata.get("framing", {}) or {}
    primary = card_data.get("primary", []) or []
    
    # Pad primary instructions to 4
    while len(primary) < 4:
        primary.append("")
    
    writer.writerow([
        data.get("video_id", ""),
        data.get("created_at", ""),
        data.get("completed_at", ""),
        motion.get("type", ""),
        motion.get("params", {}).get("speed_profile", ""),
        framing.get("suggested_scale", ""),
        metadata.get("confidence", ""),
        primary[0] if len(primary) > 0 else "",
        primary[1] if len(primary) > 1 else "",
        primary[2] if len(primary) > 2 else "",
        primary[3] if len(primary) > 3 else "",
        card_data.get("explain", ""),
    ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=shot_list_{video_id}.csv"
        }
    )


@router.get(
    "/task/{task_id}",
    response_model=TaskStatusResponse,
)
async def get_task_status_endpoint(task_id: str):
    """
    Get the status of a Celery task.
    
    Returns progress information for running tasks.
    """
    status_info = get_task_status(task_id)
    
    return TaskStatusResponse(
        task_id=status_info["task_id"],
        status=status_info["status"],
        progress=status_info.get("progress"),
        result=status_info.get("result"),
        error=status_info.get("error"),
    )


@router.delete(
    "/task/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_task_endpoint(task_id: str):
    """
    Cancel a running analysis task.
    """
    cancel_task(task_id)
    return None


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}



# =========================================================================
# Authentication Endpoints
# =========================================================================

class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str


@router.post(
    "/auth/token",
    response_model=Token,
    tags=["Authentication"],
)
async def login(request: LoginRequest):
    """
    Get an access token for API authentication.
    
    Requirement 10.5: JWT-based authentication.
    
    For demo purposes, accepts any username/password.
    In production, implement proper user authentication.
    """
    # In production, validate credentials against user database
    # For demo, generate token for any user
    user_id = str(uuid.uuid4())
    
    return generate_token_for_user(user_id, request.username)


@router.get(
    "/auth/me",
    response_model=User,
    tags=["Authentication"],
)
async def get_current_user_info(
    user: User = Depends(require_auth),
):
    """
    Get current authenticated user information.
    
    Requires valid JWT token.
    """
    return user
