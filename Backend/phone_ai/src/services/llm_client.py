"""
LLM API client for the Video Shooting Assistant.

Provides a unified interface for interacting with LLM APIs (OpenAI, Claude)
with retry logic, exponential backoff, and response validation.
"""
import asyncio
import json
import logging
import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, List, Dict
from pathlib import Path

import httpx

from configs.settings import settings


logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    SOPHNET = "sophnet"  # SophNet API (OpenAI compatible)


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class LLMRateLimitError(LLMError):
    """Rate limit exceeded error."""
    pass


class LLMTimeoutError(LLMError):
    """Request timeout error."""
    pass


class LLMResponseError(LLMError):
    """Invalid response from LLM."""
    pass


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    provider: LLMProvider = LLMProvider.OPENAI
    api_key: Optional[str] = None
    model: str = "gpt-4"
    base_url: Optional[str] = None  # Custom API base URL
    max_retries: int = 3
    timeout: int = 30
    base_delay: float = 1.0
    max_delay: float = 30.0
    temperature: float = 0.7
    max_tokens: int = 1000
    
    @classmethod
    def from_settings(cls) -> "LLMConfig":
        """Create config from application settings."""
        provider = LLMProvider(settings.llm.provider)
        base_url = getattr(settings.llm, 'base_url', None)
        
        return cls(
            provider=provider,
            api_key=settings.llm.api_key,
            model=settings.llm.model,
            base_url=base_url,
            max_retries=settings.llm.max_retries,
            timeout=settings.llm.timeout,
        )


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a completion for the given prompt.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            
        Returns:
            The generated text response
        """
        pass
    
    async def complete_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a completion with retry logic.
        
        Implements exponential backoff for transient failures.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            
        Returns:
            The generated text response
            
        Raises:
            LLMError: If all retries fail
        """
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                return await self.complete(prompt, system_prompt)
            except LLMRateLimitError as e:
                last_error = e
                delay = self._calculate_delay(attempt)
                logger.warning(
                    f"Rate limit hit, retrying in {delay:.1f}s "
                    f"(attempt {attempt + 1}/{self.config.max_retries})"
                )
                await asyncio.sleep(delay)
            except LLMTimeoutError as e:
                last_error = e
                delay = self._calculate_delay(attempt)
                logger.warning(
                    f"Timeout, retrying in {delay:.1f}s "
                    f"(attempt {attempt + 1}/{self.config.max_retries})"
                )
                await asyncio.sleep(delay)
            except LLMError as e:
                # Non-retryable error
                raise
        
        raise LLMError(
            f"All {self.config.max_retries} retries failed. Last error: {last_error}"
        )
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        delay = self.config.base_delay * (2 ** attempt)
        return min(delay, self.config.max_delay)


class OpenAIClient(BaseLLMClient):
    """OpenAI API client (also supports OpenAI-compatible APIs like SophNet)."""
    
    DEFAULT_API_URL = "https://api.openai.com/v1/chat/completions"
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        # Use custom base_url if provided, otherwise use default
        if config.base_url:
            self.api_url = f"{config.base_url.rstrip('/')}/chat/completions"
        else:
            self.api_url = self.DEFAULT_API_URL
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate completion using OpenAI-compatible API."""
        if not self.config.api_key:
            raise LLMError("API key not configured")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.config.timeout,
                )
                
                if response.status_code == 429:
                    raise LLMRateLimitError("Rate limit exceeded")
                
                if response.status_code != 200:
                    raise LLMError(
                        f"API error: {response.status_code} - {response.text}"
                    )
                
                data = response.json()
                return data["choices"][0]["message"]["content"]
                
            except httpx.TimeoutException:
                raise LLMTimeoutError(
                    f"Request timed out after {self.config.timeout}s"
                )
            except httpx.RequestError as e:
                raise LLMError(f"Request failed: {e}")


class AnthropicClient(BaseLLMClient):
    """Anthropic (Claude) API client."""
    
    API_URL = "https://api.anthropic.com/v1/messages"
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate completion using Anthropic API."""
        if not self.config.api_key:
            raise LLMError("Anthropic API key not configured")
        
        headers = {
            "x-api-key": self.config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        
        payload = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.API_URL,
                    headers=headers,
                    json=payload,
                    timeout=self.config.timeout,
                )
                
                if response.status_code == 429:
                    raise LLMRateLimitError("Anthropic rate limit exceeded")
                
                if response.status_code != 200:
                    raise LLMError(
                        f"Anthropic API error: {response.status_code} - {response.text}"
                    )
                
                data = response.json()
                return data["content"][0]["text"]
                
            except httpx.TimeoutException:
                raise LLMTimeoutError(
                    f"Anthropic request timed out after {self.config.timeout}s"
                )
            except httpx.RequestError as e:
                raise LLMError(f"Anthropic request failed: {e}")


