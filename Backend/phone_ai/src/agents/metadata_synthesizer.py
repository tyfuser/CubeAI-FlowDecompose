"""
Metadata Synthesizer Agent for the Video Shooting Assistant.

Combines rule-based inference with LLM enhancement to generate
structured metadata from heuristic indicators.
"""
import logging
from dataclasses import dataclass
from typing import Any, Optional

from src.models.data_types import (
    BBox,
    ExifData,
    FramingData,
    HeuristicOutput,
    MetadataOutput,
    MotionParams,
)
from src.models.enums import MotionType, SpeedProfile, SuggestedScale
from src.schemas.validator import SchemaValidator, SchemaValidationError
from src.services.llm_client import (
    LLMClient,
    LLMConfig,
    LLMError,
    LLMResponseError,
    MockLLMClient,
)
from src.agents.motion_rules import (
    MotionTypeInferrer,
    MotionRulesConfig,
    infer_motion_type_from_heuristics,
)
from src.agents.prompt_templates import (
    build_few_shot_prompt,
    build_simple_prompt,
    parse_llm_response,
    SYSTEM_PROMPT,
)


logger = logging.getLogger(__name__)


@dataclass
class MetadataSynthesizerConfig:
    """Configuration for the Metadata Synthesizer Agent."""
    
    # LLM settings
    use_llm: bool = True  # Whether to use LLM for enhancement
    llm_config: Optional[LLMConfig] = None
    
    # Prompt settings
    use_few_shot: bool = True  # Use few-shot prompts
    num_examples: int = 3  # Number of few-shot examples
    
    # Fallback settings
    fallback_to_rules: bool = True  # Fall back to rules if LLM fails
    
    # Validation settings
    validate_output: bool = True  # Validate output against schema
    auto_fix_invalid: bool = True  # Auto-fix invalid values


