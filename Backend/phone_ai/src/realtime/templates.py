"""
Advice Templates Module

建议模板，包含所有中文建议消息。
支持模板变量替换（如 {direction}）。
"""
from .types import AdvicePayload, AdvicePriority, AdviceCategory


# =============================================================================
# Stability Advice Templates (稳定性建议)
# Requirements: 2.1-2.4
# =============================================================================

STABILITY_CRITICAL = AdvicePayload(
    priority=AdvicePriority.CRITICAL,
    category=AdviceCategory.STABILITY,
    message="画面大幅抖动！请停下，尝试'忍者步'或寻找支撑点。",
    advanced_message="检测到高频震颤，建议检查云台电机是否过载，或开启机身增强防抖。",
    trigger_haptic=True,
    suppress_duration_s=5.0,
)

STABILITY_WARNING = AdvicePayload(
    priority=AdvicePriority.WARNING,
    category=AdviceCategory.STABILITY,
    message="手持略有不稳，请夹紧双肘，屏住呼吸。",
    suppress_duration_s=3.0,
)

STABILITY_POSITIVE = AdvicePayload(
    priority=AdvicePriority.POSITIVE,
    category=AdviceCategory.STABILITY,
    message="稳如泰山！保持当前状态。",
    suppress_duration_s=3.0,
)


# =============================================================================
# Speed Advice Templates (速度建议)
# Requirements: 3.1-3.3
# =============================================================================

SPEED_TOO_FAST = AdvicePayload(
    priority=AdvicePriority.WARNING,
    category=AdviceCategory.SPEED,
    message="移速太快了！请慢一点，给观众留出观察细节的时间。",
    suppress_duration_s=3.0,
)

SPEED_UNEVEN = AdvicePayload(
    priority=AdvicePriority.WARNING,
    category=AdviceCategory.SPEED,
    message="运镜不匀速，请保持平稳推拉，避免猛推猛拉。",
    suppress_duration_s=3.0,
)

SPEED_PERFECT = AdvicePayload(
    priority=AdvicePriority.POSITIVE,
    category=AdviceCategory.SPEED,
    message="运镜速度完美！",
    suppress_duration_s=3.0,
)


# =============================================================================
# Composition Advice Templates (构图建议)
# Requirements: 4.1-4.6
# =============================================================================

SUBJECT_OFF_CENTER = AdvicePayload(
    priority=AdvicePriority.WARNING,
    category=AdviceCategory.COMPOSITION,
    message="主体正在偏离中心（或三分法线），请向{direction}微调镜头。",
    suppress_duration_s=3.0,
)

SUBJECT_TOO_LARGE = AdvicePayload(
    priority=AdvicePriority.WARNING,
    category=AdviceCategory.COMPOSITION,
    message="主体遮挡占比过大，建议后退一步，给画面留白。",
    suppress_duration_s=3.0,
)

SUBJECT_TOO_SMALL = AdvicePayload(
    priority=AdvicePriority.WARNING,
    category=AdviceCategory.COMPOSITION,
    message="主体太小，建议靠近或使用长焦。",
    suppress_duration_s=3.0,
)

SUBJECT_LOST = AdvicePayload(
    priority=AdvicePriority.WARNING,
    category=AdviceCategory.COMPOSITION,
    message="主体丢失，请减慢运镜寻找主体。",
    suppress_duration_s=5.0,
)

DIRECTION_HINT = AdvicePayload(
    priority=AdvicePriority.INFO,
    category=AdviceCategory.COMPOSITION,
    message="正在进行{direction}，请坚持到底，不要中途{avoid}晃动。",
    suppress_duration_s=3.0,
)

# Direction mapping for template substitution
DIRECTION_NAMES = {
    "left": "向左横移",
    "right": "向右横移",
    "up": "向上摇镜",
    "down": "向下摇镜",
    "dolly_in": "推镜头",
    "dolly_out": "拉镜头",
}

AVOID_DIRECTIONS = {
    "left": "上下",
    "right": "上下",
    "up": "左右",
    "down": "左右",
    "dolly_in": "左右",
    "dolly_out": "左右",
}


# =============================================================================
# Beat Advice Templates (节拍同步建议)
# Requirements: 5.1-5.3
# =============================================================================

BEAT_UPCOMING = AdvicePayload(
    priority=AdvicePriority.INFO,
    category=AdviceCategory.BEAT,
    message="预感重音！建议此时配合一个快速推镜或转场动作。",
    suppress_duration_s=2.0,
)

