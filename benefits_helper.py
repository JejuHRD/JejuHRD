"""
혜택 문구 자동 결정 모듈

'26년 산업구조변화대응 등 특화훈련 사업운영지침 기반 규정:

[자기부담금]
- 최초 1회: 자부담 최대 10% (훈련비 구간별 금액 차등)
- 2회차 이후 140시간 미만 단기과정: 자부담 최대 10% (횟수 제한 없음)
- 2회차 이후 140시간 이상 일반과정: 일반 내일배움카드 자부담 비율 적용 (최대 55%)

[계좌차감 한도]
- 일반과정(140시간 이상): 최대 200만원까지 계좌차감
- 단기과정(140시간 미만): 최대 100만원까지 계좌차감

[훈련장려금]
- 월 20만원: 140시간 이상 과정, 훈련장려금 지급대상에 해당하는 경우

[특별훈련수당] ← '26년 핵심 혜택
- AI 전환 대응 과정 또는 육성산업·직종 훈련과정 중 350시간 이상(1일 5시간 이상)
- 훈련장려금에 추가로 지급
- 지역별 차등: 수도권 월 최대 10만원, 비수도권 20만원, 인구감소지역 30만원
- 산정: 단위기간 출석률 80% 이상 시, 출석일수 × 5천원/1만원/1만5천원
- 제주는 비수도권 → 월 최대 20만원 (출석일수 × 1만원)

[직업훈련 생계비 대부]
- 140시간 이상 참여 중인 비정규직/실업자/무급휴직자/자영업자
- 월 200만원 이내(총 1,000만원 한도), 연 1% 금리
"""

import re


# ─── 제주 지역 설정 ───
# 제주는 비수도권에 해당 (인구감소지역 아님)
# 인구감소지역은 행정안전부고시 제2024-15호에 따름
REGION = "비수도권"  # "수도권" | "비수도권" | "인구감소지역"

SPECIAL_ALLOWANCE_MAP = {
    "수도권": {"월최대": "10만원", "일당": "5천원"},
    "비수도권": {"월최대": "20만원", "일당": "1만원"},
    "인구감소지역": {"월최대": "30만원", "일당": "1만5천원"},
}


def parse_course_hours(course_data):
    """
    과정 데이터에서 총 훈련시간(숫자)을 추출합니다.

    Returns:
        int or None
    """
    course_man = course_data.get("courseMan", "")
    if course_man:
        try:
            return int(course_man)
        except (ValueError, TypeError):
            pass

    time_str = course_data.get("time", "")
    if time_str:
        match = re.search(r'(\d+)\s*시간', time_str)
        if match:
            return int(match.group(1))

    return None


def is_long_course(course_data):
    """140시간 이상 과정인지 여부 (훈련장려금 기준)"""
    hours = parse_course_hours(course_data)
    if hours is None:
        return None
    return hours >= 140


def is_special_allowance_eligible(course_data):
    """
    350시간 이상 과정인지 여부 (특별훈련수당 기준)

    지침 근거: 총 훈련시간 350시간 이상, 1일 훈련시간 5시간 이상일 것
    + AI 전환 대응 과정 또는 육성산업·직종 훈련과정일 것
    (과정 유형은 운영기관이 지정하므로, 시간 기준만 코드에서 판별)
    """
    hours = parse_course_hours(course_data)
    if hours is None:
        return None
    return hours >= 350


def get_special_allowance_info():
    """현재 지역(제주) 기준 특별훈련수당 정보"""
    return SPECIAL_ALLOWANCE_MAP[REGION]


def get_badge_text(course_data):
    """커버 이미지 상단 뱃지 텍스트"""
    if is_special_allowance_eligible(course_data):
        return "자부담 10% + 훈련수당"
    return "자부담 10%"


