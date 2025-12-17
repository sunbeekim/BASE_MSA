#!/bin/bash

# BASE_MSA 서비스 실행 스크립트
# 4개 서비스를 순차적으로 실행합니다:
# 1. llm_orchestrator (Python FastAPI) - 설정 파일에서 포트/호스트 읽기
# 2. llm-api (Java Spring Boot) - 설정 파일에서 포트 읽기
# 3. route-gateway (Java Spring Boot) - 설정 파일에서 포트 읽기
# 4. chat-frontend (React) - 환경 변수 PORT 또는 기본값 3000

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 프로젝트 루트 디렉토리
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 로그 디렉토리 생성
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# PID 파일 디렉토리
PID_DIR="$PROJECT_ROOT/pids"
mkdir -p "$PID_DIR"

# 설정 파일 경로 (기본값)
LLM_API_CONFIG="${LLM_API_CONFIG:-$PROJECT_ROOT/config/llm-api.yml}"
ROUTE_GATEWAY_CONFIG="${ROUTE_GATEWAY_CONFIG:-$PROJECT_ROOT/config/route-gateway.yml}"
LLM_ORCHESTRATOR_CONFIG="${LLM_ORCHESTRATOR_CONFIG:-$PROJECT_ROOT/llm_orchestrator/config/settings.yml}"

# Java 17 경로 확인 및 JAVA_HOME 설정
JAVA17_HOME="$PROJECT_ROOT/local/jdk-17"
if [ -d "$JAVA17_HOME" ] && [ -f "$JAVA17_HOME/bin/java" ]; then
    export JAVA_HOME="$JAVA17_HOME"
    export PATH="$JAVA_HOME/bin:$PATH"
    echo -e "${GREEN}✓ Java 17 발견: $JAVA_HOME${NC}"
    echo -e "${GREEN}  Java 버전: $($JAVA_HOME/bin/java -version 2>&1 | head -1)${NC}"
else
    echo -e "${YELLOW}⚠ Java 17을 찾을 수 없습니다: $JAVA17_HOME${NC}"
    if [ -z "$JAVA_HOME" ]; then
        echo -e "${YELLOW}  JAVA_HOME이 설정되지 않았습니다. 기본 java 명령어를 사용합니다.${NC}"
        JAVA_HOME=""
    else
        echo -e "${YELLOW}  기존 JAVA_HOME을 사용합니다: $JAVA_HOME${NC}"
    fi
fi

# Node.js 경로 확인 및 PATH 설정 (추가)
NODEJS_HOME="$PROJECT_ROOT/local/nodejs"
if [ -d "$NODEJS_HOME" ] && [ -f "$NODEJS_HOME/bin/node" ]; then
    export PATH="$NODEJS_HOME/bin:$PATH"
    echo -e "${GREEN}✓ Node.js 발견: $NODEJS_HOME${NC}"
    echo -e "${GREEN}  Node 버전: $($NODEJS_HOME/bin/node -v)${NC}"
    echo -e "${GREEN}  NPM 버전: $($NODEJS_HOME/bin/npm -v)${NC}"
else
    echo -e "${YELLOW}⚠ Node.js를 찾을 수 없습니다: $NODEJS_HOME${NC}"
    if command -v node > /dev/null 2>&1; then
        echo -e "${YELLOW}  기존 Node.js를 사용합니다: $(which node) ($(node -v))${NC}"
    else
        echo -e "${RED}✗ Node.js를 찾을 수 없습니다. Chat Frontend를 실행할 수 없습니다.${NC}"
    fi
fi
echo ""

# 함수: YAML 파일에서 포트 읽기
get_port_from_yaml() {
    local yaml_file=$1
    local key=$2
    local default=$3
    
    if [ ! -f "$yaml_file" ]; then
        echo "$default"
        return
    fi
    
    # YAML에서 포트 추출 (server: 섹션 내의 port: 찾기)
    # server: 다음에 오는 port: 또는 직접 port: 찾기
    local port=$(awk '/^server:/{found=1; next} found && /^\s*port:/{gsub(/.*:\s*/, ""); gsub(/[^0-9]/, ""); print; exit}' "$yaml_file")
    
    # 위 방법이 실패하면 직접 port: 찾기
    if [ -z "$port" ] || [ "$port" = "" ]; then
        port=$(grep -E "^\s*port:" "$yaml_file" | head -1 | sed -E 's/.*:\s*([0-9]+).*/\1/' | tr -d ' ')
    fi
    
    if [ -z "$port" ] || [ "$port" = "" ]; then
        echo "$default"
    else
        echo "$port"
    fi
}

