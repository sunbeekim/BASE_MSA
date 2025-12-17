#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$PROJECT_ROOT/pids"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}BASE_MSA 서비스 종료${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# VSCode 프로세스인지 확인하는 함수
is_vscode_process() {
    local pid=$1
    local cmd=$(ps -p $pid -o cmd= 2>/dev/null)
    
    # VSCode 관련 경로나 명령어 체크
    if echo "$cmd" | grep -q -E "vscode-server|code-server|\.vscode-server"; then
        return 0  # VSCode 프로세스임
    fi
    return 1  # VSCode 프로세스 아님
}

# 안전한 서비스 종료 함수
stop_service() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        
        # VSCode 프로세스 보호
        if is_vscode_process $pid; then
            echo -e "${RED}⚠ ${service_name}가 VSCode 서버 프로세스입니다. 건너뜁니다.${NC}"
            return 0
        fi
        
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}${service_name} 종료 중... (PID: $pid)${NC}"
            
            # SIGTERM으로 정상 종료 시도
            kill -TERM $pid 2>/dev/null
            
            # 최대 5초 대기
            local count=0
            while [ $count -lt 5 ]; do
                if ! ps -p $pid > /dev/null 2>&1; then
                    echo -e "${GREEN}✓ ${service_name} 정상 종료 완료${NC}"
                    rm -f "$pid_file"
                    return 0
                fi
                sleep 1
                count=$((count + 1))
            done
            
            # 자식 프로세스 확인 및 종료
            local children=$(pgrep -P $pid 2>/dev/null)
            if [ -n "$children" ]; then
                echo -e "${YELLOW}자식 프로세스 확인 중...${NC}"
                for child in $children; do
                    # VSCode 프로세스가 아닌 경우만 종료
                    if ! is_vscode_process $child; then
                        kill -TERM $child 2>/dev/null
                    else
                        echo -e "${YELLOW}  VSCode 프로세스 건너뜀: $child${NC}"
                    fi
                done
                sleep 2
            fi
            
            # 여전히 실행 중이면 SIGKILL
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${YELLOW}강제 종료 중...${NC}"
                kill -9 $pid 2>/dev/null
            fi
            
            echo -e "${GREEN}✓ ${service_name} 종료 완료${NC}"
        else
            echo -e "${YELLOW}${service_name}는 실행 중이 아닙니다.${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}${service_name} PID 파일을 찾을 수 없습니다.${NC}"
    fi
}

# Chat Frontend 특별 처리
stop_chat_frontend() {
    echo -e "${YELLOW}Chat Frontend 종료 확인 중...${NC}"
    
    local pid_file="$PID_DIR/chat-frontend.pid"
    local found_process=false
    
    # 1. PID 파일 확인
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1 && ! is_vscode_process $pid; then
            echo -e "${YELLOW}Chat Frontend 종료 중... (PID: $pid)${NC}"
            kill -TERM $pid 2>/dev/null
            sleep 2
            if ps -p $pid > /dev/null 2>&1; then
                kill -9 $pid 2>/dev/null
            fi
            found_process=true
        fi
        rm -f "$pid_file"
    fi
    
    # 2. 포트 3000 사용 프로세스 찾기 (가장 안전한 방법)
    local port_pids=$(lsof -ti :3000 2>/dev/null)
    if [ -n "$port_pids" ]; then
        echo -e "${YELLOW}포트 3000 사용 프로세스 발견: $port_pids${NC}"
        for pid in $port_pids; do
            if ! is_vscode_process $pid; then
                echo -e "${YELLOW}프로세스 종료 중: $pid${NC}"
                kill -TERM $pid 2>/dev/null
                sleep 1
                if ps -p $pid > /dev/null 2>&1; then
                    kill -9 $pid 2>/dev/null
                fi
                found_process=true
            else
                echo -e "${YELLOW}  VSCode 프로세스 건너뜀: $pid${NC}"
            fi
        done
    fi
    
    # 3. react-scripts 프로세스 찾기 (백업 방법)
    if [ "$found_process" = false ]; then
        # chat-frontend 디렉토리 내의 프로세스만 찾기
        local react_pids=$(ps aux | grep "react-scripts start" | grep "/sw/qubientai/chat-frontend" | grep -v grep | awk '{print $2}')
        if [ -n "$react_pids" ]; then
            echo -e "${YELLOW}React 프로세스 발견: $react_pids${NC}"
            for pid in $react_pids; do
                if ! is_vscode_process $pid; then
                    echo -e "${YELLOW}프로세스 종료 중: $pid${NC}"
                    kill -TERM $pid 2>/dev/null
                    sleep 1
                    found_process=true
                fi
            done
        fi
    fi
    
    if [ "$found_process" = true ]; then
        echo -e "${GREEN}✓ Chat Frontend 종료 완료${NC}"
    else
        echo -e "${YELLOW}Chat Frontend는 실행 중이 아닙니다.${NC}"
    fi
}

# 서비스 종료 (역순)
stop_chat_frontend
echo ""
stop_service "$PID_DIR/route-gateway.pid" "Route Gateway"
echo ""
stop_service "$PID_DIR/llm-api.pid" "LLM API"
echo ""
stop_service "$PID_DIR/llm_orchestrator.pid" "LLM Orchestrator"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}모든 서비스 종료 완료${NC}"
echo -e "${GREEN}========================================${NC}"
