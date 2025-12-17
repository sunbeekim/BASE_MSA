"""
로거 설정

로깅 구조 및 실행 상태 관리를 담당합니다.
"""
import logging
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


def setup_logger(
    level: str = "INFO",
    format_str: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_folder: str = "logs",
    log_file: Optional[str] = None,
    max_bytes: int = 10485760,
    backup_count: int = 5
):
    """
    로거 설정
    
    Args:
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
        format_str: 로그 포맷
        log_folder: 로그 폴더 경로
        log_file: 로그 파일 경로
        max_bytes: 최대 파일 크기
        backup_count: 백업 파일 개수
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # 로그 폴더 생성
    log_folder_path = Path(log_folder)
    log_folder_path.mkdir(parents=True, exist_ok=True)
    
    # 파일 핸들러 설정
    if log_file:
        log_file_path = Path(log_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(format_str))
        logging.getLogger().addHandler(file_handler)
    
    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(format_str))
    logging.getLogger().addHandler(console_handler)
    
    logging.getLogger().setLevel(log_level)
    logging.info("로거 설정 완료")


def get_logger(name: str) -> logging.Logger:
    """
    로거 인스턴스 반환
    
    Args:
        name: 로거 이름
    
    Returns:
        로거 인스턴스
    """
    return logging.getLogger(name)

