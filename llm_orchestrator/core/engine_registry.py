"""
엔진 레지스트리

LLM 엔진 타입별 설정을 관리하고 조회합니다.
"""
from typing import Optional, Dict, Any
from core.loader import load_yaml_config


class EngineRegistry:
    """엔진 레지스트리"""
    
    def __init__(self, config_data: Dict[str, Any]):
        """
        엔진 레지스트리 초기화
        
        Args:
            config_data: 설정 데이터
        """
        self.config_data = config_data
        self.llm_config = config_data.get("llm", {})
    
    def get_llm_type(self) -> str:
        """
        LLM 타입 반환
        
        Returns:
            LLM 타입 ("api", "vllm", "ollama")
        """
        return self.llm_config.get("type", "api")
    
    def get_model_config(self, model_spec: str) -> Optional[Dict[str, Any]]:
        """
        모델 설정 조회
        
        Args:
            model_spec: 모델 지정 형식 ("{type}:{model_name}")
                       예: "vllm:base_clova", "api:gpt-4"
        
        Returns:
            모델 설정 딕셔너리 또는 None
        """
        # 모델 지정 형식 파싱: "{type}:{model_name}"
        if ":" not in model_spec:
            raise ValueError(f"모델 지정 형식이 올바르지 않습니다: {model_spec}. 형식: '{{type}}:{{model_name}}' (예: 'vllm:base_clova')")
        
        llm_type, model_name = model_spec.split(":", 1)
        
        # API 키가 필요한 LLM
        if llm_type == "api":
            models = self.llm_config.get("api", {}).get("models", [])
            for model in models:
                if model.get("name") == model_name:
                    return model
            return None
        
        # vLLM (models 배열에서 찾기)
        elif llm_type == "vllm":
            vllm_config = self.llm_config.get("vllm", {})
            models = vllm_config.get("models", [])
            
            # models 배열에서 찾기
            for model in models:
                if model.get("name") == model_name:
                    # vLLM 모델 설정 구성
                    return {
                        "name": model.get("name"),
                        "model_name": model.get("model_name"),
                        "provider": "vllm",
                        "api_key": "",
                        "base_url": model.get("base_url", "http://localhost:8001"),
                        "max_tokens": model.get("max_tokens", 2000),
                        "temperature": model.get("temperature", 0.7),
                        "top_p": model.get("top_p", 1.0),
                        "streaming": model.get("streaming", False),
                        "stop_strings": model.get("stop_strings", []),
                        "extra_body": model.get("extra_body", {})
                    }
            return None
        
        # Ollama
        elif llm_type == "ollama":
            ollama_config = self.llm_config.get("ollama", {})
            actual_model_name = ollama_config.get("model_name")
            if not actual_model_name:
                raise ValueError("Ollama 설정에 model_name이 지정되지 않았습니다.")
            return {
                "name": actual_model_name,
                "model_name": actual_model_name,
                "provider": "ollama",
                "api_key": "",
                "base_url": ollama_config.get("base_url", "http://localhost:11434"),
                "max_tokens": ollama_config.get("max_tokens", 2000),
                "temperature": ollama_config.get("temperature", 0.7),
                "top_p": ollama_config.get("top_p", 1.0)
            }
        
        return None


# 전역 엔진 레지스트리 인스턴스
_engine_registry: Optional[EngineRegistry] = None


def get_engine_registry(config_path: Optional[str] = None) -> EngineRegistry:
    """
    엔진 레지스트리 싱글톤 인스턴스 반환
    
    Args:
        config_path: 설정 파일 경로
    
    Returns:
        EngineRegistry 인스턴스
    """
    global _engine_registry
    if _engine_registry is None:
        config_data = load_yaml_config(config_path)
        _engine_registry = EngineRegistry(config_data)
    return _engine_registry

