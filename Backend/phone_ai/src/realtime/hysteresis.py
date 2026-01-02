"""
Hysteresis Controller Module

滞后控制器，防止建议快速切换。
Implements hysteresis thresholds and category-based cooldown to prevent
rapid toggling of advice and repetitive notifications.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class HysteresisConfig:
    """Configuration for hysteresis thresholds."""
    # Stability thresholds (lower is worse)
    # Enter threshold: value must go BELOW this to trigger warning
    # Exit threshold: value must go ABOVE this to clear warning
    stability_critical_enter: float = 0.35
    stability_critical_exit: float = 0.45
    stability_warning_enter: float = 0.65
    stability_warning_exit: float = 0.75
    
    # Speed thresholds (higher is worse)
    # Enter threshold: value must go ABOVE this to trigger warning
    # Exit threshold: value must go BELOW this to clear warning
    speed_warning_enter: float = 22.0
    speed_warning_exit: float = 18.0
    
    # Consistency requirement - number of consecutive cycles
    # with same state before triggering advice
    consistent_cycles_required: int = 2
    
    # Category-based cooldown (seconds)
    # Don't repeat same category advice within this time
    category_cooldown_s: float = 5.0


class HysteresisController:
    """
    滞后控制器
    Prevents rapid toggling of advice by implementing hysteresis.
    Also implements category-based cooldown to avoid repetitive advice.
    
    Hysteresis works by having separate enter and exit thresholds:
    - To enter a warning state, the value must cross the enter threshold
    - To exit a warning state, the value must cross the exit threshold
    - This prevents rapid toggling when values oscillate around a single threshold
    
    Consistency counter ensures stable triggering:
    - Advice is only generated after the same state is detected for
      `consistent_cycles_required` consecutive cycles
    """
    
    def __init__(self, config: Optional[HysteresisConfig] = None):
        self.config = config or HysteresisConfig()
        # Track current state for each category: "normal", "warning", "critical"
        self._current_states: dict[str, str] = {}
        # Track consecutive cycles in same state for each category
        self._consistency_counters: dict[str, int] = {}
        # Track pending state (state we're counting towards)
        self._pending_states: dict[str, str] = {}
        # Track last advice time per category for cooldown
        self._last_advice_time: dict[str, float] = {}
    
    def check_threshold(
        self,
        category: str,
        value: float,
        enter_threshold: float,
        exit_threshold: float,
        lower_is_worse: bool = True
    ) -> bool:
        """
        Check if value crosses threshold with hysteresis.
        
        Hysteresis prevents rapid toggling by using separate enter/exit thresholds.
        For example, with enter=0.4 and exit=0.5 (lower_is_worse=True):
        - Value must drop below 0.4 to enter warning state
        - Value must rise above 0.5 to exit warning state
        - Values between 0.4 and 0.5 maintain current state
        
        Args:
            category: Advice category name (used for state tracking)
            value: Current indicator value
            enter_threshold: Threshold to enter warning state
            exit_threshold: Threshold to exit warning state
            lower_is_worse: If True, values below enter_threshold trigger warning
                           If False, values above enter_threshold trigger warning
            
        Returns:
            True if advice should be generated (state is "warning" and consistent)
        """
        current_state = self._current_states.get(category, "normal")
        
        # Determine new state based on hysteresis logic
        if lower_is_worse:
            # Lower values are worse (e.g., stability)
            if current_state == "normal":
                # Need to go below enter threshold to trigger
                if value < enter_threshold:
                    new_state = "warning"
                else:
                    new_state = "normal"
            else:  # current_state == "warning"
                # Need to go above exit threshold to clear
                if value > exit_threshold:
                    new_state = "normal"
                else:
                    new_state = "warning"
        else:
            # Higher values are worse (e.g., speed)
            if current_state == "normal":
                # Need to go above enter threshold to trigger
                if value > enter_threshold:
                    new_state = "warning"
                else:
                    new_state = "normal"
            else:  # current_state == "warning"
                # Need to go below exit threshold to clear
                if value < exit_threshold:
                    new_state = "normal"
                else:
                    new_state = "warning"
        
        # Update state
        self._current_states[category] = new_state
        
        # Return True if in warning state
        return new_state == "warning"
    
    def check_threshold_multi_level(
        self,
        category: str,
        value: float,
        critical_enter: float,
        critical_exit: float,
        warning_enter: float,
        warning_exit: float,
        lower_is_worse: bool = True
    ) -> str:
        """
        Check threshold with multiple levels (critical, warning, normal).
        
        Args:
            category: Advice category name
            value: Current indicator value
            critical_enter: Threshold to enter critical state
            critical_exit: Threshold to exit critical state
            warning_enter: Threshold to enter warning state
            warning_exit: Threshold to exit warning state
            lower_is_worse: If True, lower values are worse
            
        Returns:
            State string: "critical", "warning", or "normal"
        """
        current_state = self._current_states.get(category, "normal")
        
        if lower_is_worse:
            # Lower values are worse (e.g., stability: 0=bad, 1=good)
            if current_state == "critical":
                # Need to go above critical_exit to leave critical
                if value > critical_exit:
                    # Check if we should go to warning or normal
                    if value < warning_exit:
                        new_state = "warning"
                    else:
                        new_state = "normal"
                else:
                    new_state = "critical"
            elif current_state == "warning":
                # Check if we should go to critical
                if value < critical_enter:
                    new_state = "critical"
                # Check if we should go to normal
                elif value > warning_exit:
                    new_state = "normal"
                else:
                    new_state = "warning"
            else:  # normal
                # Check if we should enter critical or warning
                if value < critical_enter:
                    new_state = "critical"
                elif value < warning_enter:
                    new_state = "warning"
                else:
                    new_state = "normal"
        else:
            # Higher values are worse (e.g., speed: high=bad)
            if current_state == "critical":
                if value < critical_exit:
                    if value > warning_exit:
                        new_state = "warning"
                    else:
                        new_state = "normal"
                else:
                    new_state = "critical"
            elif current_state == "warning":
                if value > critical_enter:
                    new_state = "critical"
                elif value < warning_exit:
                    new_state = "normal"
                else:
                    new_state = "warning"
            else:  # normal
                if value > critical_enter:
                    new_state = "critical"
                elif value > warning_enter:
                    new_state = "warning"
                else:
                    new_state = "normal"
        
        self._current_states[category] = new_state
        return new_state
    
    def is_consistent(self, category: str, should_trigger: bool) -> bool:
        """
        Check if trigger state is consistent across multiple cycles.
        
        This prevents advice from being generated on transient spikes.
        The same state must be detected for `consistent_cycles_required`
        consecutive cycles before advice is generated.
        
        Args:
            category: Advice category name
            should_trigger: Whether current cycle wants to trigger advice
            
        Returns:
            True if state has been consistent for required cycles
        """
        pending_state = "trigger" if should_trigger else "normal"
        current_pending = self._pending_states.get(category, "normal")
        
        if pending_state == current_pending:
            # Same state as before, increment counter
            self._consistency_counters[category] = (
                self._consistency_counters.get(category, 0) + 1
            )
        else:
            # State changed, reset counter
            self._pending_states[category] = pending_state
            self._consistency_counters[category] = 1
        
        # Check if we've reached required consistency
        return (
            should_trigger and 
            self._consistency_counters.get(category, 0) >= self.config.consistent_cycles_required
        )
    
    def is_on_cooldown(self, category: str, current_time: float) -> bool:
        """
        Check if category is on cooldown (recently triggered).
        
        Cooldown prevents the same category of advice from being
        repeated too frequently, which would be annoying to users.
        
        Args:
            category: Advice category name
            current_time: Current timestamp in seconds
            
        Returns:
            True if advice should be suppressed due to cooldown
        """
        last_time = self._last_advice_time.get(category, 0)
        return (current_time - last_time) < self.config.category_cooldown_s
    
    def record_advice(self, category: str, current_time: float) -> None:
        """
        Record that advice was generated for cooldown tracking.
        
        Call this after successfully generating and sending advice
        to start the cooldown timer for this category.
        
        Args:
            category: Advice category name
            current_time: Current timestamp in seconds
        """
        self._last_advice_time[category] = current_time
    
    def get_state(self, category: str) -> str:
        """
        Get current state for a category.
        
        Args:
            category: Advice category name
            
        Returns:
            Current state: "normal", "warning", or "critical"
        """
        return self._current_states.get(category, "normal")
    
    def reset(self, category: Optional[str] = None) -> None:
        """
        Reset state for a category or all categories.
        
        Args:
            category: Category to reset, or None to reset all
        """
        if category is None:
            self._current_states.clear()
            self._consistency_counters.clear()
            self._pending_states.clear()
            self._last_advice_time.clear()
        else:
            self._current_states.pop(category, None)
            self._consistency_counters.pop(category, None)
            self._pending_states.pop(category, None)
            self._last_advice_time.pop(category, None)
