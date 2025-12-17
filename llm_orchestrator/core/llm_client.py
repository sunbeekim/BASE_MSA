"""
LLM 클라이언트

LLM 타입별 실제 API 호출을 담당합니다.
"""
import httpx
import json
from typing import Dict, Any, Optional, List
from core.logger import get_logger

logger = get_logger(__name__)

# httpx 연결 풀 제한 설정 (호스트당 최대 연결 수 증가)
# 기본값: max_connections=100, max_keepalive_connections=20
# 호스트당 연결 수 제한을 해제하기 위해 충분히 큰 값으로 설정
HTTPX_LIMITS = httpx.Limits(
    max_connections=200,  # 전체 최대 연결 수
    max_keepalive_connections=100  # keepalive 최대 연결 수
)

# 전역 httpx 클라이언트 (모든 LLMClient 인스턴스가 공유)
_global_client: Optional[httpx.AsyncClient] = None


async def get_global_httpx_client() -> httpx.AsyncClient:
    """전역 httpx 클라이언트를 가져오거나 생성 (연결 풀 재사용)"""
    global _global_client
    if _global_client is None:
        _global_client = httpx.AsyncClient(
            timeout=120.0,
            limits=HTTPX_LIMITS
        )
    return _global_client


async def close_global_httpx_client():
    """전역 httpx 클라이언트 종료"""
    global _global_client
    if _global_client is not None:
        await _global_client.aclose()
        _global_client = None


class LLMClient:
    """LLM 클라이언트"""
    
    def __init__(self, model_config: Dict[str, Any], llm_type: str):
        """
        LLM 클라이언트 초기화
        
        Args:
            model_config: 모델 설정
            llm_type: LLM 타입 ("api", "vllm", "ollama")
        """
        self.model_config = model_config
        self.llm_type = llm_type
        self.provider = model_config.get("provider", "")
        self.base_url = model_config.get("base_url", "")
        self.api_key = model_config.get("api_key", "")
        self.max_tokens = model_config.get("max_tokens", 1024)
        self.temperature = model_config.get("temperature", 0.7)
        self.top_p = model_config.get("top_p", 1.0)
    
    async def _get_client(self) -> httpx.AsyncClient:
        """httpx 클라이언트를 가져오거나 생성 (전역 클라이언트 재사용)"""
        return await get_global_httpx_client()
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model_name: Optional[str] = None
    ) -> str:
        """
        LLM 생성 요청
        
        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 유저 프롬프트
            model_name: 모델 이름 (None이면 설정에서 가져옴)
        
        Returns:
            생성된 텍스트
        """
        if self.llm_type == "api":
            return await self._call_api(system_prompt, user_prompt, model_name)
        elif self.llm_type == "vllm":
            return await self._call_vllm(system_prompt, user_prompt, model_name)
        elif self.llm_type == "ollama":
            return await self._call_ollama(system_prompt, user_prompt, model_name)
        else:
            raise ValueError(f"지원하지 않는 LLM 타입입니다: {self.llm_type}")
    
    async def _call_api(self, system_prompt: str, user_prompt: str, model_name: Optional[str]) -> str:
        """API 키가 필요한 LLM 호출 (OpenAI, Anthropic 등)"""
        if model_name is None:
            model_name = self.model_config.get("name", "gpt-4")
        
        if self.provider == "openai":
            return await self._call_openai(system_prompt, user_prompt, model_name)
        elif self.provider == "anthropic":
            return await self._call_anthropic(system_prompt, user_prompt, model_name)
        else:
            raise ValueError(f"지원하지 않는 프로바이더입니다: {self.provider}")
    
    async def _call_openai(self, system_prompt: str, user_prompt: str, model_name: str) -> str:
        """OpenAI API 호출"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        
        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p
        }
        
        client = await self._get_client()
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        # 인코딩 명시적으로 처리
        response.encoding = "utf-8"
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        logger.info(f"vLLM API 응답 수신: 길이={len(content)}, 타입={type(content)}")
        return content
    
    async def _call_anthropic(self, system_prompt: str, user_prompt: str, model_name: str) -> str:
        """Anthropic API 호출"""
        url = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        messages = [{"role": "user", "content": user_prompt}]
        
        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        client = await self._get_client()
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        # 인코딩 명시적으로 처리
        response.encoding = "utf-8"
        result = response.json()
        content = result["content"][0]["text"]
        logger.info(f"Anthropic API 응답 수신: 길이={len(content)}, 타입={type(content)}")
        return content
    
    async def _call_vllm(self, system_prompt: str, user_prompt: str, model_name: Optional[str]) -> str:
        """vLLM API 호출 (OpenAI 호환)"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json"
        }
        
        # vLLM은 API 키가 필요 없을 수 있음
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        
        # 기본 페이로드
        payload = {
            "model": self.model_config.get("model_name", model_name or "default"),
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p
        }
        
        # stop_strings 추가
        stop_strings = self.model_config.get("stop_strings", [])
        if stop_strings:
            payload["stop"] = stop_strings
        
        # streaming 설정
        streaming = self.model_config.get("streaming", False)
        if streaming:
            payload["stream"] = True
        
        # extra_body 추가
        extra_body = self.model_config.get("extra_body", {})
        if extra_body:
            # extra_body의 내용을 payload에 병합
            for key, value in extra_body.items():
                if key not in payload:  # 기존 키와 충돌하지 않도록
                    payload[key] = value
        
        client = await self._get_client()
        if streaming:
            # 스트리밍 응답 처리
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                response.encoding = "utf-8"
                full_content = ""
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # "data: " 제거
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    full_content += delta["content"]
                        except json.JSONDecodeError:
                            continue
                logger.info(f"vLLM 스트리밍 응답 수신: 길이={len(full_content)}")
                return full_content
        else:
            # 일반 응답 처리
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            # 인코딩 명시적으로 처리
            response.encoding = "utf-8"
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            logger.info(f"vLLM 응답 수신: 길이={len(content)}, 타입={type(content)}")
            return content
    
    async def _call_ollama(self, system_prompt: str, user_prompt: str, model_name: Optional[str]) -> str:
        """Ollama API 호출"""
        url = f"{self.base_url}/api/chat"
        headers = {
            "Content-Type": "application/json"
        }
        
        model = model_name or self.model_config.get("model_name", "llama2")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_predict": self.max_tokens
            },
            "stream": False
        }
        
        client = await self._get_client()
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        # 인코딩 명시적으로 처리
        response.encoding = "utf-8"
        result = response.json()
        content = result["message"]["content"]
        logger.info(f"Ollama 응답 수신: 길이={len(content)}, 타입={type(content)}")
        return content

