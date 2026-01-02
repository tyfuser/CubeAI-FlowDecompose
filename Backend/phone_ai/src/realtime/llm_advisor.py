"""
LLM-based Shooting Advisor

Takes optical flow analysis results and generates short (~10 character) 
shooting advice using LLM API.
"""
import logging
from dataclasses import dataclass
from typing import Optional

from src.services.llm_client import LLMClient, LLMConfig
from src.realtime.types import RealtimeAnalysisResult, AdvicePayload, AdvicePriority, AdviceCategory


logger = logging.getLogger(__name__)


@dataclass
class LLMAdvisorConfig:
    """Configuration for LLM advisor."""
    max_advice_length: int = 15  # Maximum characters for advice
    temperature: float = 0.7
    timeout: int = 10  # Shorter timeout for realtime


SYSTEM_PROMPT = """你是一个专业的手机拍摄助手。根据光流分析数据，生成简短的拍摄建议。

规则：
1. 建议必须在10个中文字以内
2. 使用简洁、直接的语言
3. 根据运动数据判断拍摄状态并给出实用建议
4. 只输出建议文字，不要任何解释或标点

运动状态判断：
- avg_speed < 2: 静止/稳定
- avg_speed 2-8: 缓慢移动
- avg_speed 8-20: 正常移动
- avg_speed > 20: 快速移动

- motion_smoothness > 0.7: 平滑
- motion_smoothness 0.4-0.7: 一般
- motion_smoothness < 0.4: 抖动

- speed_variance < 5: 速度稳定
- speed_variance > 15: 速度不稳定"""


def build_analysis_prompt(result: RealtimeAnalysisResult) -> str:
    """Build prompt from analysis result."""
    direction_names = {
        (0, 45): "右",
        (45, 135): "下",
        (135, 225): "左",
        (225, 315): "上",
        (315, 360): "右",
    }
    
    direction = "未知"
    deg = result.primary_direction_deg
    for (low, high), name in direction_names.items():
        if low <= deg < high:
            direction = name
            break
    
    return f"""光流分析数据：
- 平均速度: {result.avg_speed_px_frame:.1f} 像素/帧
- 速度方差: {result.speed_variance:.1f}
- 运动平滑度: {result.motion_smoothness:.2f} (0-1)
- 主要方向: {direction} ({result.primary_direction_deg:.0f}°)
- 置信度: {result.confidence:.2f}

请给出10字以内的拍摄建议："""


class LLMAdvisor:
    """
    LLM-based shooting advisor.
    
    Takes optical flow analysis results and generates short advice.
    """
    
    def __init__(self, config: Optional[LLMAdvisorConfig] = None):
        self.config = config or LLMAdvisorConfig()
        self._llm_client: Optional[LLMClient] = None
    
    def _get_llm_client(self) -> LLMClient:
        """Get or create LLM client."""
        if self._llm_client is None:
            llm_config = LLMConfig.from_settings()
            llm_config.temperature = self.config.temperature
            llm_config.timeout = self.config.timeout
            llm_config.max_tokens = 50  # Short response
            self._llm_client = LLMClient(llm_config)
        return self._llm_client
    
    async def generate_advice(
        self,
        analysis: RealtimeAnalysisResult
    ) -> AdvicePayload:
        """
        Generate shooting advice from analysis result.
        
        Args:
            analysis: Optical flow analysis result
            
        Returns:
            AdvicePayload with LLM-generated message
        """
        # Determine priority and category from analysis
        priority, category = self._determine_priority_category(analysis)
        
        try:
            # Generate advice using LLM
            client = self._get_llm_client()
            prompt = build_analysis_prompt(analysis)
            
            response = await client.complete(prompt, SYSTEM_PROMPT)
            
            # Clean and truncate response
            advice_text = response.strip()
            if len(advice_text) > self.config.max_advice_length:
                advice_text = advice_text[:self.config.max_advice_length]
            
            logger.info(f"LLM advice generated: {advice_text}")
            
            return AdvicePayload(
                priority=priority,
                category=category,
                message=advice_text,
                trigger_haptic=priority == AdvicePriority.CRITICAL,
                suppress_duration_s=3.0,
            )
            
        except Exception as e:
            logger.error(f"LLM advice generation failed: {e}")
            # Fallback to rule-based advice
            return self._generate_fallback_advice(analysis, priority, category)
    
    def _determine_priority_category(
        self,
        analysis: RealtimeAnalysisResult
    ) -> tuple[AdvicePriority, AdviceCategory]:
        """Determine advice priority and category from analysis."""
        speed = analysis.avg_speed_px_frame
        smoothness = analysis.motion_smoothness
        variance = analysis.speed_variance
        
        # Stability issues (high priority)
        if smoothness < 0.3:
            return AdvicePriority.CRITICAL, AdviceCategory.STABILITY
        
        if smoothness < 0.5:
            return AdvicePriority.WARNING, AdviceCategory.STABILITY
        
        # Speed issues
        if speed > 25:
            return AdvicePriority.WARNING, AdviceCategory.SPEED
        
        if variance > 20:
            return AdvicePriority.WARNING, AdviceCategory.SPEED
        
        # Good state
        if smoothness > 0.7 and speed < 15:
            return AdvicePriority.POSITIVE, AdviceCategory.STABILITY
        
        # Default info
        return AdvicePriority.INFO, AdviceCategory.COMPOSITION
    
    def _generate_fallback_advice(
        self,
        analysis: RealtimeAnalysisResult,
        priority: AdvicePriority,
        category: AdviceCategory
    ) -> AdvicePayload:
        """Generate rule-based fallback advice when LLM fails."""
        speed = analysis.avg_speed_px_frame
        smoothness = analysis.motion_smoothness
        
        # Rule-based advice
        if smoothness < 0.3:
            message = "画面抖动，请稳住"
        elif smoothness < 0.5:
            message = "稍有晃动，放慢"
        elif speed > 25:
            message = "移动太快了"
        elif speed > 15:
            message = "速度适中，保持"
        elif smoothness > 0.7:
            message = "很稳！继续保持"
        else:
            message = "状态良好"
        
        return AdvicePayload(
            priority=priority,
            category=category,
            message=message,
            trigger_haptic=priority == AdvicePriority.CRITICAL,
            suppress_duration_s=3.0,
        )


# Singleton instance
_advisor_instance: Optional[LLMAdvisor] = None


def get_llm_advisor() -> LLMAdvisor:
    """Get singleton LLM advisor instance."""
    global _advisor_instance
    if _advisor_instance is None:
        _advisor_instance = LLMAdvisor()
    return _advisor_instance
