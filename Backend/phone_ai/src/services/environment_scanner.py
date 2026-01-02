"""
Environment Scanner Service

使用多模态LLM分析拍摄环境的可拍性，为用户推荐低风险拍摄任务。
Uses multi-modal LLM to analyze shooting environment suitability and recommend low-risk tasks.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from pathlib import Path

from .llm_client import MMHLLMClient, MMFrameInput

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """拍摄任务风险等级"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EnvironmentTag(str, Enum):
    """环境标签枚举"""
    INDOOR = "室内"
    OUTDOOR = "室外"
    CROWDED = "人多"
    DESKTOP = "桌面"
    CORRIDOR = "走廊"
    BACKLIT = "逆光"
    DARK = "暗光"
    GLARE = "反光"
    BRIGHT = "明亮"
    SPACIOUS = "宽敞"
    NARROW = "狭窄"


@dataclass
class ShootingTask:
    """拍摄任务定义"""
    task_id: str
    name: str
    description: str
    target_duration_s: float
    risk_level: RiskLevel
    success_criteria: str
    target_motion: Optional[str] = None  # truck_right, dolly_in, etc.
    target_speed_range: Optional[tuple[float, float]] = None  # (min, max) px/frame

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "target_duration_s": self.target_duration_s,
            "risk_level": self.risk_level,
            "success_criteria": self.success_criteria,
            "target_motion": self.target_motion,
            "target_speed_range": self.target_speed_range,
        }


@dataclass
class EnvironmentAnalysis:
    """环境分析结果"""
    environment_tags: List[str]
    shootability_score: float  # 0-1, higher = better
    constraints: List[str]
    recommended_risk_level: str
    theme_candidates: List[str]
    suggested_tasks: List[ShootingTask]
    confidence: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "environment_tags": self.environment_tags,
            "shootability_score": self.shootability_score,
            "constraints": self.constraints,
            "recommended_risk_level": self.recommended_risk_level,
            "theme_candidates": self.theme_candidates,
            "suggested_tasks": [task.to_dict() for task in self.suggested_tasks],
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }


