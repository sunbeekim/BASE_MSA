"""
LLM Orchestrator 메인 애플리케이션

서버 시작 시 설정을 로드하고 FastAPI 애플리케이션을 초기화합니다.
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.loader import load_yaml_config
from core.logger import setup_logger, get_logger
from core.engine_registry import get_engine_registry
from core.pipeline_manager import get_pipeline_manager
from routers import pipeline_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작/종료 이벤트"""
    # 설정 로드 (환경 변수 LLM_CONFIG_PATH로 외부 설정 파일 경로 지정 가능)
    config_path = os.getenv("LLM_CONFIG_PATH")
    config_data = load_yaml_config(config_path)
    
    # 로깅 설정
    logging_config = config_data.get("logging", {})
    setup_logger(
        level=logging_config.get("level", "INFO"),
        format_str=logging_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
        log_folder=logging_config.get("folder", "logs"),
        log_file=logging_config.get("file"),
        max_bytes=logging_config.get("max_bytes", 10485760),
        backup_count=logging_config.get("backup_count", 5)
    )
    
    # 엔진 레지스트리 및 파이프라인 관리자 초기화
    engine_registry = get_engine_registry()
    pipeline_manager = get_pipeline_manager()
    
    # 서버 시작 로그
    server_config = config_data.get("server", {})
    logger.info("=" * 50)
    logger.info("LLM Orchestrator 서버 시작")
    logger.info(f"서버 주소: http://{server_config.get('host', '0.0.0.0')}:{server_config.get('port', 8000)}")
    logger.info(f"LLM 타입: {engine_registry.get_llm_type()}")
    logger.info(f"파이프라인 모드: {pipeline_manager.pipeline_config.get('mode', 'static')}")
    logger.info(f"정적 파이프라인: {len(pipeline_manager.pipelines)}개")
    logger.info("=" * 50)
    
    yield
    
    # 서버 종료 로그
    logger.info("LLM Orchestrator 서버 종료")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title="LLM Orchestrator",
    description="LLM 파이프라인 실행 서버",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(pipeline_router.router, prefix="/api/llm", tags=["LLM"])


if __name__ == "__main__":
    import uvicorn
    # 환경 변수로 외부 설정 파일 경로 지정 가능
    config_path = os.getenv("LLM_CONFIG_PATH")
    config_data = load_yaml_config(config_path)
    server_config = config_data.get("server", {})
    logging_config = config_data.get("logging", {})
    
    uvicorn.run(
        "main:app",
        host=server_config.get("host", "0.0.0.0"),
        port=server_config.get("port", 8000),
        reload=server_config.get("reload", False),
        log_level=logging_config.get("level", "INFO").lower(),
        workers=2
    )

