"""Provider clients used by PromptPro."""

from __future__ import annotations

import abc
import functools
import json
import time
from typing import Any, Callable, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import Config
from src.exceptions import ConnectionError as PromptProConnectionError
from src.exceptions import ErrorCode, ModelError
from src.logger import get_logger

logger = get_logger("llm_client")


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[BaseException], ...] = (requests.exceptions.RequestException,),
):
    """Retry helper with exponential backoff for transient network failures."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:  # type: ignore[misc]
                    last_exception = exc
                    if attempt < max_retries:
                        wait_time = delay * (2 ** attempt)
                        logger.warning(
                            "Request failed (%s/%s). Retrying in %.1fs: %s",
                            attempt + 1,
                            max_retries + 1,
                            wait_time,
                            exc,
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error("Request failed after %s attempts: %s", max_retries + 1, exc)
            raise last_exception

        return wrapper

    return decorator


class BaseLLMClient(abc.ABC):
    """Abstract base class for provider-specific clients."""

    def __init__(self, config: Config):
        self.config = config
        self.timeout = config.request_timeout
        self.temperature = config.temperature
        self.max_retries = config.max_retries
        self.retry_delay = config.retry_delay
        self._session = self._create_session()
        self._model = ""

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> "BaseLLMClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    @abc.abstractmethod
    def check_connection(self) -> bool:
        """Return whether the configured provider is reachable enough to use."""

    @abc.abstractmethod
    def list_models(self) -> List[str]:
        """Return available models for the current provider."""

    @abc.abstractmethod
    def chat(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate a response from the provider."""

    def set_model(self, model_name: str) -> bool:
        self._model = model_name
        logger.info("Model set to %s", model_name)
        return True

    def get_current_model(self) -> str:
        return self._model

    def set_temperature(self, temperature: float) -> None:
        if not 0.0 <= temperature <= 2.0:
            raise ValueError(f"temperature must be between 0.0 and 2.0, got {temperature}")
        self.temperature = temperature

    def get_available_models(self) -> List[str]:
        return self.list_models()


