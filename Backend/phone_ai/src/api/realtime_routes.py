"""
FastAPI routes for Realtime Shooting Advisor.

Provides WebSocket endpoints for realtime shooting sessions.

Requirements covered:
- 9.1: Session-based WebSocket architecture
- 9.2: Push advice to clients immediately
- 9.3: Support multiple concurrent clients
- 9.4: Reconnection with exponential backoff
- 9.5: Heartbeat mechanism
"""
import logging
import uuid
from typing import Optional, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status, Request
from pydantic import BaseModel

from src.realtime.websocket_handler import (
    get_session_manager,
    create_websocket_handler,
    RealtimeWebSocketHandler,
    SessionManager,
)


logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/realtime", tags=["Realtime Shooting"])

# 创建 v1 路由以兼容 rubik-ai 前端（使用 /v1/realtime 路径）
router_v1 = APIRouter(prefix="/v1/realtime", tags=["Realtime Shooting"])


# =========================================================================
# Request/Response Models
# =========================================================================

class CreateSessionResponse(BaseModel):
    """Response model for session creation."""
    session_id: str
    ws_url: str
    message: str


class SessionInfoResponse(BaseModel):
    """Response model for session info."""
    session_id: str
    created_at: float
    motion_state: str
    total_analyses: int
    avg_latency_ms: float
    active_clients: int


class AdvicePushRequest(BaseModel):
    """Request model for pushing advice to a session."""
    priority: str
    category: str
    message: str
    advanced_message: Optional[str] = None
    trigger_haptic: bool = False


class AdvicePushResponse(BaseModel):
    """Response model for advice push."""
    success: bool
    clients_notified: int


# =========================================================================
# REST API Endpoints
# =========================================================================

@router.post(
    "/session",
    response_model=CreateSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_shooting_session():
    """
    Create a new realtime shooting session.
    
    Requirement 9.1: Session-based architecture.
    
    Returns a session ID and WebSocket URL for clients to connect.
    """
    session_id = str(uuid.uuid4())[:8].upper()
    
    session_manager = get_session_manager()
    session_manager.create_session(session_id)
    
    logger.info(f"Created shooting session {session_id}")
    
    return CreateSessionResponse(
        session_id=session_id,
        ws_url=f"/api/realtime/session/{session_id}/ws",
        message="Session created successfully"
    )


# v1 兼容端点
async def create_shooting_session_v1():
    """v1 兼容的创建会话端点"""
    session_id = str(uuid.uuid4())[:8].upper()
    
    session_manager = get_session_manager()
    session_manager.create_session(session_id)
    
    logger.info(f"Created shooting session {session_id} (v1)")
    
    return CreateSessionResponse(
        session_id=session_id,
        ws_url=f"/v1/realtime/session/{session_id}/ws",
        message="Session created successfully"
    )


@router.get(
    "/session/{session_id}",
    response_model=SessionInfoResponse,
)
async def get_session_info(session_id: str):
    """
    Get information about a shooting session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session information including metrics
    """
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "SESSION_NOT_FOUND",
                "message": f"Session {session_id} not found"
            }
        )
    
    clients = session_manager.get_clients(session_id)
    
    return SessionInfoResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        motion_state=session.motion_state.value,
        total_analyses=session.total_analyses,
        avg_latency_ms=session.avg_latency_ms,
        active_clients=len(clients)
    )


@router.delete(
    "/session/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_session(session_id: str):
    """
    Delete a shooting session.
    
    Args:
        session_id: Session identifier
    """
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "SESSION_NOT_FOUND",
                "message": f"Session {session_id} not found"
            }
        )
    
    session_manager.delete_session(session_id)
    logger.info(f"Deleted shooting session {session_id}")


