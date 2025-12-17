"""
질의응답 파이프라인

정적 파이프라인 예시입니다.
시스템 프롬프트와 유저 프롬프트를 구분하여 LLM을 호출합니다.
"""
from typing import Dict, Any, Optional
from core.llm_client import LLMClient
from core.logger import get_logger

logger = get_logger(__name__)


async def execute(
    text: str,
    model_config: Dict[str, Any],
    pipeline_config: Dict[str, Any],
    settings: Dict[str, Any],
    request_data: Optional[Dict[str, Any]] = None
) -> str:
    """
    파이프라인 실행 함수
    
    Args:
        text: 처리할 텍스트 (질문)
        model_config: 모델 설정
        pipeline_config: 파이프라인 설정
        settings: 전체 설정
        request_data: 전체 요청 데이터 (추가 필드 포함)
    
    Returns:
        LLM이 생성한 답변 (문자열)
    """
    try:
        # LLM 타입 가져오기
        llm_type = settings.get("llm", {}).get("type", "api")
        
        # LLM 클라이언트 생성
        llm_client = LLMClient(model_config, llm_type)
        
        # 시스템 프롬프트 (질의응답 작업에 대한 지시사항)
        system_prompt = """당신은 도움이 되는 AI 어시스턴트입니다.
사용자의 질문에 정확하고 상세하게 답변해주세요.
답변은 명확하고 이해하기 쉬워야 합니다."""
        
        # 유저 프롬프트 (실제 질문)
        user_prompt = f"다음 질문에 답변해주세요:\n\n{text}"
        
        # LLM 호출
        logger.info(f"질의응답 파이프라인 실행: 질문 길이={len(text)}")
        result = await llm_client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model_name=model_config.get("name")
        )
        
        logger.info(f"질의응답 파이프라인 완료: 답변 길이={len(result)}")
        
        return result
        
    except Exception as e:
        logger.error(f"질의응답 파이프라인 오류: {str(e)}", exc_info=True)
        raise
