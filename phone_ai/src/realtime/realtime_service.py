"""
Realtime Shooting Service

Combines optical flow analyzer with LLM advisor to provide
end-to-end frame analysis and advice generation.
"""
import logging
import time
from dataclasses import dataclass
from typing import Optional

from src.realtime.analyzer import RealtimeAnalyzer, RealtimeAnalyzerConfig
from src.realtime.llm_advisor import LLMAdvisor, LLMAdvisorConfig, get_llm_advisor
from src.realtime.types import RealtimeAnalysisResult, AdvicePayload


logger = logging.getLogger(__name__)


@dataclass
class RealtimeServiceConfig:
    """Configuration for realtime service."""
    analyzer_config: Optional[RealtimeAnalyzerConfig] = None
    advisor_config: Optional[LLMAdvisorConfig] = None
    min_frames_for_analysis: int = 5
    enable_llm_advice: bool = True


class RealtimeService:
    """
    Realtime shooting analysis service.
    
    Processes frame buffers through:
    1. Base64 decoding
    2. Optical flow analysis
    3. LLM advice generation
    """
    
    def __init__(self, config: Optional[RealtimeServiceConfig] = None):
        self.config = config or RealtimeServiceConfig()
        self._analyzer = RealtimeAnalyzer(self.config.analyzer_config)
        self._advisor = LLMAdvisor(self.config.advisor_config)
    
    async def process_frame_buffer(
        self,
        base64_frames: list[str],
        fps: float = 30.0,
        generate_advice: bool = True
    ) -> tuple[RealtimeAnalysisResult, Optional[AdvicePayload]]:
        """
        Process a buffer of Base64-encoded frames.
        
        Args:
            base64_frames: List of Base64-encoded JPEG frames
            fps: Frames per second
            generate_advice: Whether to generate LLM advice
            
        Returns:
            Tuple of (analysis_result, advice_payload)
        """
        start_time = time.time()
        
        # Decode frames
        logger.info(f"Decoding {len(base64_frames)} frames...")
        frames = self._analyzer.decode_frame_buffer(base64_frames)
        
        if len(frames) < self.config.min_frames_for_analysis:
            logger.warning(f"Insufficient frames: {len(frames)} < {self.config.min_frames_for_analysis}")
            return RealtimeAnalysisResult(
                avg_speed_px_frame=0.0,
                speed_variance=0.0,
                motion_smoothness=0.5,
                primary_direction_deg=0.0,
                confidence=0.0,
                analysis_latency_ms=0.0,
            ), None
        
        decode_time = time.time() - start_time
        logger.info(f"Decoded {len(frames)} frames in {decode_time*1000:.1f}ms")
        
        # Analyze frames
        analysis_start = time.time()
        result = self._analyzer.analyze_buffer(frames, fps)
        analysis_time = time.time() - analysis_start
        
        logger.info(
            f"Analysis complete: speed={result.avg_speed_px_frame:.1f}, "
            f"smoothness={result.motion_smoothness:.2f}, "
            f"direction={result.primary_direction_deg:.0f}°, "
            f"latency={analysis_time*1000:.1f}ms"
        )
        
        # Generate advice if enabled
        advice = None
        if generate_advice and self.config.enable_llm_advice:
            try:
                advice_start = time.time()
                advice = await self._advisor.generate_advice(result)
                advice_time = time.time() - advice_start
                logger.info(f"Advice generated in {advice_time*1000:.1f}ms: {advice.message}")
            except Exception as e:
                logger.error(f"Advice generation failed: {e}")
        
        total_time = time.time() - start_time
        logger.info(f"Total processing time: {total_time*1000:.1f}ms")
        
        return result, advice
    
    def reset(self) -> None:
        """Reset service state."""
        self._analyzer.reset()


# Singleton instance
_service_instance: Optional[RealtimeService] = None


def get_realtime_service() -> RealtimeService:
    """Get singleton realtime service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = RealtimeService()
    return _service_instance
