"""
베이스 파이프라인

모든 파이프라인이 상속받을 기본 파이프라인 클래스입니다.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BasePipeline(ABC):
    """베이스 파이프라인 클래스"""
    
    def __init__(self, name: str, description: Optional[str] = None):
        """
        베이스 파이프라인 초기화
        
        Args:
            name: 파이프라인 이름
            description: 파이프라인 설명
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(
        self,
        text: str,
        model_config: Dict[str, Any],
        pipeline_config: Dict[str, Any],
        settings: Dict[str, Any]
    ) -> str:
        """
        파이프라인 실행
        
        Args:
            text: 처리할 텍스트
            model_config: 모델 설정
            pipeline_config: 파이프라인 설정
            settings: 전체 설정
        
        Returns:
            처리 결과 텍스트
        """
        pass
    
    def preprocess(self, text: str) -> str:
        """
        전처리 (기본 구현)
        
        Args:
            text: 원본 텍스트
        
        Returns:
            전처리된 텍스트
        """
        return text.strip()
    
    def postprocess(self, text: str) -> str:
        """
        후처리 (기본 구현)
        
        Args:
            text: 처리된 텍스트
        
        Returns:
            후처리된 텍스트
        """
        return text.strip()

