"""
요약 파이프라인

정적 파이프라인 예시입니다.
시스템 프롬프트와 유저 프롬프트를 구분하여 LLM을 호출합니다.
"""
import re
from typing import Dict, Any, Optional, List
from core.llm_client import LLMClient
from core.logger import get_logger
from pipelines.static.summary_util.split_text import extract_agent_utterances, extract_customer_utterances
from pipelines.static.summary_util.speaker_patterns import get_agent_patterns, get_customer_patterns
from pipelines.static.summary_util.stt_conversion import (
    convert_bracketed_content,
)

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
        text: 처리할 텍스트
        model_config: 모델 설정
        pipeline_config: 파이프라인 설정
        settings: 전체 설정
        request_data: 전체 요청 데이터 (추가 필드 포함)
    
    Returns:
        LLM이 생성한 답변 (문자열)
    """
    try:
        # LLM 타입 가져오기 (settings에서 직접 가져오기)
        llm_type = settings.get("llm", {}).get("type", "api")
        logger.info(f"요약 파이프라인 시작: LLM 타입={llm_type}, 모델={model_config.get('name')}")
        
        # 입력값 로깅
        logger.info("=" * 80)
        logger.info("요약 파이프라인 입력값")
        logger.info("=" * 80)
        logger.info(f"입력 텍스트 길이: {len(text)} 문자")
        logger.info(f"입력 텍스트 내용:\n{text}")
        logger.info("=" * 80)
        
        # LLM 클라이언트 생성
        llm_client = LLMClient(model_config, llm_type)
        
        # 분리 요약 모드 확인
        separate_config = pipeline_config.get("separate_speaker_summary")
        is_separate_mode = False
        
        if separate_config is not None:
            enabled = separate_config.get("enabled")
            if enabled is True:
                is_separate_mode = True
                logger.info("상담원/고객 발언 분리 요약 모드 활성화")
            elif enabled is False:
                is_separate_mode = False
                logger.info("상담원/고객 발언 분리 요약 모드 비활성화")
            else:
                is_separate_mode = False
                logger.warning(f"separate_speaker_summary.enabled 값이 올바르지 않습니다: {enabled}, 기본 모드로 진행")
        else:
            is_separate_mode = False
            logger.info("separate_speaker_summary 설정이 없습니다. 기본 모드로 진행")
        
        # 분리 요약 모드 처리
        if is_separate_mode:
            logger.info("=" * 80)
            logger.info("상담원/고객 발언 분리 요약 모드 시작")
            logger.info("=" * 80)
            
            # 상담사 발언 요약용 시스템 프롬프트 가져오기
            agent_system_prompt = separate_config.get("agent_system_prompt")
            if agent_system_prompt is None:
                error_msg = "agent_system_prompt 설정이 없습니다."
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            if not isinstance(agent_system_prompt, str):
                error_msg = f"agent_system_prompt 타입이 올바르지 않습니다. 타입={type(agent_system_prompt)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            if not agent_system_prompt.strip():
                error_msg = "agent_system_prompt가 비어있습니다."
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.info(f"상담사 발언 요약용 시스템 프롬프트 사용: 길이={len(agent_system_prompt)}")
            
            # 고객 발언 요약용 시스템 프롬프트 가져오기
            customer_system_prompt = separate_config.get("customer_system_prompt")
            if customer_system_prompt is None:
                error_msg = "customer_system_prompt 설정이 없습니다."
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            if not isinstance(customer_system_prompt, str):
                error_msg = f"customer_system_prompt 타입이 올바르지 않습니다. 타입={type(customer_system_prompt)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            if not customer_system_prompt.strip():
                error_msg = "customer_system_prompt가 비어있습니다."
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.info(f"고객 발언 요약용 시스템 프롬프트 사용: 길이={len(customer_system_prompt)}")
            
            # 발언 패턴 가져오기
            speaker_patterns = separate_config.get("speaker_patterns")
            if speaker_patterns is None:
                error_msg = "speaker_patterns 설정이 없습니다."
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 패턴 가져오기 (설정에서 가져오거나 기본값 사용)
            agent_patterns_config = speaker_patterns.get("agent")
            customer_patterns_config = speaker_patterns.get("customer")
            
            # 패턴 검증 및 기본값 적용
            agent_patterns = get_agent_patterns(agent_patterns_config)
            customer_patterns = get_customer_patterns(customer_patterns_config)
            
            logger.info(f"상담사 패턴 수: {len(agent_patterns)}, 고객 패턴 수: {len(customer_patterns)}")
            
            # 원본 텍스트 사용 여부 확인
            use_original_text = separate_config.get("use_original_text", False)
            if not isinstance(use_original_text, bool):
                use_original_text = False
                logger.warning(f"use_original_text 값이 올바르지 않습니다: {use_original_text}, 기본값(false) 사용")
            
            if use_original_text:
                logger.info("원본 텍스트 모드: 발언 분리 없이 원본 텍스트 그대로 사용")
            else:
                logger.info("발언 분리 모드: 상담사/고객 발언을 분리하여 사용")
            
            # 대괄호 안 내용 변환 (이미 []로 감싸진 것만 변환)
            logger.info("원본 텍스트 대괄호 변환 시작")
            logger.debug(f"원본 텍스트 (처음 300자): {text[:300]}")
            converted_text = convert_bracketed_content(text)
            logger.info("원본 텍스트 대괄호 변환 완료")
            logger.debug(f"대괄호 변환 후 텍스트 (처음 300자): {converted_text[:300]}")
            
            # 발언 분리 또는 원본 텍스트 사용
            if use_original_text:
                # 원본 텍스트 그대로 사용
                agent_text = converted_text
                customer_text = converted_text
                logger.info(f"원본 텍스트 사용: 길이={len(converted_text)}")
            else:
                # 발언 분리 (변환된 텍스트 사용)
                logger.info("상담사 발언 추출 시작")
                agent_text = extract_agent_utterances(converted_text, agent_patterns, customer_patterns)
                logger.info(f"상담사 발언 추출 완료: 길이={len(agent_text)}")
                
                logger.info("고객 발언 추출 시작")
                customer_text = extract_customer_utterances(converted_text, agent_patterns, customer_patterns)
                logger.info(f"고객 발언 추출 완료: 길이={len(customer_text)}")
            
            # 구분자 가져오기
            separator = separate_config.get("separator")
            if separator is None:
                separator = "---"
                logger.info("구분자가 설정되지 않아 기본값 사용: ---")
            else:
                if not isinstance(separator, str):
                    logger.warning(f"구분자 타입이 올바르지 않습니다. 타입={type(separator)}, 기본값 사용")
                    separator = "---"
                else:
                    logger.info(f"설정된 구분자 사용: {separator[:20]}")
            
            # 상담사 발언 요약
            logger.info("상담사 발언 요약 LLM 호출 시작")
            logger.info(f"상담사 발언 텍스트 길이: {len(agent_text) if agent_text else 0}")
            logger.debug(f"상담사 발언 텍스트 (처음 200자): {agent_text[:200] if agent_text else '(없음)'}")
            
            if not agent_text or not agent_text.strip():
                logger.warning("상담사 발언이 비어있습니다. 빈 요약 반환")
                agent_summary = ""
            else:
                user_prompt_agent = f"다음 상담사 발언을 요약해주세요:\n\n{agent_text}"
                
                try:
                    agent_summary = await llm_client.generate(
                        system_prompt=agent_system_prompt,
                        user_prompt=user_prompt_agent,
                        model_name=model_config.get("name")
                    )
                except Exception as e:
                    error_msg = f"상담사 발언 요약 LLM 호출 중 예외 발생: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    raise
                
                if agent_summary is None:
                    error_msg = "상담사 발언 요약 결과가 None입니다."
                    logger.error(error_msg)
                    agent_summary = ""
                elif not isinstance(agent_summary, str):
                    error_msg = f"상담사 발언 요약 결과 타입이 올바르지 않습니다. 타입={type(agent_summary)}"
                    logger.error(error_msg)
                    agent_summary = ""
                elif not agent_summary.strip():
                    logger.warning("상담사 발언 요약 결과가 빈 문자열입니다.")
                    agent_summary = ""
                else:
                    logger.info(f"상담사 발언 요약 완료: 길이={len(agent_summary)}")
                    logger.debug(f"상담사 발언 요약 내용:\n{agent_summary}")
            
            # 고객 발언 요약
            logger.info("고객 발언 요약 LLM 호출 시작")
            logger.info(f"고객 발언 텍스트 길이: {len(customer_text) if customer_text else 0}")
            logger.debug(f"고객 발언 텍스트 (처음 200자): {customer_text[:200] if customer_text else '(없음)'}")
            
            if not customer_text or not customer_text.strip():
                logger.warning("고객 발언이 비어있습니다. 빈 요약 반환")
                customer_summary = ""
            else:
                user_prompt_customer = f"다음 고객 발언을 요약해주세요:\n\n{customer_text}"
                
                try:
                    customer_summary = await llm_client.generate(
                        system_prompt=customer_system_prompt,
                        user_prompt=user_prompt_customer,
                        model_name=model_config.get("name")
                    )
                except Exception as e:
                    error_msg = f"고객 발언 요약 LLM 호출 중 예외 발생: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    raise
                
                if customer_summary is None:
                    error_msg = "고객 발언 요약 결과가 None입니다."
                    logger.error(error_msg)
                    customer_summary = ""
                elif not isinstance(customer_summary, str):
                    error_msg = f"고객 발언 요약 결과 타입이 올바르지 않습니다. 타입={type(customer_summary)}"
                    logger.error(error_msg)
                    customer_summary = ""
                elif not customer_summary.strip():
                    logger.warning("고객 발언 요약 결과가 빈 문자열입니다.")
                    customer_summary = ""
                else:
                    logger.info(f"고객 발언 요약 완료: 길이={len(customer_summary)}")
                    logger.debug(f"고객 발언 요약 내용:\n{customer_summary}")
            
            # 결과 병합
            # 빈 요약이 있는 경우 처리
            if not agent_summary or not agent_summary.strip():
                agent_summary = "■ [상담사] 상담사 발언 요약\n(요약 내용 없음)"
            if not customer_summary or not customer_summary.strip():
                customer_summary = "■ [고객] 고객 발언 요약\n(요약 내용 없음)"
            
            result = f"{agent_summary}\n{separator}\n{customer_summary}"
            
            # 대괄호, 중괄호, 큰따옴표 제거 (안의 텍스트는 유지)
            # [텍스트] → 텍스트, {텍스트} → 텍스트, "텍스트" → 텍스트
            result = re.sub(r'\[([^\]]+?)\]', r'\1', result)  # 대괄호 제거
            result = re.sub(r'\{([^\}]+?)\}', r'\1', result)  # 중괄호 제거
            result = re.sub(r'"([^"]+?)"', r'\1', result)  # 큰따옴표 제거
            
            logger.info("=" * 80)
            logger.info("상담원/고객 발언 분리 요약 모드 완료")
            logger.info("=" * 80)
            
        else:
            # 기존 단일 요약 모드 (원본 전체 사용)
            logger.info("=" * 80)
            logger.info("기존 단일 요약 모드 시작 (원본 전체 사용)")
            logger.info("=" * 80)
            
            # 대괄호 안 내용 변환 (이미 []로 감싸진 것만 변환)
            logger.info("원본 텍스트 대괄호 변환 시작")
            converted_text = convert_bracketed_content(text)
            logger.info("원본 텍스트 대괄호 변환 완료")
            
            # 구분자 가져오기 (설정에서 가져오거나 기본값 사용)
            separator = "---"
            if separate_config is not None:
                separator_from_config = separate_config.get("separator")
                if separator_from_config is not None and isinstance(separator_from_config, str):
                    separator = separator_from_config
                    logger.info(f"설정에서 구분자 사용: {separator[:20]}")
                else:
                    logger.info("설정에 구분자가 없어 기본값 사용: ---")
            else:
                logger.info("separate_speaker_summary 설정이 없어 기본 구분자 사용: ---")
            
            # 시스템 프롬프트 (요청에서 받거나 기본값 사용)
            default_system_prompt = f"""당신은 관세청 상담내용 요약 전문가입니다. 주어진 텍스트를 요약하세요.

            규칙:
            1. 텍스트에 명시된 사실만 요약 (추론, 해석, 의도 추측 절대 금지)
            2. 텍스트에 없는 정보는 절대 추가하지 않음
            3. 질문과 답변을 정확히 구분하고, 상대방에게 알려준 정보는 반드시 포함 (통관번호, 운송장번호, 전화번호, 주소, 금액, 세율, 날짜 등)
            4. 한글 숫자는 모두 아라비아 숫자로 변환하여 출력
              - 대괄호 안: [공삼이 칠사오 구칠삼하나] → [032-745-9731]
              - 대괄호 밖: 십이월 이십일 → 12월 21일, 오구오팔 → 5958
              - 숫자+단위 조합은 하나의 토큰으로 인식하여 전체를 변환: 사만 칠천 엔 → 47000엔 (40000+7000), 십이만 삼천 원 → 123000원 (120000+3000)
              - 이미 숫자/영문인 경우: [EH 0405 14658 US], [8826 5399 291] → 그대로 유지
            5. 2~4문장으로 간결하게 작성

            출력 형식:
            ■ [고객] 고객 발언 요약
            고객은 ??에 대해 문의하고 ??에 대해 안내받았습니다...
            {separator}
            
            ■ [고객] 고객 발언 요약
            고객은 ??에 대해 문의하고 ??에 대해 안내받았습니다...
            """
            
            # 요청 데이터에서 시스템 프롬프트 가져오기
            system_prompt = None
            if request_data is not None:
                system_prompt = request_data.get("system_prompt")
            
            if system_prompt is None or not system_prompt.strip():
                system_prompt = default_system_prompt
                logger.info("기본 시스템 프롬프트 사용")
            else:
                logger.info(f"사용자 지정 시스템 프롬프트 사용: 길이={len(system_prompt)}")
            
            # 유저 프롬프트 (실제 요약할 상담 내용, 변환된 텍스트 사용)
            user_prompt = f"다음 상담 내용을 요약해주세요:\n\n{converted_text}"
            
            # LLM 호출
            logger.info(f"LLM 호출 시작: 모델={model_config.get('name')}")
            try:
                result = await llm_client.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model_name=model_config.get("name")
                )
            except Exception as e:
                error_msg = f"LLM 호출 중 예외 발생: {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise
            
            if result is None:
                error_msg = "LLM 응답이 None입니다."
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            if not isinstance(result, str):
                error_msg = f"LLM 응답 타입이 올바르지 않습니다. 타입={type(result)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 대괄호, 중괄호, 큰따옴표 제거 (안의 텍스트는 유지)
            # [텍스트] → 텍스트, {텍스트} → 텍스트, "텍스트" → 텍스트
            result = re.sub(r'\[([^\]]+?)\]', r'\1', result)  # 대괄호 제거
            result = re.sub(r'\{([^\}]+?)\}', r'\1', result)  # 중괄호 제거
            result = re.sub(r'"([^"]+?)"', r'\1', result)  # 큰따옴표 제거
        
        # 출력값 로깅
        logger.info("=" * 80)
        logger.info("요약 파이프라인 출력값")
        logger.info("=" * 80)
        logger.info(f"출력 텍스트 길이: {len(result)} 문자")
        logger.info(f"출력 텍스트 내용:\n{result}")
        logger.info("=" * 80)
        logger.info(f"요약 파이프라인 완료: 입력 길이={len(text)}, 출력 길이={len(result)}")
        
        return result
        
    except Exception as e:
        logger.error(f"요약 파이프라인 오류: {str(e)}", exc_info=True)
        raise
