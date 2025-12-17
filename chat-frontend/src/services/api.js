import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://192.168.0.134:29080';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json; charset=utf-8',
  },
  timeout: 120000, // 2분
});

// 요약 요청
export const sendSummaryRequest = async (callkey, text, systemPrompt) => {
  try {
    const requestBody = {
      callkey,
      text,
    };

    // 시스템 프롬프트가 있으면 추가
    if (systemPrompt) {
      requestBody.system_prompt = systemPrompt;
    }

    const response = await api.post('/summary/stt/process', requestBody);
    return response.data;
  } catch (error) {
    if (error.response) {
      throw new Error(error.response.data.answer || '요약 요청 실패');
    } else if (error.request) {
      throw new Error('서버에 연결할 수 없습니다.');
    } else {
      throw new Error(error.message || '요약 요청 중 오류가 발생했습니다.');
    }
  }
};

// 요약 결과 조회
export const querySummary = async (callkey) => {
  try {
    const response = await api.get(`/summary/stt/query/${callkey}`);
    return response.data;
  } catch (error) {
    if (error.response) {
      throw new Error(error.response.data.original_text || '조회 실패');
    } else if (error.request) {
      throw new Error('서버에 연결할 수 없습니다.');
    } else {
      throw new Error(error.message || '조회 중 오류가 발생했습니다.');
    }
  }
};

