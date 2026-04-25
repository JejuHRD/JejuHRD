"""
reels_validators.py - Grok 영상 v2 프롬프트 검증 모듈

가이드 v2 원칙에 따라 프롬프트를 검증:
1. validate_no_format_mention(prompt) - 9:16/10s 등 UI 설정어가 본문에 섞이지 않았는지
2. validate_no_caption_request(prompt) - 자막 지시어가 없는지
3. validate_no_special_chars(text) - 특수기호(㎢ ² ℃ 등) 배제
4. validate_speech_constraints(narration_kr, max_duration_s) - 발화 시간 제약 추정 검증

사용:
    from reels_validators import validate_v2_prompt_full
    issues = validate_v2_prompt_full(prompt_text, segment_role="hook")
    if issues:
        for issue in issues:
            print(f"⚠️  {issue}")

각 함수는 문제점 리스트를 반환 (빈 리스트 = 통과).
"""

import re
from typing import List, Optional


# ── 1. UI 설정어 배제 검증 ──────────────────────────────────────
_FORMAT_PATTERNS = [
    r"\b9\s*:\s*16\b",
    r"\b16\s*:\s*9\b",
    r"\b1080\s*x\s*1920\b",
    r"\bvertical\s+format\b",
    r"\bvertical\s+video\b",
    r"\b\d+\s*[-\s]?second\s+(?:video|duration|length)\b",
    r"\b\d+\s*sec(?:ond)?s?\s+(?:long|duration)\b",
    r"\baspect\s+ratio\b",
    r"\bduration\s*:\s*\d+",
    r"\bportrait\s+orientation\b",
]

def validate_no_format_mention(prompt: str) -> List[str]:
    """프롬프트에 9:16, 10s, 비율, 길이 등 Grok UI 설정어가 섞이지 않았는지 검증.

    가이드 v2 원칙: 길이·비율은 Grok UI에서 직접 설정하므로 프롬프트에서 제외.

    Args:
        prompt: 검사할 프롬프트 텍스트

    Returns:
        발견된 위반 사항 리스트 (빈 리스트 = 통과)
    """
    issues = []
    for pattern in _FORMAT_PATTERNS:
        matches = re.findall(pattern, prompt, flags=re.IGNORECASE)
        for match in matches:
            issues.append(
                f"UI 설정어 발견: '{match}' — 길이·비율은 Grok UI에서 설정. 프롬프트에서 제거 필요."
            )
    return issues


# ── 2. 자막 지시어 배제 검증 ────────────────────────────────────
_CAPTION_REQUEST_PATTERNS = [
    r"\bon[-\s]?screen\s+text\b(?!\s*,?\s*no(?!t))",
    r"\bcaption\b(?!\s*s?\s*[,:]?\s*no(?!t))",
    r"\bsubtitle\b(?!\s*s?\s*[,:]?\s*no(?!t))",
    r"\btext\s+overlay\b",
    r"\bdisplay\s+text\b",
    r"\b\d+[-\s]\d+s\s*:\s*\"",
    r"\btitle\s+card\b",
]

_NEGATION_PHRASES = [
    "no on-screen text",
    "no captions",
    "no caption",
    "no subtitles",
    "no text overlay",
]

def validate_no_caption_request(prompt: str) -> List[str]:
    """자막을 요청하는 지시어가 프롬프트에 없는지 검증.

    가이드 v2 원칙: 자막은 Vrew 후반 작업에서 처리.
    프롬프트에는 'no on-screen text, no captions' 같은 배제 문구만 허용.

    Args:
        prompt: 검사할 프롬프트 텍스트

    Returns:
        발견된 위반 사항 리스트
    """
    issues = []
    prompt_lower = prompt.lower()

    # 배제 문구가 명시되어 있으면 자막 요청이 아님
    has_negation = any(neg in prompt_lower for neg in _NEGATION_PHRASES)
    if has_negation:
        # 배제 문구가 있어도 추가 자막 요청이 있는지 확인
        for pattern in _CAPTION_REQUEST_PATTERNS:
            matches = re.findall(pattern, prompt, flags=re.IGNORECASE)
            for match in matches:
                # 배제 문구의 일부면 통과
                if "no" not in match.lower() and "not" not in match.lower():
                    issues.append(
                        f"자막 지시어 의심: '{match}' — Vrew에서 처리할 자막은 프롬프트에서 제외."
                    )
        return issues

    # 배제 문구가 없으면 모든 자막 패턴이 위반
    for pattern in _CAPTION_REQUEST_PATTERNS:
        matches = re.findall(pattern, prompt, flags=re.IGNORECASE)
        for match in matches:
            issues.append(
                f"자막 지시어: '{match}' — 'no on-screen text, no captions' 명시 필요 또는 제거."
            )

    if not has_negation:
        issues.append(
            "자막 배제 명시 누락: '[AUDIO & NARRATION]' 블록에 'no on-screen text, no captions' 추가 필요."
        )

    return issues


# ── 3. 특수기호 배제 검증 ───────────────────────────────────────
_FORBIDDEN_UNICODE_CHARS = {
    "㎢": "km2 또는 제곱킬로미터",
    "㎡": "m2 또는 제곱미터",
    "㎘": "kL 또는 킬로리터",
    "㏊": "ha 또는 헥타르",
    "㎍": "ug 또는 마이크로그램",
    "㎏": "kg",
    "㎜": "mm",
    "㎞": "km",
    "℃": "도 또는 C",
    "℉": "F",
    "‰": "퍼밀",
    "²": "2 (위첨자 → 일반 숫자)",
    "³": "3 (위첨자 → 일반 숫자)",
    "¹": "1 (위첨자 → 일반 숫자)",
    "₁": "1 (아래첨자 → 일반 숫자)",
    "₂": "2 (아래첨자 → 일반 숫자)",
    "±": "약 또는 plus minus",
    "×": "x 또는 곱하기",
    "÷": "나누기",
    "≈": "약 또는 approximately",
    "≠": "다름 또는 not equal",
    "∞": "무한",
    "Ω": "옴 또는 ohm",
    "§": "조 또는 section",
    "¶": "단락",
    "†": "(제거)",
    "‡": "(제거)",
}

