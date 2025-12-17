"""
파이프라인 관리자

파이프라인 로드, 등록, 조회를 담당합니다.
"""
import importlib.util
from pathlib import Path
from typing import Optional, Dict, Any
from core.loader import load_yaml_config


class PipelineManager:
    """파이프라인 관리자"""
    
    def __init__(self, config_data: Dict[str, Any]):
        """
        파이프라인 관리자 초기화
        
        Args:
            config_data: 설정 데이터
        """
        self.config_data = config_data
        self.pipeline_config = config_data.get("pipeline", {})
        self.static_config = self.pipeline_config.get("static", {})
        self.pipelines: Dict[str, Any] = {}
        self._load_pipelines()
    
    def _load_pipelines(self):
        """설정에서 파이프라인 로드"""
        if not self.static_config.get("enabled", True):
            return
        
        pipelines = self.static_config.get("pipelines", [])
        for pipeline_config in pipelines:
            pipeline_name = pipeline_config.get("name")
            if pipeline_name:
                self.pipelines[pipeline_name] = pipeline_config
    
    def get_pipeline(self, pipeline_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        파이프라인 조회
        
        Args:
            pipeline_name: 파이프라인 이름 (None이면 기본 파이프라인)
        
        Returns:
            파이프라인 설정 딕셔너리 또는 None
        """
        if pipeline_name is None:
            pipeline_name = self.static_config.get("default_pipeline")
        
        return self.pipelines.get(pipeline_name) if pipeline_name else None
    
    def load_pipeline_module(self, pipeline_name: str):
        """
        파이프라인 모듈 동적 로드
        
        Args:
            pipeline_name: 파이프라인 이름 (파일 경로 자동 추론)
        
        Returns:
            로드된 모듈
        """
        # 프로젝트 루트 기준으로 경로 변환
        project_root = Path(__file__).parent.parent
        
        # 파이프라인 이름에서 파일 경로 자동 추론
        # 예: "summarize_pipeline" -> "pipelines/static/summarize_pipeline.py"
        pipeline_file = f"pipelines/static/{pipeline_name}.py"
        pipeline_path = project_root / pipeline_file
        
        if not pipeline_path.exists():
            raise FileNotFoundError(f"파이프라인 파일을 찾을 수 없습니다: {pipeline_path}")
        
        # 모듈 동적 로드
        spec = importlib.util.spec_from_file_location("pipeline_module", pipeline_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"파이프라인 모듈을 로드할 수 없습니다: {pipeline_path}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return module
    
    async def execute_pipeline(
        self, 
        pipeline_name: str, 
        text: str, 
        model_config: Dict[str, Any],
        request_data: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        파이프라인 실행
        
        Args:
            pipeline_name: 파이프라인 이름
            text: 처리할 텍스트
            model_config: 모델 설정
            request_data: 전체 요청 데이터 (추가 필드 포함)
        
        Returns:
            처리 결과 (str 또는 Dict[str, Any])
        """
        pipeline_config = self.get_pipeline(pipeline_name)
        if pipeline_config is None:
            raise ValueError(f"파이프라인을 찾을 수 없습니다: {pipeline_name}")
        
        # 파이프라인 모듈 로드 (파이프라인 이름에서 파일 경로 자동 추론)
        pipeline_module = self.load_pipeline_module(pipeline_name)
        
        # 파이프라인 실행 함수 호출
        if not hasattr(pipeline_module, 'execute'):
            raise AttributeError(f"파이프라인 모듈에 'execute' 함수가 없습니다: {pipeline_name}")
        
        execute_func = getattr(pipeline_module, 'execute')
        
        # 파이프라인 실행 (async 함수)
        # request_data를 포함하여 전달
        import inspect
        sig = inspect.signature(execute_func)
        params = list(sig.parameters.keys())
        
        # request_data 파라미터가 있으면 전달
        if "request_data" in params:
            return await execute_func(text, model_config, pipeline_config, self.config_data, request_data or {})
        else:
            return await execute_func(text, model_config, pipeline_config, self.config_data)


# 전역 파이프라인 관리자 인스턴스
_pipeline_manager: Optional[PipelineManager] = None


def get_pipeline_manager(config_path: Optional[str] = None) -> PipelineManager:
    """
    파이프라인 관리자 싱글톤 인스턴스 반환
    
    Args:
        config_path: 설정 파일 경로
    
    Returns:
        PipelineManager 인스턴스
    """
    global _pipeline_manager
    if _pipeline_manager is None:
        config_data = load_yaml_config(config_path)
        _pipeline_manager = PipelineManager(config_data)
    return _pipeline_manager