BEAT_NOW = AdvicePayload(
    priority=AdvicePriority.INFO,
    category=AdviceCategory.BEAT,
    message="节奏点已到，可以考虑在此处切断或变换景别。",
    suppress_duration_s=2.0,
)


# =============================================================================
# Equipment Advice Templates (设备建议)
# Requirements: 6.1-6.3
# =============================================================================

MOTION_BLUR = AdvicePayload(
    priority=AdvicePriority.INFO,
    category=AdviceCategory.EQUIPMENT,
    message="检测到运动模糊较重，建议将快门速度提高到 1/125s 以上。",
    suppress_duration_s=5.0,
)

TELEPHOTO_SHAKE = AdvicePayload(
    priority=AdvicePriority.WARNING,
    category=AdviceCategory.EQUIPMENT,
    message="当前长焦段放大抖动明显，建议切换至广角端（0.5x）拍摄更稳。",
    suppress_duration_s=5.0,
)

STABILIZATION_SUGGESTION = AdvicePayload(
    priority=AdvicePriority.INFO,
    category=AdviceCategory.EQUIPMENT,
    message="建议使用三脚架或手持稳定器以获得更稳定的画面。",
    suppress_duration_s=5.0,
)


# =============================================================================
# Status Messages (状态消息)
# =============================================================================

ANALYZING_STATUS = AdvicePayload(
    priority=AdvicePriority.INFO,
    category=AdviceCategory.STABILITY,
    message="分析中...",
    suppress_duration_s=1.0,
)

LOW_CONFIDENCE_STATUS = AdvicePayload(
    priority=AdvicePriority.INFO,
    category=AdviceCategory.STABILITY,
    message="分析中...",
    suppress_duration_s=2.0,
)


# =============================================================================
# Template Dictionary (模板字典)
# =============================================================================

ADVICE_TEMPLATES = {
    # Stability
    "stability_critical": STABILITY_CRITICAL,
    "stability_warning": STABILITY_WARNING,
    "stability_positive": STABILITY_POSITIVE,
    
    # Speed
    "speed_too_fast": SPEED_TOO_FAST,
    "speed_uneven": SPEED_UNEVEN,
    "speed_perfect": SPEED_PERFECT,
    
    # Composition
    "subject_off_center": SUBJECT_OFF_CENTER,
    "subject_too_large": SUBJECT_TOO_LARGE,
    "subject_too_small": SUBJECT_TOO_SMALL,
    "subject_lost": SUBJECT_LOST,
    "direction_hint": DIRECTION_HINT,
    
    # Beat
    "beat_upcoming": BEAT_UPCOMING,
    "beat_now": BEAT_NOW,
    
    # Equipment
    "motion_blur": MOTION_BLUR,
    "telephoto_shake": TELEPHOTO_SHAKE,
    "stabilization_suggestion": STABILIZATION_SUGGESTION,
    
    # Status
    "analyzing": ANALYZING_STATUS,
    "low_confidence": LOW_CONFIDENCE_STATUS,
}


def get_template(template_key: str) -> AdvicePayload:
    """
    Get an advice template by key.
    
    Args:
        template_key: Key of the template to retrieve
        
    Returns:
        AdvicePayload template
        
    Raises:
        KeyError: If template key is not found
    """
    if template_key not in ADVICE_TEMPLATES:
        raise KeyError(f"Unknown template key: {template_key}")
    return ADVICE_TEMPLATES[template_key]


def get_direction_hint(direction: str) -> AdvicePayload:
    """
    Get a direction hint advice with proper substitution.
    
    Args:
        direction: Direction key (left, right, up, down, dolly_in, dolly_out)
        
    Returns:
        AdvicePayload with substituted direction text
    """
    direction_name = DIRECTION_NAMES.get(direction, direction)
    avoid_direction = AVOID_DIRECTIONS.get(direction, "其他方向")
    
    return DIRECTION_HINT.with_substitution(
        direction=direction_name,
        avoid=avoid_direction,
    )


def get_subject_off_center_advice(direction: str) -> AdvicePayload:
    """
    Get subject off-center advice with direction.
    
    Args:
        direction: Direction to adjust (左, 右, 上, 下)
        
    Returns:
        AdvicePayload with substituted direction
    """
    return SUBJECT_OFF_CENTER.with_substitution(direction=direction)
