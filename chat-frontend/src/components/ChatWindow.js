import React, { useState, useRef, useEffect } from 'react';
import './ChatWindow.css';
import { sendSummaryRequest, querySummary } from '../services/api';

const ChatWindow = () => {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [callkey, setCallkey] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const generateCallkey = () => {
    return `test-${Date.now()}`;
  };

  const handleSend = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage = inputText.trim();
    const currentCallkey = callkey || generateCallkey();
    
    if (!callkey) {
      setCallkey(currentCallkey);
    }

    // 사용자 메시지 추가
    setMessages(prev => [...prev, {
      type: 'user',
      text: userMessage,
      timestamp: new Date()
    }]);

    setInputText('');
    setIsLoading(true);

    try {
      // 요약 요청 (시스템 프롬프트 포함, 없으면 undefined)
      const response = await sendSummaryRequest(
        currentCallkey, 
        userMessage, 
        systemPrompt.trim() || undefined
      );
      
      if (response.result === '1' && response.code === 'OK') {
        // 요약 결과 추가
        setMessages(prev => [...prev, {
          type: 'summary',
          text: response.answer,
          timestamp: new Date()
        }]);
      } else {
        throw new Error(response.answer || '요약 실패');
      }
    } catch (error) {
      console.error('요약 요청 실패:', error);
      setMessages(prev => [...prev, {
        type: 'error',
        text: `오류: ${error.message || '요약 요청 중 오류가 발생했습니다.'}`,
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuery = async () => {
    if (!callkey || isLoading) return;

    setIsLoading(true);

    try {
      const response = await querySummary(callkey);
      
      if (response.result === '1' && response.code === 'OK') {
        setMessages(prev => [...prev, {
          type: 'query',
          text: `저장된 원본: ${response.original_text}\n\n저장된 요약: ${response.processed_text}`,
          timestamp: new Date()
        }]);
      } else {
        throw new Error(response.original_text || '조회 실패');
      }
    } catch (error) {
      console.error('조회 실패:', error);
      setMessages(prev => [...prev, {
        type: 'error',
        text: `오류: ${error.message || '조회 중 오류가 발생했습니다.'}`,
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClear = () => {
    setMessages([]);
    setCallkey(null);
  };

  return (
    <div className="chat-window">
      <div className="chat-header">
        <div className="callkey-info">
          {callkey && <span>Callkey: {callkey}</span>}
        </div>
        <div className="chat-actions">
          {callkey && (
            <button onClick={handleQuery} disabled={isLoading} className="btn-query">
              저장된 결과 조회
            </button>
          )}
          <button onClick={handleClear} className="btn-clear">
            초기화
          </button>
        </div>
      </div>

      <div className="messages-container">
        {messages.length === 0 && (
          <div className="empty-state">
            <p>상담 내용을 입력하고 요약을 요청하세요</p>
            <p className="hint">예: 상담사와 상담자의 대화 내용</p>
          </div>
        )}
        
        {messages.map((msg, index) => (
          <div key={index} className={`message message-${msg.type}`}>
            <div className="message-content">
              <div className="message-text">{msg.text}</div>
              <div className="message-time">
                {msg.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="message message-loading">
            <div className="message-content">
              <div className="loading-spinner"></div>
              <div className="message-text">요약 중...</div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <div className="input-fields">
          <div className="input-group">
            <label className="input-label">시스템 프롬프트 (선택)</label>
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder="시스템 프롬프트를 입력하세요 (없으면 기본 프롬프트 사용)..."
              rows={2}
              disabled={isLoading}
              className="input-textarea system-prompt"
            />
          </div>
          <div className="input-group">
            <label className="input-label">상담 내용 (필수)</label>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="상담 내용을 입력하세요..."
              rows={3}
              disabled={isLoading}
              className="input-textarea"
            />
          </div>
        </div>
        <button
          onClick={handleSend}
          disabled={!inputText.trim() || isLoading}
          className="btn-send"
        >
          요약 요청
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;

