package com.example.llm.summary.service;

import com.example.llm.client.OrchestratorClient;
import com.example.llm.summary.dto.SummaryRequest;
import com.example.llm.summary.dto.SummaryResponse;
import com.example.llm.summary.dto.SummaryQueryResponse;
import com.example.llm.summary.entity.Summary;
import com.example.llm.summary.repository.SummaryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

@Slf4j
@Service
@RequiredArgsConstructor
public class SummaryService {
    
    private final OrchestratorClient orchestratorClient;
    private final SummaryRepository repository;
    
    @Transactional
    public SummaryResponse process(SummaryRequest request) {
        try {
            log.info("LLM 처리 시작: callkey={}", request.getCallkey());
            
            // 1. DB에 원본 텍스트 저장
            Summary summary = repository.findByCallkey(request.getCallkey())
                    .orElseGet(() -> {
                        Summary newSummary = Summary.builder()
                                .callkey(request.getCallkey())
                                .originalText(request.getText())
                                .build();
                        return repository.save(newSummary);
                    });
            
            // 원본 텍스트가 변경된 경우 업데이트
            if (!summary.getOriginalText().equals(request.getText())) {
                summary = Summary.builder()
                        .id(summary.getId())
                        .callkey(summary.getCallkey())
                        .originalText(request.getText())
                        .processedText(summary.getProcessedText())
                        .build();
                summary = repository.save(summary);
            }
            
            // 2. llm_orchestrator로 요청 전달 (다양한 형태의 요청 지원)
            String answer = orchestratorClient.process(request);
            
            // 3. 응답 받아서 DB에 처리 결과 저장
            summary.updateProcessedText(answer);
            repository.save(summary);
            
            // 4. SummaryResponse로 변환하여 반환
            return SummaryResponse.success(answer);
            
        } catch (Exception e) {
            log.error("LLM 처리 중 오류 발생: callkey={}, error={}", 
                    request.getCallkey(), e.getMessage(), e);
            return SummaryResponse.error("E500", "처리 중 오류가 발생했습니다: " + e.getMessage());
        }
    }
    
    @Transactional(readOnly = true)
    public SummaryQueryResponse queryByCallkey(String callkey) {
        try {
            log.info("LLM 처리 결과 조회: callkey={}", callkey);
            
            Optional<Summary> summary = repository.findByCallkey(callkey);
            
            if (summary.isEmpty()) {
                return SummaryQueryResponse.error("E404", 
                        "해당 callkey로 저장된 결과를 찾을 수 없습니다: " + callkey);
            }
            
            Summary process = summary.get();
            return SummaryQueryResponse.success(
                    process.getCallkey(),
                    process.getOriginalText(),
                    process.getProcessedText(),
                    process.getCreatedAt(),
                    process.getUpdatedAt()
            );
            
        } catch (Exception e) {
            log.error("LLM 처리 결과 조회 중 오류 발생: callkey={}, error={}", 
                    callkey, e.getMessage(), e);
            return SummaryQueryResponse.error("E500", "조회 중 오류가 발생했습니다: " + e.getMessage());
        }
    }
}

