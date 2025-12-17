"""
상담사/고객 발언 식별 패턴 정의

정규식 패턴을 관리하는 모듈입니다.
"""
from typing import List

# 기본 상담사 패턴
DEFAULT_AGENT_PATTERNS: List[str] = [
    r"\(상담사\)",
    r"\(상담원\)",
    r"\(에이전트\)"
]

# 기본 고객 패턴
DEFAULT_CUSTOMER_PATTERNS: List[str] = [
    r"\(고객\)",
    r"\(고\s+객\)",
    r"\(클라이언트\)"
]


def get_agent_patterns(config_patterns: List[str] = None) -> List[str]:
    """
    상담사 패턴 가져오기
    
    Args:
        config_patterns: 설정에서 가져온 패턴 리스트 (None이면 기본값 사용)
    
    Returns:
        상담사 패턴 리스트
    """
    if config_patterns is not None and isinstance(config_patterns, list) and len(config_patterns) > 0:
        return config_patterns
    return DEFAULT_AGENT_PATTERNS.copy()


def get_customer_patterns(config_patterns: List[str] = None) -> List[str]:
    """
    고객 패턴 가져오기
    
    Args:
        config_patterns: 설정에서 가져온 패턴 리스트 (None이면 기본값 사용)
    
    Returns:
        고객 패턴 리스트
    """
    if config_patterns is not None and isinstance(config_patterns, list) and len(config_patterns) > 0:
        return config_patterns
    return DEFAULT_CUSTOMER_PATTERNS.copy()

