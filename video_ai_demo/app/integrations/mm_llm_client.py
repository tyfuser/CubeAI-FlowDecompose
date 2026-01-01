"""多模态大模型客户端适配层"""
import httpx
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import base64

from ..core.config import settings
from ..core.errors import LLMAPIError, ValidationError
from ..core.json_schema import validate_decompose_result
from ..core.logging import logger


class FrameInput:
    """帧输入"""
    def __init__(self, ts_ms: float, image_path: str):
        self.ts_ms = ts_ms
        self.image_path = image_path


class MMHLLMClient:
    """多模态大模型客户端"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.base_url = base_url or settings.mm_llm_base_url
        self.api_key = api_key or settings.mm_llm_api_key
        self.model = model or settings.mm_llm_model
        
        if not self.api_key:
            raise LLMAPIError("未配置MM_LLM_API_KEY")
    
    async def decompose_video(
        self,
        frames: List[FrameInput],
        prompt_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        拆解视频：两段式调用
        1. 先识别镜头边界
        2. 再分析每个镜头的特征
        """
        logger.info(f"开始拆解视频，共{len(frames)}帧")
        
        # 第一步：识别镜头边界
        segments_raw = await self._identify_shot_boundaries(frames, prompt_config)
        
        # 第二步：分析每个镜头的特征
        result = await self._analyze_segments(frames, segments_raw, prompt_config)
        
        # 校验结果
        try:
            validate_decompose_result(result)
            logger.info(f"拆解完成，共{len(result['segments'])}个镜头")
            return result
        except ValidationError as e:
            # 尝试一次修正
            logger.warning(f"拆解结果校验失败，尝试修正: {e.message}")
            corrected = await self._try_correct_result(result, e.message)
            validate_decompose_result(corrected)
            return corrected
    
    async def _identify_shot_boundaries(
        self,
        frames: List[FrameInput],
        prompt_config: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """第一步：识别镜头边界"""
        
        # 采样关键帧（避免发送太多图片）
        sampled_frames = self._sample_frames(frames, max_frames=20)
        
        prompt = self._build_shot_boundary_prompt(frames, sampled_frames)
        
        response = await self._call_api(sampled_frames, prompt)
        
        try:
            # 尝试解析JSON
            segments = json.loads(response)
            if isinstance(segments, dict) and "segments" in segments:
                segments = segments["segments"]
            return segments
        except json.JSONDecodeError:
            # 尝试从文本中提取JSON
            segments = self._extract_json_from_text(response)
            return segments
    
    async def _analyze_segments(
        self,
        frames: List[FrameInput],
        segments_raw: List[Dict[str, Any]],
        prompt_config: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """第二步：分析每个镜头的特征"""
        
        segments_with_features = []
        
        for i, seg in enumerate(segments_raw):
            segment_id = seg.get("segment_id", f"seg_{i:03d}")
            start_ms = seg.get("start_ms", 0)
            end_ms = seg.get("end_ms", frames[-1].ts_ms if frames else 0)
            
            # 获取该段的帧
            segment_frames = [
                f for f in frames
                if start_ms <= f.ts_ms <= end_ms
            ]
            
            if not segment_frames:
                continue
            
            # 分析该段特征
            features = await self._analyze_segment_features(
                segment_frames,
                segment_id,
                start_ms,
                end_ms,
                prompt_config
            )
            
            segments_with_features.append({
                "segment_id": segment_id,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "duration_ms": end_ms - start_ms,
                "features": features
            })
        
        return {"segments": segments_with_features}
    
    async def _analyze_segment_features(
        self,
        frames: List[FrameInput],
        segment_id: str,
        start_ms: float,
        end_ms: float,
        prompt_config: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """分析单个镜头的特征"""
        
        # 采样几帧代表性帧
        sampled = self._sample_frames(frames, max_frames=5)
        
        enabled_modules = (prompt_config or {}).get("enabled_modules", [
            "camera_motion", "lighting", "color_grading"
        ])
        
        prompt = self._build_feature_analysis_prompt(
            segment_id,
            start_ms,
            end_ms,
            enabled_modules
        )
        
        response = await self._call_api(sampled, prompt)
        
        try:
            features = json.loads(response)
            if isinstance(features, dict) and "features" in features:
                features = features["features"]
            # 规范化features，补充缺失字段
            return self._normalize_features(features, start_ms, end_ms)
        except json.JSONDecodeError:
            features = self._extract_json_from_text(response)
            return self._normalize_features(features, start_ms, end_ms)
    
    def _normalize_features(
        self,
        features: List[Dict[str, Any]],
        start_ms: float,
        end_ms: float
    ) -> List[Dict[str, Any]]:
        """规范化features，补充缺失字段"""
        normalized = []
        
        if not isinstance(features, list):
            logger.warning(f"Features不是列表格式: {type(features)}")
            return []
        
        for feature in features:
            if not isinstance(feature, dict):
                continue
            
            # 补充必需字段
            normalized_feature = {
                "category": feature.get("category", "unknown"),
                "type": feature.get("type", "unknown"),
                "value": feature.get("value", "未识别"),
                "confidence": float(feature.get("confidence", 0.75)),  # 默认置信度
                "evidence": feature.get("evidence", {
                    "time_ranges_ms": [[start_ms, end_ms]]
                })
            }
            
            # 确保evidence有正确的结构
            if "time_ranges_ms" not in normalized_feature["evidence"]:
                normalized_feature["evidence"]["time_ranges_ms"] = [[start_ms, end_ms]]
            
            # 确保time_ranges是正确格式
            if not isinstance(normalized_feature["evidence"]["time_ranges_ms"], list):
                normalized_feature["evidence"]["time_ranges_ms"] = [[start_ms, end_ms]]
            
            # 处理详细描述字段（可选）
            if "detailed_description" in feature:
                detailed = feature["detailed_description"]
                if isinstance(detailed, dict):
                    normalized_feature["detailed_description"] = {
                        "summary": detailed.get("summary", ""),
                        "technical_terms": detailed.get("technical_terms", []),
                        "purpose": detailed.get("purpose", ""),
                        "parameters": detailed.get("parameters", {}),
                        "diagram": detailed.get("diagram", "")
                    }
            
            normalized.append(normalized_feature)
        
        logger.info(f"规范化了{len(normalized)}个特征")
        return normalized
    
    async def _call_api(
        self,
        frames: List[FrameInput],
        prompt: str
    ) -> str:
        """调用多模态API"""
        
        # 构建消息内容
        content = [{"type": "text", "text": prompt}]
        
        # 添加图片
        for frame in frames:
            image_url = self._prepare_image_url(frame.image_path)
            content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })
        
        # 构建请求
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ]
        }
        
        # 调用API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                
                # 提取回复内容
                if "choices" in result and len(result["choices"]) > 0:
                    message = result["choices"][0].get("message", {})
                    return message.get("content", "")
                
                raise LLMAPIError("API响应格式异常", {"response": result})
        
        except httpx.HTTPError as e:
            raise LLMAPIError(f"API调用失败: {str(e)}")
    
    def _prepare_image_url(self, image_path: str) -> str:
        """准备图片URL（转base64或使用文件路径）"""
        path = Path(image_path)
        if not path.exists():
            raise LLMAPIError(f"图片不存在: {image_path}")
        
        # 读取图片并转base64
        with open(path, "rb") as f:
            image_data = f.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # 检测图片格式
            suffix = path.suffix.lower()
            mime_type = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }.get(suffix, 'image/jpeg')
            
            return f"data:{mime_type};base64,{base64_image}"
    
    def _sample_frames(
        self,
        frames: List[FrameInput],
        max_frames: int
    ) -> List[FrameInput]:
        """采样帧"""
        if len(frames) <= max_frames:
            return frames
        
        step = len(frames) / max_frames
        indices = [int(i * step) for i in range(max_frames)]
        return [frames[i] for i in indices]
    
    def _build_shot_boundary_prompt(
        self,
        all_frames: List[FrameInput],
        sampled_frames: List[FrameInput]
    ) -> str:
        """构建镜头边界识别提示词"""
        
        duration_ms = all_frames[-1].ts_ms if all_frames else 0
        
        return f"""请分析这段视频的镜头切分（Shot Segmentation）。

视频总时长: {duration_ms}ms
提供的关键帧: {len(sampled_frames)}帧

请识别视频中的镜头边界，输出JSON格式：

```json
[
  {{
    "segment_id": "seg_001",
    "start_ms": 0,
    "end_ms": 3500
  }},
  {{
    "segment_id": "seg_002", 
    "start_ms": 3500,
    "end_ms": 8200
  }}
]
```

要求：
1. 根据画面变化识别镜头切换点
2. segment_id按顺序命名
3. 时间范围连续不重叠
4. 只输出JSON，不要其他文字
"""
    
    def _build_feature_analysis_prompt(
        self,
        segment_id: str,
        start_ms: float,
        end_ms: float,
        enabled_modules: List[str]
    ) -> str:
        """构建特征分析提示词"""
        
        modules_desc = {
            "camera_motion": "运镜方式（如推镜、拉镜、平移、固定等）",
            "lighting": "光线布局（如主光位置、补光、轮廓光等）",
            "color_grading": "调色风格（如色温、饱和度、对比度风格等）"
        }
        
        enabled_desc = "\n".join([
            f"- {modules_desc.get(m, m)}" for m in enabled_modules
        ])
        
        return f"""请分析这个镜头片段的影视特征，并提供详细的专业解读。

镜头ID: {segment_id}
时间范围: {start_ms}ms - {end_ms}ms

需要分析的特征维度：
{enabled_desc}

输出JSON格式：

```json
[
  {{
    "category": "camera_motion",
    "type": "push_in",
    "value": "缓慢推镜",
    "confidence": 0.85,
    "evidence": {{
      "time_ranges_ms": [[{start_ms}, {end_ms}]]
    }},
    "detailed_description": {{
      "summary": "摄像机以缓慢的速度向拍摄主体推进，焦距逐渐拉近",
      "technical_terms": ["推镜头", "Dolly In", "景深变化"],
      "purpose": "引导观众注意力聚焦到主体，营造逐渐接近、深入的感觉，增强情感张力",
      "parameters": {{
        "speed": "缓慢",
        "distance": "中距离推进",
        "focal_length_change": "无明显变化"
      }}
    }}
  }},
  {{
    "category": "lighting",
    "type": "three_point",
    "value": "三点布光",
    "confidence": 0.90,
    "evidence": {{
      "time_ranges_ms": [[{start_ms}, {end_ms}]]
    }},
    "detailed_description": {{
      "summary": "经典的三点布光系统，包含主光、补光和轮廓光",
      "technical_terms": ["Key Light主光", "Fill Light补光", "Back Light轮廓光"],
      "purpose": "塑造人物立体感，突出轮廓，营造专业的影像质感",
      "parameters": {{
        "key_light_position": "左前方45度，高于眼平",
        "fill_light_ratio": "1:2（主光与补光比例）",
        "back_light_position": "后上方，勾勒轮廓"
      }},
      "diagram": "主光源↗️（左前上） + 补光源➡️（右前方） + 轮廓光⬇️（后上方）"
    }}
  }},
  {{
    "category": "color_grading",
    "type": "warm_tone",
    "value": "暖色调",
    "confidence": 0.80,
    "evidence": {{
      "time_ranges_ms": [[{start_ms}, {end_ms}]]
    }},
    "detailed_description": {{
      "summary": "整体画面偏向暖色系，色温较高，橙黄色调为主",
      "technical_terms": ["暖色温", "Orange & Teal", "黄金时段色调"],
      "purpose": "营造温暖、舒适、怀旧或浪漫的氛围，增强情感共鸣",
      "parameters": {{
        "color_temperature": "5500K-6500K（偏暖）",
        "saturation": "中等偏高（60-70%）",
        "contrast": "柔和对比",
        "shadow_tint": "轻微橙色偏移",
        "highlight_tint": "柔和黄色"
      }}
    }}
  }}
]
```

关键要求：
1. value字段：简洁的特征名称，单一特征，不使用连接词
2. detailed_description字段：
   - summary：特征的简要描述（1-2句话）
   - technical_terms：相关专业术语（中英文均可）
   - purpose：此特征的镜头意义和艺术效果
   - parameters：具体的技术参数（根据类别提供）
   - diagram：（仅lighting类别）简单的光路图示意
3. confidence：0-1之间的数值
4. 只输出JSON数组，不要其他文字
5. 如果某个特征不明显，可以不输出该项
"""
    
    def _extract_json_from_text(self, text: str) -> Any:
        """从文本中提取JSON"""
        # 尝试找到```json或```之间的内容
        import re
        
        # 移除markdown代码块标记
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        # 尝试找到JSON对象或数组
        json_match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        raise LLMAPIError(f"无法从响应中提取JSON: {text[:200]}")
    
    async def _try_correct_result(
        self,
        result: Dict[str, Any],
        error_msg: str
    ) -> Dict[str, Any]:
        """尝试修正结果（暂不实现，直接返回原结果）"""
        logger.warning("结果修正功能暂未实现")
        return result
    
    async def summarize_video_analysis(
        self,
        segments: List[Dict[str, Any]],
        duration_ms: float
    ) -> Dict[str, Any]:
        """
        总结视频分析结果
        生成任务标题和学习要点
        
        Args:
            segments: 分析出的片段列表
            duration_ms: 视频总时长（毫秒）
        
        Returns:
            {
                "title": "任务标题",
                "learning_points": ["要点1", "要点2", "要点3"]
            }
        """
        logger.info(f"开始总结视频分析结果，共{len(segments)}个片段")
        
        # 构建总结提示词
        prompt = self._build_summary_prompt(segments, duration_ms)
        
        # 调用 LLM（不传图片，只基于特征数据）
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    message = result["choices"][0].get("message", {})
                    content = message.get("content", "")
                    
                    # 解析JSON
                    summary = self._extract_json_from_text(content)
                    
                    # 校验格式
                    if isinstance(summary, dict) and "title" in summary and "learning_points" in summary:
                        logger.info(f"总结完成: {summary['title']}")
                        return summary
                    else:
                        raise LLMAPIError("总结结果格式不正确")
                
                raise LLMAPIError("API响应格式异常")
        
        except httpx.HTTPError as e:
            logger.error(f"总结视频失败: {str(e)}")
            # 返回默认值
            return {
                "title": f"视频分析 - {len(segments)}个镜头",
                "learning_points": [
                    "这个视频包含多个镜头，展现了不同的拍摄技巧",
                    "注意观察不同镜头的运镜、光线和调色变化"
                ]
            }
    
    def _build_summary_prompt(
        self,
        segments: List[Dict[str, Any]],
        duration_ms: float
    ) -> str:
        """构建总结提示词"""
        
        # 收集所有特征
        camera_features = []
        lighting_features = []
        color_features = []
        
        for seg in segments:
            for feature in seg.get("features", []):
                if feature["category"] == "camera_motion":
                    camera_features.append(feature["value"])
                elif feature["category"] == "lighting":
                    lighting_features.append(feature["value"])
                elif feature["category"] == "color_grading":
                    color_features.append(feature["value"])
        
        # 统计信息
        stats = {
            "segment_count": len(segments),
            "duration_sec": duration_ms / 1000,
            "camera_features": list(set(camera_features)),
            "lighting_features": list(set(lighting_features)),
            "color_features": list(set(color_features))
        }
        
        return f"""请为这个视频分析任务生成一个简洁的标题和3-5个学习要点。

视频统计信息：
- 总时长: {stats['duration_sec']:.1f}秒
- 镜头数: {stats['segment_count']}个
- 运镜特征: {', '.join(stats['camera_features'][:5]) if stats['camera_features'] else '无'}
- 光线特征: {', '.join(stats['lighting_features'][:5]) if stats['lighting_features'] else '无'}
- 调色特征: {', '.join(stats['color_features'][:5]) if stats['color_features'] else '无'}

请输出JSON格式：

```json
{{
  "title": "简短的任务标题（10-20字，描述视频的主要风格或内容）",
  "learning_points": [
    "学习要点1：描述这个视频中值得学习的拍摄技巧或特征",
    "学习要点2：另一个值得注意的技术亮点",
    "学习要点3：镜头语言或视觉风格的总结"
  ]
}}
```

要求：
1. title要简洁、专业、有吸引力
2. learning_points要具体、实用、有指导意义
3. 每个要点控制在30字以内
4. 只输出JSON，不要其他文字
"""