class EnvironmentScanner:
    """
    环境判读器
    Analyzes shooting environment and recommends low-risk tasks.
    """

    def __init__(self, mm_llm_client: Optional[MMHLLMClient] = None):
        """
        Initialize environment scanner.

        Args:
            mm_llm_client: Multi-modal LLM client for analysis
        """
        self.mm_llm_client = mm_llm_client or MMHLLMClient()
        self._predefined_tasks = self._create_predefined_tasks()

    def _create_predefined_tasks(self) -> Dict[str, ShootingTask]:
        """创建预定义的拍摄任务库"""
        tasks = {}

        # Anchor Hold - 锚点成立
        tasks["anchor_hold"] = ShootingTask(
            task_id="anchor_hold",
            name="静止锁定",
            description="保持静止，锁定主体位置，建立稳定的视觉锚点",
            target_duration_s=3.0,
            risk_level=RiskLevel.VERY_LOW,
            success_criteria="画面稳定，主体清晰，无明显抖动",
            target_motion="static",
            target_speed_range=(0, 2),
        )

        # Slow Truck - 关系稳定
        tasks["slow_truck_right"] = ShootingTask(
            task_id="slow_truck_right",
            name="缓慢右移",
            description="缓慢向右移动镜头，展示主体与环境的稳定关系",
            target_duration_s=4.0,
            risk_level=RiskLevel.LOW,
            success_criteria="匀速移动，节奏平稳，主体保持在画面中",
            target_motion="truck_right",
            target_speed_range=(3, 8),
        )

        tasks["slow_truck_left"] = ShootingTask(
            task_id="slow_truck_left",
            name="缓慢左移",
            description="缓慢向左移动镜头，展示主体与环境的稳定关系",
            target_duration_s=4.0,
            risk_level=RiskLevel.LOW,
            success_criteria="匀速移动，节奏平稳，主体保持在画面中",
            target_motion="truck_left",
            target_speed_range=(3, 8),
        )

        # Gentle Dolly - 信息完成
        tasks["gentle_dolly_in"] = ShootingTask(
            task_id="gentle_dolly_in",
            name="轻柔推进",
            description="轻柔向前推进镜头，逐步揭示更多信息",
            target_duration_s=3.5,
            risk_level=RiskLevel.LOW,
            success_criteria="推进速度均匀，景深变化自然",
            target_motion="dolly_in",
            target_speed_range=(2, 6),
        )

        tasks["gentle_dolly_out"] = ShootingTask(
            task_id="gentle_dolly_out",
            name="轻柔拉远",
            description="轻柔向后拉远镜头，展现更广阔的场景",
            target_duration_s=3.5,
            risk_level=RiskLevel.LOW,
            success_criteria="拉远速度均匀，景深变化自然",
            target_motion="dolly_out",
            target_speed_range=(2, 6),
        )

        # Reveal - 低风险揭示
        tasks["subtle_pan_right"] = ShootingTask(
            task_id="subtle_pan_right",
            name="微妙右摇",
            description="微妙向右摇镜头，逐渐揭示隐藏的元素",
            target_duration_s=3.0,
            risk_level=RiskLevel.MEDIUM,
            success_criteria="摇镜角度适中，不引起眩晕感",
            target_motion="pan_right",
            target_speed_range=(1, 4),
        )

        tasks["subtle_pan_left"] = ShootingTask(
            task_id="subtle_pan_left",
            name="微妙左摇",
            description="微妙向左摇镜头，逐渐揭示隐藏的元素",
            target_duration_s=3.0,
            risk_level=RiskLevel.MEDIUM,
            success_criteria="摇镜角度适中，不引起眩晕感",
            target_motion="pan_left",
            target_speed_range=(1, 4),
        )

        return tasks

    async def analyze_environment(
        self,
        frame_paths: List[str],
        timestamps_ms: Optional[List[float]] = None
    ) -> EnvironmentAnalysis:
        """
        分析拍摄环境并推荐任务。

        Args:
            frame_paths: 帧图片文件路径列表
            timestamps_ms: 对应的时间戳（毫秒），如果为None则自动生成

        Returns:
            EnvironmentAnalysis: 环境分析结果
        """
        logger.info(f"开始环境分析，共{len(frame_paths)}帧")

        # 准备帧输入
        if timestamps_ms is None:
            timestamps_ms = [i * 1000 for i in range(len(frame_paths))]  # 假设1秒间隔

        frame_inputs = [
            MMFrameInput(ts_ms=ts, image_path=path)
            for ts, path in zip(timestamps_ms, frame_paths)
        ]

        try:
            # 调用多模态LLM进行分析
            result = await self.mm_llm_client.analyze_environment(frame_inputs)

            # 解析结果并转换为结构化数据
            analysis = self._parse_llm_result(result)

            logger.info(f"环境分析完成，得分: {analysis.shootability_score:.2f}, "
                       f"推荐风险等级: {analysis.recommended_risk_level}")

            return analysis

        except Exception as e:
            logger.error(f"环境分析失败: {e}")
            # 返回兜底结果
            return self._create_fallback_analysis()

    def _parse_llm_result(self, llm_result: Dict[str, Any]) -> EnvironmentAnalysis:
        """解析LLM结果并转换为结构化数据"""
        # 解析环境标签
        env_tags = llm_result.get("environment_tags", [])

        # 解析可拍性得分
        shootability_score = float(llm_result.get("shootability_score", 0.5))
        shootability_score = max(0.0, min(1.0, shootability_score))

        # 解析约束条件
        constraints = llm_result.get("constraints", [])

        # 解析推荐风险等级
        risk_level = llm_result.get("recommended_risk_level", "low")

        # 解析主题候选
        theme_candidates = llm_result.get("theme_candidates", [])

        # 解析建议任务
        suggested_tasks_raw = llm_result.get("suggested_tasks", [])
        suggested_tasks = []

        for task_data in suggested_tasks_raw:
            task_id = task_data.get("task_id", "")
            predefined_task = self._predefined_tasks.get(task_id)

            if predefined_task:
                # 使用预定义任务
                suggested_tasks.append(predefined_task)
            else:
                # 创建自定义任务
                try:
                    task = ShootingTask(
                        task_id=task_id,
                        name=task_data.get("name", "未知任务"),
                        description=task_data.get("description", ""),
                        target_duration_s=float(task_data.get("target_duration_s", 3.0)),
                        risk_level=RiskLevel(task_data.get("risk_level", "low")),
                        success_criteria=task_data.get("success_criteria", ""),
                        target_motion=task_data.get("target_motion"),
                        target_speed_range=task_data.get("target_speed_range"),
                    )
                    suggested_tasks.append(task)
                except (ValueError, KeyError):
                    logger.warning(f"跳过无效任务: {task_data}")

        # 如果没有建议任务，使用默认的锚点任务
        if not suggested_tasks:
            suggested_tasks = [self._predefined_tasks["anchor_hold"]]

        # 解析置信度
        confidence = float(llm_result.get("confidence", 0.5))

        return EnvironmentAnalysis(
            environment_tags=env_tags,
            shootability_score=shootability_score,
            constraints=constraints,
            recommended_risk_level=risk_level,
            theme_candidates=theme_candidates,
            suggested_tasks=suggested_tasks,
            confidence=confidence,
        )

    def _create_fallback_analysis(self) -> EnvironmentAnalysis:
        """创建兜底环境分析结果"""
        return EnvironmentAnalysis(
            environment_tags=["未知环境"],
            shootability_score=0.5,
            constraints=["环境分析失败"],
            recommended_risk_level="low",
            theme_candidates=["通用"],
            suggested_tasks=[self._predefined_tasks["anchor_hold"]],
            confidence=0.3,
        )

    def get_task_by_id(self, task_id: str) -> Optional[ShootingTask]:
        """根据ID获取预定义任务"""
        return self._predefined_tasks.get(task_id)

    def get_tasks_by_risk_level(self, risk_level: RiskLevel) -> List[ShootingTask]:
        """根据风险等级获取任务列表"""
        return [
            task for task in self._predefined_tasks.values()
            if task.risk_level == risk_level
        ]

    def get_low_risk_tasks(self) -> List[ShootingTask]:
        """获取所有低风险任务"""
        return [
            task for task in self._predefined_tasks.values()
            if task.risk_level in (RiskLevel.VERY_LOW, RiskLevel.LOW)
        ]


# 全局实例
_environment_scanner: Optional[EnvironmentScanner] = None


def get_environment_scanner() -> EnvironmentScanner:
    """获取环境扫描器实例"""
    global _environment_scanner
    if _environment_scanner is None:
        _environment_scanner = EnvironmentScanner()
    return _environment_scanner
