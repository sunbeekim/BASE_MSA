"""
STT 텍스트 변환 모듈

목표:
- [] 안의 내용을 숫자/영문으로 변환 (이미 []로 감싸진 것만)
"""
import re
from typing import Dict
from core.logger import get_logger

logger = get_logger(__name__)

KOREAN_NUMBER_MAP: Dict[str, str] = {
    "여섯": "6",
    "일곱": "7",
    "여덟": "8",
    "아홉": "9",
    "다섯": "5",
    "하나": "1",
    "영": "0",
    "공": "0",
    "일": "1",
    "이": "2",
    "둘": "2",
    "삼": "3",
    "셋": "3",
    "사": "4",
    "넷": "4",
    "오": "5",
    "육": "6",
    "륙": "6",
    "칠": "7",
    "팔": "8",
    "구": "9",
    "십": "10",
    "백": "100",
    "천": "1000",
    "만": "10000",
}

KOREAN_ALPHABET_MAP: Dict[str, str] = {
    "에이": "A",
    "비": "B",
    "씨": "C",
    "디": "D",
    "이": "E",
    "에프": "F",
    "지": "G",
    "에이치": "H",
    "아이": "I",
    "제이": "J",
    "케이": "K",
    "엘": "L",
    "엠": "M",
    "엔": "N",
    "오": "O",
    "피": "P",
    "큐": "Q",
    "알": "R",
    "에스": "S",
    "티": "T",
    "유": "U",
    "브이": "V",
    "더블유": "W",
    "엑스": "X",
    "와이": "Y",
    "지": "Z",
}


def convert_korean_number_to_arabic(korean_number: str) -> int:
    if not korean_number or not korean_number.strip():
        return 0

    s = korean_number.strip().replace(" ", "")

    # 단위 없는 순차 숫자(공사공오/일사육...)
    if not any(u in s for u in ("십", "백", "천", "만")):
        digits = []
        remaining = s
        while remaining:
            matched = False
            for k, a in sorted(KOREAN_NUMBER_MAP.items(), key=lambda x: len(x[0]), reverse=True):
                if k in ("십", "백", "천", "만"):
                    continue
                if remaining.startswith(k):
                    digits.append(a)
                    remaining = remaining[len(k) :]
                    matched = True
                    break
            if not matched:
                break
        return int("".join(digits)) if digits else 0

    total = 0
    section = 0
    num = 0

    def one_if_empty(x: int) -> int:
        return x if x != 0 else 1

    i = 0
    while i < len(s):
        ch = s[i]

        if ch in KOREAN_NUMBER_MAP and ch not in ("십", "백", "천", "만"):
            num = int(KOREAN_NUMBER_MAP[ch])
            i += 1
            continue

        if ch in ("십", "백", "천"):
            unit = {"십": 10, "백": 100, "천": 1000}[ch]
            section += one_if_empty(num) * unit
            num = 0
            i += 1
            continue

        if ch == "만":
            section += one_if_empty(num)
            total += section * 10000
            section = 0
            num = 0
            i += 1
            continue

        break

    section += num
    total += section
    return total


def can_convert_to_alphabet(t: str) -> bool:
    """문자열 전체가 한글 알파벳 발음 조합으로만 이루어졌는지 체크"""
    t_clean = t.replace(" ", "")
    if not t_clean:
        return False

    remaining = t_clean
    sorted_map = sorted(KOREAN_ALPHABET_MAP.items(), key=lambda x: len(x[0]), reverse=True)

    while remaining:
        matched = False
        for korean, _english in sorted_map:
            if remaining.startswith(korean):
                remaining = remaining[len(korean):]
                matched = True
                break
        if not matched:
            return False
    return True

def can_convert_to_number(t: str) -> bool:
    """문자열 전체가 한글 숫자로만 변환 가능한지 체크"""
    t_clean = t.replace(" ", "")
    if not t_clean:
        return False
    
    remaining = t_clean
    sorted_map = sorted(KOREAN_NUMBER_MAP.items(), key=lambda x: len(x[0]), reverse=True)
    
    while remaining:
        matched = False
        for korean, _arabic in sorted_map:
            if remaining.startswith(korean):
                remaining = remaining[len(korean):]
                matched = True
                break
        if not matched:
            return False
    return True