class MockLLMClient(BaseLLMClient):
    """
    Mock LLM client for testing.
    
    Returns predefined responses based on input patterns.
    """
    
    def __init__(self, config: LLMConfig, responses: Optional[dict] = None):
        super().__init__(config)
        self.responses = responses or {}
        self.call_count = 0
        self.last_prompt = None
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """Return mock response."""
        self.call_count += 1
        self.last_prompt = prompt
        
        # Check for predefined responses
        for pattern, response in self.responses.items():
            if pattern in prompt:
                return response
        
        # Default mock response
        return json.dumps({
            "motion": {
                "type": "static",
                "params": {
                    "speed_profile": "linear"
                }
            },
            "framing": {
                "suggested_scale": "medium"
            },
            "confidence": 0.75,
            "explainability": "这是一个测试响应。运动分析显示静态镜头特征。"
        }, ensure_ascii=False)


class LLMClient:
    """
    Unified LLM client factory.
    
    Creates the appropriate client based on configuration.
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize the LLM client.
        
        Args:
            config: LLM configuration. If None, loads from settings.
        """
        self.config = config or LLMConfig.from_settings()
        self._client = self._create_client()
    
    def _create_client(self) -> BaseLLMClient:
        """Create the appropriate client based on provider."""
        if self.config.provider in (LLMProvider.OPENAI, LLMProvider.SOPHNET):
            return OpenAIClient(self.config)
        elif self.config.provider == LLMProvider.ANTHROPIC:
            return AnthropicClient(self.config)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config.provider}")
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a completion.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            
        Returns:
            The generated text response
        """
        return await self._client.complete_with_retry(prompt, system_prompt)
    
    async def complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Generate a completion and parse as JSON.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            
        Returns:
            Parsed JSON response
            
        Raises:
            LLMResponseError: If response is not valid JSON
        """
        from src.agents.prompt_templates import parse_llm_response
        
        response = await self.complete(prompt, system_prompt)
        
        try:
            return parse_llm_response(response)
        except ValueError as e:
            raise LLMResponseError(f"Failed to parse LLM response as JSON: {e}")


