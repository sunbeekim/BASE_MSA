package com.example.llm.client;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.client.RestClientException;

import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
public class OrchestratorClient {
    
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    
    @Value("${llm.orchestrator.url}")
    private String orchestratorUrl;
    
    /**
     * LLM Orchestrator로 요청 전달
     * 
     * @param requestBody 요청 본문 (Map, Object 등 다양한 형태)
     * @return LLM 답변 (문자열)
     */
    public String process(Map<String, Object> requestBody) {
        try {
            log.debug("LLM Orchestrator 호출: URL={}, requestBody={}", orchestratorUrl, requestBody);
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<Map<String, Object>> httpEntity = new HttpEntity<>(requestBody, headers);
            
            // Python 서버는 문자열만 반환
            ResponseEntity<String> response = restTemplate.postForEntity(
                    orchestratorUrl + "/api/llm/process",
                    httpEntity,
                    String.class
            );
            
            String answer = response.getBody();
            if (answer == null || answer.isEmpty()) {
                throw new RuntimeException("LLM Orchestrator 응답이 비어있습니다.");
            }
            
            return answer;
            
        } catch (RestClientException e) {
            log.error("LLM Orchestrator 호출 실패: requestBody={}, error={}", 
                    requestBody, e.getMessage(), e);
            throw new RuntimeException("LLM Orchestrator 호출 실패: " + e.getMessage(), e);
        }
    }
    
    /**
     * LLM Orchestrator로 요청 전달 (Object를 Map으로 변환)
     * 
     * @param request 요청 객체 (Object)
     * @return LLM 답변 (문자열)
     */
    public String process(Object request) {
        try {
            // Object를 JSON으로 직렬화한 후 다시 Map으로 역직렬화하여 @JsonProperty 적용
            String json = objectMapper.writeValueAsString(request);
            Map<String, Object> requestBody = objectMapper.readValue(json, 
                    objectMapper.getTypeFactory().constructMapType(Map.class, String.class, Object.class));
            
            // null 값 제거 (Python 서버에서 None으로 처리되지 않도록)
            requestBody.entrySet().removeIf(entry -> entry.getValue() == null);
            
            log.debug("Python 서버로 전달할 요청 본문: {}", requestBody);
            return process(requestBody);
        } catch (Exception e) {
            log.error("요청 객체를 Map으로 변환 실패: request={}, error={}", request, e.getMessage(), e);
            throw new RuntimeException("요청 객체 변환 실패: " + e.getMessage(), e);
        }
    }
}
