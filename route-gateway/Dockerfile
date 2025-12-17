FROM openjdk:17-jdk-slim

# 필요한 패키지 설치
RUN apt update && apt install -y curl

WORKDIR /app

COPY build/libs/*.jar app.jar
COPY src/main/resources/application.properties application.properties

ENV SPRING_PROFILES_ACTIVE=prod

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/app/app.jar"] 