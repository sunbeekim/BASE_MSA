package com.example.llm;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * LLM 로직 호출용 공통 서비스
 * 
 * LLM Orchestrator와 연결하여 다양한 LLM 작업을 처리하는 공통 서비스
 * (요약, 번역, 분석 등 다양한 LLM 작업 지원)
 * 
 * 주요 기능:
 * - LLM Orchestrator로 요청 전달
 * - 텍스트 처리 및 결과 저장
 * - 처리 결과 조회
 * 
 * Gateway에서 /api/llm/** 경로로 라우팅됨
 */
@SpringBootApplication(exclude = {
	org.springframework.boot.autoconfigure.http.client.HttpClientAutoConfiguration.class,
	org.springframework.boot.autoconfigure.web.client.RestClientAutoConfiguration.class
})
public class LLMServiceApplication {

	public static void main(String[] args) {
		SpringApplication.run(LLMServiceApplication.class, args);
	}

}

