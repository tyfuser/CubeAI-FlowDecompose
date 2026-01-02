# Agents module
"""
Agent modules for the Video Shooting Assistant.

Each agent handles a specific stage of the video analysis pipeline.
"""

from src.agents.uploader import (
    UploaderAgent,
    UploaderConfig,
    ValidationResult,
    VideoFormat,
)

from src.agents.feature_extractor import (
    FeatureExtractorAgent,
    FeatureExtractorConfig,
)

from src.agents.heuristic_analyzer import (
    HeuristicAnalyzerAgent,
    HeuristicAnalyzerConfig,
)

from src.agents.motion_rules import (
    MotionTypeInferrer,
    MotionRulesConfig,
    infer_motion_type_from_heuristics,
)

from src.agents.metadata_synthesizer import (
    MetadataSynthesizerAgent,
    MetadataSynthesizerConfig,
)

from src.agents.instruction_generator import (
    InstructionGeneratorAgent,
    InstructionGeneratorConfig,
)

from src.agents.prompt_templates import (
    build_few_shot_prompt,
    build_simple_prompt,
    parse_llm_response,
    SYSTEM_PROMPT,
    FEW_SHOT_EXAMPLES,
)

from src.agents.retrieval_agent import (
    RetrievalAgent,
    RetrievalAgentConfig,
    create_retrieval_agent,
)

__all__ = [
    "UploaderAgent",
    "UploaderConfig",
    "ValidationResult",
    "VideoFormat",
    "FeatureExtractorAgent",
    "FeatureExtractorConfig",
    "HeuristicAnalyzerAgent",
    "HeuristicAnalyzerConfig",
    "MotionTypeInferrer",
    "MotionRulesConfig",
    "infer_motion_type_from_heuristics",
    "MetadataSynthesizerAgent",
    "MetadataSynthesizerConfig",
    "InstructionGeneratorAgent",
    "InstructionGeneratorConfig",
    "build_few_shot_prompt",
    "build_simple_prompt",
    "parse_llm_response",
    "SYSTEM_PROMPT",
    "FEW_SHOT_EXAMPLES",
    "RetrievalAgent",
    "RetrievalAgentConfig",
    "create_retrieval_agent",
]
