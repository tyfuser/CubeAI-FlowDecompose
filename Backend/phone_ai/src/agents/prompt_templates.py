"""
LLM prompt templates for the Metadata Synthesizer Agent.

Contains few-shot prompt templates with examples for generating
structured metadata from heuristic indicators.
"""
from typing import Optional

from src.models.data_types import ExifData, HeuristicOutput


# System prompt for metadata synthesis
SYSTEM_PROMPT = """你是一个专业的视频拍摄分析助手。你的任务是根据视频分析数据生成结构化的拍摄元数据。

你需要分析以下指标并生成JSON格式的元数据：
- avg_motion_px_per_s: 平均运动速度（像素/秒）
- frame_pct_change: 画幅占比变化率（0-1）
- motion_smoothness: 运动平滑度（0-1，越高越平滑）
- subject_occupancy: 主体占比（0-1）
- beat_alignment_score: 节拍对齐度（0-1）

你需要输出以下字段：
1. motion.type: 运动类型 (dolly_in/dolly_out/pan/tilt/track/handheld/static)
2. motion.params.speed_profile: 速度曲线 (ease_in/ease_out/ease_in_out/linear)
3. framing.suggested_scale: 建议景别 (extreme_closeup/closeup/medium/wide)
4. confidence: 置信度 (0-1)
5. explainability: 2句话的中文解释

请严格按照JSON格式输出，不要添加额外的文字说明。"""


# Few-shot examples for the prompt
FEW_SHOT_EXAMPLES = [
    {
        "input": {
            "avg_motion_px_per_s": 2.5,
            "frame_pct_change": 0.02,
            "motion_smoothness": 0.95,
            "subject_occupancy": 0.35,
            "beat_alignment_score": 0.6,
            "exif": {"focal_length_mm": 50, "aperture": 2.8}
        },
        "output": {
            "motion": {
                "type": "static",
                "params": {
                    "speed_profile": "linear"
                }
            },
            "framing": {
                "suggested_scale": "medium"
            },
            "confidence": 0.92,
            "explainability": "该镜头几乎没有运动，属于静态镜头。主体占画面约35%，适合中景构图。"
        }
    },
    {
        "input": {
            "avg_motion_px_per_s": 85.0,
            "frame_pct_change": 0.18,
            "motion_smoothness": 0.78,
            "subject_occupancy": 0.45,
            "beat_alignment_score": 0.75,
            "exif": {"focal_length_mm": 35, "aperture": 4.0}
        },
        "output": {
            "motion": {
                "type": "dolly_in",
                "params": {
                    "speed_profile": "ease_in_out"
                }
            },
            "framing": {
                "suggested_scale": "closeup"
            },
            "confidence": 0.85,
            "explainability": "画幅变化明显（18%），表明镜头在推进。运动平滑度较高，建议使用渐入渐出的速度曲线。"
        }
    },
    {
        "input": {
            "avg_motion_px_per_s": 120.0,
            "frame_pct_change": 0.05,
            "motion_smoothness": 0.65,
            "subject_occupancy": 0.15,
            "beat_alignment_score": 0.45,
            "exif": {"focal_length_mm": 24, "aperture": 5.6}
        },
        "output": {
            "motion": {
                "type": "pan",
                "params": {
                    "speed_profile": "linear"
                }
            },
            "framing": {
                "suggested_scale": "medium"
            },
            "confidence": 0.72,
            "explainability": "运动速度中等但画幅变化小，符合横摇特征。广角镜头配合中景构图适合展示环境。"
        }
    },
    {
        "input": {
            "avg_motion_px_per_s": 180.0,
            "frame_pct_change": 0.08,
            "motion_smoothness": 0.35,
            "subject_occupancy": 0.25,
            "beat_alignment_score": 0.55,
            "exif": {"focal_length_mm": 85, "aperture": 1.8}
        },
        "output": {
            "motion": {
                "type": "handheld",
                "params": {
                    "speed_profile": "linear"
                }
            },
            "framing": {
                "suggested_scale": "closeup"
            },
            "confidence": 0.68,
            "explainability": "运动平滑度较低（0.35），呈现手持拍摄特征。长焦镜头配合近景可以突出主体。"
        }
    }
]