def get_benefits_text(course_data):
    """
    과정 시간에 따른 혜택 요약 (카드뉴스용, 파이프 구분)

    - 350시간 이상: 자부담 10% + 훈련장려금 월 20만원 + 특별훈련수당 월 최대 30만원
    - 140시간 이상: 자부담 10% + 훈련장려금 월 20만원
    - 140시간 미만: 자부담 10%
    """
    special = is_special_allowance_eligible(course_data)
    long = is_long_course(course_data)
    allowance = get_special_allowance_info()

    if special is True:
        return f"자부담 10% | 장려금 월 20만원 + 수당 월 최대 {allowance['월최대']}"
    elif long is True:
        return "자부담 10% | 훈련장려금 월 최대 20만원"
    elif long is False:
        return "자부담 10%"
    else:
        return "자부담 10% | 훈련장려금은 140시간 이상 과정만 해당"


def get_benefits_detail_lines(course_data):
    """블로그용 혜택 상세 설명 라인"""
    special = is_special_allowance_eligible(course_data)
    long = is_long_course(course_data)
    hours = parse_course_hours(course_data)
    allowance = get_special_allowance_info()

    lines = []
    lines.append("- 최초 참여 시 자부담 최대 10%로 배울 수 있어요")

    if special is True:
        lines.append(
            f"- 매달 훈련장려금 최대 20만원 + 특별훈련수당 최대 {allowance['월최대']}을 "
            f"받을 수 있어요 ({hours}시간 과정)"
        )
        lines.append(
            f"  (출석 80% 이상 시, 출석일수 × {allowance['일당']}으로 산정)"
        )
    elif long is True:
        lines.append(f"- 매달 훈련장려금 최대 20만원을 받을 수 있어요 ({hours}시간 과정)")
    elif long is False:
        lines.append(
            f"- {hours}시간 단기과정이라 훈련장려금은 없지만, 부담 없이 빠르게 배울 수 있어요"
        )
    else:
        lines.append("- 140시간 이상 과정은 훈련장려금 월 최대 20만원")
        lines.append("- 350시간 이상 과정은 특별훈련수당 추가 지급 (제주: 월 최대 20만원)")

    return lines


def get_cost_info_text(course_data):
    """블로그 인포박스용 비용 안내 텍스트"""
    special = is_special_allowance_eligible(course_data)
    long = is_long_course(course_data)
    allowance = get_special_allowance_info()

    if special is True:
        return (
            f"이 과정은 최초 참여 시 **자부담 최대 10%**만 내면 돼요.\n"
            f"계좌에서 최대 200만원까지 차감되고, 나머지는 정부가 지원합니다.\n"
            f"2회차부터 일반과정은 내일배움카드 기준 자부담 비율이 적용돼요.\n"
            f"자세한 자부담 금액은 고용24에서 확인해주세요!"
        )
    elif long is True:
        return (
            "이 과정은 최초 참여 시 **자부담 최대 10%**만 내면 돼요.\n"
            "계좌에서 최대 200만원까지 차감되고, 나머지는 정부가 지원합니다.\n"
            "2회차부터 일반과정은 내일배움카드 기준 자부담 비율이 적용돼요.\n"
            "자세한 자부담 금액은 고용24에서 확인해주세요!"
        )
    elif long is False:
        return (
            "이 과정은 **자부담 최대 10%**만 내면 돼요.\n"
            "140시간 미만 단기과정은 횟수 제한 없이 자부담 최대 10%로 참여할 수 있어요!\n"
            "계좌에서 최대 100만원까지 차감됩니다."
        )
    else:
        return "이 과정은 최초 참여 시 **자부담 최대 10%**만 내면 돼요."


def get_living_expense_loan_text(course_data):
    """
    직업훈련 생계비 대부 안내 텍스트 (140시간 이상 과정만 해당)

    지침 근거 (p.21):
    - 140시간 이상 참여 중인 비정규직/실업자/무급휴직자/자영업자
    - 월 200만원 이내(총 1,000만원), 연 1% 금리
    """
    long = is_long_course(course_data)

    if long is True:
        return (
            "훈련 기간 동안 생활비가 걱정되시나요? "
            "140시간 이상 훈련에 참여 중인 실업자, 비정규직 근로자 등은 "
            "**직업훈련 생계비 대부**(월 200만원 이내, 연 1% 금리)도 "
            "신청할 수 있어요. 자세한 내용은 고용센터에 문의해주세요."
        )
    return None
