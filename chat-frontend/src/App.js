import React, { useState } from 'react';
import './App.css';
import ChatWindow from './components/ChatWindow';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>요약 테스트 챗</h1>
        <p>상담 내용을 입력하고 요약을 요청하세요</p>
      </header>
      <ChatWindow />
    </div>
  );
}

export default App;

