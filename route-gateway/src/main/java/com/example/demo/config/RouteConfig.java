package com.example.demo.config;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.cloud.gateway.route.RouteLocator;
import org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder;
import com.example.demo.filter.JwtAuthenticationFilter;

import org.springframework.http.HttpHeaders;

@Configuration
public class RouteConfig {
        @Autowired
        private JwtAuthenticationFilter jwtFilter;

        @Value("${spring.profiles.active:local}")
        private String activeProfile;

        @Value("${gateway.routes.summary.uri}")
        private String summaryServiceUri;

        @Value("${gateway.routes.summary.prod-uri}")
        private String summaryServiceProdUri;

        @Value("${gateway.routes.summary.path}")
        private String summaryServicePath;

        // 확장용 라우트 1
        @Value("${gateway.routes.route1.enabled:false}")
        private boolean route1Enabled;

        @Value("${gateway.routes.route1.id:customRoute1}")
        private String route1Id;

        @Value("${gateway.routes.route1.uri:http://localhost:8081}")
        private String route1Uri;

        @Value("${gateway.routes.route1.prod-uri:http://service1-container:8081}")
        private String route1ProdUri;

        @Value("${gateway.routes.route1.path:/api/v1/**}")
        private String route1Path;

        // 확장용 라우트 2
        @Value("${gateway.routes.route2.enabled:false}")
        private boolean route2Enabled;

        @Value("${gateway.routes.route2.id:customRoute2}")
        private String route2Id;

        @Value("${gateway.routes.route2.uri:http://localhost:8082}")
        private String route2Uri;

        @Value("${gateway.routes.route2.prod-uri:http://service2-container:8082}")
        private String route2ProdUri;

        @Value("${gateway.routes.route2.path:/api/v2/**}")
        private String route2Path;

        // 확장용 라우트 3
        @Value("${gateway.routes.route3.enabled:false}")
        private boolean route3Enabled;

        @Value("${gateway.routes.route3.id:customRoute3}")
        private String route3Id;

        @Value("${gateway.routes.route3.uri:http://localhost:8083}")
        private String route3Uri;

        @Value("${gateway.routes.route3.prod-uri:http://service3-container:8083}")
        private String route3ProdUri;

        @Value("${gateway.routes.route3.path:/api/v3/**}")
        private String route3Path;

        // 확장용 라우트 4
        @Value("${gateway.routes.route4.enabled:false}")
        private boolean route4Enabled;

        @Value("${gateway.routes.route4.id:customRoute4}")
        private String route4Id;

        @Value("${gateway.routes.route4.uri:http://localhost:8084}")
        private String route4Uri;

        @Value("${gateway.routes.route4.prod-uri:http://service4-container:8084}")
        private String route4ProdUri;

        @Value("${gateway.routes.route4.path:/api/v4/**}")
        private String route4Path;

        // 확장용 라우트 5
        @Value("${gateway.routes.route5.enabled:false}")
        private boolean route5Enabled;

        @Value("${gateway.routes.route5.id:customRoute5}")
        private String route5Id;

        @Value("${gateway.routes.route5.uri:http://localhost:8085}")
        private String route5Uri;

        @Value("${gateway.routes.route5.prod-uri:http://service5-container:8085}")
        private String route5ProdUri;

        @Value("${gateway.routes.route5.path:/api/v5/**}")
        private String route5Path;

