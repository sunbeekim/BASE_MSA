"""
상담사/고객 발언 분리 모듈

원본 텍스트에서 상담사와 고객 발언을 분리하는 기능을 제공합니다.
"""
import re
from typing import List
from core.logger import get_logger
from .speaker_patterns import get_agent_patterns, get_customer_patterns

logger = get_logger(__name__)


def extract_agent_utterances(
    text: str, 
    agent_patterns: List[str] = None, 
    customer_patterns: List[str] = None
) -> str:
    """
    상담사 발언 추출
    
    Args:
        text: 전체 상담 내용
        agent_patterns: 상담사 식별 정규식 패턴 리스트 (None이면 기본값 사용)
        customer_patterns: 고객 식별 정규식 패턴 리스트 (None이면 기본값 사용)
    
    Returns:
        상담사 발언만 추출한 텍스트
    """
    logger.debug(f"상담사 발언 추출 시작: 패턴 수={len(agent_patterns) if agent_patterns else '기본값'}")
    
    if not text or not text.strip():
        logger.warning("입력 텍스트가 비어있습니다.")
        return ""
    
    # 패턴 가져오기
    agent_patterns = get_agent_patterns(agent_patterns)
    customer_patterns = get_customer_patterns(customer_patterns)
    
    if not agent_patterns:
        logger.warning("상담사 패턴이 설정되지 않았습니다.")
        return ""
    
    lines = text.split('\n')
    agent_lines = []
    current_speaker = None
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        
        # 상담사 패턴 확인
        agent_matched = False
        for pattern in agent_patterns:
            try:
                if re.search(pattern, line):
                    current_speaker = 'agent'
                    # 발언 내용 추출 (패턴 이후 부분)
                    content = re.sub(pattern, '', line).strip()
                    if content.startswith(':'):
                        content = content[1:].strip()
                    if content:
                        agent_lines.append(content)
                        logger.debug(f"라인 {line_num}: 상담사 발언 매칭 - 패턴={pattern}, 내용={content[:50]}")
                    agent_matched = True
                    break
            except re.error as e:
                logger.error(f"정규식 패턴 오류 (상담사): {pattern}, 오류={str(e)}")
                continue
        
        # 고객 패턴 확인 (발언 전환)
        if not agent_matched:
            customer_matched = False
            for pattern in customer_patterns:
                try:
                    if re.search(pattern, line):
                        current_speaker = 'customer'
                        customer_matched = True
                        logger.debug(f"라인 {line_num}: 고객 발언으로 전환 - 패턴={pattern}")
                        break
                except re.error as e:
                    logger.error(f"정규식 패턴 오류 (고객): {pattern}, 오류={str(e)}")
                    continue
        
        # 현재 발언이 상담사이면 내용 추가
        if not agent_matched and not customer_matched:
            if current_speaker == 'agent':
                agent_lines.append(line)
                logger.debug(f"라인 {line_num}: 상담사 발언 연속 - 내용={line[:50]}")
    
    result = '\n'.join(agent_lines)
    logger.info(f"상담사 발언 추출 완료: 추출된 라인 수={len(agent_lines)}, 총 길이={len(result)}")
    logger.debug(f"상담사 발언 내용:\n{result}")
    
    return result


def extract_customer_utterances(
    text: str, 
    agent_patterns: List[str] = None, 
    customer_patterns: List[str] = None
) -> str:
    """
    고객 발언 추출
    
    Args:
        text: 전체 상담 내용
        agent_patterns: 상담사 식별 정규식 패턴 리스트 (None이면 기본값 사용)
        customer_patterns: 고객 식별 정규식 패턴 리스트 (None이면 기본값 사용)
    
    Returns:
        고객 발언만 추출한 텍스트
    """
    logger.debug(f"고객 발언 추출 시작: 패턴 수={len(customer_patterns) if customer_patterns else '기본값'}")
    
    if not text or not text.strip():
        logger.warning("입력 텍스트가 비어있습니다.")
        return ""
    
    # 패턴 가져오기
    agent_patterns = get_agent_patterns(agent_patterns)
    customer_patterns = get_customer_patterns(customer_patterns)
    
    if not customer_patterns:
        logger.warning("고객 패턴이 설정되지 않았습니다.")
        return ""
    
    lines = text.split('\n')
    customer_lines = []
    current_speaker = None
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        
        # 고객 패턴 확인
        customer_matched = False
        for pattern in customer_patterns:
            try:
                if re.search(pattern, line):
                    current_speaker = 'customer'
                    # 발언 내용 추출 (패턴 이후 부분)
                    content = re.sub(pattern, '', line).strip()
                    if content.startswith(':'):
                        content = content[1:].strip()
                    if content:
                        customer_lines.append(content)
                        logger.debug(f"라인 {line_num}: 고객 발언 매칭 - 패턴={pattern}, 내용={content[:50]}")
                    customer_matched = True
                    break
            except re.error as e:
                logger.error(f"정규식 패턴 오류 (고객): {pattern}, 오류={str(e)}")
                continue
        
        # 상담사 패턴 확인 (발언 전환)
        if not customer_matched:
            agent_matched = False
            for pattern in agent_patterns:
                try:
                    if re.search(pattern, line):
                        current_speaker = 'agent'
                        agent_matched = True
                        logger.debug(f"라인 {line_num}: 상담사 발언으로 전환 - 패턴={pattern}")
                        break
                except re.error as e:
                    logger.error(f"정규식 패턴 오류 (상담사): {pattern}, 오류={str(e)}")
                    continue
        
        # 현재 발언이 고객이면 내용 추가
        if not customer_matched and not agent_matched:
            if current_speaker == 'customer':
                customer_lines.append(line)
                logger.debug(f"라인 {line_num}: 고객 발언 연속 - 내용={line[:50]}")
    
    result = '\n'.join(customer_lines)
    logger.info(f"고객 발언 추출 완료: 추출된 라인 수={len(customer_lines)}, 총 길이={len(result)}")
    logger.debug(f"고객 발언 내용:\n{result}")
    
    return result