def build_few_shot_prompt(
    heuristic_output: HeuristicOutput,
    exif_data: Optional[ExifData] = None,
    num_examples: int = 3
) -> str:
    """
    Build a few-shot prompt for metadata synthesis.
    
    Args:
        heuristic_output: Output from the Heuristic Analyzer
        exif_data: Optional EXIF metadata
        num_examples: Number of few-shot examples to include (2-4)
        
    Returns:
        Complete prompt string for the LLM
    """
    # Limit examples to available range
    num_examples = max(2, min(4, num_examples, len(FEW_SHOT_EXAMPLES)))
    examples = FEW_SHOT_EXAMPLES[:num_examples]
    
    # Build examples section
    examples_text = ""
    for i, example in enumerate(examples, 1):
        examples_text += f"\n### 示例 {i}\n"
        examples_text += f"输入数据:\n```json\n{_format_input(example['input'])}\n```\n"
        examples_text += f"输出:\n```json\n{_format_output(example['output'])}\n```\n"
    
    # Build current input
    current_input = {
        "avg_motion_px_per_s": heuristic_output.avg_motion_px_per_s,
        "frame_pct_change": heuristic_output.frame_pct_change,
        "motion_smoothness": heuristic_output.motion_smoothness,
        "subject_occupancy": heuristic_output.subject_occupancy,
        "beat_alignment_score": heuristic_output.beat_alignment_score,
        "time_range": list(heuristic_output.time_range),
    }
    
    if exif_data:
        current_input["exif"] = {
            "focal_length_mm": exif_data.focal_length_mm,
            "aperture": exif_data.aperture,
            "sensor_size": exif_data.sensor_size,
        }
    
    # Construct the full prompt
    prompt = f"""{SYSTEM_PROMPT}

## 示例
{examples_text}

## 当前任务

请根据以下视频分析数据生成元数据：

输入数据:
```json
{_format_input(current_input)}
```

请输出完整的JSON格式元数据，包含motion、framing、confidence和explainability字段。
只输出JSON，不要添加其他文字。"""
    
    return prompt


def build_simple_prompt(
    heuristic_output: HeuristicOutput,
    exif_data: Optional[ExifData] = None
) -> str:
    """
    Build a simpler prompt without few-shot examples.
    
    Useful for faster inference or when token limits are a concern.
    
    Args:
        heuristic_output: Output from the Heuristic Analyzer
        exif_data: Optional EXIF metadata
        
    Returns:
        Simple prompt string for the LLM
    """
    current_input = {
        "avg_motion_px_per_s": heuristic_output.avg_motion_px_per_s,
        "frame_pct_change": heuristic_output.frame_pct_change,
        "motion_smoothness": heuristic_output.motion_smoothness,
        "subject_occupancy": heuristic_output.subject_occupancy,
        "beat_alignment_score": heuristic_output.beat_alignment_score,
    }
    
    if exif_data:
        current_input["exif"] = {
            "focal_length_mm": exif_data.focal_length_mm,
            "aperture": exif_data.aperture,
        }
    
    prompt = f"""分析以下视频数据并生成拍摄元数据JSON：

数据: {_format_input(current_input)}

输出格式要求：
{{
  "motion": {{
    "type": "dolly_in|dolly_out|pan|tilt|track|handheld|static",
    "params": {{
      "speed_profile": "ease_in|ease_out|ease_in_out|linear"
    }}
  }},
  "framing": {{
    "suggested_scale": "extreme_closeup|closeup|medium|wide"
  }},
  "confidence": 0.0-1.0,
  "explainability": "2句话中文解释"
}}

只输出JSON。"""
    
    return prompt


def _format_input(data: dict) -> str:
    """Format input data as JSON string."""
    import json
    return json.dumps(data, ensure_ascii=False, indent=2)


def _format_output(data: dict) -> str:
    """Format output data as JSON string."""
    import json
    return json.dumps(data, ensure_ascii=False, indent=2)


def parse_llm_response(response: str) -> dict:
    """
    Parse the LLM response to extract JSON metadata.
    
    Handles various response formats including:
    - Pure JSON
    - JSON wrapped in markdown code blocks
    - JSON with surrounding text
    
    Args:
        response: Raw LLM response string
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        ValueError: If JSON cannot be extracted from response
    """
    import json
    import re
    
    # Try direct JSON parsing first
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    code_block_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
    matches = re.findall(code_block_pattern, response)
    
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue
    
    # Try to find JSON object in the response
    json_pattern = r'\{[\s\S]*\}'
    matches = re.findall(json_pattern, response)
    
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    raise ValueError(f"Could not extract valid JSON from LLM response: {response[:200]}...")