def validate_no_special_chars(text: str) -> List[str]:
    """텍스트(자막·나레이션 등)에 폰트 미지원 특수기호가 없는지 검증.

    가이드 v2 원칙: 자막 렌더링에서 깨질 수 있는 복합 유니코드는 평문으로 변환.

    Args:
        text: 검사할 텍스트

    Returns:
        발견된 특수기호와 권장 대체안 리스트
    """
    issues = []
    for char, replacement in _FORBIDDEN_UNICODE_CHARS.items():
        if char in text:
            issues.append(
                f"특수기호 '{char}' 발견 → 대체 권장: '{replacement}'"
            )
    return issues


# ── 4. 발화 시간 제약 검증 ──────────────────────────────────────
# 한국어 발화 속도 추정 상수
_SYLLABLE_PER_SEC_NORMAL = 5.5   # 보통 속도
_SYLLABLE_PER_SEC_SNAPPY = 6.5   # 광고·뉴스 톤 빠른 속도

def _count_korean_syllables(text: str) -> int:
    """한국어 음절 수 카운트 (한글 1글자 = 1음절).

    공백·문장부호·영문·숫자는 제외.
    """
    return sum(1 for ch in text if "\uac00" <= ch <= "\ud7a3")


def validate_speech_constraints(
    narration_kr: str,
    max_duration_s: float = 7.0,
    pace: str = "snappy",
) -> List[str]:
    """한국어 나레이션·대사가 시간 제약 안에 발화 가능한지 추정 검증.

    Args:
        narration_kr: 한국어 텍스트
        max_duration_s: 최대 허용 발화 시간 (초). 세그먼트 1·2는 10s, 세그먼트 3은 7s 권장
        pace: "normal" 또는 "snappy"

    Returns:
        시간 초과 또는 음절 부족 경고 리스트
    """
    issues = []
    syllables = _count_korean_syllables(narration_kr)
    rate = _SYLLABLE_PER_SEC_SNAPPY if pace == "snappy" else _SYLLABLE_PER_SEC_NORMAL
    estimated_duration = syllables / rate

    if estimated_duration > max_duration_s:
        issues.append(
            f"발화 시간 초과 추정: {syllables}음절 / {rate} 음절/초 = "
            f"약 {estimated_duration:.1f}초 (제한: {max_duration_s}초). "
            f"대사를 약 {int((max_duration_s * rate))}음절 이하로 줄이세요."
        )
    elif estimated_duration < max_duration_s * 0.4:
        issues.append(
            f"발화 시간 짧음 추정: {syllables}음절 / {rate} 음절/초 = "
            f"약 {estimated_duration:.1f}초 (제한: {max_duration_s}초). "
            f"내용이 너무 짧아 영상 시간이 남을 수 있습니다."
        )

    return issues


# ── 통합 검증 ────────────────────────────────────────────────────
def validate_v2_prompt_full(
    prompt: str,
    narration_kr: Optional[str] = None,
    segment_role: str = "hook",
) -> List[str]:
    """v2 프롬프트 통합 검증 — 4개 검증 함수를 한 번에 실행.

    Args:
        prompt: Grok에 입력할 프롬프트 전문
        narration_kr: 한국어 나레이션·대사 (선택)
        segment_role: "hook" / "demo" / "cta" — CTA는 발화 시간 제약이 7초

    Returns:
        모든 위반 사항 통합 리스트 (빈 리스트 = 모두 통과)
    """
    all_issues = []

    # 1. UI 설정어 검증
    all_issues.extend(validate_no_format_mention(prompt))

    # 2. 자막 지시어 검증
    all_issues.extend(validate_no_caption_request(prompt))

    # 3. 특수기호 검증 (프롬프트 + 나레이션 모두)
    all_issues.extend(validate_no_special_chars(prompt))
    if narration_kr:
        all_issues.extend(validate_no_special_chars(narration_kr))

    # 4. 발화 시간 검증 (나레이션이 있을 때만)
    if narration_kr:
        if segment_role == "cta":
            all_issues.extend(
                validate_speech_constraints(narration_kr, max_duration_s=7.0, pace="snappy")
            )
        else:
            all_issues.extend(
                validate_speech_constraints(narration_kr, max_duration_s=10.0, pace="snappy")
            )

    return all_issues


# ── CLI 테스트 ──────────────────────────────────────────────────
if __name__ == "__main__":
    # 자체 테스트
    test_prompt = """
    [SCENE & LOCATION]
    9:16 vertical aerial view over Jeju oreum, 1,283㎢ area.

    [AUDIO & NARRATION]
    Bright Korean voiceover. On-screen text appears at 0-3s.
    """
    test_narration = "사람 손으론 반나절, 드론은 단 몇 분! 제주 오름 꼭대기까지 건축자재를 실어나르는 배송드론의 시대, 대한민국 최대 드론 특별자유화구역 제주가 앞서 갑니다."

    print("=== 통합 검증 테스트 (의도적 위반 케이스) ===")
    issues = validate_v2_prompt_full(test_prompt, test_narration, segment_role="hook")
    for issue in issues:
        print(f"⚠️  {issue}")
    print(f"\n총 {len(issues)}개 이슈 발견.")