class MetadataSynthesizerAgent:
    """
    元数据合成模块（LLM辅助）
    
    Synthesizes structured metadata from heuristic indicators using
    a combination of rule-based inference and LLM enhancement.
    """
    
    def __init__(
        self,
        config: Optional[MetadataSynthesizerConfig] = None,
        llm_client: Optional[LLMClient] = None
    ):
        """
        Initialize the Metadata Synthesizer Agent.
        
        Args:
            config: Configuration options
            llm_client: Optional pre-configured LLM client
        """
        self.config = config or MetadataSynthesizerConfig()
        self.llm_client = llm_client
        self.motion_inferrer = MotionTypeInferrer()
        self.schema_validator = SchemaValidator()
        
        # Initialize LLM client if needed
        if self.config.use_llm and self.llm_client is None:
            try:
                self.llm_client = LLMClient(self.config.llm_config)
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client: {e}")
                self.llm_client = None
    
    async def process(
        self,
        heuristic_output: HeuristicOutput,
        exif_data: Optional[ExifData] = None,
        primary_direction_deg: Optional[float] = None
    ) -> MetadataOutput:
        """
        Generate structured metadata from heuristic indicators.
        
        This is the main entry point for the Metadata Synthesizer Agent.
        
        Args:
            heuristic_output: Output from the Heuristic Analyzer
            exif_data: Optional EXIF metadata
            primary_direction_deg: Optional primary motion direction
            
        Returns:
            MetadataOutput with all required fields
        """
        # Step 1: Rule-based inference for baseline
        rule_based_result = self._infer_from_rules(
            heuristic_output,
            primary_direction_deg
        )
        
        # Step 2: LLM enhancement (if enabled)
        llm_result = None
        if self.config.use_llm and self.llm_client is not None:
            try:
                llm_result = await self._enhance_with_llm(
                    heuristic_output,
                    exif_data
                )
            except LLMError as e:
                logger.warning(f"LLM enhancement failed: {e}")
                if not self.config.fallback_to_rules:
                    raise
        
        # Step 3: Merge results (LLM takes precedence for certain fields)
        metadata = self._merge_results(
            heuristic_output,
            rule_based_result,
            llm_result,
            exif_data
        )
        
        # Step 4: Validate and fix if needed
        if self.config.validate_output:
            metadata = self._validate_and_fix(metadata)
        
        return metadata
    
    def _infer_from_rules(
        self,
        heuristic_output: HeuristicOutput,
        primary_direction_deg: Optional[float] = None
    ) -> dict[str, Any]:
        """
        Perform rule-based inference.
        
        Args:
            heuristic_output: Heuristic indicators
            primary_direction_deg: Primary motion direction
            
        Returns:
            Dictionary with inferred values
        """
        motion_type, speed_profile, suggested_scale, confidence = \
            infer_motion_type_from_heuristics(
                heuristic_output,
                primary_direction_deg
            )
        
        return {
            "motion_type": motion_type,
            "speed_profile": speed_profile,
            "suggested_scale": suggested_scale,
            "confidence": confidence,
        }
    
    async def _enhance_with_llm(
        self,
        heuristic_output: HeuristicOutput,
        exif_data: Optional[ExifData] = None
    ) -> dict[str, Any]:
        """
        Enhance metadata using LLM.
        
        Args:
            heuristic_output: Heuristic indicators
            exif_data: Optional EXIF data
            
        Returns:
            Dictionary with LLM-generated values
        """
        # Build prompt
        if self.config.use_few_shot:
            prompt = build_few_shot_prompt(
                heuristic_output,
                exif_data,
                self.config.num_examples
            )
        else:
            prompt = build_simple_prompt(heuristic_output, exif_data)
        
        # Call LLM
        response = await self.llm_client.complete(prompt, SYSTEM_PROMPT)
        
        # Parse response
        try:
            result = parse_llm_response(response)
            return self._normalize_llm_result(result)
        except ValueError as e:
            raise LLMResponseError(f"Failed to parse LLM response: {e}")
    
    def _normalize_llm_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize LLM result to expected format.
        
        Args:
            result: Raw LLM result
            
        Returns:
            Normalized result dictionary
        """
        normalized = {}
        
        # Extract motion type
        if "motion" in result and "type" in result["motion"]:
            motion_type_str = result["motion"]["type"]
            try:
                normalized["motion_type"] = MotionType(motion_type_str)
            except ValueError:
                logger.warning(f"Invalid motion type from LLM: {motion_type_str}")
        
        # Extract speed profile
        if "motion" in result and "params" in result["motion"]:
            params = result["motion"]["params"]
            if "speed_profile" in params:
                try:
                    normalized["speed_profile"] = SpeedProfile(params["speed_profile"])
                except ValueError:
                    logger.warning(
                        f"Invalid speed profile from LLM: {params['speed_profile']}"
                    )
        
        # Extract suggested scale
        if "framing" in result and "suggested_scale" in result["framing"]:
            scale_str = result["framing"]["suggested_scale"]
            try:
                normalized["suggested_scale"] = SuggestedScale(scale_str)
            except ValueError:
                logger.warning(f"Invalid suggested scale from LLM: {scale_str}")
        
        # Extract confidence
        if "confidence" in result:
            normalized["confidence"] = float(result["confidence"])
        
        # Extract explainability
        if "explainability" in result:
            normalized["explainability"] = str(result["explainability"])
        
        return normalized
    
    def _merge_results(
        self,
        heuristic_output: HeuristicOutput,
        rule_based: dict[str, Any],
        llm_result: Optional[dict[str, Any]],
        exif_data: Optional[ExifData]
    ) -> MetadataOutput:
        """
        Merge rule-based and LLM results.
        
        LLM results take precedence for:
        - explainability (always from LLM if available)
        - confidence (weighted combination of rule-based and LLM)
        
        Rule-based results are used as fallback.
        
        Args:
            heuristic_output: Original heuristic indicators
            rule_based: Rule-based inference results
            llm_result: Optional LLM results
            exif_data: Optional EXIF data
            
        Returns:
            Merged MetadataOutput
        """
        # Start with rule-based values
        motion_type = rule_based["motion_type"]
        speed_profile = rule_based["speed_profile"]
        suggested_scale = rule_based["suggested_scale"]
        rule_confidence = rule_based["confidence"]
        
        # Override with LLM values if available
        llm_confidence = None
        llm_explainability = None
        if llm_result:
            if "motion_type" in llm_result:
                motion_type = llm_result["motion_type"]
            if "speed_profile" in llm_result:
                speed_profile = llm_result["speed_profile"]
            if "suggested_scale" in llm_result:
                suggested_scale = llm_result["suggested_scale"]
            if "confidence" in llm_result:
                llm_confidence = llm_result["confidence"]
            if "explainability" in llm_result:
                llm_explainability = llm_result["explainability"]
        
        # Generate confidence score (Requirements 4.5)
        confidence = self._calculate_final_confidence(
            rule_confidence,
            llm_confidence,
            heuristic_output
        )
        
        # Generate explainability (Requirements 4.6)
        explainability = self._generate_explainability(
            motion_type,
            heuristic_output,
            exif_data,
            llm_explainability
        )
        
        # Build subject bbox from heuristic data
        # Use average bbox if available, otherwise default
        subject_bbox = self._get_average_bbox(heuristic_output)
        
        # Calculate duration from time range
        duration_s = heuristic_output.time_range[1] - heuristic_output.time_range[0]
        
        # Create motion params
        motion_params = MotionParams(
            duration_s=duration_s,
            frame_pct_change=heuristic_output.frame_pct_change,
            speed_profile=speed_profile,
            motion_smoothness=heuristic_output.motion_smoothness,
        )
        
        # Create framing data
        framing = FramingData(
            subject_bbox=subject_bbox,
            subject_occupancy=heuristic_output.subject_occupancy,
            suggested_scale=suggested_scale,
        )
        
        return MetadataOutput(
            time_range=heuristic_output.time_range,
            motion_type=motion_type,
            motion_params=motion_params,
            framing=framing,
            beat_alignment_score=heuristic_output.beat_alignment_score,
            confidence=confidence,
            explainability=explainability,
        )
    
    def _calculate_final_confidence(
        self,
        rule_confidence: float,
        llm_confidence: Optional[float],
        heuristic_output: HeuristicOutput
    ) -> float:
        """
        Calculate the final confidence score for the recommendation.
        
        Combines rule-based confidence with LLM confidence (if available)
        and adjusts based on data quality indicators.
        
        Requirements 4.5: Include confidence score (0-1) for overall recommendation.
        
        Args:
            rule_confidence: Confidence from rule-based inference
            llm_confidence: Optional confidence from LLM
            heuristic_output: Heuristic indicators for quality assessment
            
        Returns:
            Final confidence score in range [0, 1]
        """
        # Base confidence from rule-based inference
        confidence = rule_confidence
        
        # If LLM confidence is available, use weighted average
        # LLM gets higher weight (0.6) as it considers more context
        if llm_confidence is not None:
            confidence = 0.4 * rule_confidence + 0.6 * llm_confidence
        
        # Adjust confidence based on data quality indicators
        # Higher motion smoothness indicates clearer signal
        smoothness_factor = 0.1 * (heuristic_output.motion_smoothness - 0.5)
        confidence += smoothness_factor
        
        # Penalize if indicators are at extreme boundaries (less reliable)
        if heuristic_output.frame_pct_change < 0.01 or heuristic_output.frame_pct_change > 0.95:
            confidence -= 0.05
        
        # Boost confidence if beat alignment is high (consistent with music)
        if heuristic_output.beat_alignment_score > 0.7:
            confidence += 0.05
        
        # Ensure confidence is in valid range [0, 1]
        return max(0.0, min(1.0, confidence))
    
    def _generate_explainability(
        self,
        motion_type: MotionType,
        heuristic_output: HeuristicOutput,
        exif_data: Optional[ExifData],
        llm_explainability: Optional[str]
    ) -> str:
        """
        Generate the explainability field with 2-sentence Chinese explanation.
        
        Requirements 4.6: Include explainability field with 2-sentence Chinese explanation.
        
        If LLM provides explainability, use it. Otherwise, generate from rules.
        
        Args:
            motion_type: Inferred motion type
            heuristic_output: Heuristic indicators
            exif_data: Optional EXIF data for additional context
            llm_explainability: Optional explainability from LLM
            
        Returns:
            2-sentence Chinese explanation string
        """
        # Use LLM explainability if available and valid
        if llm_explainability and len(llm_explainability.strip()) > 10:
            # Ensure it's not too long (max 500 chars per schema)
            if len(llm_explainability) <= 500:
                return llm_explainability
            return llm_explainability[:497] + "..."
        
        # Generate default explainability
        return self._generate_default_explainability(
            motion_type,
            heuristic_output,
            exif_data
        )
    
    def _get_average_bbox(self, heuristic_output: HeuristicOutput) -> BBox:
        """
        Get average bounding box from heuristic output.
        
        Since HeuristicOutput doesn't store bbox sequence directly,
        we create a default bbox based on subject_occupancy.
        
        Args:
            heuristic_output: Heuristic indicators
            
        Returns:
            Estimated bounding box
        """
        # Estimate bbox from subject_occupancy
        # Assume centered subject with square-ish aspect ratio
        occupancy = heuristic_output.subject_occupancy
        
        if occupancy <= 0:
            # Default small centered bbox
            return BBox(x=0.4, y=0.4, w=0.2, h=0.2)
        
        # Calculate approximate dimensions
        # Assume 4:3 aspect ratio for subject
        import math
        area = occupancy
        # w * h = area, w/h = 4/3 -> w = 4h/3 -> 4h^2/3 = area -> h = sqrt(3*area/4)
        h = min(1.0, math.sqrt(3 * area / 4))
        w = min(1.0, 4 * h / 3)
        
        # Center the bbox
        x = max(0.0, (1.0 - w) / 2)
        y = max(0.0, (1.0 - h) / 2)
        
        return BBox(x=x, y=y, w=w, h=h)
    
    def _generate_default_explainability(
        self,
        motion_type: MotionType,
        heuristic_output: HeuristicOutput,
        exif_data: Optional[ExifData] = None
    ) -> str:
        """
        Generate default explainability text with 2 sentences in Chinese.
        
        Requirements 4.6: Include explainability field with 2-sentence Chinese explanation.
        
        Args:
            motion_type: Inferred motion type
            heuristic_output: Heuristic indicators
            exif_data: Optional EXIF data for additional context
            
        Returns:
            2-sentence Chinese explanation string
        """
        motion_descriptions = {
            MotionType.STATIC: "静态镜头",
            MotionType.DOLLY_IN: "推镜头",
            MotionType.DOLLY_OUT: "拉镜头",
            MotionType.PAN: "横摇镜头",
            MotionType.TILT: "纵摇镜头",
            MotionType.TRACK: "跟踪镜头",
            MotionType.HANDHELD: "手持镜头",
        }
        
        motion_desc = motion_descriptions.get(motion_type, "未知运动类型")
        smoothness = heuristic_output.motion_smoothness
        occupancy = heuristic_output.subject_occupancy
        frame_change = heuristic_output.frame_pct_change
        beat_score = heuristic_output.beat_alignment_score
        
        # First sentence: Describe the motion characteristics
        smoothness_desc = "平滑" if smoothness > 0.7 else "中等流畅度" if smoothness > 0.4 else "略有抖动"
        
        if motion_type == MotionType.STATIC:
            sentence1 = f"该镜头为{motion_desc}，画面稳定无明显运动。"
        elif motion_type in (MotionType.DOLLY_IN, MotionType.DOLLY_OUT):
            direction = "推进" if motion_type == MotionType.DOLLY_IN else "拉远"
            speed_desc = "缓慢" if frame_change < 0.1 else "中速" if frame_change <= 0.25 else "快速"
            sentence1 = f"该镜头为{speed_desc}{direction}，运动{smoothness_desc}。"
        elif motion_type == MotionType.PAN:
            sentence1 = f"该镜头为横向摇移，运动{smoothness_desc}，适合展示宽广场景。"
        elif motion_type == MotionType.TILT:
            sentence1 = f"该镜头为纵向摇移，运动{smoothness_desc}，适合展示高度变化。"
        elif motion_type == MotionType.TRACK:
            sentence1 = f"该镜头为跟踪运动，运动{smoothness_desc}，持续跟随主体。"
        elif motion_type == MotionType.HANDHELD:
            sentence1 = f"该镜头呈现手持拍摄特征，具有自然的运动感。"
        else:
            sentence1 = f"该镜头为{motion_desc}，运动{smoothness_desc}。"
        
        # Second sentence: Provide composition and recommendation context
        occupancy_pct = int(occupancy * 100)
        
        if occupancy >= 0.5:
            composition_advice = f"主体占画面约{occupancy_pct}%，构图紧凑"
        elif occupancy >= 0.25:
            composition_advice = f"主体占画面约{occupancy_pct}%，构图适中"
        elif occupancy >= 0.1:
            composition_advice = f"主体占画面约{occupancy_pct}%，留有环境空间"
        else:
            composition_advice = f"主体占画面约{occupancy_pct}%，以环境为主"
        
        # Add equipment or technique suggestion based on smoothness
        if smoothness > 0.7:
            technique_hint = "建议使用滑轨或稳定器保持流畅"
        elif smoothness > 0.4:
            technique_hint = "可配合云台使用"
        else:
            technique_hint = "建议增加稳定措施或采用静态拍摄"
        
        # Add beat alignment context if significant
        if beat_score > 0.7:
            rhythm_hint = "，节奏感强"
        elif beat_score > 0.4:
            rhythm_hint = ""
        else:
            rhythm_hint = ""
        
        sentence2 = f"{composition_advice}{rhythm_hint}，{technique_hint}。"
        
        return sentence1 + sentence2
    
    def _validate_and_fix(self, metadata: MetadataOutput) -> MetadataOutput:
        """
        Validate metadata and fix invalid values.
        
        Args:
            metadata: Metadata to validate
            
        Returns:
            Validated (and possibly fixed) metadata
        """
        # Convert to dict for validation
        metadata_dict = metadata.to_dict()
        
        # Validate against schema
        is_valid, errors = self.schema_validator.validate_metadata(metadata_dict)
        
        if is_valid:
            return metadata
        
        logger.warning(f"Metadata validation errors: {errors}")
        
        if not self.config.auto_fix_invalid:
            raise SchemaValidationError("Metadata validation failed", errors)
        
        # Auto-fix common issues
        fixed_metadata = self._auto_fix_metadata(metadata, errors)
        
        # Re-validate
        fixed_dict = fixed_metadata.to_dict()
        is_valid, errors = self.schema_validator.validate_metadata(fixed_dict)
        
        if not is_valid:
            logger.error(f"Could not auto-fix metadata: {errors}")
            raise SchemaValidationError("Metadata validation failed after auto-fix", errors)
        
        return fixed_metadata
    
    def _auto_fix_metadata(
        self,
        metadata: MetadataOutput,
        errors: list[str]
    ) -> MetadataOutput:
        """
        Attempt to auto-fix invalid metadata.
        
        Args:
            metadata: Invalid metadata
            errors: List of validation errors
            
        Returns:
            Fixed metadata
        """
        # Clamp numeric values to valid ranges
        confidence = max(0.0, min(1.0, metadata.confidence))
        beat_alignment = max(0.0, min(1.0, metadata.beat_alignment_score))
        
        # Fix motion params
        frame_pct_change = max(0.0, min(1.0, metadata.motion_params.frame_pct_change))
        motion_smoothness = max(0.0, min(1.0, metadata.motion_params.motion_smoothness))
        duration_s = max(0.001, metadata.motion_params.duration_s)  # Must be > 0
        
        motion_params = MotionParams(
            duration_s=duration_s,
            frame_pct_change=frame_pct_change,
            speed_profile=metadata.motion_params.speed_profile,
            motion_smoothness=motion_smoothness,
        )
        
        # Fix framing
        subject_occupancy = max(0.0, min(1.0, metadata.framing.subject_occupancy))
        subject_bbox = metadata.framing.subject_bbox.normalize()
        
        framing = FramingData(
            subject_bbox=subject_bbox,
            subject_occupancy=subject_occupancy,
            suggested_scale=metadata.framing.suggested_scale,
        )
        
        # Fix time range
        start, end = metadata.time_range
        if start < 0:
            start = 0.0
        if end <= start:
            end = start + 1.0
        
        # Truncate explainability if too long
        explainability = metadata.explainability
        if len(explainability) > 500:
            explainability = explainability[:497] + "..."
        
        return MetadataOutput(
            time_range=(start, end),
            motion_type=metadata.motion_type,
            motion_params=motion_params,
            framing=framing,
            beat_alignment_score=beat_alignment,
            confidence=confidence,
            explainability=explainability,
        )
    
    def validate_schema(self, metadata: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate metadata dictionary against JSON Schema.
        
        Args:
            metadata: Metadata dictionary to validate
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        return self.schema_validator.validate_metadata(metadata)
    
    def process_sync(
        self,
        heuristic_output: HeuristicOutput,
        exif_data: Optional[ExifData] = None,
        primary_direction_deg: Optional[float] = None
    ) -> MetadataOutput:
        """
        Synchronous version of process() for non-async contexts.
        
        Args:
            heuristic_output: Output from the Heuristic Analyzer
            exif_data: Optional EXIF metadata
            primary_direction_deg: Optional primary motion direction
            
        Returns:
            MetadataOutput with all required fields
        """
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.process(heuristic_output, exif_data, primary_direction_deg)
        )
    
    async def generate_metadata(
        self,
        heuristic_output: HeuristicOutput,
        exif_data: Optional[ExifData] = None,
        primary_direction_deg: Optional[float] = None
    ) -> MetadataOutput:
        """
        Generate metadata by combining rule-based inference with LLM enhancement.
        
        This is the main metadata generation pipeline that:
        1. Performs rule-based inference for baseline values
        2. Enhances with LLM for better explainability and context
        3. Calculates confidence score based on multiple factors
        4. Generates 2-sentence Chinese explainability
        5. Validates output against JSON Schema
        
        Requirements 4.5: Include confidence score (0-1) for overall recommendation
        Requirements 4.6: Include explainability field with 2-sentence Chinese explanation
        
        Args:
            heuristic_output: Output from the Heuristic Analyzer
            exif_data: Optional EXIF metadata for additional context
            primary_direction_deg: Optional primary motion direction in degrees
            
        Returns:
            MetadataOutput with confidence score and explainability
        """
        return await self.process(heuristic_output, exif_data, primary_direction_deg)
    
    def generate_metadata_sync(
        self,
        heuristic_output: HeuristicOutput,
        exif_data: Optional[ExifData] = None,
        primary_direction_deg: Optional[float] = None
    ) -> MetadataOutput:
        """
        Synchronous version of generate_metadata() for non-async contexts.
        
        Combines rule-based inference with LLM enhancement to generate
        metadata with confidence score and explainability.
        
        Requirements 4.5: Include confidence score (0-1) for overall recommendation
        Requirements 4.6: Include explainability field with 2-sentence Chinese explanation
        
        Args:
            heuristic_output: Output from the Heuristic Analyzer
            exif_data: Optional EXIF metadata
            primary_direction_deg: Optional primary motion direction
            
        Returns:
            MetadataOutput with confidence score and explainability
        """
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop and loop.is_running():
            # If we're already in an async context, create a new loop in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.generate_metadata(heuristic_output, exif_data, primary_direction_deg)
                )
                return future.result()
        else:
            return asyncio.run(
                self.generate_metadata(heuristic_output, exif_data, primary_direction_deg)
            )


class MetadataGenerationPipeline:
    """
    High-level metadata generation pipeline.
    
    Orchestrates the complete metadata generation process by combining
    rule-based inference with LLM enhancement to produce structured
    metadata with confidence scores and explainability.
    
    This pipeline implements Requirements 4.5 and 4.6:
    - 4.5: Include confidence score (0-1) for overall recommendation
    - 4.6: Include explainability field with 2-sentence Chinese explanation
    
    The pipeline follows these steps:
    1. Rule-based inference for baseline motion type, speed profile, and scale
    2. LLM enhancement for better context understanding and explainability
    3. Confidence score calculation based on multiple quality factors
    4. Explainability generation with 2-sentence Chinese explanation
    5. Schema validation and auto-fix for invalid values
    """
    
    def __init__(
        self,
        config: Optional[MetadataSynthesizerConfig] = None,
        llm_client: Optional[LLMClient] = None
    ):
        """
        Initialize the metadata generation pipeline.
        
        Args:
            config: Configuration options for the pipeline
            llm_client: Optional pre-configured LLM client
        """
        self.config = config or MetadataSynthesizerConfig()
        self.synthesizer = MetadataSynthesizerAgent(
            config=self.config,
            llm_client=llm_client
        )
        self.schema_validator = SchemaValidator()
        logger.info("MetadataGenerationPipeline initialized")
    
    async def run(
        self,
        heuristic_output: HeuristicOutput,
        exif_data: Optional[ExifData] = None,
        primary_direction_deg: Optional[float] = None
    ) -> MetadataOutput:
        """
        Run the complete metadata generation pipeline.
        
        Combines rule-based inference with LLM enhancement to generate
        structured metadata with confidence score and explainability.
        
        Requirements 4.5: Include confidence score (0-1) for overall recommendation
        Requirements 4.6: Include explainability field with 2-sentence Chinese explanation
        
        Args:
            heuristic_output: Output from the Heuristic Analyzer
            exif_data: Optional EXIF metadata for additional context
            primary_direction_deg: Optional primary motion direction in degrees
            
        Returns:
            MetadataOutput with all required fields including confidence and explainability
            
        Raises:
            SchemaValidationError: If output fails validation and cannot be auto-fixed
        """
        logger.info(f"Starting metadata generation for video: {heuristic_output.video_id}")
        
        # Validate input
        if not heuristic_output.is_valid():
            logger.warning("Heuristic output has invalid values, attempting to proceed")
        
        # Run the synthesizer pipeline
        metadata = await self.synthesizer.generate_metadata(
            heuristic_output,
            exif_data,
            primary_direction_deg
        )
        
        # Log pipeline results
        logger.info(
            f"Metadata generated: motion_type={metadata.motion_type.value}, "
            f"confidence={metadata.confidence:.2f}"
        )
        
        return metadata
    
    def run_sync(
        self,
        heuristic_output: HeuristicOutput,
        exif_data: Optional[ExifData] = None,
        primary_direction_deg: Optional[float] = None
    ) -> MetadataOutput:
        """
        Synchronous version of run() for non-async contexts.
        
        Args:
            heuristic_output: Output from the Heuristic Analyzer
            exif_data: Optional EXIF metadata
            primary_direction_deg: Optional primary motion direction
            
        Returns:
            MetadataOutput with confidence score and explainability
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.run(heuristic_output, exif_data, primary_direction_deg)
        )
    
    def validate_output(self, metadata: MetadataOutput) -> tuple[bool, list[str]]:
        """
        Validate metadata output against JSON Schema.
        
        Args:
            metadata: Metadata to validate
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        return self.schema_validator.validate_metadata(metadata.to_dict())
    
    def get_confidence_action(self, confidence: float) -> str:
        """
        Determine the action based on confidence score.
        
        Requirements 7.4, 7.5, 7.6:
        - confidence > 0.75: proceed normally
        - 0.55 <= confidence <= 0.75: add warning prompt
        - confidence < 0.55: request manual intervention
        
        Args:
            confidence: Confidence score (0-1)
            
        Returns:
            Action string: "proceed", "warn", or "manual"
        """
        if confidence > 0.75:
            return "proceed"
        elif confidence >= 0.55:
            return "warn"
        else:
            return "manual"


def create_metadata_pipeline(
    use_llm: bool = True,
    llm_config: Optional[LLMConfig] = None,
    validate_output: bool = True
) -> MetadataGenerationPipeline:
    """
    Factory function to create a metadata generation pipeline.
    
    Args:
        use_llm: Whether to use LLM for enhancement
        llm_config: Optional LLM configuration
        validate_output: Whether to validate output against schema
        
    Returns:
        Configured MetadataGenerationPipeline instance
    """
    config = MetadataSynthesizerConfig(
        use_llm=use_llm,
        llm_config=llm_config,
        validate_output=validate_output,
        auto_fix_invalid=True,
    )
    return MetadataGenerationPipeline(config=config)
