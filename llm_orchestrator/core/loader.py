"""
설정 로더

YAML 설정 파일을 로드하고 관리합니다.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Optional, Dict
from pydantic import BaseModel


def replace_env_variables(data: Any) -> Any:
    """환경 변수 치환"""
    if isinstance(data, dict):
        return {k: replace_env_variables(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace_env_variables(item) for item in data]
    elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
        var_expr = data[2:-1]
        if ":" in var_expr:
            var_name, default_value = var_expr.split(":", 1)
        else:
            var_name = var_expr
            default_value = ""
        return os.getenv(var_name, default_value)
    else:
        return data


def load_yaml_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    YAML 설정 파일 로드
    
    Args:
        config_path: 설정 파일 경로 (None이면 기본 경로 사용)
    
    Returns:
        설정 딕셔너리
    """
    if config_path is None:
        # 기본 경로: config/settings.yml
        config_path = Path(__file__).parent.parent / "config" / "settings.yml"
    
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_file}")
    
    print(f"설정 파일 로드: {config_file}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    # 환경 변수 치환
    config_data = replace_env_variables(config_data)
    
    return config_data

