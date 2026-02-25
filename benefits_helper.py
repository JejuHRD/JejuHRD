"""
혜택 문구 자동 결정 모듈

특화훈련 훈련시간별 혜택 체계 (2026년 사업운영지침 기준):

[140시간 미만 - 단기과정]
- 자부담 10% (횟수 무관)
- 훈련장려금: 없음
- 특별훈련수당: 없음

[140시간 이상 ~ 350시간 미만 - 일반과정]
- 자부담: 최초 10%, 2회차부터 최대 55%
- 훈련장려금: 월 20만원 (출석 80% 이상)
- 특별훈련수당: 없음

[350시간 이상 - 장기과정]
- 자부담: 최초 10%, 2회차부터 최대 55%
- 훈련장려금: 월 20만원
- 특별훈련수당: 월 최대 20만원 (비수도권 기준, 제주 해당)
  → 합계 월 최대 40만원
"""


def get_total_hours(course_data):
    """총 훈련시간 반환"""
    h = course_data.get("totalHours", 0)
    try:
        return int(h)
    except (ValueError, TypeError):
        return 0


def get_course_type(course_data):
    """
    과정 유형 판별.
    Returns: "short" | "general" | "long" | "unknown"
    """
    hours = get_total_hours(course_data)
    if hours <= 0:
        return "unknown"
    if hours < 140:
        return "short"
    if hours < 350:
        return "general"
    return "long"


def get_badge_text(course_data):
    """커버 이미지 상단 뱃지 텍스트"""
    return "자부담 10%"


def get_benefits_text(course_data):
    """
    카드뉴스 '이런 혜택이!' 영역 - 훈련시간 맞춤형
    """
    ctype = get_course_type(course_data)
    hours = get_total_hours(course_data)

    if ctype == "long":
        return (f"국민내일배움카드 소지자라면 자부담 10%!\n"
                f"훈련장려금 + 특별훈련수당 월 최대 40만원")
    elif ctype == "general":
        return (f"국민내일배움카드 소지자라면 자부담 10%!\n"
                f"훈련장려금 월 최대 20만원")
    elif ctype == "short":
        return "국민내일배움카드 소지자라면 자부담 10%만으로 교육 참여 가능!"
    else:
        return "국민내일배움카드 소지자라면 자부담 10%만으로 교육 참여 가능!"


def get_benefits_footnote(course_data=None):
    """
    카드뉴스 하단 ※ 주석 문구 - 훈련시간 맞춤형
    """
    if course_data is None:
        return "※ 훈련장려금·수당은 과정 시간 및 출석률 등 조건에 따라 지급"

    ctype = get_course_type(course_data)

    if ctype == "long":
        return "※ 장려금·수당은 출석 80% 이상 시 지급 | 예산 사정에 따라 변동 가능"
    elif ctype == "general":
        return "※ 훈련장려금은 출석 80% 이상 시 지급"
    elif ctype == "short":
        return "※ 단기과정은 횟수 제한 없이 자부담 10%로 참여 가능"
    else:
        return "※ 훈련장려금·수당은 과정 시간 및 출석률 등 조건에 따라 지급"


def get_step3_text(course_data):
    """카드뉴스 STEP3 문구 - 훈련시간 맞춤형"""
    ctype = get_course_type(course_data)

    if ctype == "long":
        return ("훈련장려금 + 특별수당 받기",
                "자부담 10% + 월 최대 40만원 지원!\n배우면서 경제적 부담도 덜어요")
    elif ctype == "general":
        return ("훈련장려금 받으며 배우기",
                "자부담 10% + 월 최대 20만원 장려금!\n출석 80% 이상이면 매달 지급돼요")
    elif ctype == "short":
        return ("부담 없이 빠르게 배우기",
                "자부담 10%로 부담 없이\n신기술 트렌드에 맞는 교육 참여 가능!")
    else:
        return ("혜택 받으며 배우기",
                "자부담 10%로 부담 없이\n신기술 트렌드에 맞는 교육 참여 가능!")


def get_benefits_detail_lines(course_data):
    """블로그용 혜택 상세 설명 라인"""
    ctype = get_course_type(course_data)
    hours = get_total_hours(course_data)

    lines = ["- 최초 참여 시 자부담 10%로 배울 수 있어요"]

    if ctype == "long":
        lines.append(f"- 총 {hours}시간 장기과정으로, **훈련장려금 월 20만원** + **특별훈련수당 월 최대 20만원**을 받을 수 있어요")
        lines.append("- 합계 **월 최대 40만원**까지 지원! (출석 80% 이상 시)")
    elif ctype == "general":
        lines.append(f"- 총 {hours}시간 과정으로, **훈련장려금 월 최대 20만원**을 받을 수 있어요 (출석 80% 이상)")
    elif ctype == "short":
        lines.append(f"- 총 {hours}시간 단기과정이라 훈련장려금은 없지만, 횟수 제한 없이 자부담 10%로 참여할 수 있어요")

    lines.append("- 자세한 내용은 고용24에서 확인해주세요")
    return lines


def get_cost_info_text(course_data):
    """블로그 인포박스용 비용 안내 텍스트"""
    self_cost = course_data.get("selfCost", "")
    course_cost = course_data.get("courseCost", "")
    ctype = get_course_type(course_data)

    parts = ["이 과정은 최초 참여 시 **자부담 10%**만 내면 돼요."]

    if self_cost and course_cost:
        parts.append(f"수강비 {course_cost} 중 자부담금은 **{self_cost}**이며, 나머지는 국비로 지원됩니다.")

    if ctype == "long":
        parts.append("350시간 이상 장기과정이라 **훈련장려금 + 특별훈련수당 월 최대 40만원**까지 받을 수 있어요!")
    elif ctype == "general":
        parts.append("140시간 이상 과정이라 **훈련장려금 월 최대 20만원**도 받을 수 있어요!")
    elif ctype == "short":
        parts.append("단기과정이라 훈련장려금은 없지만, 횟수 제한 없이 부담 없이 참여할 수 있어요!")

    parts.append("자세한 자부담 금액은 고용24에서 확인해주세요!")
    return "\n".join(parts)