# 함수: YAML 파일에서 호스트 읽기
get_host_from_yaml() {
    local yaml_file=$1
    local key=$2
    local default=$3
    
    if [ ! -f "$yaml_file" ]; then
        echo "$default"
        return
    fi
    
    # YAML에서 호스트 추출 (server: 섹션 내의 host: 찾기)
    local host=$(awk '/^server:/{found=1; next} found && /^\s*host:/{gsub(/.*:\s*/, ""); gsub(/["'\'']/, ""); print; exit}' "$yaml_file")
    
    # 위 방법이 실패하면 직접 host: 찾기
    if [ -z "$host" ] || [ "$host" = "" ]; then
        host=$(grep -E "^\s*host:" "$yaml_file" | head -1 | sed -E 's/.*:\s*["'\'']?([^"'\'' ]+)["'\'']?.*/\1/' | tr -d ' ')
    fi
    
    if [ -z "$host" ] || [ "$host" = "" ]; then
        echo "$default"
    else
        # 0.0.0.0은 localhost로 표시
        if [ "$host" = "0.0.0.0" ]; then
            echo "localhost"
        else
            echo "$host"
        fi
    fi
}

# 함수: 서비스 실행 확인 (포트 및 프로세스 확인)
check_service() {
    local port=$1
    local service_name=$2
    local pid=$3  # PID (선택적)
    local max_attempts=30
    local attempt=0
    
    echo -e "${YELLOW}${service_name} 시작 대기 중...${NC}"
    while [ $attempt -lt $max_attempts ]; do
        # 프로세스 확인 (PID가 제공된 경우)
        if [ -n "$pid" ] && ! ps -p $pid > /dev/null 2>&1; then
            echo -e "${RED}✗ ${service_name} 프로세스가 종료되었습니다 (PID: $pid)${NC}"
            return 1
        fi
        
        # 포트 확인
        if nc -z localhost $port 2>/dev/null || curl -s http://localhost:$port > /dev/null 2>&1; then
            # 프로세스도 확인 (PID가 제공된 경우)
            if [ -n "$pid" ] && ps -p $pid > /dev/null 2>&1; then
                echo -e "${GREEN}✓ ${service_name} 실행 중 (포트: $port, PID: $pid)${NC}"
            elif [ -z "$pid" ]; then
                echo -e "${GREEN}✓ ${service_name} 실행 중 (포트: $port)${NC}"
            else
                echo -e "${YELLOW}⚠ ${service_name} 포트는 열려있지만 프로세스가 실행 중이 아닙니다${NC}"
                return 1
            fi
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    echo -e "${RED}✗ ${service_name} 시작 실패 (포트: $port)${NC}"
    return 1
}

# 함수: 서비스 종료
stop_service() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}${service_name} 종료 중... (PID: $pid)${NC}"
            kill $pid 2>/dev/null
            sleep 2
            if ps -p $pid > /dev/null 2>&1; then
                kill -9 $pid 2>/dev/null
            fi
        fi
        rm -f "$pid_file"
    fi
}

