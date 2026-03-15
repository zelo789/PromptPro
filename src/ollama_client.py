"""
LLM API 客户端模块

提供统一的 LLM API 接口，支持多种提供商：
- Ollama (本地)
- OpenAI
- Claude (Anthropic)
- 自定义 OpenAI 兼容 API
"""
import logging
import time
import functools
from typing import List, Optional, Callable, Any, Dict
import json
import abc

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import Config
from src.exceptions import (
    ConnectionError as PromptProConnectionError,
    ModelError,
    ErrorCode,
)
from src.logger import get_logger

logger: logging.Logger


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (requests.exceptions.RequestException,),
):
    """
    重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 重试延迟（秒）
        exceptions: 触发重试的异常类型
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = delay * (2 ** attempt)  # 指数退避
                        logger.warning(
                            f"请求失败 (尝试 {attempt + 1}/{max_retries + 1})，"
                            f"{wait_time:.1f}秒后重试: {e}"
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"请求失败，已达最大重试次数: {e}")
            raise last_exception
        return wrapper
    return decorator


class BaseLLMClient(abc.ABC):
    """LLM 客户端基类"""

    def __init__(self, config: Config):
        self.config = config
        self.timeout = config.request_timeout
        self.temperature = config.temperature
        self.max_retries = config.max_retries
        self.retry_delay = config.retry_delay
        self._session = self._create_session()
        self._model = ""

    def _create_session(self) -> requests.Session:
        """创建带重试和连接池的 Session"""
        session = requests.Session()

        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20,
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def close(self) -> None:
        """关闭连接"""
        self._session.close()

    def __enter__(self) -> "BaseLLMClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    @abc.abstractmethod
    def check_connection(self) -> bool:
        """检查服务是否可用"""
        pass

    @abc.abstractmethod
    def list_models(self) -> List[str]:
        """获取可用模型列表"""
        pass

    @abc.abstractmethod
    def chat(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
    ) -> str:
        """聊天模式生成"""
        pass

    def set_model(self, model_name: str) -> bool:
        """设置当前使用的模型"""
        self._model = model_name
        logger.info(f"设置模型: {model_name}")
        return True

    def get_current_model(self) -> str:
        """获取当前使用的模型名称"""
        return self._model

    def set_temperature(self, temperature: float) -> None:
        """设置温度参数"""
        if not 0.0 <= temperature <= 2.0:
            raise ValueError(f"temperature 必须在 0.0 到 2.0 之间，当前值: {temperature}")
        self.temperature = temperature
        logger.debug(f"温度参数已设置为: {temperature}")

    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return self.list_models()


class OllamaClient(BaseLLMClient):
    """Ollama API 客户端"""

    def __init__(self, config: Config, model: Optional[str] = None):
        super().__init__(config)
        self.base_url = config.ollama_base_url
        self._model = model or config.default_model

        logger.debug(
            f"初始化 OllamaClient: base_url={self.base_url}, "
            f"model={self._model or 'auto'}"
        )

    @retry_on_failure(max_retries=2, delay=1.0)
    def check_connection(self) -> bool:
        """检查 Ollama 服务是否可用"""
        try:
            response = self._session.get(
                f"{self.base_url}/api/tags",
                timeout=5,
            )
            if response.status_code == 200:
                logger.debug("Ollama 服务连接成功")
                return True
            else:
                logger.warning(f"Ollama 服务返回非 200 状态码：{response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.warning(f"Ollama 服务连接失败：{e}")
            return False

    @retry_on_failure(max_retries=2, delay=1.0)
    def list_models(self) -> List[str]:
        """获取已安装的模型列表"""
        try:
            logger.debug("获取 Ollama 模型列表...")
            response = self._session.get(
                f"{self.base_url}/api/tags",
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            logger.info(f"获取到 {len(models)} 个模型：{', '.join(models)}")
            return models
        except requests.exceptions.RequestException as e:
            logger.error(f"无法连接 Ollama 服务获取模型列表：{e}")
            raise PromptProConnectionError(
                f"无法连接 Ollama 服务：{e}",
                error_code=ErrorCode.CONNECTION_FAILED,
                details=str(e),
            )

    def chat(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
    ) -> str:
        """聊天模式生成"""
        model = model or self._model
        temperature = temperature if temperature is not None else self.temperature

        if not model:
            logger.warning("未指定模型，将使用第一个可用模型")
            models = self.list_models()
            if models:
                model = models[0]
                self._model = model
            else:
                raise ModelError(
                    "没有可用的模型",
                    error_code=ErrorCode.MODEL_UNAVAILABLE,
                )

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {"temperature": temperature},
        }

        logger.debug(f"发送聊天请求到 Ollama 模型：{model}")

        return self._chat_with_retry(payload)

    @retry_on_failure(max_retries=3, delay=1.0)
    def _chat_with_retry(self, payload: dict) -> str:
        """带重试的聊天请求"""
        try:
            response = self._session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
                stream=True,
            )
            response.raise_for_status()
            result = self._parse_chat_stream(response)
            logger.debug(f"聊天请求完成，响应长度：{len(result)}")
            return result
        except requests.exceptions.Timeout as e:
            logger.error(f"Ollama API 请求超时：{e}")
            raise PromptProConnectionError(
                f"Ollama API 请求超时 ({self.timeout}s)",
                error_code=ErrorCode.CONNECTION_TIMEOUT,
                details=str(e),
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API 调用失败：{e}")
            raise PromptProConnectionError(
                f"Ollama API 调用失败：{e}",
                error_code=ErrorCode.CONNECTION_FAILED,
                details=str(e),
            )

    def _parse_chat_stream(self, response: requests.Response) -> str:
        """解析聊天流式响应"""
        result: List[str] = []
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    if "message" in data:
                        content = data["message"].get("content", "")
                        result.append(content)
                except json.JSONDecodeError:
                    logger.debug(f"解析 JSON 行失败：{line[:50]}...")
                    continue
        return "".join(result)


class OpenAIClient(BaseLLMClient):
    """OpenAI API 客户端"""

    def __init__(self, config: Config, model: Optional[str] = None):
        super().__init__(config)
        self.base_url = config.openai_base_url
        self.api_key = config.openai_api_key
        self._model = model or config.openai_model

        # 设置默认请求头
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.debug(
            f"初始化 OpenAIClient: base_url={self.base_url}, "
            f"model={self._model}"
        )

    def check_connection(self) -> bool:
        """检查 OpenAI API 是否可用"""
        if not self.api_key:
            logger.warning("OpenAI API Key 未配置")
            return False
        return True

    def list_models(self) -> List[str]:
        """获取可用模型列表"""
        # OpenAI 不支持动态获取用户可用模型，返回常用模型
        return [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ]

    def chat(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
    ) -> str:
        """聊天模式生成"""
        model = model or self._model or "gpt-4o-mini"
        temperature = temperature if temperature is not None else self.temperature

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }

        logger.debug(f"发送聊天请求到 OpenAI 模型：{model}")

        return self._chat_with_retry(payload)

    @retry_on_failure(max_retries=3, delay=1.0)
    def _chat_with_retry(self, payload: dict) -> str:
        """带重试的聊天请求"""
        try:
            response = self._session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            logger.debug(f"聊天请求完成，响应长度：{len(content)}")
            return content
        except requests.exceptions.Timeout as e:
            logger.error(f"OpenAI API 请求超时：{e}")
            raise PromptProConnectionError(
                f"OpenAI API 请求超时 ({self.timeout}s)",
                error_code=ErrorCode.CONNECTION_TIMEOUT,
                details=str(e),
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API 调用失败：{e}")
            raise PromptProConnectionError(
                f"OpenAI API 调用失败：{e}",
                error_code=ErrorCode.CONNECTION_FAILED,
                details=str(e),
            )


class ClaudeClient(BaseLLMClient):
    """Claude API 客户端"""

    def __init__(self, config: Config, model: Optional[str] = None):
        super().__init__(config)
        self.base_url = config.claude_base_url
        self.api_key = config.claude_api_key
        self._model = model or config.claude_model

        # 设置默认请求头
        self._headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        logger.debug(
            f"初始化 ClaudeClient: base_url={self.base_url}, "
            f"model={self._model}"
        )

    def check_connection(self) -> bool:
        """检查 Claude API 是否可用"""
        if not self.api_key:
            logger.warning("Claude API Key 未配置")
            return False
        return True

    def list_models(self) -> List[str]:
        """获取可用模型列表"""
        return [
            "claude-opus-4-6",
            "claude-sonnet-4-6",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

    def chat(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
    ) -> str:
        """聊天模式生成"""
        model = model or self._model or "claude-3-5-sonnet-20241022"
        temperature = temperature if temperature is not None else self.temperature

        # Claude API 需要分离 system 消息
        system_prompt = ""
        chat_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                chat_messages.append(msg)

        payload = {
            "model": model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": chat_messages,
        }

        if temperature is not None:
            payload["temperature"] = temperature

        logger.debug(f"发送聊天请求到 Claude 模型：{model}")

        return self._chat_with_retry(payload)

    @retry_on_failure(max_retries=3, delay=1.0)
    def _chat_with_retry(self, payload: dict) -> str:
        """带重试的聊天请求"""
        try:
            response = self._session.post(
                f"{self.base_url}/v1/messages",
                json=payload,
                headers=self._headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            content = data["content"][0]["text"]
            logger.debug(f"聊天请求完成，响应长度：{len(content)}")
            return content
        except requests.exceptions.Timeout as e:
            logger.error(f"Claude API 请求超时：{e}")
            raise PromptProConnectionError(
                f"Claude API 请求超时 ({self.timeout}s)",
                error_code=ErrorCode.CONNECTION_TIMEOUT,
                details=str(e),
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Claude API 调用失败：{e}")
            raise PromptProConnectionError(
                f"Claude API 调用失败：{e}",
                error_code=ErrorCode.CONNECTION_FAILED,
                details=str(e),
            )


class CustomClient(BaseLLMClient):
    """自定义 OpenAI 兼容 API 客户端"""

    def __init__(self, config: Config, model: Optional[str] = None):
        super().__init__(config)
        self.base_url = config.custom_base_url
        self.api_key = config.custom_api_key
        self._model = model or config.custom_model

        # 设置默认请求头
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.debug(
            f"初始化 CustomClient: base_url={self.base_url}, "
            f"model={self._model}"
        )

    def check_connection(self) -> bool:
        """检查自定义 API 是否可用"""
        if not self.base_url:
            logger.warning("自定义 API Base URL 未配置")
            return False
        return True

    def list_models(self) -> List[str]:
        """获取可用模型列表"""
        # 尝试获取模型列表，如果失败返回默认
        try:
            response = self._session.get(
                f"{self.base_url}/models",
                headers=self._headers,
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                models = [m["id"] for m in data.get("data", [])]
                return models[:20]  # 限制返回数量
        except Exception as e:
            logger.debug(f"获取模型列表失败: {e}")

        return [self._model] if self._model else ["custom-model"]

    def chat(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
    ) -> str:
        """聊天模式生成"""
        model = model or self._model or "default"
        temperature = temperature if temperature is not None else self.temperature

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }

        logger.debug(f"发送聊天请求到自定义 API 模型：{model}")

        return self._chat_with_retry(payload)

    @retry_on_failure(max_retries=3, delay=1.0)
    def _chat_with_retry(self, payload: dict) -> str:
        """带重试的聊天请求"""
        try:
            response = self._session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            logger.debug(f"聊天请求完成，响应长度：{len(content)}")
            return content
        except requests.exceptions.Timeout as e:
            logger.error(f"自定义 API 请求超时：{e}")
            raise PromptProConnectionError(
                f"自定义 API 请求超时 ({self.timeout}s)",
                error_code=ErrorCode.CONNECTION_TIMEOUT,
                details=str(e),
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"自定义 API 调用失败：{e}")
            raise PromptProConnectionError(
                f"自定义 API 调用失败：{e}",
                error_code=ErrorCode.CONNECTION_FAILED,
                details=str(e),
            )


class LLMClient:
    """
    统一的 LLM 客户端

    根据配置自动选择对应的 API 提供商
    """

    def __init__(self, config: Optional[Config] = None, model: Optional[str] = None):
        """
        初始化 LLM 客户端

        Args:
            config: 配置对象，可选
            model: 初始模型名称，可选
        """
        global logger
        logger = get_logger("llm_client")

        self.config = config or Config.load()
        self._model = model
        self._client = self._create_client()
        self.temperature = self.config.temperature

        logger.debug(f"初始化 LLMClient: provider={self.config.provider}")

    def _create_client(self) -> BaseLLMClient:
        """根据配置创建对应的客户端"""
        provider = self.config.provider

        if provider == "ollama":
            return OllamaClient(self.config, self._model)
        elif provider == "openai":
            return OpenAIClient(self.config, self._model)
        elif provider == "claude":
            return ClaudeClient(self.config, self._model)
        elif provider == "custom":
            return CustomClient(self.config, self._model)
        else:
            logger.warning(f"未知的 provider: {provider}，使用 Ollama")
            return OllamaClient(self.config, self._model)

    def check_connection(self) -> bool:
        """检查服务是否可用"""
        return self._client.check_connection()

    def list_models(self) -> List[str]:
        """获取可用模型列表"""
        return self._client.list_models()

    def chat(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
    ) -> str:
        """聊天模式生成"""
        temp = temperature if temperature is not None else self.temperature
        return self._client.chat(messages, model, stream, temp)

    def set_model(self, model_name: str) -> bool:
        """设置当前使用的模型"""
        return self._client.set_model(model_name)

    def get_current_model(self) -> str:
        """获取当前使用的模型名称"""
        return self._client.get_current_model()

    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return self._client.get_available_models()

    def set_temperature(self, temperature: float) -> None:
        """设置温度参数"""
        if not 0.0 <= temperature <= 2.0:
            raise ValueError(f"temperature 必须在 0.0 到 2.0 之间，当前值: {temperature}")
        self.temperature = temperature
        self._client.temperature = temperature
        logger.debug(f"温度参数已设置为: {temperature}")

    def close(self) -> None:
        """关闭连接"""
        self._client.close()

    def __enter__(self) -> "LLMClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()