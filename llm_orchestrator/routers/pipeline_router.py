"""
파이프라인 라우터

FastAPI 라우터 및 파이프라인 엔드포인트를 정의합니다.
다양한 형태의 요청을 받아 LLM 답변(문자열)을 반환합니다.
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import PlainTextResponse
from typing import Dict, Any

from core.engine_registry import get_engine_registry
from core.pipeline_manager import get_pipeline_manager
from core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/process", response_class=PlainTextResponse)
async def process(request: Request) -> str:
    """
    LLM 처리 요청
    
    다양한 형태의 요청을 받아 LLM 답변(문자열)을 반환합니다.
    응답 필드 구성은 Spring Boot 서버에서 처리합니다.
    
    PlainTextResponse를 사용하여 JSON 직렬화 없이 순수 문자열로 반환합니다.
    """
    try:
        # 요청 본문을 Dict로 파싱
        body = await request.json()
        
        # 필드 추출 (검증은 Spring Boot 서버에서 이미 수행)
        text = body.get("text", "")
        pipeline_name = body.get("pipeline_name")
        
        engine_registry = get_engine_registry()
        pipeline_manager = get_pipeline_manager()
        
        # 파이프라인 모드 확인
        pipeline_mode = pipeline_manager.pipeline_config.get("mode", "static")
        
        if pipeline_mode == "static":
            # 정적 파이프라인 처리
            static_config = pipeline_manager.pipeline_config.get("static", {})
            
            if not static_config.get("enabled", True):
                raise HTTPException(status_code=400, detail="정적 파이프라인이 비활성화되어 있습니다.")
            
            # 파이프라인 이름이 지정되지 않으면 기본 파이프라인 사용
            if pipeline_name is None:
                pipeline_name = static_config.get("default_pipeline")
            
            # 파이프라인 조회
            pipeline_config = pipeline_manager.get_pipeline(pipeline_name)
            if pipeline_config is None:
                raise HTTPException(status_code=404, detail=f"파이프라인을 찾을 수 없습니다: {pipeline_name}")
            
            # 모델 설정 조회
            # 파이프라인 설정의 model 필드 사용 ("{type}:{model_name}" 형식 필수)
            model_spec = pipeline_config.get("model")
            if model_spec is None:
                raise HTTPException(status_code=400, detail=f"파이프라인 '{pipeline_name}'에 모델이 지정되지 않았습니다. 형식: '{{type}}:{{model_name}}' (예: 'vllm:base_clova')")
            
            logger.info(f"파이프라인 라우터: 파이프라인={pipeline_name}, 모델 지정={model_spec}")
            
            try:
                model_config = engine_registry.get_model_config(model_spec)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            
            if model_config is None:
                raise HTTPException(status_code=404, detail=f"모델을 찾을 수 없습니다: 모델 지정={model_spec}")
            logger.info(f"파이프라인 라우터: 모델 설정={model_config.get('name')}, 타입={model_config.get('provider')}")
            
            # 파이프라인 실행 (전체 요청 본문과 설정 전달)
            result = await pipeline_manager.execute_pipeline(
                pipeline_name=pipeline_name,
                text=text,
                model_config=model_config,
                request_data=body  # 전체 요청 데이터 전달
            )
            
        elif pipeline_mode == "dynamic":
            # 동적 파이프라인 처리 (미구현)
            dynamic_config = pipeline_manager.pipeline_config.get("dynamic", {})
            
            if not dynamic_config.get("enabled", False):
                raise HTTPException(status_code=400, detail="동적 파이프라인이 비활성화되어 있습니다.")
            
            raise HTTPException(status_code=501, detail="동적 파이프라인은 아직 구현되지 않았습니다.")
        
        else:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 파이프라인 모드입니다: {pipeline_mode}")
        
        # LLM 답변(문자열) 반환
        # PlainTextResponse를 사용하여 JSON 직렬화 없이 순수 문자열로 반환
        result_str = str(result) if result is not None else ""
        logger.info(f"파이프라인 라우터: 응답 반환 - 길이={len(result_str)}")
        return result_str
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"처리 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"처리 중 오류가 발생했습니다: {str(e)}")


@router.get("/health")
async def health_check():
    """헬스 체크"""
    pipeline_manager = get_pipeline_manager()
    return {
        "status": "healthy",
        "pipeline_mode": pipeline_manager.pipeline_config.get("mode", "static"),
        "static_pipelines": len(pipeline_manager.pipelines)
    }