# 설정 파일에서 포트와 호스트 읽기 (함수 정의 후)
LLM_ORCHESTRATOR_PORT=$(get_port_from_yaml "$LLM_ORCHESTRATOR_CONFIG" "port" "8000")
LLM_ORCHESTRATOR_HOST=$(get_host_from_yaml "$LLM_ORCHESTRATOR_CONFIG" "host" "localhost")
LLM_API_PORT=$(get_port_from_yaml "$LLM_API_CONFIG" "port" "28083")
ROUTE_GATEWAY_PORT=$(get_port_from_yaml "$ROUTE_GATEWAY_CONFIG" "port" "29080")
CHAT_FRONTEND_PORT="${PORT:-3000}"  # 환경 변수 또는 기본값 3000

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Summary Service Start${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 기존 프로세스 종료
echo -e "${YELLOW}기존 프로세스 확인 중...${NC}"
stop_service "$PID_DIR/llm_orchestrator.pid" "LLM Orchestrator"
stop_service "$PID_DIR/llm-api.pid" "LLM API"
stop_service "$PID_DIR/route-gateway.pid" "Route Gateway"
stop_service "$PID_DIR/chat-frontend.pid" "Chat Frontend"
sleep 2

# 1. LLM Orchestrator 실행
echo -e "${GREEN}[1/4] LLM Orchestrator 시작${NC}"
if [ ! -d "$PROJECT_ROOT/llm_orchestrator" ]; then
    echo -e "${RED}✗ llm_orchestrator 디렉토리를 찾을 수 없습니다.${NC}"
    exit 1
fi

cd "$PROJECT_ROOT/llm_orchestrator"

# Python 가상환경 확인 및 활성화
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 설정 파일 확인
if [ ! -f "$LLM_ORCHESTRATOR_CONFIG" ]; then
    echo -e "${YELLOW}경고: 설정 파일을 찾을 수 없습니다: $LLM_ORCHESTRATOR_CONFIG${NC}"
    echo -e "${YELLOW}기본 설정 파일을 사용합니다.${NC}"
    LLM_ORCHESTRATOR_CONFIG=""
fi

export LLM_CONFIG_PATH="$LLM_ORCHESTRATOR_CONFIG"
nohup /sw/qubientai/summary_env/bin/python /sw/qubientai/llm_orchestrator/main.py > "$LOG_DIR/llm_orchestrator.log" 2>&1 &
PYTHON_PID=$!
echo $PYTHON_PID > "$PID_DIR/llm_orchestrator.pid"
cd "$PROJECT_ROOT"

# 프로세스가 실제로 실행 중인지 확인
sleep 2
if ! ps -p $PYTHON_PID > /dev/null 2>&1; then
    echo -e "${RED}✗ LLM Orchestrator 프로세스가 시작 후 종료되었습니다. 로그를 확인하세요: $LOG_DIR/llm_orchestrator.log${NC}"
    echo -e "${YELLOW}마지막 20줄:${NC}"
    tail -20 "$LOG_DIR/llm_orchestrator.log" 2>/dev/null || echo "로그 파일을 읽을 수 없습니다."
else
    check_service "$LLM_ORCHESTRATOR_PORT" "LLM Orchestrator" "$PYTHON_PID" || echo -e "${YELLOW}LLM Orchestrator 시작 확인 실패 (수동 확인 필요)${NC}"
fi
echo ""

# 2. LLM API 실행
echo -e "${GREEN}[2/4] LLM API 시작${NC}"

# JAR 파일 확인 (루트 디렉토리)
JAR_FILE="$PROJECT_ROOT/llm-api-0.0.1-SNAPSHOT.jar"
if [ ! -f "$JAR_FILE" ]; then
    echo -e "${RED}✗ JAR 파일을 찾을 수 없습니다: $JAR_FILE${NC}"
    exit 1
fi

# 설정 파일 확인
if [ ! -f "$LLM_API_CONFIG" ]; then
    echo -e "${YELLOW}경고: 설정 파일을 찾을 수 없습니다: $LLM_API_CONFIG${NC}"
    echo -e "${YELLOW}기본 설정 파일을 사용합니다.${NC}"
    LLM_API_CONFIG=""
fi

if [ -n "$LLM_API_CONFIG" ]; then
    if [ -n "$JAVA_HOME" ]; then
        nohup "$JAVA_HOME/bin/java" -jar "$JAR_FILE" --spring.config.location="file:$LLM_API_CONFIG" > "$LOG_DIR/llm-api.log" 2>&1 &
    else
        nohup java -jar "$JAR_FILE" --spring.config.location="file:$LLM_API_CONFIG" > "$LOG_DIR/llm-api.log" 2>&1 &
    fi
else
    if [ -n "$JAVA_HOME" ]; then
        nohup "$JAVA_HOME/bin/java" -jar "$JAR_FILE" > "$LOG_DIR/llm-api.log" 2>&1 &
    else
        nohup java -jar "$JAR_FILE" > "$LOG_DIR/llm-api.log" 2>&1 &
    fi
fi
JAVA_PID=$!
echo $JAVA_PID > "$PID_DIR/llm-api.pid"

# 프로세스가 실제로 실행 중인지 확인
sleep 2
if ! ps -p $JAVA_PID > /dev/null 2>&1; then
    echo -e "${RED}✗ LLM API 프로세스가 시작 후 종료되었습니다. 로그를 확인하세요: $LOG_DIR/llm-api.log${NC}"
    echo -e "${YELLOW}마지막 20줄:${NC}"
    tail -20 "$LOG_DIR/llm-api.log" 2>/dev/null || echo "로그 파일을 읽을 수 없습니다."
else
    check_service "$LLM_API_PORT" "LLM API" "$JAVA_PID" || echo -e "${YELLOW}LLM API 시작 확인 실패 (수동 확인 필요)${NC}"
fi
echo ""

# 3. Route Gateway 실행
echo -e "${GREEN}[3/4] Route Gateway 시작${NC}"

# JAR 파일 확인 (루트 디렉토리)
JAR_FILE="$PROJECT_ROOT/route-gateway-0.0.1-SNAPSHOT.jar"
if [ ! -f "$JAR_FILE" ]; then
    echo -e "${RED}✗ JAR 파일을 찾을 수 없습니다: $JAR_FILE${NC}"
    exit 1
fi

# 설정 파일 확인
if [ ! -f "$ROUTE_GATEWAY_CONFIG" ]; then
    echo -e "${YELLOW}경고: 설정 파일을 찾을 수 없습니다: $ROUTE_GATEWAY_CONFIG${NC}"
    echo -e "${YELLOW}기본 설정 파일을 사용합니다.${NC}"
    ROUTE_GATEWAY_CONFIG=""
fi

if [ -n "$ROUTE_GATEWAY_CONFIG" ]; then
    if [ -n "$JAVA_HOME" ]; then
        nohup "$JAVA_HOME/bin/java" -jar "$JAR_FILE" --spring.config.location="file:$ROUTE_GATEWAY_CONFIG" > "$LOG_DIR/route-gateway.log" 2>&1 &
    else
        nohup java -jar "$JAR_FILE" --spring.config.location="file:$ROUTE_GATEWAY_CONFIG" > "$LOG_DIR/route-gateway.log" 2>&1 &
    fi
else
    if [ -n "$JAVA_HOME" ]; then
        nohup "$JAVA_HOME/bin/java" -jar "$JAR_FILE" > "$LOG_DIR/route-gateway.log" 2>&1 &
    else
        nohup java -jar "$JAR_FILE" > "$LOG_DIR/route-gateway.log" 2>&1 &
    fi
fi
JAVA_PID=$!
echo $JAVA_PID > "$PID_DIR/route-gateway.pid"

# 프로세스가 실제로 실행 중인지 확인
sleep 2
if ! ps -p $JAVA_PID > /dev/null 2>&1; then
    echo -e "${RED}✗ Route Gateway 프로세스가 시작 후 종료되었습니다. 로그를 확인하세요: $LOG_DIR/route-gateway.log${NC}"
    echo -e "${YELLOW}마지막 20줄:${NC}"
    tail -20 "$LOG_DIR/route-gateway.log" 2>/dev/null || echo "로그 파일을 읽을 수 없습니다."
else
    check_service "$ROUTE_GATEWAY_PORT" "Route Gateway" "$JAVA_PID" || echo -e "${YELLOW}Route Gateway 시작 확인 실패 (수동 확인 필요)${NC}"
fi
echo ""

# 4. Chat Frontend 실행
echo -e "${GREEN}[4/4] Chat Frontend 시작${NC}"
if [ ! -d "$PROJECT_ROOT/chat-frontend" ]; then
    echo -e "${RED}✗ chat-frontend 디렉토리를 찾을 수 없습니다.${NC}"
    exit 1
fi

cd "$PROJECT_ROOT/chat-frontend"

# node_modules 확인
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}node_modules가 없습니다. npm install을 실행합니다...${NC}"
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ npm install 실패${NC}"
        exit 1
    fi
