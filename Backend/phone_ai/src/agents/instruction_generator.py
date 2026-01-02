"""
Instruction Generator Agent for the Video Shooting Assistant.

Generates three-layer shooting instruction cards from metadata:
- Layer 1 (Primary): 1-4 lines of actionable advice
- Layer 2 (Explain): 1-3 sentences explaining rationale
- Layer 3 (Advanced): Adjustable parameters and professional tips

Requirements covered:
- 5.1: Generate Layer1 Primary instructions
- 5.2: Include time range, action type, duration, operation tips, equipment, confidence
- 5.3: Generate Layer2 Explain with 1-3 sentences
- 5.4: Generate Layer3 Advanced with adjustable parameters
- 5.5-5.7: Speed description mapping based on frame_pct_change
- 5.8-5.10: Equipment recommendation mapping based on motion_smoothness
"""
import logging
from dataclasses import dataclass
from typing import Optional

from src.models.data_types import (
    AdvancedParams,
    InstructionCard,
    MetadataOutput,
)
from src.models.enums import MotionType, SpeedProfile, SuggestedScale


logger = logging.getLogger(__name__)


@dataclass
class InstructionGeneratorConfig:
    """Configuration for the Instruction Generator Agent."""
    
    # Speed description thresholds (Requirements 5.5-5.7)
    slow_threshold: float = 0.1  # frame_pct_change < 0.1 -> "缓慢"
    fast_threshold: float = 0.25  # frame_pct_change > 0.25 -> "快速"
    
    # Equipment recommendation thresholds (Requirements 5.8-5.10)
    high_smoothness_threshold: float = 0.7  # motion_smoothness > 0.7 -> slider/dolly/gimbal
    low_smoothness_threshold: float = 0.4  # motion_smoothness < 0.4 -> static/minimal
    
    # Confidence thresholds for alternative suggestions
    high_confidence_threshold: float = 0.75
    medium_confidence_threshold: float = 0.55


