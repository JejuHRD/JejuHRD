"""
혜택 문구 자동 결정 모듈

특화훈련 자부담/훈련장려금 규정:
- 특화훈련은 최초 1회 자부담 10%
- 훈련장려금(월 최대 20만원): 140시간 이상 과정 해당

※ 고용24 목록 API에는 훈련시간 필드가 없으므로,
   모든 특화훈련 과정에 공통 혜택 문구를 표시합니다.
"""


def get_badge_text(course_data):
    """커버 이미지 상단 뱃지 텍스트"""
    return "자부담 10%"


def get_benefits_text(course_data):
    """
    혜택 요약 (카드뉴스용, 파이프 구분)
    """
    return "자부담 10% | 훈련장려금 월 최대 20만원 (140시간 이상 과정)"


def get_benefits_detail_lines(course_data):
    """블로그용 혜택 상세 설명 라인"""
    lines = [
        "- 최초 참여 시 자부담 10%로 배울 수 있어요",
        "- 140시간 이상 과정은 매달 훈련장려금 최대 20만원을 받을 수 있어요",
        "- 정확한 자부담 금액은 고용24에서 확인해주세요",
    ]
    return lines


def get_cost_info_text(course_data):
    """블로그 인포박스용 비용 안내 텍스트"""
    real_cost = course_data.get("realCost", "")
    course_cost = course_data.get("courseCost", "")

    parts = []
    parts.append("이 과정은 최초 참여 시 **자부담 10%**만 내면 돼요.")

    if real_cost:
        parts.append(f"실제 훈련비는 **{real_cost}**이며, 나머지는 국비로 지원됩니다.")
    elif course_cost:
        parts.append(f"전체 수강비 {course_cost} 중 자부담 10%만 부담하면 돼요.")

    parts.append("자세한 자부담 금액은 고용24에서 확인해주세요!")
    return "\n".join(parts)
