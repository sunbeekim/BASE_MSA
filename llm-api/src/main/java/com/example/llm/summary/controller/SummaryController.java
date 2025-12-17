package com.example.llm.summary.controller;

import com.example.llm.summary.dto.SummaryRequest;
import com.example.llm.summary.dto.SummaryResponse;
import com.example.llm.summary.dto.SummaryQueryResponse;
import com.example.llm.summary.service.SummaryService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping("/summary/stt")
@RequiredArgsConstructor
public class SummaryController {
    
    private final SummaryService summaryService;
    
    @PostMapping("/process")
    public ResponseEntity<SummaryResponse> process(@Valid @RequestBody SummaryRequest request,
                                                      BindingResult bindingResult) {
        log.info("LLM 처리 요청 수신: callkey={}", request.getCallkey());
        
        if (bindingResult.hasErrors()) {
            String errorMessage = bindingResult.getFieldErrors().stream()
                    .map(error -> error.getField() + ": " + error.getDefaultMessage())
                    .reduce((msg1, msg2) -> msg1 + ", " + msg2)
                    .orElse("요청 파라미터 오류");
            
            if (bindingResult.hasFieldErrors("callkey")) {
                return ResponseEntity.badRequest()
                        .body(SummaryResponse.error("E400", errorMessage));
            }
            if (bindingResult.hasFieldErrors("text")) {
                return ResponseEntity.badRequest()
                        .body(SummaryResponse.error("E401", errorMessage));
            }
            
            return ResponseEntity.badRequest()
                    .body(SummaryResponse.error("E400", errorMessage));
        }
        
        SummaryResponse response = summaryService.process(request);
        
        if (response.isSuccess()) {
            return ResponseEntity.ok(response);
        } else {
            if ("E400".equals(response.getCode()) || "E401".equals(response.getCode())) {
                return ResponseEntity.badRequest().body(response);
            } else if ("E404".equals(response.getCode())) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(response);
            } else {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
            }
        }
    }
    
    @GetMapping("/query/{callkey}")
    public ResponseEntity<SummaryQueryResponse> query(@PathVariable String callkey) {
        log.info("LLM 처리 결과 조회 요청: callkey={}", callkey);
        
        SummaryQueryResponse response = summaryService.queryByCallkey(callkey);
        
        if (response.getResult() != null && "1".equals(response.getResult())) {
            return ResponseEntity.ok(response);
        } else {
            if ("E404".equals(response.getCode())) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(response);
            } else {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
            }
        }
    }
}

