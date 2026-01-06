"""
WebSocket Handler for Realtime Shooting Advisor

实时拍摄建议系统的 WebSocket 处理器。
Handles WebSocket communication for realtime shooting sessions.

Requirements: 9.1-9.5
"""
import asyncio
import base64
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Optional

import cv2
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect

from .analyzer import RealtimeAnalyzer, RealtimeAnalyzerConfig
from .advice_engine import AdviceEngine, AdviceEngineConfig
from .task_manager import TaskManager, TaskManagerConfig
from .types import (
    AdvicePayload,
    FrameBufferPayload,
    SessionState,
    ErrorPayload,
    TelemetryPayload,
    TaskPayload,
    EnvironmentAnalysisPayload,
    RealtimeAnalysisResult,
    ERROR_CODES,
)
from ..services.environment_scanner import EnvironmentAnalysis, get_environment_scanner
from .task_manager import TaskExecutionContext


logger = logging.getLogger(__name__)


@dataclass
class WebSocketHandlerConfig:
    """Configuration for WebSocket handler."""
    # Heartbeat interval (Requirement 9.5)
    heartbeat_interval_s: float = 5.0
    
    # Reconnection settings (Requirement 9.4)
    max_reconnect_attempts: int = 5
    initial_reconnect_delay_s: float = 1.0
    max_reconnect_delay_s: float = 30.0
    reconnect_backoff_multiplier: float = 2.0
    
    # Frame processing
    max_frame_buffer_size: int = 10
    min_frame_buffer_size: int = 5
    
    # Advice delivery timeout (Requirement 7.5)
    advice_delivery_timeout_ms: float = 100.0


