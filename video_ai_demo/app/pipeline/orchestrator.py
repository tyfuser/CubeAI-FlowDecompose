"""Pipeline编排器"""
import asyncio
from pathlib import Path
from typing import Dict, Any, List
import uuid

from .steps.ingest import ingest_video
from .steps.extract_frames import extract_frames
from .steps.scene_detect import detect_scenes
from .steps.mm_llm_decompose import decompose_with_mm_llm
from .steps.artifacts import generate_artifacts
from .steps.compare_map import map_segments
from .steps.improve_steps import generate_improvements

from ..db.session import get_db
from ..db.repo import JobRepository, AssetRepository, ArtifactRepository
from ..db.models import JobStatus, Asset, AssetRole, Artifact, ArtifactType
from ..core.config import settings
from ..core.errors import JobExecutionError
from ..core.logging import logger


class PipelineOrchestrator:
    """Pipeline编排器"""
    
    def __init__(self, job_id: str, job_config: Dict[str, Any]):
        self.job_id = job_id
        self.job_config = job_config
        self.mode = job_config.get("mode", "learn")
        self.job_dir = settings.data_dir / "jobs" / job_id
    
    async def execute(self) -> Dict[str, Any]:
        """执行Pipeline"""
        logger.info(f"开始执行Job {self.job_id}, mode={self.mode}")
        
        try:
            if self.mode == "learn":
                result = await self._execute_learn()
            elif self.mode == "compare":
                result = await self._execute_compare()
            else:
                raise JobExecutionError(f"不支持的mode: {self.mode}")
            
            logger.info(f"Job {self.job_id} 执行成功")
            return result
        
        except Exception as e:
            logger.error(f"Job {self.job_id} 执行失败: {str(e)}")
            raise
    
    async def _execute_learn(self) -> Dict[str, Any]:
        """执行Learn模式"""
        
        target_video = self.job_config.get("target_video", {})
        options = self.job_config.get("options", {})
        
        # 1. Ingest
        self._update_progress("ingest", 10, "下载视频...")
        ingest_result = await self._ingest_asset(target_video, AssetRole.TARGET)
        
        # 2. CV场景检测（新增）
        use_cv_detection = options.get("scene_detection", {}).get("use_cv", True)
        
        if use_cv_detection:
            self._update_progress("scene_detection", 25, "CV场景检测...")
            cv_segments = detect_scenes(
                ingest_result["local_path"],
                self.job_dir / "target",
                threshold=options.get("scene_detection", {}).get("threshold", 27.0)
            )
            logger.info(f"CV检测到{len(cv_segments)}个场景")
        else:
            cv_segments = None
        
        # 3. Extract frames
        self._update_progress("extract_frames", 35, "抽取关键帧...")
        frames_result = self._extract_frames_for_asset(
            ingest_result["local_path"],
            options.get("frame_extract", {})
        )
        
        # 4. LLM特征分析（基于CV检测的场景）
        self._update_progress("feature_analysis", 60, "分析视频特征...")
        
        if cv_segments:
            # 使用CV检测的场景边界，LLM只分析特征
            decompose_result = await self._analyze_cv_segments(
                cv_segments,
                frames_result["frames_index"],
                options.get("llm", {})
            )
        else:
            # 完全使用LLM拆解
            decompose_result = await decompose_with_mm_llm(
                frames_result["frames_index"],
                options.get("llm", {})
            )
        
        # 5. Generate artifacts
        self._update_progress("artifacts", 85, "生成产物...")
        artifacts_result = generate_artifacts(
            decompose_result["segments"],
            frames_result["frames_index"],
            self.job_dir / "target",
            asset_role="target"
        )
        
        # 6. Build result
        self._update_progress("finalize", 95, "完成...")
        
        result = {
            "mode": "learn",
            "target": {
                "asset_id": ingest_result.get("asset_id"),
                "segments": decompose_result["segments"],
                "keyframes": artifacts_result["keyframes"],
                "detection_method": "cv" if use_cv_detection else "llm"
            }
        }
        
        # 保存结果
        with get_db() as db:
            job_repo = JobRepository(db)
            job_repo.save_result(self.job_id, result)
        
        return result
    
    async def _execute_compare(self) -> Dict[str, Any]:
        """执行Compare模式"""
        
        target_video = self.job_config.get("target_video", {})
        user_video = self.job_config.get("user_video", {})
        options = self.job_config.get("options", {})
        
        # Target 全流程
        self._update_progress("target_ingest", 5, "处理target视频...")
        target_ingest = await self._ingest_asset(target_video, AssetRole.TARGET)
        
        self._update_progress("target_extract", 15, "抽取target关键帧...")
        target_frames = self._extract_frames_for_asset(
            target_ingest["local_path"],
            options.get("frame_extract", {})
        )
        
        self._update_progress("target_decompose", 25, "分析target特征...")
        target_decompose = await decompose_with_mm_llm(
            target_frames["frames_index"],
            options.get("llm", {})
        )
        
        target_artifacts = generate_artifacts(
            target_decompose["segments"],
            target_frames["frames_index"],
            self.job_dir / "target",
            asset_role="target"
        )
        
        # User 全流程
        self._update_progress("user_ingest", 40, "处理user视频...")
        user_ingest = await self._ingest_asset(user_video, AssetRole.USER)
        
        self._update_progress("user_extract", 50, "抽取user关键帧...")
        user_frames = self._extract_frames_for_asset(
            user_ingest["local_path"],
            options.get("frame_extract", {})
        )
        
        self._update_progress("user_decompose", 60, "分析user特征...")
        user_decompose = await decompose_with_mm_llm(
            user_frames["frames_index"],
            options.get("llm", {})
        )
        
        user_artifacts = generate_artifacts(
            user_decompose["segments"],
            user_frames["frames_index"],
            self.job_dir / "user",
            asset_role="user"
        )
        
        # Compare 和 Improve
        self._update_progress("compare", 75, "对比分析...")
        mappings = map_segments(
            target_decompose["segments"],
            user_decompose["segments"]
        )
        
        self._update_progress("improve", 85, "生成改进建议...")
        improvements = generate_improvements(
            user_decompose["segments"],
            target_decompose["segments"],
            mappings
        )
        
        # Build result
        self._update_progress("finalize", 95, "完成...")
        
        result = {
            "mode": "compare",
            "target": {
                "asset_id": target_ingest.get("asset_id"),
                "segments": target_decompose["segments"],
                "keyframes": target_artifacts["keyframes"]
            },
            "user": {
                "asset_id": user_ingest.get("asset_id"),
                "segments": user_decompose["segments"],
                "keyframes": user_artifacts["keyframes"]
            },
            "comparison": {
                "mappings": mappings,
                "improvements": improvements
            }
        }
        
        # 保存结果
        with get_db() as db:
            job_repo = JobRepository(db)
            job_repo.save_result(self.job_id, result)
        
        return result
    
    async def _ingest_asset(
        self,
        video_config: Dict[str, Any],
        role: AssetRole
    ) -> Dict[str, Any]:
        """摄取资源"""
        
        source = video_config.get("source", {})
        source_type = source.get("type", "url")
        source_url = source.get("url")
        source_path = source.get("path")
        
        output_dir = self.job_dir / role.value
        
        ingest_result = await ingest_video(
            source_type,
            source_url,
            source_path,
            output_dir
        )
        
        # 保存到数据库
        with get_db() as db:
            asset_repo = AssetRepository(db)
            
            asset_id = f"{self.job_id}_{role.value}"
            asset = Asset(
                id=asset_id,
                job_id=self.job_id,
                role=role,
                source_type=source_type,
                source_url=source_url,
                source_path=source_path,
                local_path=ingest_result["local_path"],
                duration_ms=ingest_result["duration_ms"],
                width=ingest_result["width"],
                height=ingest_result["height"],
                fps=ingest_result["fps"],
                codec=ingest_result["codec"]
            )
            
            asset_repo.create(asset)
        
        return {**ingest_result, "asset_id": asset_id}
    
    def _extract_frames_for_asset(
        self,
        video_path: str,
        frame_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """为资源抽取帧"""
        
        fps = frame_config.get("fps", 2.0)
        max_frames = frame_config.get("max_frames", 240)
        
        return extract_frames(
            video_path,
            self.job_dir,
            fps,
            max_frames
        )
    
    async def _analyze_cv_segments(
        self,
        cv_segments: List[Dict[str, Any]],
        frames_index: List[Dict[str, Any]],
        llm_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        基于CV检测的场景，使用LLM分析特征
        """
        from .steps.mm_llm_decompose import decompose_with_mm_llm
        from ..integrations.mm_llm_client import MMHLLMClient, FrameInput
        
        logger.info(f"开始分析{len(cv_segments)}个CV检测的场景")
        
        segments_with_features = []
        
        # 为每个CV检测的场景分析特征
        for segment in cv_segments:
            segment_id = segment["segment_id"]
            start_ms = segment["start_ms"]
            end_ms = segment["end_ms"]
            
            # 获取该场景的帧
            segment_frames = [
                f for f in frames_index
                if start_ms <= f["ts_ms"] <= end_ms
            ]
            
            if not segment_frames:
                # 如果没有帧，使用边界附近的帧
                closest_frame = min(frames_index, key=lambda f: abs(f["ts_ms"] - start_ms))
                segment_frames = [closest_frame]
            
            # 准备帧输入
            frame_inputs = [
                FrameInput(ts_ms=frame["ts_ms"], image_path=frame["path"])
                for frame in segment_frames[:5]  # 最多5帧
            ]
            
            # 创建LLM客户端
            client = MMHLLMClient(model=llm_config.get("model"))
            
            # 只分析特征，不做场景切分
            enabled_modules = llm_config.get("enabled_modules", [
                "camera_motion", "lighting", "color_grading"
            ])
            
            prompt = self._build_feature_only_prompt(
                segment_id, start_ms, end_ms, enabled_modules
            )
            
            try:
                response = await client._call_api(frame_inputs, prompt)
                
                # 解析特征
                import json
                try:
                    features = json.loads(response)
                    if isinstance(features, dict) and "features" in features:
                        features = features["features"]
                except json.JSONDecodeError:
                    features = client._extract_json_from_text(response)
                
                # 规范化特征
                normalized_features = client._normalize_features(features, start_ms, end_ms)
                
                segments_with_features.append({
                    "segment_id": segment_id,
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "duration_ms": end_ms - start_ms,
                    "features": normalized_features
                })
                
                logger.info(f"场景{segment_id}分析完成，{len(normalized_features)}个特征")
                
            except Exception as e:
                logger.error(f"场景{segment_id}分析失败: {str(e)}")
                # 添加空特征的场景
                segments_with_features.append({
                    "segment_id": segment_id,
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "duration_ms": end_ms - start_ms,
                    "features": []
                })
        
        return {"segments": segments_with_features}
    
    def _build_feature_only_prompt(
        self,
        segment_id: str,
        start_ms: float,
        end_ms: float,
        enabled_modules: List[str]
    ) -> str:
        """构建仅分析特征的提示词（不做场景切分）"""
        
        modules_desc = {
            "camera_motion": "运镜方式（如推镜、拉镜、平移、固定等）",
            "lighting": "光线布局（如主光位置、补光、轮廓光等）",
            "color_grading": "调色风格（如色温、饱和度、对比度风格等）"
        }
        
        enabled_desc = "\n".join([
            f"- {modules_desc.get(m, m)}" for m in enabled_modules
        ])
        
        return f"""请分析这个视频片段的影视特征。

片段ID: {segment_id}
时间范围: {start_ms}ms - {end_ms}ms

需要分析的特征：
{enabled_desc}

请输出JSON格式，包含所有需要分析的特征：

```json
[
  {{
    "category": "camera_motion",
    "type": "push_in",
    "value": "缓慢推镜",
    "confidence": 0.85,
    "evidence": {{
      "time_ranges_ms": [[{start_ms}, {end_ms}]]
    }}
  }},
  {{
    "category": "lighting",
    "type": "natural",
    "value": "自然光从侧面照射",
    "confidence": 0.90,
    "evidence": {{
      "time_ranges_ms": [[{start_ms}, {end_ms}]]
    }}
  }},
  {{
    "category": "color_grading",
    "type": "warm_tone",
    "value": "暖色调，高饱和度",
    "confidence": 0.88,
    "evidence": {{
      "time_ranges_ms": [[{start_ms}, {end_ms}]]
    }}
  }}
]
```

要求：
1. 必须分析所有启用的特征类别（camera_motion、lighting、color_grading）
2. 每个category至少输出一个特征
3. 每个feature的value只描述一个特征
4. confidence为0-1的数值
5. 只输出JSON数组，不要其他文字
"""
    
    def _update_progress(self, stage: str, percent: float, message: str):
        """更新进度"""
        with get_db() as db:
            job_repo = JobRepository(db)
            job_repo.update_progress(self.job_id, stage, percent, message)


# 全局Job运行器（简单版本：内存字典）
_running_jobs: Dict[str, asyncio.Task] = {}


async def submit_job(job_id: str, job_config: Dict[str, Any]):
    """提交Job到运行器"""
    
    logger.info(f"提交Job {job_id}")
    
    # 更新状态为running
    with get_db() as db:
        job_repo = JobRepository(db)
        job_repo.update_status(job_id, JobStatus.RUNNING)
    
    # 创建orchestrator
    orchestrator = PipelineOrchestrator(job_id, job_config)
    
    # 创建异步任务
    task = asyncio.create_task(_run_job(job_id, orchestrator))
    _running_jobs[job_id] = task
    
    return task


async def _run_job(job_id: str, orchestrator: PipelineOrchestrator):
    """运行Job（后台任务）"""
    
    try:
        result = await orchestrator.execute()
        
        # 更新状态为succeeded
        with get_db() as db:
            job_repo = JobRepository(db)
            job_repo.update_status(job_id, JobStatus.SUCCEEDED)
            job_repo.update_progress(job_id, "completed", 100, "完成")
        
        logger.info(f"Job {job_id} 完成")
    
    except Exception as e:
        logger.error(f"Job {job_id} 失败: {str(e)}", exc_info=True)
        
        # 更新状态为failed
        with get_db() as db:
            job_repo = JobRepository(db)
            job_repo.update_status(
                job_id,
                JobStatus.FAILED,
                error_message=str(e),
                error_details={"exception": str(type(e).__name__)}
            )
    
    finally:
        # 清理任务
        if job_id in _running_jobs:
            del _running_jobs[job_id]

