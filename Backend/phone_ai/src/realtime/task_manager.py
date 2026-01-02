"""
Task Manager for Realtime Shooting Advisor

管理拍摄任务的状态机和执行流程。
Manages the state machine and execution flow for shooting tasks.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable

from ..services.environment_scanner import (
    EnvironmentScanner,
    EnvironmentAnalysis,
    ShootingTask,
    RiskLevel
)

logger = logging.getLogger(__name__)


class TaskState(str, Enum):
    """任务状态枚举"""
    ENV_SCAN = "env_scan"           # 环境扫描中
    TASK_PICKED = "task_picked"     # 已选择任务
    EXECUTING = "executing"         # 执行中
    RECOVERY = "recovery"           # 纠错中
    DONE = "done"                   # 完成
    FAILED = "failed"               # 失败


@dataclass
class TaskExecutionContext:
    """任务执行上下文"""
    task: ShootingTask
    start_time: float
    current_state: TaskState
    progress: float = 0.0  # 0-1
    last_feedback_time: float = 0.0
    error_count: int = 0
    success_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "task": self.task.to_dict(),
            "start_time": self.start_time,
            "current_state": self.current_state,
            "progress": self.progress,
            "last_feedback_time": self.last_feedback_time,
            "error_count": self.error_count,
            "success_metrics": self.success_metrics,
        }


@dataclass
class TaskManagerConfig:
    """任务管理器配置"""
    env_scan_timeout_s: float = 10.0     # 环境扫描超时时间
    task_execution_timeout_s: float = 30.0  # 任务执行超时时间
    recovery_max_attempts: int = 3      # 最大纠错次数
    feedback_interval_s: float = 1.0    # 反馈间隔
    success_threshold: float = 0.8      # 成功阈值


class TaskManager:
    """
    任务管理器
    Manages shooting task state machine and execution.
    """

    def __init__(
        self,
        config: Optional[TaskManagerConfig] = None,
        environment_scanner: Optional[EnvironmentScanner] = None
    ):
        """
        Initialize task manager.

        Args:
            config: Task manager configuration
            environment_scanner: Environment scanner instance
        """
        self.config = config or TaskManagerConfig()
        self.environment_scanner = environment_scanner
        self._current_context: Optional[TaskExecutionContext] = None
        self._environment_analysis: Optional[EnvironmentAnalysis] = None
        self._state_callbacks: Dict[TaskState, List[Callable]] = {}
        self._task_callbacks: Dict[str, List[Callable]] = {}

    def register_state_callback(
        self,
        state: TaskState,
        callback: Callable[[TaskExecutionContext], None]
    ) -> None:
        """注册状态变更回调"""
        if state not in self._state_callbacks:
            self._state_callbacks[state] = []
        self._state_callbacks[state].append(callback)

    def register_task_callback(
        self,
        task_id: str,
        callback: Callable[[TaskExecutionContext], None]
    ) -> None:
        """注册任务特定回调"""
        if task_id not in self._task_callbacks:
            self._task_callbacks[task_id] = []
        self._task_callbacks[task_id].append(callback)

    async def start_environment_scan(
        self,
        frame_paths: List[str],
        timestamps_ms: Optional[List[float]] = None
    ) -> None:
        """
        开始环境扫描。

        Args:
            frame_paths: 帧图片路径列表
            timestamps_ms: 时间戳列表
        """
        logger.info("开始环境扫描")

        # 重置上下文
        self._current_context = None
        self._environment_analysis = None

        try:
            # 执行环境分析
            self._environment_analysis = await asyncio.wait_for(
                self.environment_scanner.analyze_environment(
                    frame_paths, timestamps_ms
                ),
                timeout=self.config.env_scan_timeout_s
            )

            # 触发状态变更
            await self._notify_state_change(TaskState.ENV_SCAN)

            logger.info(f"环境扫描完成，可拍性得分: {self._environment_analysis.shootability_score:.2f}")

        except asyncio.TimeoutError:
            logger.error("环境扫描超时")
            await self._handle_scan_failure("环境扫描超时")
        except Exception as e:
            logger.error(f"环境扫描失败: {e}")
            await self._handle_scan_failure(f"环境扫描失败: {e}")

    async def pick_task(self, task_id: Optional[str] = None) -> bool:
        """
        选择执行任务。

        Args:
            task_id: 指定任务ID，如果为None则自动选择

        Returns:
            是否成功选择任务
        """
        if not self._environment_analysis:
            logger.error("未完成环境分析，无法选择任务")
            return False

        # 选择任务
        selected_task = self._select_task(task_id)
        if not selected_task:
            logger.error("无法选择合适任务")
            return False

        # 创建执行上下文
        self._current_context = TaskExecutionContext(
            task=selected_task,
            start_time=time.time(),
            current_state=TaskState.TASK_PICKED,
        )

        # 触发状态变更
        await self._notify_state_change(TaskState.TASK_PICKED)

        logger.info(f"选择任务: {selected_task.name} ({selected_task.task_id})")
        return True

    def _select_task(self, preferred_task_id: Optional[str] = None) -> Optional[ShootingTask]:
        """选择要执行的任务"""
        if not self._environment_analysis:
            return None

        # 如果指定了任务ID，优先使用
        if preferred_task_id:
            for task in self._environment_analysis.suggested_tasks:
                if task.task_id == preferred_task_id:
                    return task
            # 如果找不到，尝试从预定义任务中获取
            return self.environment_scanner.get_task_by_id(preferred_task_id)

        # 自动选择：按风险等级从低到高，选择第一个可用的
        risk_order = [RiskLevel.VERY_LOW, RiskLevel.LOW, RiskLevel.MEDIUM]

        for risk_level in risk_order:
            for task in self._environment_analysis.suggested_tasks:
                if task.risk_level == risk_level:
                    return task

        # 如果没有建议任务，返回默认的锚点任务
        return self.environment_scanner.get_task_by_id("anchor_hold")

    async def start_task_execution(self) -> bool:
        """
        开始任务执行。

        Returns:
            是否成功开始执行
        """
        if not self._current_context:
            logger.error("没有活动的任务上下文")
            return False

        if self._current_context.current_state != TaskState.TASK_PICKED:
            logger.error(f"任务状态不正确: {self._current_context.current_state}")
            return False

        # 更新状态
        self._current_context.current_state = TaskState.EXECUTING
        self._current_context.start_time = time.time()

        # 触发状态变更
        await self._notify_state_change(TaskState.EXECUTING)

        logger.info(f"开始执行任务: {self._current_context.task.name}")
        return True

    async def update_progress(
        self,
        current_time: float,
        motion_smoothness: float,
        avg_speed: float,
        speed_variance: float,
        direction_deg: float
    ) -> Dict[str, Any]:
        """
        更新任务执行进度。

        Args:
            current_time: 当前时间戳
            motion_smoothness: 运动平滑度 (0-1)
            avg_speed: 平均速度 (px/frame)
            speed_variance: 速度方差
            direction_deg: 主方向角度

        Returns:
            反馈信息字典
        """
        if not self._current_context:
            return {"type": "idle"}

        context = self._current_context
        task = context.task

        # 计算进度
        elapsed = current_time - context.start_time
        progress = min(elapsed / task.target_duration_s, 1.0)
        context.progress = progress

        # 检查是否完成
        if progress >= 1.0:
            await self._complete_task()
            return {"type": "completed", "task": task.to_dict()}

        # 检查是否需要纠错
        feedback = self._check_execution_quality(
            motion_smoothness, avg_speed, speed_variance, direction_deg
        )

        if feedback["needs_recovery"]:
            await self._enter_recovery(feedback["issues"])
            return {
                "type": "recovery",
                "issues": feedback["issues"],
                "suggestions": feedback["suggestions"]
            }

        # 正常执行中，定期给出鼓励反馈
        if current_time - context.last_feedback_time > self.config.feedback_interval_s:
            context.last_feedback_time = current_time
            return {
                "type": "progress",
                "progress": progress,
                "message": self._generate_progress_message(progress)
            }

        return {"type": "executing", "progress": progress}

    def _check_execution_quality(
        self,
        smoothness: float,
        speed: float,
        variance: float,
        direction: float
    ) -> Dict[str, Any]:
        """检查执行质量"""
        issues = []
        suggestions = []

        task = self._current_context.task

        # 检查平滑度
        if smoothness < 0.4:
            issues.append("抖动严重")
            suggestions.append("请夹紧双肘，屏住呼吸")

        # 检查速度
        if task.target_speed_range:
            min_speed, max_speed = task.target_speed_range
            if speed < min_speed * 0.5:  # 太慢
                issues.append("移动太慢")
                suggestions.append("请加快移动速度")
            elif speed > max_speed * 1.5:  # 太快
                issues.append("移动太快")
                suggestions.append("请放慢移动速度")

        # 检查速度一致性
        if variance > 10:
            issues.append("速度不稳定")
            suggestions.append("保持匀速移动")

        # 检查方向（如果有指定方向）
        if task.target_motion and "truck" in task.target_motion:
            expected_direction = self._motion_to_direction(task.target_motion)
            if expected_direction is not None:
                angle_diff = abs(direction - expected_direction)
                if angle_diff > 45:  # 偏差太大
                    issues.append("移动方向不正确")
                    suggestions.append(f"请向{self._direction_to_text(expected_direction)}移动")

        return {
            "needs_recovery": len(issues) > 0,
            "issues": issues,
            "suggestions": suggestions
        }

    def _motion_to_direction(self, motion: str) -> Optional[float]:
        """将运动类型转换为期望方向角度"""
        direction_map = {
            "truck_right": 0,      # 右移
            "truck_left": 180,     # 左移
            "pan_right": 90,       # 右摇
            "pan_left": 270,       # 左摇
        }
        return direction_map.get(motion)

    def _direction_to_text(self, angle_deg: float) -> str:
        """将角度转换为文字方向"""
        angle = angle_deg % 360
        if angle < 45 or angle >= 315:
            return "右"
        elif 45 <= angle < 135:
            return "下"
        elif 135 <= angle < 225:
            return "左"
        else:
            return "上"

    async def _enter_recovery(self, issues: List[str]) -> None:
        """进入纠错状态"""
        if not self._current_context:
            return

        context = self._current_context

        if context.current_state == TaskState.RECOVERY:
            context.error_count += 1
            if context.error_count >= self.config.recovery_max_attempts:
                await self._fail_task("超过最大纠错次数")
                return
        else:
            context.current_state = TaskState.RECOVERY
            context.error_count = 1
            await self._notify_state_change(TaskState.RECOVERY)

        logger.warning(f"进入纠错状态: {issues}")

    async def _complete_task(self) -> None:
        """完成任务"""
        if not self._current_context:
            return

        context = self._current_context
        context.current_state = TaskState.DONE
        context.progress = 1.0

        # 计算成功指标
        elapsed = time.time() - context.start_time
        context.success_metrics = {
            "duration": elapsed,
            "on_time": elapsed <= context.task.target_duration_s * 1.2,  # 允许20%误差
            "error_count": context.error_count,
        }

        await self._notify_state_change(TaskState.DONE)

        logger.info(f"任务完成: {context.task.name}")

    async def _fail_task(self, reason: str) -> None:
        """任务失败"""
        if not self._current_context:
            return

        context = self._current_context
        context.current_state = TaskState.FAILED

        await self._notify_state_change(TaskState.FAILED)

        logger.error(f"任务失败: {reason}")

    async def _handle_scan_failure(self, reason: str) -> None:
        """处理扫描失败"""
        logger.error(f"环境扫描失败: {reason}")

        # 创建兜底环境分析
        from ..services.environment_scanner import EnvironmentAnalysis, ShootingTask, RiskLevel
        self._environment_analysis = EnvironmentAnalysis(
            environment_tags=["未知环境"],
            shootability_score=0.3,
            constraints=[reason],
            recommended_risk_level="low",
            theme_candidates=["通用"],
            suggested_tasks=[self.environment_scanner.get_task_by_id("anchor_hold")],
            confidence=0.1,
        )

    async def _notify_state_change(self, new_state: TaskState) -> None:
        """通知状态变更"""
        if new_state in self._state_callbacks:
            for callback in self._state_callbacks[new_state]:
                try:
                    await callback(self._current_context)
                except Exception as e:
                    logger.error(f"状态回调失败: {e}")

        # 任务特定回调
        if self._current_context and self._current_context.task.task_id in self._task_callbacks:
            for callback in self._task_callbacks[self._current_context.task.task_id]:
                try:
                    await callback(self._current_context)
                except Exception as e:
                    logger.error(f"任务回调失败: {e}")

    def _generate_progress_message(self, progress: float) -> str:
        """生成进度消息"""
        percentage = int(progress * 100)
        if progress < 0.3:
            return "开始良好，继续保持"
        elif progress < 0.7:
            return f"进度{percentage}%，状态稳定"
        else:
            return f"即将完成{percentage}%，请坚持"

    def get_current_context(self) -> Optional[TaskExecutionContext]:
        """获取当前执行上下文"""
        return self._current_context

    def get_environment_analysis(self) -> Optional[EnvironmentAnalysis]:
        """获取环境分析结果"""
        return self._environment_analysis

    def reset(self) -> None:
        """重置任务管理器状态"""
        self._current_context = None
        self._environment_analysis = None
        logger.info("任务管理器已重置")


# 全局实例
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """获取任务管理器实例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager
