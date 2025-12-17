package com.example.llm.summary.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SummaryResponse {
    
    // Jackson PropertyNamingStrategy에 의해 자동으로 스네이크 케이스로 변환됨
    private String result;
    private String code;
    private String answer;
    
    public static SummaryResponse success(String answer) {
        return SummaryResponse.builder()
                .result("1")
                .code("OK")
                .answer(answer)
                .build();
    }
    
    public static SummaryResponse error(String code, String message) {
        return SummaryResponse.builder()
                .result("0")
                .code(code)
                .answer(message)
                .build();
    }
    
    public boolean isSuccess() {
        return "1".equals(result) && "OK".equals(code);
    }
}

