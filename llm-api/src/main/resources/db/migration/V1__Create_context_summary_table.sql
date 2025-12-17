-- V1: Create context_summary table
-- 테이블이 없으면 생성, 있으면 스킵

CREATE TABLE IF NOT EXISTS context_summary (
    id BIGSERIAL PRIMARY KEY,
    callkey VARCHAR(100) NOT NULL UNIQUE,
    original_text TEXT NOT NULL,
    summarized_text TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_callkey UNIQUE (callkey)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_callkey ON context_summary(callkey);

-- 코멘트 추가
COMMENT ON TABLE context_summary IS '컨텍스트 요약 정보를 저장하는 테이블';
COMMENT ON COLUMN context_summary.id IS 'Primary Key, 자동 증가 인덱스';
COMMENT ON COLUMN context_summary.callkey IS '비즈니스 키, 고유 식별자';
COMMENT ON COLUMN context_summary.original_text IS '원본 컨텍스트';
COMMENT ON COLUMN context_summary.summarized_text IS '요약된 컨텍스트';
COMMENT ON COLUMN context_summary.created_at IS '생성 시간';
COMMENT ON COLUMN context_summary.updated_at IS '수정 시간';