fi

export BROWSER=none

# node_modules/.bin/ 디렉토리의 실행 파일에 실행 권한 부여
if [ -d "node_modules/.bin" ]; then
    echo -e "${YELLOW}실행 파일 권한 확인 중...${NC}"
    chmod +x node_modules/.bin/* 2>/dev/null || true
fi

# npm start는 포그라운드로 실행되므로 setsid를 사용하거나 직접 백그라운드로 실행
PORT=$CHAT_FRONTEND_PORT nohup npm start > "$LOG_DIR/chat-frontend.log" 2>&1 &
NPM_PID=$!
echo $NPM_PID > "$PID_DIR/chat-frontend.pid"
cd "$PROJECT_ROOT"

# React 개발 서버는 자식 프로세스로 실행되므로 실제 node 프로세스를 찾아서 PID 업데이트
sleep 5
# 프로세스가 실행 중인지 확인
if ! ps -p $NPM_PID > /dev/null 2>&1; then
    echo -e "${RED}✗ Chat Frontend 프로세스가 시작 후 종료되었습니다. 로그를 확인하세요: $LOG_DIR/chat-frontend.log${NC}"
    echo -e "${YELLOW}마지막 20줄:${NC}"
    tail -20 "$LOG_DIR/chat-frontend.log" 2>/dev/null || echo "로그 파일을 읽을 수 없습니다."
else
    # node 프로세스 중 react-scripts를 실행하는 프로세스 찾기
    REACT_PID=$(ps aux | grep -E "react-scripts|node.*start" | grep -v grep | awk '{print $2}' | head -1)
    if [ -n "$REACT_PID" ]; then
        echo $REACT_PID > "$PID_DIR/chat-frontend.pid"
        echo -e "${GREEN}✓ Chat Frontend 실행 중 (포트: $CHAT_FRONTEND_PORT, PID: $REACT_PID)${NC}"
    else
        # npm 프로세스가 실행 중이면 일단 성공으로 표시
        echo -e "${GREEN}✓ Chat Frontend 실행 중 (포트: $CHAT_FRONTEND_PORT, npm PID: $NPM_PID)${NC}"
    fi
fi
echo ""

# 완료 메시지
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}모든 서비스 시작 완료${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "서비스 상태:"

# LLM Orchestrator 상태 확인 (Python 프로세스 확인)
ORCHESTRATOR_PID=$(cat $PID_DIR/llm_orchestrator.pid 2>/dev/null || echo "")
# 호스트가 비어있거나 0.0.0.0이면 localhost로 표시
ORCHESTRATOR_DISPLAY_HOST="${LLM_ORCHESTRATOR_HOST:-localhost}"
if [ "$ORCHESTRATOR_DISPLAY_HOST" = "0.0.0.0" ]; then
    ORCHESTRATOR_DISPLAY_HOST="localhost"
fi

if [ -n "$ORCHESTRATOR_PID" ] && ps -p $ORCHESTRATOR_PID > /dev/null 2>&1; then
    echo -e "  - LLM Orchestrator: ${GREEN}http://${ORCHESTRATOR_DISPLAY_HOST}:${LLM_ORCHESTRATOR_PORT}${NC} (PID: $ORCHESTRATOR_PID) ${GREEN}✓ 실행 중${NC}"
else
    # Python 프로세스로 다시 확인 (main.py를 실행하는 프로세스 찾기)
    PYTHON_PID=$(ps aux | grep "[p]ython.*main.py" | grep -v grep | awk '{print $2}' | head -1)
    if [ -n "$PYTHON_PID" ]; then
        echo $PYTHON_PID > "$PID_DIR/llm_orchestrator.pid"
        echo -e "  - LLM Orchestrator: ${GREEN}http://${ORCHESTRATOR_DISPLAY_HOST}:${LLM_ORCHESTRATOR_PORT}${NC} (PID: $PYTHON_PID) ${GREEN}✓ 실행 중${NC}"
    else
        # 포트로 확인
        if nc -z localhost $LLM_ORCHESTRATOR_PORT 2>/dev/null || curl -s http://localhost:$LLM_ORCHESTRATOR_PORT > /dev/null 2>&1; then
            echo -e "  - LLM Orchestrator: ${GREEN}http://${ORCHESTRATOR_DISPLAY_HOST}:${LLM_ORCHESTRATOR_PORT}${NC} ${GREEN}✓ 실행 중 (포트 확인)${NC}"
        else
            echo -e "  - LLM Orchestrator: ${RED}실행 중이 아닙니다${NC} (로그 확인: $LOG_DIR/llm_orchestrator.log)"
        fi
    fi
fi

# LLM API 상태 확인 (Java 프로세스 확인)
LLM_API_PID=$(cat $PID_DIR/llm-api.pid 2>/dev/null || echo "")
if [ -n "$LLM_API_PID" ] && ps -p $LLM_API_PID > /dev/null 2>&1; then
    echo -e "  - LLM API: ${GREEN}http://localhost:${LLM_API_PORT}${NC} (PID: $LLM_API_PID) ${GREEN}✓ 실행 중${NC}"
else
    # Java 프로세스로 다시 확인 (JAR 파일 이름으로)
    JAVA_PID=$(ps aux | grep "llm-api-0.0.1-SNAPSHOT.jar" | grep -v grep | awk '{print $2}' | head -1)
    if [ -n "$JAVA_PID" ]; then
        echo $JAVA_PID > "$PID_DIR/llm-api.pid"
        echo -e "  - LLM API: ${GREEN}http://localhost:${LLM_API_PORT}${NC} (PID: $JAVA_PID) ${GREEN}✓ 실행 중${NC}"
    else
        echo -e "  - LLM API: ${RED}실행 중이 아닙니다${NC} (로그 확인: $LOG_DIR/llm-api.log)"
    fi
fi

# Route Gateway 상태 확인 (Java 프로세스 확인)
GATEWAY_PID=$(cat $PID_DIR/route-gateway.pid 2>/dev/null || echo "")
if [ -n "$GATEWAY_PID" ] && ps -p $GATEWAY_PID > /dev/null 2>&1; then
    echo -e "  - Route Gateway: ${GREEN}http://localhost:${ROUTE_GATEWAY_PORT}${NC} (PID: $GATEWAY_PID) ${GREEN}✓ 실행 중${NC}"
else
    # Java 프로세스로 다시 확인 (JAR 파일 이름으로)
    JAVA_PID=$(ps aux | grep "route-gateway-0.0.1-SNAPSHOT.jar" | grep -v grep | awk '{print $2}' | head -1)
    if [ -n "$JAVA_PID" ]; then
        echo $JAVA_PID > "$PID_DIR/route-gateway.pid"
        echo -e "  - Route Gateway: ${GREEN}http://localhost:${ROUTE_GATEWAY_PORT}${NC} (PID: $JAVA_PID) ${GREEN}✓ 실행 중${NC}"
    else
        echo -e "  - Route Gateway: ${RED}실행 중이 아닙니다${NC} (로그 확인: $LOG_DIR/route-gateway.log)"
    fi
fi

# Chat Frontend 상태 확인 (포트 확인 포함)
FRONTEND_PID=$(cat $PID_DIR/chat-frontend.pid 2>/dev/null || echo "")
# 포트가 실제로 리스닝 중인지 확인
PORT_LISTENING=false
if nc -z localhost $CHAT_FRONTEND_PORT 2>/dev/null || ss -lntp 2>/dev/null | grep -q ":$CHAT_FRONTEND_PORT " || netstat -lntp 2>/dev/null | grep -q ":$CHAT_FRONTEND_PORT "; then
    PORT_LISTENING=true
fi

if [ "$PORT_LISTENING" = true ]; then
    # 포트가 열려있으면 실행 중
    if [ -n "$FRONTEND_PID" ] && ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "  - Chat Frontend: ${GREEN}http://localhost:${CHAT_FRONTEND_PORT}${NC} (PID: $FRONTEND_PID) ${GREEN}✓ 실행 중${NC}"
    else
        # node 프로세스로 다시 확인
        NODE_PID=$(ps aux | grep -E "react-scripts|node.*start" | grep -v grep | awk '{print $2}' | head -1)
        if [ -n "$NODE_PID" ]; then
            echo $NODE_PID > "$PID_DIR/chat-frontend.pid"
            echo -e "  - Chat Frontend: ${GREEN}http://localhost:${CHAT_FRONTEND_PORT}${NC} (PID: $NODE_PID) ${GREEN}✓ 실행 중${NC}"
        else
            echo -e "  - Chat Frontend: ${GREEN}http://localhost:${CHAT_FRONTEND_PORT}${NC} ${GREEN}✓ 실행 중 (포트 확인)${NC}"
        fi
    fi
elif [ -n "$FRONTEND_PID" ] && ps -p $FRONTEND_PID > /dev/null 2>&1; then
    # 프로세스는 있지만 포트가 열려있지 않음
    echo -e "  - Chat Frontend: ${YELLOW}프로세스는 실행 중이지만 포트 ${CHAT_FRONTEND_PORT}가 열려있지 않습니다${NC} (로그 확인: $LOG_DIR/chat-frontend.log)"
else
    # 프로세스도 없고 포트도 열려있지 않음
    echo -e "  - Chat Frontend: ${RED}실행 중이 아닙니다${NC} (로그 확인: $LOG_DIR/chat-frontend.log)"
fi
echo ""
echo -e "로그 파일 위치: ${YELLOW}$LOG_DIR${NC}"
echo -e "PID 파일 위치: ${YELLOW}$PID_DIR${NC}"
echo ""
echo -e "서비스 종료: ${YELLOW}./stop.sh${NC} 또는 ${YELLOW}Ctrl+C${NC}"