class InstructionGeneratorAgent:
    """
    拍摄指令卡生成模块
    
    Generates three-layer shooting instruction cards from metadata.
    Maps numerical indicators to human-readable Chinese descriptions
    and actionable shooting advice.
    """
    
    def __init__(self, config: Optional[InstructionGeneratorConfig] = None):
        """
        Initialize the Instruction Generator Agent.
        
        Args:
            config: Configuration options for instruction generation
        """
        self.config = config or InstructionGeneratorConfig()
    
    # =========================================================================
    # Speed Description Mapping (Requirements 5.5, 5.6, 5.7)
    # =========================================================================
    
    def map_speed_description(
        self,
        frame_pct_change: float,
        motion_type: MotionType
    ) -> str:
        """
        Map frame_pct_change to speed description text.
        
        Requirements:
        - 5.5: frame_pct_change < 0.1 -> "缓慢推进"
        - 5.6: 0.1 <= frame_pct_change <= 0.25 -> "中速推进/拉远"
        - 5.7: frame_pct_change > 0.25 -> "快速推进或换镜头"
        
        Args:
            frame_pct_change: Subject area change ratio (0-1)
            motion_type: Type of camera motion
            
        Returns:
            Chinese speed description string
        """
        # Determine direction based on motion type
        if motion_type == MotionType.DOLLY_IN:
            direction = "推进"
        elif motion_type == MotionType.DOLLY_OUT:
            direction = "拉远"
        elif motion_type == MotionType.PAN:
            direction = "横移"
        elif motion_type == MotionType.TILT:
            direction = "纵移"
        elif motion_type == MotionType.TRACK:
            direction = "跟踪"
        elif motion_type == MotionType.HANDHELD:
            direction = "手持移动"
        elif motion_type == MotionType.STATIC:
            return "静止"
        else:
            direction = "运动"
        
        # Map speed based on frame_pct_change thresholds
        if frame_pct_change < self.config.slow_threshold:
            # Requirement 5.5: 缓慢
            return f"缓慢{direction}"
        elif frame_pct_change <= self.config.fast_threshold:
            # Requirement 5.6: 中速
            return f"中速{direction}"
        else:
            # Requirement 5.7: 快速
            if motion_type in (MotionType.DOLLY_IN, MotionType.DOLLY_OUT):
                return f"快速{direction}或换镜头"
            else:
                return f"快速{direction}"
    
    def get_speed_category(self, frame_pct_change: float) -> str:
        """
        Get the speed category for a given frame_pct_change value.
        
        Args:
            frame_pct_change: Subject area change ratio (0-1)
            
        Returns:
            Speed category: "slow", "medium", or "fast"
        """
        if frame_pct_change < self.config.slow_threshold:
            return "slow"
        elif frame_pct_change <= self.config.fast_threshold:
            return "medium"
        else:
            return "fast"

    
    # =========================================================================
    # Equipment Recommendation Mapping (Requirements 5.8, 5.9, 5.10)
    # =========================================================================
    
    def map_equipment_suggestion(self, motion_smoothness: float) -> str:
        """
        Map motion_smoothness to equipment recommendation.
        
        Requirements:
        - 5.8: motion_smoothness > 0.7 -> slider/dolly/gimbal
        - 5.9: 0.4 <= motion_smoothness <= 0.7 -> handheld with gimbal
        - 5.10: motion_smoothness < 0.4 -> static shot or minimal movement
        
        Args:
            motion_smoothness: Motion smoothness score (0-1, higher = smoother)
            
        Returns:
            Chinese equipment recommendation string
        """
        if motion_smoothness > self.config.high_smoothness_threshold:
            # Requirement 5.8: High smoothness -> professional stabilization
            return "建议使用滑轨/电动滑轨/三轴稳定器"
        elif motion_smoothness >= self.config.low_smoothness_threshold:
            # Requirement 5.9: Medium smoothness -> handheld with gimbal
            return "建议手持配合云台/稳定器使用"
        else:
            # Requirement 5.10: Low smoothness -> static or minimal
            return "建议使用三脚架静态拍摄或减少运动幅度"
    
    def get_equipment_category(self, motion_smoothness: float) -> str:
        """
        Get the equipment category for a given motion_smoothness value.
        
        Args:
            motion_smoothness: Motion smoothness score (0-1)
            
        Returns:
            Equipment category: "professional", "handheld_gimbal", or "static"
        """
        if motion_smoothness > self.config.high_smoothness_threshold:
            return "professional"
        elif motion_smoothness >= self.config.low_smoothness_threshold:
            return "handheld_gimbal"
        else:
            return "static"
    
    def get_stabilization_recommendation(
        self,
        motion_smoothness: float,
        motion_type: MotionType
    ) -> str:
        """
        Get detailed stabilization recommendation based on motion characteristics.
        
        Args:
            motion_smoothness: Motion smoothness score (0-1)
            motion_type: Type of camera motion
            
        Returns:
            Detailed stabilization recommendation in Chinese
        """
        equipment_category = self.get_equipment_category(motion_smoothness)
        
        if equipment_category == "professional":
            if motion_type in (MotionType.DOLLY_IN, MotionType.DOLLY_OUT):
                return "电动滑轨或轨道车"
            elif motion_type == MotionType.TRACK:
                return "三轴稳定器或斯坦尼康"
            elif motion_type in (MotionType.PAN, MotionType.TILT):
                return "电动云台或液压云台"
            else:
                return "三轴稳定器"
        elif equipment_category == "handheld_gimbal":
            if motion_type == MotionType.HANDHELD:
                return "手持稳定器"
            else:
                return "手持云台"
        else:
            if motion_type == MotionType.STATIC:
                return "三脚架"
            else:
                return "三脚架或独脚架"

    
    # =========================================================================
    # Layer 1: Primary Instructions (Requirements 5.1, 5.2)
    # =========================================================================
    
    def generate_primary(self, metadata: MetadataOutput) -> list[str]:
        """
        Generate Layer1 Primary instructions with 1-4 lines of actionable advice.
        
        Requirements:
        - 5.1: Generate Layer1 Primary instructions with 1-4 lines
        - 5.2: Include time range, action type, duration, operation tips,
               equipment suggestions, and confidence
        
        Args:
            metadata: Metadata from the Metadata Synthesizer
            
        Returns:
            List of 1-4 actionable instruction strings in Chinese
        """
        instructions = []
        
        # Extract key values
        time_range = metadata.time_range
        motion_type = metadata.motion_type
        motion_params = metadata.motion_params
        confidence = metadata.confidence
        
        # Line 1: Time range and action type
        start_time = f"{time_range[0]:.1f}"
        end_time = f"{time_range[1]:.1f}"
        action_type = self._get_action_type_chinese(motion_type)
        instructions.append(
            f"时间段 {start_time}s - {end_time}s：{action_type}"
        )
        
        # Line 2: Speed description and duration
        speed_desc = self.map_speed_description(
            motion_params.frame_pct_change,
            motion_type
        )
        duration = motion_params.duration_s
        instructions.append(
            f"运动方式：{speed_desc}，持续 {duration:.1f} 秒"
        )
        
        # Line 3: Equipment suggestion
        equipment = self.map_equipment_suggestion(motion_params.motion_smoothness)
        instructions.append(equipment)
        
        # Line 4: Confidence and alternative (if confidence is not high)
        if confidence > self.config.high_confidence_threshold:
            instructions.append(f"置信度：{confidence:.0%}，推荐执行")
        elif confidence >= self.config.medium_confidence_threshold:
            instructions.append(
                f"置信度：{confidence:.0%}，请尝试并拍摄两条版本"
            )
        else:
            alternative = self._get_alternative_suggestion(metadata)
            instructions.append(
                f"置信度：{confidence:.0%}，建议人工确认。备选：{alternative}"
            )
        
        return instructions
    
    def _get_action_type_chinese(self, motion_type: MotionType) -> str:
        """
        Get Chinese description for motion type.
        
        Args:
            motion_type: Type of camera motion
            
        Returns:
            Chinese action type description
        """
        action_map = {
            MotionType.DOLLY_IN: "推镜头",
            MotionType.DOLLY_OUT: "拉镜头",
            MotionType.PAN: "横摇镜头",
            MotionType.TILT: "纵摇镜头",
            MotionType.TRACK: "跟踪镜头",
            MotionType.HANDHELD: "手持镜头",
            MotionType.STATIC: "静态镜头",
        }
        return action_map.get(motion_type, "未知镜头类型")
    
    def _get_alternative_suggestion(self, metadata: MetadataOutput) -> str:
        """
        Generate alternative suggestion for low confidence cases.
        
        Args:
            metadata: Metadata from the Metadata Synthesizer
            
        Returns:
            Alternative suggestion string
        """
        motion_type = metadata.motion_type
        
        # Suggest simpler alternatives
        alternatives = {
            MotionType.DOLLY_IN: "静态特写或缓慢推进",
            MotionType.DOLLY_OUT: "静态全景或缓慢拉远",
            MotionType.PAN: "静态拍摄或分段横摇",
            MotionType.TILT: "静态拍摄或分段纵摇",
            MotionType.TRACK: "固定机位跟拍或手持跟踪",
            MotionType.HANDHELD: "三脚架固定拍摄",
            MotionType.STATIC: "保持当前静态拍摄",
        }
        return alternatives.get(motion_type, "静态拍摄")

    
    # =========================================================================
    # Layer 2: Explain (Requirement 5.3)
    # =========================================================================
    
    def generate_explain(self, metadata: MetadataOutput) -> str:
        """
        Generate Layer2 Explain with 1-3 sentences explaining the recommendation rationale.
        
        Requirement 5.3: Generate Layer2 Explain with 1-3 sentences explaining
        the recommendation rationale.
        
        Args:
            metadata: Metadata from the Metadata Synthesizer
            
        Returns:
            1-3 sentence explanation string in Chinese
        """
        motion_type = metadata.motion_type
        motion_params = metadata.motion_params
        framing = metadata.framing
        beat_alignment = metadata.beat_alignment_score
        
        sentences = []
        
        # Sentence 1: Explain the motion type choice
        motion_reason = self._explain_motion_type(
            motion_type,
            motion_params.frame_pct_change,
            motion_params.motion_smoothness
        )
        sentences.append(motion_reason)
        
        # Sentence 2: Explain composition/framing
        framing_reason = self._explain_framing(
            framing.subject_occupancy,
            framing.suggested_scale
        )
        sentences.append(framing_reason)
        
        # Sentence 3 (optional): Explain rhythm/beat alignment if significant
        if beat_alignment > 0.5:
            rhythm_reason = self._explain_rhythm(beat_alignment)
            sentences.append(rhythm_reason)
        
        return "".join(sentences)
    
    def _explain_motion_type(
        self,
        motion_type: MotionType,
        frame_pct_change: float,
        motion_smoothness: float
    ) -> str:
        """
        Generate explanation for the motion type recommendation.
        
        Args:
            motion_type: Type of camera motion
            frame_pct_change: Subject area change ratio
            motion_smoothness: Motion smoothness score
            
        Returns:
            Explanation sentence in Chinese
        """
        speed_category = self.get_speed_category(frame_pct_change)
        smoothness_desc = "流畅" if motion_smoothness > 0.7 else "适中" if motion_smoothness > 0.4 else "需要稳定"
        
        explanations = {
            MotionType.DOLLY_IN: f"画面呈现向前推进的特征，主体逐渐放大，运动{smoothness_desc}。",
            MotionType.DOLLY_OUT: f"画面呈现向后拉远的特征，展示更多环境，运动{smoothness_desc}。",
            MotionType.PAN: f"画面呈现水平横移特征，适合展示宽广场景，运动{smoothness_desc}。",
            MotionType.TILT: f"画面呈现垂直移动特征，适合展示高度变化，运动{smoothness_desc}。",
            MotionType.TRACK: f"画面呈现跟随主体运动的特征，保持主体在画面中的位置，运动{smoothness_desc}。",
            MotionType.HANDHELD: f"画面呈现手持拍摄的自然晃动特征，具有临场感。",
            MotionType.STATIC: f"画面稳定无明显运动，适合静态构图或等待动作发生。",
        }
        
        return explanations.get(motion_type, f"检测到{motion_type.value}类型的镜头运动。")
    
    def _explain_framing(
        self,
        subject_occupancy: float,
        suggested_scale: SuggestedScale
    ) -> str:
        """
        Generate explanation for the framing recommendation.
        
        Args:
            subject_occupancy: Subject area ratio (0-1)
            suggested_scale: Suggested framing scale
            
        Returns:
            Explanation sentence in Chinese
        """
        occupancy_pct = int(subject_occupancy * 100)
        
        scale_descriptions = {
            SuggestedScale.EXTREME_CLOSEUP: "特写",
            SuggestedScale.CLOSEUP: "近景",
            SuggestedScale.MEDIUM: "中景",
            SuggestedScale.WIDE: "远景/全景",
        }
        scale_desc = scale_descriptions.get(suggested_scale, "中景")
        
        if subject_occupancy >= 0.5:
            return f"主体占画面约{occupancy_pct}%，构图紧凑，建议{scale_desc}拍摄以突出主体细节。"
        elif subject_occupancy >= 0.25:
            return f"主体占画面约{occupancy_pct}%，构图均衡，建议{scale_desc}拍摄以平衡主体与环境。"
        elif subject_occupancy >= 0.1:
            return f"主体占画面约{occupancy_pct}%，环境占比较大，建议{scale_desc}拍摄以展示场景氛围。"
        else:
            return f"主体占画面约{occupancy_pct}%，以环境为主，建议{scale_desc}拍摄以呈现整体场景。"
    
    def _explain_rhythm(self, beat_alignment: float) -> str:
        """
        Generate explanation for rhythm/beat alignment.
        
        Args:
            beat_alignment: Beat alignment score (0-1)
            
        Returns:
            Explanation sentence in Chinese
        """
        if beat_alignment > 0.8:
            return "镜头运动与音乐节拍高度同步，建议保持这种节奏感。"
        elif beat_alignment > 0.6:
            return "镜头运动与音乐节拍较为同步，可适当强化节奏配合。"
        else:
            return "镜头运动与音乐节拍有一定关联，可考虑调整以增强节奏感。"

    
    # =========================================================================
    # Layer 3: Advanced Parameters (Requirement 5.4)
    # =========================================================================
    
    def generate_advanced(self, metadata: MetadataOutput) -> AdvancedParams:
        """
        Generate Layer3 Advanced with adjustable parameters and professional tips.
        
        Requirement 5.4: Generate Layer3 Advanced with specific adjustable
        parameters and professional tips.
        
        Args:
            metadata: Metadata from the Metadata Synthesizer
            
        Returns:
            AdvancedParams with adjustable parameters and notes
        """
        motion_params = metadata.motion_params
        framing = metadata.framing
        motion_type = metadata.motion_type
        
        # Target occupancy description
        target_occupancy = self._get_target_occupancy_description(
            framing.subject_occupancy,
            framing.suggested_scale
        )
        
        # Duration
        duration_s = motion_params.duration_s
        
        # Speed curve description
        speed_curve = self._get_speed_curve_description(motion_params.speed_profile)
        
        # Stabilization recommendation
        stabilization = self.get_stabilization_recommendation(
            motion_params.motion_smoothness,
            motion_type
        )
        
        # Professional notes
        notes = self._generate_professional_notes(metadata)
        
        return AdvancedParams(
            target_occupancy=target_occupancy,
            duration_s=duration_s,
            speed_curve=speed_curve,
            stabilization=stabilization,
            notes=notes,
        )
    
    def _get_target_occupancy_description(
        self,
        current_occupancy: float,
        suggested_scale: SuggestedScale
    ) -> str:
        """
        Get target occupancy description based on suggested scale.
        
        Args:
            current_occupancy: Current subject occupancy (0-1)
            suggested_scale: Suggested framing scale
            
        Returns:
            Target occupancy description string
        """
        # Target occupancy ranges for each scale
        target_ranges = {
            SuggestedScale.EXTREME_CLOSEUP: "60%-80%",
            SuggestedScale.CLOSEUP: "40%-60%",
            SuggestedScale.MEDIUM: "20%-40%",
            SuggestedScale.WIDE: "5%-20%",
        }
        
        target = target_ranges.get(suggested_scale, "20%-40%")
        current_pct = int(current_occupancy * 100)
        
        return f"当前{current_pct}%，目标{target}"
    
    def _get_speed_curve_description(self, speed_profile: SpeedProfile) -> str:
        """
        Get speed curve description in Chinese.
        
        Args:
            speed_profile: Speed profile enum
            
        Returns:
            Speed curve description string
        """
        descriptions = {
            SpeedProfile.EASE_IN: "渐入（开始慢，逐渐加速）",
            SpeedProfile.EASE_OUT: "渐出（开始快，逐渐减速）",
            SpeedProfile.EASE_IN_OUT: "渐入渐出（两端慢，中间快）",
            SpeedProfile.LINEAR: "线性（匀速运动）",
        }
        return descriptions.get(speed_profile, "线性")
    
    def _generate_professional_notes(self, metadata: MetadataOutput) -> list[str]:
        """
        Generate professional tips and physical estimates.
        
        Args:
            metadata: Metadata from the Metadata Synthesizer
            
        Returns:
            List of professional notes/tips
        """
        notes = []
        motion_type = metadata.motion_type
        motion_params = metadata.motion_params
        framing = metadata.framing
        
        # Tip 1: Physical movement estimate
        physical_estimate = self._estimate_physical_movement(
            motion_type,
            motion_params.frame_pct_change,
            motion_params.duration_s
        )
        if physical_estimate:
            notes.append(physical_estimate)
        
        # Tip 2: Lens/focal length suggestion
        lens_tip = self._suggest_lens(framing.suggested_scale, motion_type)
        if lens_tip:
            notes.append(lens_tip)
        
        # Tip 3: Timing/rhythm tip
        if metadata.beat_alignment_score > 0.5:
            notes.append("注意与音乐节拍配合，可在节拍点开始或结束运动")
        
        # Tip 4: Smoothness improvement tip
        if motion_params.motion_smoothness < 0.5:
            notes.append("当前运动较为抖动，建议增加稳定措施或降低运动速度")
        
        # Tip 5: Composition tip based on scale
        composition_tip = self._get_composition_tip(framing.suggested_scale)
        if composition_tip:
            notes.append(composition_tip)
        
        return notes
    
    def _estimate_physical_movement(
        self,
        motion_type: MotionType,
        frame_pct_change: float,
        duration_s: float
    ) -> Optional[str]:
        """
        Estimate physical camera movement distance/angle.
        
        Args:
            motion_type: Type of camera motion
            frame_pct_change: Subject area change ratio
            duration_s: Duration in seconds
            
        Returns:
            Physical movement estimate string or None
        """
        if motion_type == MotionType.STATIC:
            return None
        
        if motion_type in (MotionType.DOLLY_IN, MotionType.DOLLY_OUT):
            # Estimate distance based on frame change
            # Rough estimate: 10% change ≈ 0.5m movement
            distance_m = frame_pct_change * 5.0
            speed_m_s = distance_m / duration_s if duration_s > 0 else 0
            return f"预估移动距离约 {distance_m:.1f}m，速度约 {speed_m_s:.2f}m/s"
        
        elif motion_type in (MotionType.PAN, MotionType.TILT):
            # Estimate angle based on frame change
            # Rough estimate: 10% change ≈ 15° rotation
            angle_deg = frame_pct_change * 150
            angular_speed = angle_deg / duration_s if duration_s > 0 else 0
            direction = "水平" if motion_type == MotionType.PAN else "垂直"
            return f"预估{direction}旋转约 {angle_deg:.0f}°，角速度约 {angular_speed:.1f}°/s"
        
        elif motion_type == MotionType.TRACK:
            # Estimate tracking distance
            distance_m = frame_pct_change * 3.0
            return f"预估跟踪距离约 {distance_m:.1f}m"
        
        return None
    
    def _suggest_lens(
        self,
        suggested_scale: SuggestedScale,
        motion_type: MotionType
    ) -> Optional[str]:
        """
        Suggest lens/focal length based on scale and motion.
        
        Args:
            suggested_scale: Suggested framing scale
            motion_type: Type of camera motion
            
        Returns:
            Lens suggestion string or None
        """
        # Base focal length suggestions
        focal_suggestions = {
            SuggestedScale.EXTREME_CLOSEUP: "85-135mm 或微距镜头",
            SuggestedScale.CLOSEUP: "50-85mm",
            SuggestedScale.MEDIUM: "35-50mm",
            SuggestedScale.WIDE: "16-35mm 广角镜头",
        }
        
        base_suggestion = focal_suggestions.get(suggested_scale)
        if not base_suggestion:
            return None
        
        # Adjust for motion type
        if motion_type in (MotionType.DOLLY_IN, MotionType.DOLLY_OUT):
            return f"建议焦段：{base_suggestion}，推拉镜头可考虑变焦镜头配合"
        elif motion_type == MotionType.HANDHELD:
            return f"建议焦段：{base_suggestion}，手持拍摄建议使用防抖镜头"
        else:
            return f"建议焦段：{base_suggestion}"
    
    def _get_composition_tip(self, suggested_scale: SuggestedScale) -> Optional[str]:
        """
        Get composition tip based on suggested scale.
        
        Args:
            suggested_scale: Suggested framing scale
            
        Returns:
            Composition tip string or None
        """
        tips = {
            SuggestedScale.EXTREME_CLOSEUP: "特写构图注意眼神光和皮肤质感",
            SuggestedScale.CLOSEUP: "近景构图注意头部空间和视线方向",
            SuggestedScale.MEDIUM: "中景构图注意人物与环境的平衡",
            SuggestedScale.WIDE: "远景构图注意前景元素和景深层次",
        }
        return tips.get(suggested_scale)
    
    # =========================================================================
    # Main Processing Method
    # =========================================================================
    
    async def process(self, metadata: MetadataOutput) -> InstructionCard:
        """
        Generate complete three-layer instruction card from metadata.
        
        This is the main entry point for the Instruction Generator Agent.
        
        Args:
            metadata: Metadata from the Metadata Synthesizer
            
        Returns:
            InstructionCard with primary, explain, and advanced layers
        """
        # Generate all three layers
        primary = self.generate_primary(metadata)
        explain = self.generate_explain(metadata)
        advanced = self.generate_advanced(metadata)
        
        # Create instruction card
        # Note: video_id is not in MetadataOutput, we'll use a placeholder
        # In real usage, video_id should be passed separately or included in metadata
        video_id = getattr(metadata, 'video_id', 'unknown')
        
        card = InstructionCard(
            video_id=video_id,
            primary=primary,
            explain=explain,
            advanced=advanced,
        )
        
        # Validate completeness
        if not card.is_complete():
            logger.warning("Generated instruction card is incomplete")
        
        return card
    
    def process_sync(self, metadata: MetadataOutput) -> InstructionCard:
        """
        Synchronous version of process() for non-async contexts.
        
        Args:
            metadata: Metadata from the Metadata Synthesizer
            
        Returns:
            InstructionCard with primary, explain, and advanced layers
        """
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self.process(metadata))
    
    def generate_instruction_card(
        self,
        metadata: MetadataOutput,
        video_id: Optional[str] = None
    ) -> InstructionCard:
        """
        Generate instruction card with explicit video_id.
        
        Args:
            metadata: Metadata from the Metadata Synthesizer
            video_id: Optional video identifier
            
        Returns:
            InstructionCard with all three layers
        """
        primary = self.generate_primary(metadata)
        explain = self.generate_explain(metadata)
        advanced = self.generate_advanced(metadata)
        
        return InstructionCard(
            video_id=video_id or "unknown",
            primary=primary,
            explain=explain,
            advanced=advanced,
        )
