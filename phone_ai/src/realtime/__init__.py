"""
Realtime Shooting Advisor Module

实时拍摄建议系统模块，提供边拍边分析的实时反馈功能。

Components:
- RealtimeAnalyzer: 实时帧分析器
- AdviceEngine: 建议生成引擎
- SmoothingFilter: 平滑滤波器
- MotionStateMachine: 运动状态机
- HysteresisController: 滞后控制器
- RealtimeWebSocketHandler: WebSocket 处理器
- SessionManager: 会话管理器
"""

from .types import (
    AdvicePriority,
    AdviceCategory,
    RealtimeAnalysisResult,
    AdvicePayload,
    SessionState,
    FrameBufferPayload,
)
from .analyzer import RealtimeAnalyzer, RealtimeAnalyzerConfig
from .advice_engine import AdviceEngine, AdviceEngineConfig
from .smoothing import SmoothingFilter, SmoothingFilterConfig
from .state_machine import MotionStateMachine, MotionStateMachineConfig
from .hysteresis import HysteresisController, HysteresisConfig
from .templates import ADVICE_TEMPLATES
from .websocket_handler import (
    RealtimeWebSocketHandler,
    SessionManager,
    WebSocketHandlerConfig,
    ReconnectionManager,
    get_session_manager,
    create_websocket_handler,
)
from .session_manager import (
    PersistentSessionManager,
    SessionConfig,
    SessionData,
    ClientConnection,
    get_persistent_session_manager,
)

__all__ = [
    # Types and Enums
    "AdvicePriority",
    "AdviceCategory",
    "RealtimeAnalysisResult",
    "AdvicePayload",
    "SessionState",
    "FrameBufferPayload",
    # Components
    "RealtimeAnalyzer",
    "RealtimeAnalyzerConfig",
    "AdviceEngine",
    "AdviceEngineConfig",
    "SmoothingFilter",
    "SmoothingFilterConfig",
    "MotionStateMachine",
    "MotionStateMachineConfig",
    "HysteresisController",
    "HysteresisConfig",
    # WebSocket
    "RealtimeWebSocketHandler",
    "SessionManager",
    "WebSocketHandlerConfig",
    "ReconnectionManager",
    "get_session_manager",
    "create_websocket_handler",
    # Session Management
    "PersistentSessionManager",
    "SessionConfig",
    "SessionData",
    "ClientConnection",
    "get_persistent_session_manager",
    # Templates
    "ADVICE_TEMPLATES",
]
