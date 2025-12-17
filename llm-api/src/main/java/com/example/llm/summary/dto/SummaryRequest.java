package com.example.llm.summary.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@AllArgsConstructor
public class SummaryRequest {
    
    @NotBlank(message = "callkey는 필수입니다")
    private String callkey;
    
    @NotBlank(message = "text는 필수입니다")
    private String text;
    
    // 시스템 프롬프트 (선택적, 없으면 파이썬 서버의 기본 프롬프트 사용)
    private String systemPrompt;
}