def convert_bracketed_content(text: str) -> str:
    """
    [] 안의 내용만 변환:
    - 숫자(한글 수사/순차숫자) -> 숫자
    - 영문(한글 알파벳 발음) -> 대문자 알파벳
    - 혼합/판단불가 -> 그대로
    """
    if not text or not text.strip():
        return text

    def convert_single_content(single_content: str) -> str:
        """
        단일 토큰 변환
        - 숫자로 전체 변환 가능하면 숫자로 변환
        - 영문으로 전체 변환 가능하면 영문으로 변환
        - 둘 다 전체 변환 불가하면 그대로
        """
        raw = single_content
        s = raw.strip()
        s_nospace = s.replace(" ", "")

        # 이미 숫자/영문이면 그대로
        if re.fullmatch(r"\d+", s_nospace):
            return raw
        if re.fullmatch(r"[A-Z]+", s_nospace):
            return raw

        # 1) 숫자로 전체 변환 가능한지 체크
        if can_convert_to_number(s):
            # 단위 있는 수사면 파서로
            has_units = any(u in s_nospace for u in ("만", "천", "백", "십"))
            if has_units:
                out = str(convert_korean_number_to_arabic(s))
                logger.info(f"[] 숫자(단위) 변환: [{raw}] -> [{out}]")
                return out
            
            # 단위 없는 순차 숫자: 앞자리 0 유지해야 하므로 직접 이어붙이기
            digits = []
            remaining = s_nospace
            for _ in range(len(remaining) + 1):
                if not remaining:
                    break
                matched = False
                for k, a in sorted(KOREAN_NUMBER_MAP.items(), key=lambda x: len(x[0]), reverse=True):
                    if k in ("십", "백", "천", "만"):
                        continue
                    if remaining.startswith(k):
                        digits.append(a)
                        remaining = remaining[len(k):]
                        matched = True
                        break
                if not matched:
                    break

            if digits:
                out = "".join(digits)
                logger.info(f"[] 숫자(순차) 변환: [{raw}] -> [{out}]")
                return out

        # 2) 영문으로 전체 변환 가능한지 체크
        if can_convert_to_alphabet(s):
            out = s
            for korean, english in sorted(KOREAN_ALPHABET_MAP.items(), key=lambda x: len(x[0]), reverse=True):
                out = out.replace(korean, english)
            logger.info(f"[] 영문 변환: [{raw}] -> [{out}]")
            return out

        # 3) 둘 다 전체 변환 불가 -> 그대로
        return raw

    def repl(m: re.Match) -> str:
        inside = m.group(1)

        # 공백으로 구분된 여러 토큰이더라도 "괄호 하나" 단위로 판단
        # (전화번호처럼 [이에이치 공사공오 ...] 같은 케이스)
        parts = inside.split()
        if len(parts) >= 2:
            converted = [convert_single_content(p) for p in parts]
            return "[" + " ".join(converted) + "]"

        return "[" + convert_single_content(inside) + "]"

    return re.sub(r"\[([^\]]+)\]", repl, text)


def merge_phone_blocks(text: str) -> str:
    """
    (옵션) 변환된 결과에서 연속된 숫자 블록을 전화번호로 합치기
    예: [032] [720] [7400] -> [032-720-7400]
        [032] [745] [9747] -> [032-745-9747]
    - 완전히 숫자만인 [] 3개가 연속일 때만 합친다.
    """
    if not text or not text.strip():
        return text

    pattern = re.compile(r"\[(\d{2,4})\]\s*\[(\d{2,4})\]\s*\[(\d{3,4})\]")
    return pattern.sub(lambda m: f"[{m.group(1)}-{m.group(2)}-{m.group(3)}]", text)


def normalize_stt_text(text: str, *, merge_phones: bool = False) -> str:
    """
    권장 엔트리포인트
    - [] 안의 내용을 숫자/영문으로 변환 (이미 []로 감싸진 것만)
    - (옵션) 전화번호 합치기
    """
    out = convert_bracketed_content(text)
    
    if merge_phones:
        out = merge_phone_blocks(out)
    return out