def create_llm_client(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> LLMClient:
    """
    Factory function to create an LLM client.

    Args:
        provider: LLM provider ("openai" or "anthropic")
        api_key: API key for the provider
        model: Model name to use

    Returns:
        Configured LLM client
    """
    config = LLMConfig.from_settings()

    if provider:
        config.provider = LLMProvider(provider)
    if api_key:
        config.api_key = api_key
    if model:
        config.model = model

    return LLMClient(config)


# =============================================================================
# Multi-Modal LLM Client (for environment scanning)
# =============================================================================

@dataclass
class MMFrameInput:
    """Frame input for multi-modal LLM."""
    ts_ms: float
    image_path: str


@dataclass
class MMHLLMConfig:
    """Configuration for multi-modal LLM client."""
    provider: LLMProvider = LLMProvider.SOPHNET
    api_key: Optional[str] = None
    model: str = "Qwen2.5-VL-7B-Instruct"
    base_url: str = "https://www.sophnet.com/api/open-apis/v1"
    max_retries: int = 3
    timeout: int = 30
    temperature: float = 0.7
    max_tokens: int = 1000

    @classmethod
    def from_settings(cls) -> "MMHLLMConfig":
        """Create config from application settings."""
        return cls(
            api_key=settings.mm_llm.api_key,
            model=settings.mm_llm.model,
            base_url=settings.mm_llm.base_url,
            max_retries=settings.mm_llm.max_retries,
            timeout=settings.mm_llm.timeout,
        )


class MMHLLMClient:
    """Multi-modal LLM client for environment scanning."""

    def __init__(self, config: Optional[MMHLLMConfig] = None):
        self.config = config or MMHLLMConfig.from_settings()

        if not self.config.api_key:
            raise LLMError(
                "未配置多模态LLM API密钥。\n"
                "请设置环境变量 MM_LLM_API_KEY"
            )

    async def analyze_environment(
        self,
        frames: List[MMFrameInput],
        prompt_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze environment for shooting suitability.

        Args:
            frames: List of frame inputs with timestamps and paths
            prompt_config: Optional prompt configuration

        Returns:
            Environment analysis result with tags, constraints, and recommendations
        """
        logger.info(f"开始分析环境，共{len(frames)}帧")

        # Sample frames for analysis (avoid too many images)
        sampled_frames = self._sample_frames(frames, max_frames=3)

        prompt = self._build_environment_prompt(sampled_frames, prompt_config)

        response = await self._call_mm_api(sampled_frames, prompt)

        try:
            result = json.loads(response)
            logger.info("环境分析完成")
            return result
        except json.JSONDecodeError:
            logger.warning(f"环境分析响应不是JSON: {response[:200]}")
            # Return a fallback result
            return self._create_fallback_environment_result()

    async def _call_mm_api(
        self,
        frames: List[MMFrameInput],
        prompt: str
    ) -> str:
        """Call multi-modal API."""

        # Build messages with images
        content = [{"type": "text", "text": prompt}]

        for frame in frames:
            image_url = self._prepare_image_url(frame.image_path)
            content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                response = await client.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()

                result = response.json()

                if "choices" in result and len(result["choices"]) > 0:
                    message = result["choices"][0].get("message", {})
                    return message.get("content", "")

                raise LLMAPIError("API响应格式异常")

            except httpx.TimeoutException:
                raise LLMTimeoutError("多模态LLM请求超时")
            except httpx.RequestError as e:
                raise LLMAPIError(f"多模态LLM请求失败: {e}")

    def _prepare_image_url(self, image_path: str) -> str:
        """Prepare image URL (convert to base64 data URL)."""
        path = Path(image_path)
        if not path.exists():
            raise LLMAPIError(f"图片不存在: {image_path}")

        # Read image and convert to base64
        with open(path, "rb") as f:
            image_data = f.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')

        # Detect mime type
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
        frames: List[MMFrameInput],
        max_frames: int
    ) -> List[MMFrameInput]:
        """Sample frames to avoid too many images."""
        if len(frames) <= max_frames:
            return frames

        step = len(frames) / max_frames
        indices = [int(i * step) for i in range(max_frames)]
        return [frames[i] for i in indices]

    def _build_environment_prompt(
        self,
        frames: List[MMFrameInput],
        prompt_config: Optional[Dict[str, Any]]
    ) -> str:
        """Build environment analysis prompt."""

        duration_ms = frames[-1].ts_ms if frames else 0

        return f"""请分析这段视频环境，评估拍摄条件并推荐低风险拍摄任务。

视频时长: {duration_ms}ms
分析帧数: {len(frames)}帧

请输出JSON格式：

```json
{{
  "environment_tags": ["室内", "室外", "人多", "桌面", "走廊", "逆光", "暗光", "反光"],
  "shootability_score": 0.8,
  "constraints": ["暗光", "反光", "主体模糊", "空间狭窄", "人流密集"],
  "recommended_risk_level": "low",
  "theme_candidates": ["人物", "物件", "空间", "氛围", "行动"],
  "suggested_tasks": [
    {{
      "task_id": "anchor_hold",
      "name": "静止锁定",
      "description": "保持静止，锁定主体位置",
      "target_duration_s": 3.0,
      "risk_level": "very_low",
      "success_criteria": "画面稳定，主体清晰"
    }},
    {{
      "task_id": "slow_truck_right",
      "name": "缓慢右移",
      "description": "缓慢向右移动镜头",
      "target_duration_s": 4.0,
      "risk_level": "low",
      "success_criteria": "匀速移动，节奏平稳"
    }}
  ],
  "confidence": 0.85
}}
```

关键要求：
1. environment_tags：选择最相关的标签（最多3个）
2. shootability_score：0-1之间的数值，表示环境适合度
3. constraints：当前环境的限制条件
4. recommended_risk_level：low/medium/high
5. theme_candidates：适合当前环境的主题类型
6. suggested_tasks：推荐的具体拍摄任务，按风险从低到高排序
7. 只输出JSON，不要其他文字
"""

    def _create_fallback_environment_result(self) -> Dict[str, Any]:
        """Create fallback environment analysis result when LLM fails."""
        return {
            "environment_tags": ["未知环境"],
            "shootability_score": 0.5,
            "constraints": ["分析失败"],
            "recommended_risk_level": "low",
            "theme_candidates": ["通用"],
            "suggested_tasks": [
                {
                    "task_id": "anchor_hold",
                    "name": "静止锁定",
                    "description": "保持静止，锁定主体位置",
                    "target_duration_s": 3.0,
                    "risk_level": "very_low",
                    "success_criteria": "画面稳定，主体清晰"
                }
            ],
            "confidence": 0.5
        }


def create_mm_llm_client() -> MMHLLMClient:
    """
    Factory function to create multi-modal LLM client.

    Returns:
        Configured MMHLLMClient instance
    """
    return MMHLLMClient()
