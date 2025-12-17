package com.example.demo.filter;

import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * 모든 요청과 응답을 로깅하는 Global Filter
 */
@Component
public class LoggingGlobalFilter implements GlobalFilter, Ordered {

    private static final DateTimeFormatter FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss.SSS");

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String method = request.getMethod().name();
        String path = request.getPath().value();
        String remoteAddress = request.getRemoteAddress() != null 
            ? request.getRemoteAddress().getAddress().getHostAddress() 
            : "unknown";
        String userAgent = request.getHeaders().getFirst("User-Agent");
        String contentType = request.getHeaders().getFirst("Content-Type");
        
        String timestamp = LocalDateTime.now().format(FORMATTER);
        
        // 요청 로깅
        System.out.println("=".repeat(80));
        System.out.println(String.format("[%s] [REQUEST] %s %s", timestamp, method, path));
        System.out.println(String.format("  Remote Address: %s", remoteAddress));
        System.out.println(String.format("  User-Agent: %s", userAgent != null ? userAgent : "N/A"));
        System.out.println(String.format("  Content-Type: %s", contentType != null ? contentType : "N/A"));
        System.out.println("=".repeat(80));
        
        // 응답 로깅을 위한 후처리
        return chain.filter(exchange).then(Mono.fromRunnable(() -> {
            ServerHttpResponse response = exchange.getResponse();
            int statusCode = response.getStatusCode() != null ? response.getStatusCode().value() : 0;
            String responseTimestamp = LocalDateTime.now().format(FORMATTER);
            
            System.out.println("=".repeat(80));
            System.out.println(String.format("[%s] [RESPONSE] %s %s - Status: %d", 
                responseTimestamp, method, path, statusCode));
            System.out.println("=".repeat(80));
        }));
    }

    @Override
    public int getOrder() {
        // 가장 먼저 실행되도록 설정 (낮은 숫자가 먼저 실행)
        return -1;
    }
}

