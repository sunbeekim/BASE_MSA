# Database Migration (Flyway)

이 디렉토리는 Flyway를 사용한 데이터베이스 마이그레이션 스크립트를 포함합니다.

## 파일 명명 규칙

Flyway 마이그레이션 파일은 다음 형식을 따라야 합니다:

```
V{version}__{description}.sql
```

예시:
- `V1__Create_context_summary_table.sql`
- `V2__Add_index_to_created_at.sql`
- `V3__Add_new_column.sql`

## 규칙

1. **버전 번호**: 순차적으로 증가 (V1, V2, V3, ...)
2. **언더스코어 2개**: 버전과 설명 사이에 `__` (언더스코어 2개)
3. **설명**: 마이그레이션 내용을 간단히 설명
4. **대문자 V**: 버전 번호 앞에 대문자 V 필수

## 마이그레이션 작성 시 주의사항

1. **IF NOT EXISTS 사용**: 테이블/인덱스 생성 시 `IF NOT EXISTS` 사용 권장
2. **롤백 고려**: 필요시 롤백 스크립트도 작성
3. **데이터 마이그레이션**: 기존 데이터가 있는 경우 주의
4. **트랜잭션**: 각 마이그레이션은 자동으로 트랜잭션으로 실행됨

## 실행 순서

애플리케이션 부팅 시 Flyway가 자동으로:
1. `flyway_schema_history` 테이블 생성 (없는 경우)
2. 마이그레이션 파일을 버전 순서대로 실행
3. 실행된 마이그레이션은 기록되어 재실행되지 않음

## 수동 실행

필요시 Maven 플러그인으로 수동 실행 가능:

```bash
mvn flyway:migrate
```

## 상태 확인

```bash
mvn flyway:info
```

