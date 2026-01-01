"""
Motion State Machine Module

运动类型状态机，跟踪当前运动类型并提供抑制规则。
Tracks current motion type and provides suppression rules for advice filtering.
"""
from collections import deque
from dataclasses import dataclass
from typing import Optional

from src.models.enums import MotionType
from src.models.data_types import HeuristicOutput
from src.agents.motion_rules import MotionTypeInferrer, MotionRulesConfig


@dataclass
class MotionStateMachineConfig:
    """Configuration for motion state machine."""
    # History size for state tracking
    history_size: int = 5
    
    # Minimum confidence to accept a state change
    min_confidence_threshold: float = 0.4
    
    # Number of consistent inferences required to change state
    consistency_required: int = 2
    
    # Confidence decay factor when state is inconsistent
    confidence_decay: float = 0.9


class MotionStateMachine:
    """
    运动类型状态机
    Tracks current motion type and provides suppression rules.
    
    The state machine:
    1. Uses MotionTypeInferrer to classify motion from heuristic indicators
    2. Maintains state history for stability
    3. Requires consistent inferences before changing state
    4. Provides suppression rules based on current motion type
    
    Requirements:
    - 8.4: Motion type changes update state within 1 second
    - 8.5: Maintain motion type state across consecutive analysis cycles
    """
    
    def __init__(
        self,
        config: Optional[MotionStateMachineConfig] = None,
        motion_rules_config: Optional[MotionRulesConfig] = None
    ):
        """
        Initialize the motion state machine.
        
        Args:
            config: Configuration for state machine behavior
            motion_rules_config: Configuration for motion type inference
        """
        self.config = config or MotionStateMachineConfig()
        self._inferrer = MotionTypeInferrer(motion_rules_config)
        
        # Current state
        self._current_state: MotionType = MotionType.STATIC
        self._state_confidence: float = 0.0
        
        # State history for stability tracking
        self._state_history: deque[MotionType] = deque(maxlen=self.config.history_size)
        self._confidence_history: deque[float] = deque(maxlen=self.config.history_size)
        
        # Consistency counter for state changes
        self._pending_state: Optional[MotionType] = None
        self._pending_count: int = 0
        
        # Suppression rules per motion type
        self._suppression_rules = self._init_suppression_rules()
    
    def _init_suppression_rules(self) -> dict[MotionType, set[str]]:
        """
        Initialize suppression rules for each motion type.
        
        Suppression rules define which advice categories should be
        suppressed when a specific motion type is detected, to avoid
        giving irrelevant warnings during intentional camera movements.
        
        Requirements:
        - 8.1: Dolly/Track suppresses subject size change warnings
        - 8.2: Pan suppresses horizontal drift warnings
        - 8.3: Tilt suppresses vertical drift warnings
        """
        return {
            MotionType.DOLLY_IN: {"subject_size_change"},
            MotionType.DOLLY_OUT: {"subject_size_change"},
            MotionType.PAN: {"horizontal_drift"},
            MotionType.TILT: {"vertical_drift"},
            MotionType.TRACK: {"subject_size_change", "horizontal_drift"},
            MotionType.HANDHELD: set(),
            MotionType.STATIC: set(),
        }
    
    def get_current_state(self) -> MotionType:
        """
        Get the current motion type state.
        
        Returns:
            Current MotionType
        """
        return self._current_state
    
    def get_state_confidence(self) -> float:
        """
        Get the confidence level of the current state.
        
        Returns:
            Confidence value in range [0, 1]
        """
        return self._state_confidence
    
    def get_state_history(self) -> list[MotionType]:
        """
        Get the recent state history.
        
        Returns:
            List of recent motion types (oldest first)
        """
        return list(self._state_history)
    
    def get_suppression_rules(self) -> set[str]:
        """
        Get advice categories to suppress for current motion type.
        
        Returns:
            Set of category names to suppress
        """
        return self._suppression_rules.get(self._current_state, set())
    
    def should_suppress(self, category: str) -> bool:
        """
        Check if a specific advice category should be suppressed.
        
        Args:
            category: Advice category name
            
        Returns:
            True if the category should be suppressed
        """
        return category in self.get_suppression_rules()
    
    def update(
        self,
        indicators: HeuristicOutput,
        primary_direction_deg: Optional[float] = None
    ) -> MotionType:
        """
        Update state machine with new indicators.
        
        This method:
        1. Infers motion type from current indicators
        2. Calculates confidence for the inference
        3. Updates state if inference is consistent
        4. Maintains state history
        
        Args:
            indicators: Current heuristic indicators
            primary_direction_deg: Primary motion direction in degrees
            
        Returns:
            Current motion type (may or may not have changed)
        """
        # Infer motion type from indicators
        inferred_type = self._inferrer.infer_motion_type(
            indicators,
            primary_direction_deg
        )
        
        # Calculate confidence for this inference
        confidence = self._inferrer.calculate_confidence(
            indicators,
            inferred_type
        )
        
        # Update state based on inference
        self._process_inference(inferred_type, confidence)
        
        # Record in history
        self._state_history.append(self._current_state)
        self._confidence_history.append(self._state_confidence)
        
        return self._current_state
    
    def _process_inference(self, inferred_type: MotionType, confidence: float) -> None:
        """
        Process a new motion type inference and update state if appropriate.
        
        State changes require:
        1. Confidence above threshold
        2. Consistent inference across multiple cycles
        
        Args:
            inferred_type: Newly inferred motion type
            confidence: Confidence of the inference
        """
        # If inference matches current state, reinforce it
        if inferred_type == self._current_state:
            # Boost confidence (exponential moving average)
            self._state_confidence = 0.3 * confidence + 0.7 * self._state_confidence
            self._pending_state = None
            self._pending_count = 0
            return
        
        # If confidence is too low, decay current confidence but don't change
        if confidence < self.config.min_confidence_threshold:
            self._state_confidence *= self.config.confidence_decay
            return
        
        # Check if this is a consistent new state
        if inferred_type == self._pending_state:
            self._pending_count += 1
        else:
            # New pending state
            self._pending_state = inferred_type
            self._pending_count = 1
        
        # Change state if we have enough consistent inferences
        if self._pending_count >= self.config.consistency_required:
            self._current_state = inferred_type
            self._state_confidence = confidence
            self._pending_state = None
            self._pending_count = 0
    
    def reset(self) -> None:
        """
        Reset the state machine to initial state.
        
        Clears all history and resets to STATIC state.
        """
        self._current_state = MotionType.STATIC
        self._state_confidence = 0.0
        self._state_history.clear()
        self._confidence_history.clear()
        self._pending_state = None
        self._pending_count = 0
    
    def force_state(self, state: MotionType, confidence: float = 1.0) -> None:
        """
        Force the state machine to a specific state.
        
        Useful for testing or manual override.
        
        Args:
            state: Motion type to set
            confidence: Confidence level for the state
        """
        self._current_state = state
        self._state_confidence = max(0.0, min(1.0, confidence))
        self._pending_state = None
        self._pending_count = 0