        @Bean
        public RouteLocator customRouteLocator(RouteLocatorBuilder builder) {
                System.out.println("=== RouteConfig 초기화 ===");
                System.out.println("현재 활성화된 프로필: " + activeProfile);

                // 관세청 요약 서비스 (요약용 커스텀 서비스)
                final String authServiceUri = "prod".equals(activeProfile)
                                ? "http://auth-container:28089"
                                : "http://localhost:28089";

                // 관세청 요약 서비스 URI (yml에서 설정값 사용)
                final String summaryServiceUriFinal = "prod".equals(activeProfile)
                                ? summaryServiceProdUri
                                : summaryServiceUri;

                final String webSocketUri = "prod".equals(activeProfile)
                                ? "ws://core-container:8087" // 도커 브릿지 네트워크로 사용하기 때문에 wss 사용 해도 되지만 ws도 가능
                                : "ws://localhost:8087";

                System.out.println("인증 서비스 URI: " + authServiceUri);
                System.out.println("관세청 요약 서비스 URI: " + summaryServiceUriFinal);
                System.out.println("관세청 요약 서비스 Path: " + summaryServicePath);
                System.out.println("WebSocket URI: " + webSocketUri);

                // 관세청 요약 서비스와 WebSocket 라우팅만 설정
                RouteLocatorBuilder.Builder routesBuilder = builder.routes()
                                .route("authService", r -> r
                                                .path("/auth/**")
                                                .uri(authServiceUri))
                                .route("summaryCustomService", r -> r
                                                .path(summaryServicePath)
                                                // .filters(f -> f.filter(jwtFilter.apply(new
                                                // JwtAuthenticationFilter.Config())))
                                                // JWT 필터 제외 (관세청 요약 서비스는 JWT 검증하지 않음)
                                                .uri(summaryServiceUriFinal))
                                // 웹소켓 라우팅
                                .route("coreSockJsWebSocket", r -> r
                                                .path("/ws/**", "/ws", "/topic/**")
                                                .filters(f -> f
                                                                // 웹소켓 헤더 보존 및 추가
                                                                .preserveHostHeader()
                                                                .removeRequestHeader(HttpHeaders.HOST)
                                                                .addRequestHeader("Connection", "Upgrade")
                                                                .addRequestHeader("Upgrade", "websocket")
                                                                .addRequestHeader("Sec-WebSocket-Version", "13")
                                                // 인증 필터 제외 (JWT 인증은 STOMP 단에서 처리)
                                                )
                                                .uri(webSocketUri));

                // 확장용 라우트 1
                if (route1Enabled) {
                        final String route1UriFinal = "prod".equals(activeProfile) ? route1ProdUri : route1Uri;
                        System.out.println("확장 라우트 1 활성화 - ID: " + route1Id + ", URI: " + route1UriFinal + ", Path: " + route1Path);
                        routesBuilder.route(route1Id, r -> r
                                        .path(route1Path)
                                        .uri(route1UriFinal));
                }

                // 확장용 라우트 2
                if (route2Enabled) {
                        final String route2UriFinal = "prod".equals(activeProfile) ? route2ProdUri : route2Uri;
                        System.out.println("확장 라우트 2 활성화 - ID: " + route2Id + ", URI: " + route2UriFinal + ", Path: " + route2Path);
                        routesBuilder.route(route2Id, r -> r
                                        .path(route2Path)
                                        .uri(route2UriFinal));
                }

                // 확장용 라우트 3
                if (route3Enabled) {
                        final String route3UriFinal = "prod".equals(activeProfile) ? route3ProdUri : route3Uri;
                        System.out.println("확장 라우트 3 활성화 - ID: " + route3Id + ", URI: " + route3UriFinal + ", Path: " + route3Path);
                        routesBuilder.route(route3Id, r -> r
                                        .path(route3Path)
                                        .uri(route3UriFinal));
                }

                // 확장용 라우트 4
                if (route4Enabled) {
                        final String route4UriFinal = "prod".equals(activeProfile) ? route4ProdUri : route4Uri;
                        System.out.println("확장 라우트 4 활성화 - ID: " + route4Id + ", URI: " + route4UriFinal + ", Path: " + route4Path);
                        routesBuilder.route(route4Id, r -> r
                                        .path(route4Path)
                                        .uri(route4UriFinal));
                }

                // 확장용 라우트 5
                if (route5Enabled) {
                        final String route5UriFinal = "prod".equals(activeProfile) ? route5ProdUri : route5Uri;
                        System.out.println("확장 라우트 5 활성화 - ID: " + route5Id + ", URI: " + route5UriFinal + ", Path: " + route5Path);
                        routesBuilder.route(route5Id, r -> r
                                        .path(route5Path)
                                        .uri(route5UriFinal));
                }

                return routesBuilder.build();

        }
}
