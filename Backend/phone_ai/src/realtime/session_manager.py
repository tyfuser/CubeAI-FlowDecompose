"""
Session Management for Realtime Shooting Advisor

会话管理模块，提供会话状态存储、心跳机制和重连支持。
Provides session state storage, heartbeat mechanism, and reconnection support.

Requirements: 9.4, 9.5
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from collections import defaultdict

from .types import SessionState
from .analyzer import RealtimeAnalyzer
from .advice_engine import AdviceEngine


logger = logging.getLogger(__name__)


@dataclass
class SessionConfig:
    """Configuration for session management."""
    # Heartbeat settings (Requirement 9.5)
    heartbeat_interval_s: float = 5.0
    heartbeat_timeout_s: float = 15.0  # 3 missed heartbeats
    
    # Session cleanup
    session_timeout_s: float = 300.0  # 5 minutes without activity
    cleanup_interval_s: float = 60.0  # Check for stale sessions every minute
    
    # Reconnection settings (Requirement 9.4)
    max_reconnect_attempts: int = 5
    initial_reconnect_delay_s: float = 1.0
    max_reconnect_delay_s: float = 30.0
    reconnect_backoff_multiplier: float = 2.0


@dataclass
class ClientConnection:
    """Represents a client connection to a session."""
    client_id: str
    websocket: Any  # WebSocket instance
    connected_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    reconnect_attempts: int = 0
    
    def update_heartbeat(self) -> None:
        """Update last heartbeat time."""
        self.last_heartbeat = time.time()
    
    def is_stale(self, timeout_s: float) -> bool:
        """Check if connection is stale (missed heartbeats)."""
        return (time.time() - self.last_heartbeat) > timeout_s


@dataclass
class SessionData:
    """Complete session data including state and connections."""
    state: SessionState
    analyzer: RealtimeAnalyzer
    advice_engine: AdviceEngine
    clients: dict[str, ClientConnection] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    
    # Reconnection state per client
    reconnect_delays: dict[str, float] = field(default_factory=dict)
    
    def add_client(self, client_id: str, websocket: Any) -> ClientConnection:
        """Add a client connection."""
        conn = ClientConnection(client_id=client_id, websocket=websocket)
        self.clients[client_id] = conn
        self.last_activity = time.time()
        return conn
    
    def remove_client(self, client_id: str) -> Optional[ClientConnection]:
        """Remove a client connection."""
        return self.clients.pop(client_id, None)
    
    def get_client(self, client_id: str) -> Optional[ClientConnection]:
        """Get a client connection."""
        return self.clients.get(client_id)
    
    def get_active_clients(self, timeout_s: float) -> list[ClientConnection]:
        """Get all active (non-stale) client connections."""
        return [c for c in self.clients.values() if not c.is_stale(timeout_s)]
    
    def update_activity(self) -> None:
        """Update last activity time."""
        self.last_activity = time.time()
    
    def is_stale(self, timeout_s: float) -> bool:
        """Check if session is stale (no activity)."""
        return (time.time() - self.last_activity) > timeout_s


class PersistentSessionManager:
    """
    持久化会话管理器
    Manages session state with persistence and cleanup.
    
    This manager provides:
    - Session state storage
    - Heartbeat mechanism (Requirement 9.5)
    - Reconnection with exponential backoff (Requirement 9.4)
    - Automatic cleanup of stale sessions
    
    Requirements:
    - 9.4: Reconnection with exponential backoff
    - 9.5: Heartbeat every 5 seconds
    """
    
    def __init__(self, config: Optional[SessionConfig] = None):
        self.config = config or SessionConfig()
        self._sessions: dict[str, SessionData] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._heartbeat_tasks: dict[str, asyncio.Task] = {}
        self._on_session_expired: Optional[Callable[[str], None]] = None
    
    def set_session_expired_callback(
        self,
        callback: Callable[[str], None]
    ) -> None:
        """Set callback for when a session expires."""
        self._on_session_expired = callback
    
    def create_session(self, session_id: str) -> SessionData:
        """
        Create a new session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Created SessionData
        """
        if session_id in self._sessions:
            return self._sessions[session_id]
        
        state = SessionState(session_id=session_id)
        analyzer = RealtimeAnalyzer()
        advice_engine = AdviceEngine()
        
        session_data = SessionData(
            state=state,
            analyzer=analyzer,
            advice_engine=advice_engine,
        )
        
        self._sessions[session_id] = session_data
        logger.info(f"Created session {session_id}")
        
        return session_data
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session by ID."""
        session = self._sessions.get(session_id)
        if session:
            session.update_activity()
        return session
    
    def delete_session(self, session_id: str) -> None:
        """Delete a session and clean up resources."""
        if session_id not in self._sessions:
            return
        
        # Cancel heartbeat task
        if session_id in self._heartbeat_tasks:
            self._heartbeat_tasks[session_id].cancel()
            del self._heartbeat_tasks[session_id]
        
        # Remove session
        del self._sessions[session_id]
        logger.info(f"Deleted session {session_id}")
    
    def add_client(
        self,
        session_id: str,
        client_id: str,
        websocket: Any
    ) -> Optional[ClientConnection]:
        """
        Add a client to a session.
        
        Args:
            session_id: Session identifier
            client_id: Client identifier
            websocket: WebSocket connection
            
        Returns:
            ClientConnection or None if session not found
        """
        session = self.get_session(session_id)
        if session is None:
            return None
        
        conn = session.add_client(client_id, websocket)
        logger.info(f"Client {client_id} joined session {session_id}")
        
        # Reset reconnection state on successful connection
        session.reconnect_delays.pop(client_id, None)
        
        return conn
    
    def remove_client(self, session_id: str, client_id: str) -> None:
        """Remove a client from a session."""
        session = self.get_session(session_id)
        if session:
            session.remove_client(client_id)
            logger.info(f"Client {client_id} left session {session_id}")
    
    def update_client_heartbeat(
        self,
        session_id: str,
        client_id: str
    ) -> bool:
        """
        Update heartbeat for a client.
        
        Requirement 9.5: Track heartbeat for connection health.
        
        Args:
            session_id: Session identifier
            client_id: Client identifier
            
        Returns:
            True if updated, False if client not found
        """
        session = self.get_session(session_id)
        if session is None:
            return False
        
        client = session.get_client(client_id)
        if client is None:
            return False
        
        client.update_heartbeat()
        return True
    
    def get_reconnect_delay(
        self,
        session_id: str,
        client_id: str
    ) -> float:
        """
        Get the delay before next reconnection attempt.
        
        Requirement 9.4: Exponential backoff for reconnection.
        
        Args:
            session_id: Session identifier
            client_id: Client identifier
            
        Returns:
            Delay in seconds
        """
        session = self.get_session(session_id)
        if session is None:
            return self.config.initial_reconnect_delay_s
        
        # Get current delay or initialize
        current_delay = session.reconnect_delays.get(
            client_id,
            self.config.initial_reconnect_delay_s
        )
        
        return current_delay
    
    def record_reconnect_attempt(
        self,
        session_id: str,
        client_id: str
    ) -> tuple[bool, float]:
        """
        Record a reconnection attempt and calculate next delay.
        
        Requirement 9.4: Exponential backoff with max attempts.
        
        Args:
            session_id: Session identifier
            client_id: Client identifier
            
        Returns:
            Tuple of (should_continue, next_delay)
        """
        session = self.get_session(session_id)
        if session is None:
            return False, 0
        
        client = session.get_client(client_id)
        if client:
            client.reconnect_attempts += 1
            
            if client.reconnect_attempts >= self.config.max_reconnect_attempts:
                return False, 0
        
        # Calculate next delay with exponential backoff
        current_delay = session.reconnect_delays.get(
            client_id,
            self.config.initial_reconnect_delay_s
        )
        
        next_delay = min(
            current_delay * self.config.reconnect_backoff_multiplier,
            self.config.max_reconnect_delay_s
        )
        
        # Add jitter (±20%)
        import random
        jitter = next_delay * 0.2 * (random.random() * 2 - 1)
        next_delay += jitter
        
        session.reconnect_delays[client_id] = next_delay
        
        return True, next_delay
    
    def reset_reconnect_state(
        self,
        session_id: str,
        client_id: str
    ) -> None:
        """Reset reconnection state for a client."""
        session = self.get_session(session_id)
        if session:
            session.reconnect_delays.pop(client_id, None)
            client = session.get_client(client_id)
            if client:
                client.reconnect_attempts = 0
    
    async def start_cleanup_task(self) -> None:
        """Start the background cleanup task."""
        if self._cleanup_task is not None:
            return
        
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Started session cleanup task")
    
    async def stop_cleanup_task(self) -> None:
        """Stop the background cleanup task."""
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Stopped session cleanup task")
    
    async def _cleanup_loop(self) -> None:
        """Background loop to clean up stale sessions and connections."""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval_s)
                await self._cleanup_stale()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _cleanup_stale(self) -> None:
        """Clean up stale sessions and connections."""
        stale_sessions = []
        
        for session_id, session in self._sessions.items():
            # Check for stale clients
            stale_clients = []
            for client_id, client in session.clients.items():
                if client.is_stale(self.config.heartbeat_timeout_s):
                    stale_clients.append(client_id)
            
            # Remove stale clients
            for client_id in stale_clients:
                session.remove_client(client_id)
                logger.info(f"Removed stale client {client_id} from session {session_id}")
            
            # Check if session is stale
            if session.is_stale(self.config.session_timeout_s):
                stale_sessions.append(session_id)
        
        # Remove stale sessions
        for session_id in stale_sessions:
            self.delete_session(session_id)
            if self._on_session_expired:
                self._on_session_expired(session_id)
            logger.info(f"Removed stale session {session_id}")
    
    def get_all_sessions(self) -> list[str]:
        """Get all session IDs."""
        return list(self._sessions.keys())
    
    def get_session_count(self) -> int:
        """Get total number of sessions."""
        return len(self._sessions)
    
    def get_session_stats(self, session_id: str) -> Optional[dict]:
        """
        Get statistics for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session statistics or None if not found
        """
        session = self.get_session(session_id)
        if session is None:
            return None
        
        active_clients = session.get_active_clients(
            self.config.heartbeat_timeout_s
        )
        
        return {
            "session_id": session_id,
            "created_at": session.created_at,
            "last_activity": session.last_activity,
            "total_clients": len(session.clients),
            "active_clients": len(active_clients),
            "total_analyses": session.state.total_analyses,
            "avg_latency_ms": session.state.avg_latency_ms,
            "motion_state": session.state.motion_state.value,
        }


# Global persistent session manager instance
_persistent_session_manager: Optional[PersistentSessionManager] = None


def get_persistent_session_manager() -> PersistentSessionManager:
    """Get the global persistent session manager instance."""
    global _persistent_session_manager
    if _persistent_session_manager is None:
        _persistent_session_manager = PersistentSessionManager()
    return _persistent_session_manager