class OllamaClient(BaseLLMClient):
    """Client for local Ollama servers."""

    def __init__(self, config: Config, model: Optional[str] = None):
        super().__init__(config)
        self.base_url = config.ollama_base_url.rstrip("/")
        self._model = model or config.default_model

    @retry_on_failure(max_retries=2, delay=1.0)
    def check_connection(self) -> bool:
        try:
            response = self._session.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException as exc:
            logger.warning("Ollama connection check failed: %s", exc)
            return False

    @retry_on_failure(max_retries=2, delay=1.0)
    def list_models(self) -> List[str]:
        try:
            response = self._session.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except requests.exceptions.RequestException as exc:
            raise PromptProConnectionError(
                f"Unable to fetch Ollama models: {exc}",
                error_code=ErrorCode.CONNECTION_FAILED,
                details=str(exc),
            ) from exc

    def chat(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
    ) -> str:
        model_name = model or self._model
        temp = self.temperature if temperature is None else temperature

        if not model_name:
            models = self.list_models()
            if not models:
                raise ModelError("No Ollama models are available.", error_code=ErrorCode.MODEL_UNAVAILABLE)
            model_name = models[0]
            self._model = model_name

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": stream,
            "options": {"temperature": temp},
        }
        return self._chat_with_retry(payload)

    @retry_on_failure(max_retries=3, delay=1.0)
    def _chat_with_retry(self, payload: dict) -> str:
        try:
            response = self._session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
                stream=True,
            )
            response.raise_for_status()
            return self._parse_chat_stream(response)
        except requests.exceptions.Timeout as exc:
            raise PromptProConnectionError(
                f"Ollama request timed out after {self.timeout}s.",
                error_code=ErrorCode.CONNECTION_TIMEOUT,
                details=str(exc),
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise PromptProConnectionError(
                f"Ollama request failed: {exc}",
                error_code=ErrorCode.CONNECTION_FAILED,
                details=str(exc),
            ) from exc

    def _parse_chat_stream(self, response: requests.Response) -> str:
        chunks: List[str] = []
        for line in response.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                logger.debug("Skipping non-JSON stream fragment from Ollama.")
                continue
            if "message" in data:
                chunks.append(data["message"].get("content", ""))
        return "".join(chunks)


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI-compatible chat completion endpoints."""

    def __init__(self, config: Config, model: Optional[str] = None):
        super().__init__(config)
        self.base_url = config.openai_base_url.rstrip("/")
        self.api_key = config.openai_api_key
        self._model = model or config.openai_model
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def check_connection(self) -> bool:
        return bool(self.api_key)

    def list_models(self) -> List[str]:
        return ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]

    def chat(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
    ) -> str:
        payload = {
            "model": model or self._model or "gpt-4o-mini",
            "messages": messages,
            "temperature": self.temperature if temperature is None else temperature,
            "stream": False,
        }
        return self._chat_with_retry(payload)

    @retry_on_failure(max_retries=3, delay=1.0)
    def _chat_with_retry(self, payload: dict) -> str:
        try:
            response = self._session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout as exc:
            raise PromptProConnectionError(
                f"OpenAI request timed out after {self.timeout}s.",
                error_code=ErrorCode.CONNECTION_TIMEOUT,
                details=str(exc),
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise PromptProConnectionError(
                f"OpenAI request failed: {exc}",
                error_code=ErrorCode.CONNECTION_FAILED,
                details=str(exc),
            ) from exc


class ClaudeClient(BaseLLMClient):
    """Client for Anthropic's Messages API."""

    def __init__(self, config: Config, model: Optional[str] = None):
        super().__init__(config)
        self.base_url = config.claude_base_url.rstrip("/")
        self.api_key = config.claude_api_key
        self._model = model or config.claude_model
        self._headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    def check_connection(self) -> bool:
        return bool(self.api_key)

    def list_models(self) -> List[str]:
        return [
            "claude-opus-4-1",
            "claude-sonnet-4-0",
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
        system_prompt = ""
        chat_messages = []
        for message in messages:
            if message["role"] == "system":
                system_prompt = message["content"]
            else:
                chat_messages.append(message)

        payload: Dict[str, Any] = {
            "model": model or self._model or "claude-3-5-sonnet-20241022",
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": chat_messages,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        return self._chat_with_retry(payload)

    @retry_on_failure(max_retries=3, delay=1.0)
    def _chat_with_retry(self, payload: dict) -> str:
        try:
            response = self._session.post(
                f"{self.base_url}/v1/messages",
                json=payload,
                headers=self._headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
        except requests.exceptions.Timeout as exc:
            raise PromptProConnectionError(
                f"Claude request timed out after {self.timeout}s.",
                error_code=ErrorCode.CONNECTION_TIMEOUT,
                details=str(exc),
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise PromptProConnectionError(
                f"Claude request failed: {exc}",
                error_code=ErrorCode.CONNECTION_FAILED,
                details=str(exc),
            ) from exc


class CustomClient(BaseLLMClient):
    """Client for arbitrary OpenAI-compatible endpoints."""

    def __init__(self, config: Config, model: Optional[str] = None):
        super().__init__(config)
        self.base_url = config.custom_base_url.rstrip("/")
        self.api_key = config.custom_api_key
        self._model = model or config.custom_model
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def check_connection(self) -> bool:
        return bool(self.base_url)

    def list_models(self) -> List[str]:
        try:
            response = self._session.get(f"{self.base_url}/models", headers=self._headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model["id"] for model in data.get("data", [])][:20]
        except Exception as exc:
            logger.debug("Custom provider model discovery failed: %s", exc)
        return [self._model] if self._model else ["custom-model"]

    def chat(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
    ) -> str:
        payload = {
            "model": model or self._model or "default",
            "messages": messages,
            "temperature": self.temperature if temperature is None else temperature,
            "stream": False,
        }
        return self._chat_with_retry(payload)

    @retry_on_failure(max_retries=3, delay=1.0)
    def _chat_with_retry(self, payload: dict) -> str:
        try:
            response = self._session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout as exc:
            raise PromptProConnectionError(
                f"Custom provider request timed out after {self.timeout}s.",
                error_code=ErrorCode.CONNECTION_TIMEOUT,
                details=str(exc),
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise PromptProConnectionError(
                f"Custom provider request failed: {exc}",
                error_code=ErrorCode.CONNECTION_FAILED,
                details=str(exc),
            ) from exc


class LLMClient:
    """Thin wrapper that picks a provider client from configuration."""

    def __init__(self, config: Optional[Config] = None, model: Optional[str] = None):
        self.config = config or Config.load()
        self._model = model
        self._client = self._create_client()
        self.temperature = self.config.temperature

    def _create_client(self) -> BaseLLMClient:
        provider = self.config.provider
        if provider == "ollama":
            return OllamaClient(self.config, self._model)
        if provider == "openai":
            return OpenAIClient(self.config, self._model)
        if provider == "claude":
            return ClaudeClient(self.config, self._model)
        if provider == "custom":
            return CustomClient(self.config, self._model)
        logger.warning("Unknown provider '%s'; falling back to Ollama.", provider)
        return OllamaClient(self.config, self._model)

    def check_connection(self) -> bool:
        return self._client.check_connection()

    def list_models(self) -> List[str]:
        return self._client.list_models()

    def chat(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
    ) -> str:
        temp = self.temperature if temperature is None else temperature
        return self._client.chat(messages, model, stream, temp)

    def set_model(self, model_name: str) -> bool:
        return self._client.set_model(model_name)

    def get_current_model(self) -> str:
        return self._client.get_current_model()

    def get_available_models(self) -> List[str]:
        return self._client.get_available_models()

    def set_temperature(self, temperature: float) -> None:
        if not 0.0 <= temperature <= 2.0:
            raise ValueError(f"temperature must be between 0.0 and 2.0, got {temperature}")
        self.temperature = temperature
        self._client.temperature = temperature

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "LLMClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