class SessionManager:
    """
    会话管理器
    Manages realtime shooting sessions.
    
    Requirements:
    - 9.1: Session-based architecture from story-galaxy-controller
    - 9.3: Support multiple concurrent clients per session
    - 9.4: Reconnection with exponential backoff
    - 9.5: Heartbeat mechanism
    """
    
    def __init__(self):
        self._sessions: dict[str, SessionState] = {}
        self._clients: dict[str, set[WebSocket]] = {}  # session_id -> set of websockets
        self._analyzers: dict[str, RealtimeAnalyzer] = {}
        self._advice_engines: dict[str, AdviceEngine] = {}
        self._task_managers: dict[str, TaskManager] = {}  # session_id -> TaskManager
        self._heartbeat_tasks: dict[str, asyncio.Task] = {}
    
    def create_session(self, session_id: str) -> SessionState:
        """
        Create a new session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Created SessionState
        """
        if session_id in self._sessions:
            return self._sessions[session_id]
        
        session = SessionState(session_id=session_id)
        self._sessions[session_id] = session
        self._clients[session_id] = set()
        self._analyzers[session_id] = RealtimeAnalyzer()
        self._advice_engines[session_id] = AdviceEngine()
        self._task_managers[session_id] = TaskManager(
            environment_scanner=get_environment_scanner()
        )
        
        logger.info(f"Created session {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get session by ID."""
        return self._sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> None:
        """Delete a session and clean up resources."""
        if session_id in self._sessions:
            # Cancel heartbeat task
            if session_id in self._heartbeat_tasks:
                self._heartbeat_tasks[session_id].cancel()
                del self._heartbeat_tasks[session_id]
            
            # Close all client connections
            for ws in list(self._clients.get(session_id, [])):
                asyncio.create_task(ws.close())
            
            # Clean up
            del self._sessions[session_id]
            self._clients.pop(session_id, None)
            self._analyzers.pop(session_id, None)
            self._advice_engines.pop(session_id, None)
            self._task_managers.pop(session_id, None)
            
            logger.info(f"Deleted session {session_id}")
    
    def add_client(self, session_id: str, websocket: WebSocket) -> None:
        """Add a client to a session."""
        if session_id not in self._clients:
            self._clients[session_id] = set()
        self._clients[session_id].add(websocket)
        logger.info(f"Client joined session {session_id}, total: {len(self._clients[session_id])}")
    
    def remove_client(self, session_id: str, websocket: WebSocket) -> None:
        """Remove a client from a session."""
        if session_id in self._clients:
            self._clients[session_id].discard(websocket)
            logger.info(f"Client left session {session_id}, remaining: {len(self._clients[session_id])}")
    
    def get_clients(self, session_id: str) -> set[WebSocket]:
        """Get all clients in a session."""
        return self._clients.get(session_id, set())
    
    def get_analyzer(self, session_id: str) -> Optional[RealtimeAnalyzer]:
        """Get analyzer for a session."""
        return self._analyzers.get(session_id)
    
    def get_advice_engine(self, session_id: str) -> Optional[AdviceEngine]:
        """Get advice engine for a session."""
        return self._advice_engines.get(session_id)

    def get_task_manager(self, session_id: str) -> Optional[TaskManager]:
        """Get task manager for a session."""
        return self._task_managers.get(session_id)
    
    def get_all_sessions(self) -> list[str]:
        """Get all session IDs."""
        return list(self._sessions.keys())
    
    def get_session_count(self) -> int:
        """Get total number of sessions."""
        return len(self._sessions)


class RealtimeWebSocketHandler:
    """
    实时 WebSocket 处理器
    Handles WebSocket communication for realtime shooting sessions.
    
    This handler:
    1. Receives frame buffers from mobile clients
    2. Decodes Base64 JPEG frames
    3. Runs analysis pipeline
    4. Pushes advice to all connected clients
    
    Requirements:
    - 9.1: Session-based architecture
    - 9.2: Push advice immediately
    - 9.3: Multiple concurrent clients
    - 9.4: Reconnection with exponential backoff
    - 9.5: Heartbeat every 5 seconds
    """
    
    def __init__(
        self,
        session_manager: SessionManager,
        config: Optional[WebSocketHandlerConfig] = None
    ):
        self.session_manager = session_manager
        self.config = config or WebSocketHandlerConfig()
    
    async def handle_connection(
        self,
        websocket: WebSocket,
        session_id: str
    ) -> None:
        """
        Handle a WebSocket connection for a shooting session.
        
        Args:
            websocket: FastAPI WebSocket connection
            session_id: Session identifier
        """
        # Accept WebSocket connection with CORS headers
        await websocket.accept()
        
        # Get or create session
        session = self.session_manager.get_session(session_id)
        if session is None:
            session = self.session_manager.create_session(session_id)
        
        # Add client to session
        self.session_manager.add_client(session_id, websocket)
        
        # Send welcome message
        await self._send_message(websocket, {
            "type": "connected",
            "session_id": session_id,
            "timestamp": int(time.time() * 1000)
        })
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(websocket, session_id)
        )
        
        try:
            # Main message loop
            await self._message_loop(websocket, session_id)
        except WebSocketDisconnect:
            logger.info(f"Client disconnected from session {session_id}")
        except Exception as e:
            logger.error(f"Error in session {session_id}: {e}")
            await self._send_error(websocket, "CONNECTION_LOST")
        finally:
            # Clean up
            heartbeat_task.cancel()
            self.session_manager.remove_client(session_id, websocket)
            
            # Clean up empty sessions after delay
            if not self.session_manager.get_clients(session_id):
                await asyncio.sleep(60)  # 1 minute delay
                if not self.session_manager.get_clients(session_id):
                    self.session_manager.delete_session(session_id)
    
    async def _message_loop(
        self,
        websocket: WebSocket,
        session_id: str
    ) -> None:
        """
        Main message processing loop.
        
        Args:
            websocket: WebSocket connection
            session_id: Session identifier
        """
        while True:
            try:
                message = await websocket.receive_text()
                await self._handle_message(websocket, session_id, message)
            except WebSocketDisconnect:
                raise
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await self._send_error(websocket, "PARSE_ERROR", str(e))
    
    async def _handle_message(
        self,
        websocket: WebSocket,
        session_id: str,
        message: str
    ) -> None:
        """
        Handle incoming WebSocket message.
        
        Args:
            websocket: WebSocket connection
            session_id: Session identifier
            message: Raw message string
        """
        try:
            payload = json.loads(message)
            msg_type = payload.get("type")
            
            if msg_type == "frames":
                await self._handle_frame_buffer(websocket, session_id, payload)
            elif msg_type == "heartbeat":
                await self._send_message(websocket, {
                    "type": "heartbeat_ack",
                    "timestamp": int(time.time() * 1000)
                })
            elif msg_type == "status":
                session = self.session_manager.get_session(session_id)
                if session:
                    await self._send_message(websocket, {
                        "type": "status",
                        **session.to_dict()
                    })
            elif msg_type == "start_environment_scan":
                await self._handle_environment_scan_request(websocket, session_id, payload)
            elif msg_type == "pick_task":
                await self._handle_task_pick_request(websocket, session_id, payload)
            elif msg_type == "start_task_execution":
                await self._handle_task_execution_request(websocket, session_id, payload)
            else:
                logger.warning(f"Unknown message type: {msg_type}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            await self._send_error(websocket, "PARSE_ERROR", str(e))
    
    async def _handle_frame_buffer(
        self,
        websocket: WebSocket,
        session_id: str,
        payload: dict
    ) -> None:
        """
        Handle incoming frame buffer and run analysis.
        
        Args:
            websocket: WebSocket connection
            session_id: Session identifier
            payload: Frame buffer payload
        """
        frames_b64 = payload.get("frames", [])
        fps = payload.get("fps", 30.0)
        
        if not frames_b64:
            await self._send_error(websocket, "INVALID_FRAME_BUFFER")
            return
        
        # Get analyzer and advice engine
        analyzer = self.session_manager.get_analyzer(session_id)
        advice_engine = self.session_manager.get_advice_engine(session_id)
        session = self.session_manager.get_session(session_id)
        
        if not analyzer or not advice_engine or not session:
            await self._send_error(websocket, "SESSION_EXPIRED")
            return
        
        # Decode frames
        frames = analyzer.decode_frame_buffer(frames_b64)
        
        if len(frames) < self.config.min_frame_buffer_size:
            await self._send_message(websocket, {
                "type": "frame_ack",
                "frame_count": len(frames),
                "status": "insufficient_frames",
                "timestamp": int(time.time() * 1000)
            })
            return
        
        # Run analysis
        start_time = time.time()
        analysis_result = analyzer.analyze_buffer(frames, fps)
        
        # Update session metrics
        session.update_latency(analysis_result.analysis_latency_ms)
        
        # Generate advice
        current_time = time.time()
        advice_list = advice_engine.generate_advice(
            analysis_result=analysis_result,
            current_time=current_time,
        )
        
        # Send acknowledgment
        await self._send_message(websocket, {
            "type": "frame_ack",
            "frame_count": len(frames),
            "analysis_latency_ms": analysis_result.analysis_latency_ms,
            "timestamp": int(time.time() * 1000)
        })
        
        # Push advice to all clients (Requirement 9.2)
        if advice_list:
            await self._broadcast_advice(session_id, advice_list)

        # Send telemetry data
        await self._broadcast_telemetry(session_id, analysis_result)
    
    async def _broadcast_advice(
        self,
        session_id: str,
        advice_list: list[AdvicePayload]
    ) -> None:
        """
        Broadcast advice to all clients in a session.
        
        Requirement 9.2: Push advice immediately to all connected clients.
        
        Args:
            session_id: Session identifier
            advice_list: List of advice payloads
        """
        clients = self.session_manager.get_clients(session_id)
        
        for advice in advice_list:
            payload = advice.to_dict()
            
            # Send to all clients concurrently
            tasks = []
            for client in clients:
                if client.client_state.name == "CONNECTED":
                    tasks.append(self._send_message(client, payload))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def _broadcast_telemetry(
        self,
        session_id: str,
        analysis_result: RealtimeAnalysisResult
    ) -> None:
        """
        Broadcast telemetry data to all clients in a session.

        Args:
            session_id: Session identifier
            analysis_result: Analysis result to broadcast
        """
        clients = self.session_manager.get_clients(session_id)

        telemetry_payload = {
            "type": "telemetry",
            "avg_speed_px_frame": analysis_result.avg_speed_px_frame,
            "speed_variance": analysis_result.speed_variance,
            "motion_smoothness": analysis_result.motion_smoothness,
            "primary_direction_deg": analysis_result.primary_direction_deg,
            "subject_occupancy": analysis_result.subject_occupancy,
            "confidence": analysis_result.confidence,
            "timestamp": int(time.time() * 1000)
        }

        tasks = []
        for client in clients:
            if client.client_state.name == "CONNECTED":
                tasks.append(self._send_message(client, telemetry_payload))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _handle_environment_scan_request(
        self,
        websocket: WebSocket,
        session_id: str,
        payload: dict
    ) -> None:
        """
        Handle environment scan request from client.

        Args:
            websocket: WebSocket connection
            session_id: Session identifier
            payload: Request payload containing frame paths
        """
        frame_paths = payload.get("frame_paths", [])
        timestamps_ms = payload.get("timestamps_ms")

        if not frame_paths:
            await self._send_error(websocket, "INVALID_REQUEST", "frame_paths is required")
            return

        task_manager = self.session_manager.get_task_manager(session_id)
        if not task_manager:
            await self._send_error(websocket, "SESSION_EXPIRED")
            return

        try:
            # Start environment scan
            await task_manager.start_environment_scan(frame_paths, timestamps_ms)

            # Get analysis result
            analysis = task_manager.get_environment_analysis()
            if analysis:
                # Broadcast environment analysis to all clients
                await self._broadcast_environment_analysis(session_id, analysis)

        except Exception as e:
            logger.error(f"Environment scan failed: {e}")
            await self._send_error(websocket, "SCAN_FAILED", str(e))

    async def _handle_task_pick_request(
        self,
        websocket: WebSocket,
        session_id: str,
        payload: dict
    ) -> None:
        """
        Handle task pick request from client.

        Args:
            websocket: WebSocket connection
            session_id: Session identifier
            payload: Request payload containing task_id (optional)
        """
        task_id = payload.get("task_id")

        task_manager = self.session_manager.get_task_manager(session_id)
        if not task_manager:
            await self._send_error(websocket, "SESSION_EXPIRED")
            return

        try:
            success = await task_manager.pick_task(task_id)
            if success:
                context = task_manager.get_current_context()
                if context:
                    await self._broadcast_task_update(session_id, context)
            else:
                await self._send_error(websocket, "TASK_PICK_FAILED")

        except Exception as e:
            logger.error(f"Task pick failed: {e}")
            await self._send_error(websocket, "TASK_PICK_FAILED", str(e))

    async def _handle_task_execution_request(
        self,
        websocket: WebSocket,
        session_id: str,
        payload: dict
    ) -> None:
        """
        Handle task execution start request from client.

        Args:
            websocket: WebSocket connection
            session_id: Session identifier
            payload: Request payload
        """
        task_manager = self.session_manager.get_task_manager(session_id)
        if not task_manager:
            await self._send_error(websocket, "SESSION_EXPIRED")
            return

        try:
            success = await task_manager.start_task_execution()
            if success:
                context = task_manager.get_current_context()
                if context:
                    await self._broadcast_task_update(session_id, context)
            else:
                await self._send_error(websocket, "TASK_EXECUTION_FAILED")

        except Exception as e:
            logger.error(f"Task execution start failed: {e}")
            await self._send_error(websocket, "TASK_EXECUTION_FAILED", str(e))

    async def _broadcast_environment_analysis(
        self,
        session_id: str,
        analysis: "EnvironmentAnalysis"
    ) -> None:
        """
        Broadcast environment analysis to all clients.

        Args:
            session_id: Session identifier
            analysis: Environment analysis result
        """
        clients = self.session_manager.get_clients(session_id)

        payload = {
            "type": "environment",
            **analysis.to_dict(),
            "timestamp": int(time.time() * 1000)
        }

        tasks = []
        for client in clients:
            if client.client_state.name == "CONNECTED":
                tasks.append(self._send_message(client, payload))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _broadcast_task_update(
        self,
        session_id: str,
        context: "TaskExecutionContext"
    ) -> None:
        """
        Broadcast task update to all clients.

        Args:
            session_id: Session identifier
            context: Task execution context
        """
        clients = self.session_manager.get_clients(session_id)

        task = context.task
        payload = {
            "type": "task",
            "task_id": task.task_id,
            "task_name": task.name,
            "description": task.description,
            "target_duration_s": task.target_duration_s,
            "risk_level": task.risk_level,
            "success_criteria": task.success_criteria,
            "target_motion": task.target_motion,
            "target_speed_range": list(task.target_speed_range) if task.target_speed_range else None,
            "state": context.current_state,
            "progress": context.progress,
            "timestamp": int(time.time() * 1000)
        }

        tasks = []
        for client in clients:
            if client.client_state.name == "CONNECTED":
                tasks.append(self._send_message(client, payload))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _heartbeat_loop(
        self,
        websocket: WebSocket,
        session_id: str
    ) -> None:
        """
        Send periodic heartbeat messages.
        
        Requirement 9.5: Heartbeat every 5 seconds.
        
        Args:
            websocket: WebSocket connection
            session_id: Session identifier
        """
        while True:
            try:
                await asyncio.sleep(self.config.heartbeat_interval_s)
                await self._send_message(websocket, {
                    "type": "heartbeat",
                    "session_id": session_id,
                    "timestamp": int(time.time() * 1000)
                })
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break
    
    async def _send_message(
        self,
        websocket: WebSocket,
        payload: dict
    ) -> None:
        """Send a JSON message to a WebSocket client."""
        try:
            await websocket.send_json(payload)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def _send_error(
        self,
        websocket: WebSocket,
        error_code: str,
        details: Optional[str] = None
    ) -> None:
        """Send an error message to a WebSocket client."""
        message, recoverable = ERROR_CODES.get(
            error_code,
            ("未知错误", True)
        )
        
        payload = {
            "type": "error",
            "code": error_code,
            "message": message,
            "recoverable": recoverable,
            "timestamp": int(time.time() * 1000)
        }
        
        if details:
            payload["details"] = details
        
        await self._send_message(websocket, payload)


class ReconnectionManager:
    """
    重连管理器
    Handles reconnection with exponential backoff.
    
    Requirement 9.4: Reconnection with exponential backoff.
    """
    
    def __init__(self, config: Optional[WebSocketHandlerConfig] = None):
        self.config = config or WebSocketHandlerConfig()
        self._attempt_counts: dict[str, int] = {}
        self._last_attempt_times: dict[str, float] = {}
    
    def get_reconnect_delay(self, session_id: str) -> float:
        """
        Get the delay before next reconnection attempt.
        
        Uses exponential backoff with jitter.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Delay in seconds
        """
        attempts = self._attempt_counts.get(session_id, 0)
        
        # Calculate delay with exponential backoff
        delay = self.config.initial_reconnect_delay_s * (
            self.config.reconnect_backoff_multiplier ** attempts
        )
        
        # Cap at max delay
        delay = min(delay, self.config.max_reconnect_delay_s)
        
        # Add jitter (±20%)
        import random
        jitter = delay * 0.2 * (random.random() * 2 - 1)
        delay += jitter
        
        return max(0, delay)
    
    def record_attempt(self, session_id: str) -> bool:
        """
        Record a reconnection attempt.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if more attempts are allowed, False if max reached
        """
        self._attempt_counts[session_id] = self._attempt_counts.get(session_id, 0) + 1
        self._last_attempt_times[session_id] = time.time()
        
        return self._attempt_counts[session_id] < self.config.max_reconnect_attempts
    
    def reset(self, session_id: str) -> None:
        """Reset reconnection state for a session."""
        self._attempt_counts.pop(session_id, None)
        self._last_attempt_times.pop(session_id, None)
    
    def should_reconnect(self, session_id: str) -> bool:
        """Check if reconnection should be attempted."""
        attempts = self._attempt_counts.get(session_id, 0)
        return attempts < self.config.max_reconnect_attempts


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def create_websocket_handler(
    config: Optional[WebSocketHandlerConfig] = None
) -> RealtimeWebSocketHandler:
    """
    Create a WebSocket handler with the global session manager.
    
    Args:
        config: Optional handler configuration
        
    Returns:
        RealtimeWebSocketHandler instance
    """
    return RealtimeWebSocketHandler(
        session_manager=get_session_manager(),
        config=config
    )
