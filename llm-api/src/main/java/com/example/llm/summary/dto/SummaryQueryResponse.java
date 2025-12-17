package com.example.llm.summary.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SummaryQueryResponse {
    
    // Jackson PropertyNamingStrategy에 의해 자동으로 스네이크 케이스로 변환됨
    private String result;
    private String code;
    private String callkey;
    private String originalText;
    private String processedText;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    
    public static SummaryQueryResponse success(String callkey, String originalText, 
                                          String processedText, 
                                          LocalDateTime createdAt, 
                                          LocalDateTime updatedAt) {
        return SummaryQueryResponse.builder()
                .result("1")
                .code("OK")
                .callkey(callkey)
                .originalText(originalText)
                .processedText(processedText)
                .createdAt(createdAt)
                .updatedAt(updatedAt)
                .build();
    }
    
    public static SummaryQueryResponse error(String code, String message) {
        return SummaryQueryResponse.builder()
                .result("0")
                .code(code)
                .originalText(message)
                .build();
    }
}