@router.post(
    "/session/{session_id}/advice",
    response_model=AdvicePushResponse,
)
async def push_advice(session_id: str, advice: AdvicePushRequest):
    """
    Push advice to all clients in a session.
    
    Requirement 9.2: Push advice immediately.
    
    This endpoint is used by external systems to push advice
    to connected mobile clients.
    
    Args:
        session_id: Session identifier
        advice: Advice payload to push
        
    Returns:
        Number of clients notified
    """
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "SESSION_NOT_FOUND",
                "message": f"Session {session_id} not found"
            }
        )
    
    clients = session_manager.get_clients(session_id)
    
    # Create advice payload
    from src.realtime.types import AdvicePayload, AdvicePriority, AdviceCategory
    
    try:
        priority = AdvicePriority(advice.priority)
        category = AdviceCategory(advice.category)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_ADVICE",
                "message": str(e)
            }
        )
    
    advice_payload = AdvicePayload(
        priority=priority,
        category=category,
        message=advice.message,
        advanced_message=advice.advanced_message,
        trigger_haptic=advice.trigger_haptic,
    )
    
    # Broadcast to all clients
    handler = create_websocket_handler()
    import asyncio
    await handler._broadcast_advice(session_id, [advice_payload])
    
    return AdvicePushResponse(
        success=True,
        clients_notified=len(clients)
    )


# Temporarily disabled - missing request model definition
# @router.post("/analyze")
# async def analyze_frames(request: dict):
    """
    Analyze video frames and generate LLM-based shooting advice.
    
    This endpoint:
    1. Decodes Base64 JPEG frames
    2. Performs optical flow analysis using CV algorithms
    3. Sends analysis results to LLM for advice generation
    4. Returns analysis metrics and advice
    
    Args:
        request: Frame analysis request with Base64 frames
        
    Returns:
        Analysis results and LLM-generated advice
    """
    from src.realtime.realtime_service import get_realtime_service
    
    try:
        service = get_realtime_service()
        
        # Process frames and generate advice
        result, advice = await service.process_frame_buffer(
            base64_frames=request.frames,
            fps=request.fps,
            generate_advice=request.generate_advice,
        )
        
        # Build response
        analysis_response = AnalysisResultResponse(
            avg_speed_px_frame=result.avg_speed_px_frame,
            speed_variance=result.speed_variance,
            motion_smoothness=result.motion_smoothness,
            primary_direction_deg=result.primary_direction_deg,
            confidence=result.confidence,
            analysis_latency_ms=result.analysis_latency_ms,
        )
        
        advice_response = None
        if advice:
            advice_response = AdviceResponse(
                priority=advice.priority.value,
                category=advice.category.value,
                message=advice.message,
                trigger_haptic=advice.trigger_haptic,
                suppress_duration_ms=int(advice.suppress_duration_s * 1000),
            )
        
        return AnalyzeFramesResponse(
            success=True,
            analysis=analysis_response,
            advice=advice_response,
        )
        
    except Exception as e:
        logger.error(f"Frame analysis failed: {e}")
        return AnalyzeFramesResponse(
            success=False,
            error=str(e),
        )


# =========================================================================
# WebSocket Endpoint
# =========================================================================

@router.websocket("/session/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for realtime shooting sessions.
    
    Requirements:
    - 9.1: Session-based architecture
    - 9.2: Push advice immediately
    - 9.3: Multiple concurrent clients
    - 9.4: Reconnection support
    - 9.5: Heartbeat every 5 seconds
    
    Message types (Client → Server):
    - frames: Frame buffer for analysis
    - heartbeat: Client heartbeat
    - status: Request session status
    
    Message types (Server → Client):
    - connected: Connection established
    - advice: Shooting advice
    - heartbeat: Server heartbeat
    - heartbeat_ack: Heartbeat acknowledgment
    - frame_ack: Frame buffer acknowledgment
    - status: Session status
    - error: Error message
    
    Args:
        websocket: FastAPI WebSocket connection
        session_id: Session identifier
    """
    handler = create_websocket_handler()
    await handler.handle_connection(websocket, session_id)

# v1 兼容 WebSocket
@router_v1.websocket("/session/{session_id}/ws")
async def websocket_endpoint_v1(websocket: WebSocket, session_id: str):
    """v1 兼容 WebSocket 端点"""
    handler = create_websocket_handler()
    await handler.handle_connection(websocket, session_id)
