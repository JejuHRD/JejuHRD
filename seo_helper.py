"""
SEO 및 마케팅 최적화 헬퍼 모듈

블로그/인스타그램 콘텐츠의 검색 노출과 도달률을 높이기 위한 유틸리티.

기능:
- 과정 제목에서 검색 키워드 자동 추출 및 매핑
- 네이버 블로그 SEO 최적화 제목 생성
- 공감형 도입부 자동 생성 (과정별 차별화)
- 인스타그램 해시태그 전략 (대형+중소형+지역 믹스)
- 인스타그램 캡션 자동 생성
- 게시 타이밍 권장 안내
"""

import re
from datetime import datetime, timedelta


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 키워드 매핑 시스템
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 과정 제목에 포함된 키워드 → 검색량 높은 키워드 매핑
KEYWORD_MAP = {
    # AI/디지털 분야
    "AI": ["AI교육", "인공지능교육", "AI활용", "AI자격증"],
    "인공지능": ["AI교육", "인공지능교육", "AI활용"],
    "영상": ["영상편집교육", "영상제작", "유튜브편집", "프리미어프로"],
    "편집": ["영상편집교육", "편집디자인"],
    "디자인": ["디자인교육", "디지털디자인", "웹디자인", "UI디자인"],
    "디지털": ["디지털교육", "디지털전환"],
    "UX": ["UIUX교육", "UX디자인"],
    "UI": ["UIUX교육", "UI디자인", "웹디자인"],
    "웹": ["웹디자인", "웹개발", "홈페이지제작"],
    "출판": ["출판디자인", "편집디자인", "전자책"],
    "멀티미디어": ["멀티미디어교육", "콘텐츠제작"],
    "콘텐츠": ["콘텐츠제작", "콘텐츠마케팅", "SNS콘텐츠"],
    "마케팅": ["디지털마케팅", "콘텐츠마케팅", "SNS마케팅"],
    "데이터": ["데이터분석", "빅데이터", "데이터활용"],
    "프로그래밍": ["코딩교육", "프로그래밍교육"],
    "코딩": ["코딩교육", "프로그래밍교육"],
    "파이썬": ["파이썬교육", "코딩교육"],
    "3D": ["3D모델링", "3D프린팅"],
    "그래픽": ["그래픽디자인", "포토샵교육"],
    "포토샵": ["포토샵교육", "그래픽디자인"],
    "일러스트": ["일러스트교육", "일러스트레이터"],
    "사진": ["사진촬영교육", "사진편집"],
    "드론": ["드론자격증", "드론교육"],
    "바리스타": ["바리스타자격증", "바리스타교육"],
    "요리": ["요리교육", "조리사자격증"],
    "조리": ["조리사자격증", "요리교육"],
    "관광": ["관광교육", "관광가이드"],
    "호텔": ["호텔리어교육", "호텔취업"],
    "서비스": ["서비스교육", "고객응대"],
    "회계": ["회계교육", "전산회계"],
    "사무": ["사무행정", "컴퓨터활용"],
    "컴퓨터": ["컴퓨터교육", "ITQ", "컴퓨터활용"],
    "엑셀": ["엑셀교육", "컴퓨터활용"],
    "OA": ["OA교육", "사무자동화"],
    "자동화": ["업무자동화", "RPA"],
    "숏폼": ["숏폼제작", "릴스제작", "틱톡영상"],
    "유튜브": ["유튜브크리에이터", "유튜브편집"],
    "SNS": ["SNS마케팅", "SNS콘텐츠"],
}

# 공통 검색 키워드 (모든 과정에 적용)
COMMON_SEARCH_KEYWORDS = [
    "국비지원무료교육",
    "국민내일배움카드",
    "제주교육",
    "제주무료교육",
    "국비지원",
]

# 인스타그램 해시태그 풀
INSTAGRAM_HASHTAGS = {
    # 대형 (검색량 높음, 경쟁 높음) - 5~7개
    "large": [
        "#국비지원", "#무료교육", "#국민내일배움카드", "#자기계발",
        "#직무교육", "#국비지원무료교육", "#배움", "#재취업",
        "#이직준비", "#직업훈련",
    ],
    # 중소형 (적정 경쟁) - 5~7개
    "medium": [
        "#국민내일배움카드신청", "#국비지원교육", "#직업훈련포털",
        "#고용24", "#HRD", "#취업준비생", "#경력개발",
        "#무료자격증", "#스킬업", "#리스킬링",
    ],
    # 지역 태그 (필수) - 3~5개
    "local": [
        "#제주", "#제주시", "#제주교육", "#제주취업",
        "#제주도생활", "#제주직업훈련", "#제주이직",
        "#제주무료교육", "#제주자기계발",
    ],
}

# 분야별 인스타그램 해시태그
FIELD_HASHTAGS = {
    "AI": ["#AI교육", "#인공지능", "#AI활용", "#디지털전환", "#AI시대"],
    "영상": ["#영상편집", "#프리미어프로", "#영상제작", "#유튜브", "#영상크리에이터"],
    "디자인": ["#디자인교육", "#디지털디자인", "#UIUX", "#피그마", "#웹디자인"],
    "출판": ["#출판디자인", "#편집디자인", "#인디자인", "#전자책", "#북디자인"],
    "멀티미디어": ["#멀티미디어", "#콘텐츠제작", "#크리에이터", "#미디어"],
    "콘텐츠": ["#콘텐츠제작", "#SNS마케팅", "#콘텐츠크리에이터"],
    "마케팅": ["#디지털마케팅", "#SNS마케팅", "#콘텐츠마케팅"],
    "데이터": ["#데이터분석", "#빅데이터", "#데이터사이언스"],
    "코딩": ["#코딩교육", "#개발자", "#프로그래밍"],
    "숏폼": ["#숏폼", "#릴스", "#숏폼제작", "#틱톡"],
}

# 공감형 도입부 템플릿 (과정 분야별)
EMPATHY_INTROS = {
    "AI": [
        "요즘 어디를 가든 AI 이야기가 빠지지 않죠. \"나도 AI를 배워야 하나?\" 고민만 하다가 시간이 흘러가고 있다면, 지금이 딱 시작할 타이밍이에요.",
        "ChatGPT, 미드저니, AI 영상 생성... 세상은 빠르게 바뀌고 있는데, 어디서부터 배워야 할지 막막하셨죠? 제주에서 체계적으로 배울 수 있는 기회가 열렸어요.",
        "\"AI가 내 일자리를 대체한다\"는 뉴스, 불안하기만 하셨나요? AI를 활용하는 쪽에 서면 오히려 기회가 됩니다. 제주에서 그 첫걸음을 시작해보세요.",
    ],
    "영상": [
        "유튜브, 릴스, 숏폼... 영상이 대세인 건 알겠는데, 혼자 독학하기엔 너무 막막하셨죠? 촬영부터 편집, AI 활용까지 한번에 배울 수 있는 과정이 있어요.",
        "\"나도 영상 하나 만들어볼까?\" 한번쯤 생각해보셨을 거예요. 스마트폰 하나로 시작해서 프로 수준까지, 제주에서 제대로 배워보세요.",
        "영상 편집 배우고 싶었는데 비용이 걱정이었다면, 좋은 소식이에요. 자부담 10%로 전문 영상 제작 기술을 배울 수 있는 과정이 제주에서 열려요.",
    ],
    "디자인": [
        "피그마, 포토샵, UI/UX... 디자인 도구는 많은데 뭘 어떻게 배워야 할지 막막하셨나요? 현업에서 바로 쓸 수 있는 스킬을 체계적으로 알려드려요.",
        "이직을 준비하면서 \"디자인 스킬이 있으면 좋겠다\" 생각해보신 적 있나요? 비전공자도 부담 없이 시작할 수 있는 과정이 제주에서 열립니다.",
        "디지털 시대에 디자인 감각은 모든 직군에서 필요해지고 있어요. 제주에서 체계적으로 디자인 역량을 키워보세요.",
    ],
    "출판": [
        "\"내 책을 한 번 만들어보고 싶다\"는 꿈, 생각보다 가까이 있어요. AI와 전문 편집 도구를 활용하면 누구나 출판제작자가 될 수 있습니다.",
        "전자책, 오디오북, 독립출판... 출판의 세계가 달라지고 있어요. 기획부터 제작, 유통까지 한번에 배울 수 있는 기회를 놓치지 마세요.",
    ],
    "default": [
        "새로운 기술을 배우고 싶은데, 어디서 시작해야 할지 막막하셨나요? 국민내일배움카드만 있으면 자부담 10%로 바로 시작할 수 있는 과정이 열렸어요.",
        "이직을 고민하거나, 새로운 분야에 도전하고 싶은 마음... 누구나 한번쯤 있죠. 제주에서 부담 없이 새로운 기술을 배울 수 있는 기회를 소개합니다.",
        "경력을 쌓고 싶은데 교육비가 부담이셨나요? 국민내일배움카드로 자부담 10%만 내고 전문 기술을 배울 수 있어요. 제주에서 만나는 특화훈련을 확인해보세요.",
    ],
}


def detect_course_field(title):
    """
    과정 제목에서 분야를 감지합니다.

    Returns:
        str: 분야 키 (예: 'AI', '영상', '디자인' 등)
    """
    title_upper = title.upper()

    # 우선순위 순서대로 체크
    field_keywords = {
        "AI": ["AI", "인공지능", "챗GPT", "CHATGPT", "머신러닝", "딥러닝"],
        "영상": ["영상", "비디오", "유튜브", "숏폼", "프리미어", "에프터이펙트", "촬영"],
        "디자인": ["디자인", "UI", "UX", "피그마", "FIGMA", "웹디자인"],
        "출판": ["출판", "인디자인", "편집디자인", "전자책", "EPUB"],
        "멀티미디어": ["멀티미디어"],
        "콘텐츠": ["콘텐츠", "크리에이터"],
        "마케팅": ["마케팅"],
        "데이터": ["데이터", "빅데이터", "분석"],
        "코딩": ["코딩", "프로그래밍", "파이썬", "개발"],
    }

    for field, keywords in field_keywords.items():
        for kw in keywords:
            if kw in title_upper:
                return field

    return "default"


def extract_seo_keywords(course_data):
    """
    과정 데이터에서 SEO 키워드를 추출합니다.

    키워드 소스:
    1. 과정명 (title)
    2. 훈련목표 (trainingGoal) — 크롤링 데이터
    3. NCS직종명 (ncsName)
    4. 공통 키워드

    Returns:
        list[str]: 검색 최적화 키워드 리스트
    """
    title = course_data.get("title", "")
    training_goal = course_data.get("trainingGoal", "")
    ncs_name = course_data.get("ncsName", "")
    keywords = set()

    # 키워드 매핑 대상 텍스트 (제목 + 훈련목표 + NCS직종)
    source_text = f"{title} {training_goal} {ncs_name}".upper()

    for trigger, mapped in KEYWORD_MAP.items():
        if trigger.upper() in source_text:
            keywords.update(mapped)

    # 공통 키워드 추가
    keywords.update(COMMON_SEARCH_KEYWORDS)

    # 연도 키워드
    year = datetime.now().year
    keywords.add(f"{year}국비지원")
    keywords.add(f"{year}국민내일배움카드")

    return sorted(keywords)


def generate_seo_title(course_data):
    """
    네이버 블로그 SEO에 최적화된 제목을 생성합니다.

    네이버 검색 알고리즘 반영 포인트:
    - 제목에 핵심 검색 키워드 포함
    - 30~40자 내외 (너무 길면 잘림)
    - [지역] 태그로 지역 검색 유입
    - 혜택 키워드로 클릭율 향상

    Returns:
        str: SEO 최적화 블로그 제목
    """
    title = course_data.get("title", "")
    field = detect_course_field(title)
    year = datetime.now().year

    # 과정명에서 핵심 키워드 추출
    core_keyword = title
    if len(core_keyword) > 20:
        core_keyword = core_keyword[:20]

    # 분야별 SEO 키워드
    seo_kw_map = {
        "AI": "AI교육",
        "영상": "영상편집교육",
        "디자인": "디지털디자인교육",
        "출판": "출판디자인교육",
        "멀티미디어": "멀티미디어교육",
        "콘텐츠": "콘텐츠제작교육",
        "마케팅": "디지털마케팅교육",
        "데이터": "데이터분석교육",
        "코딩": "코딩교육",
    }
    seo_keyword = seo_kw_map.get(field, "직업훈련")

    # 제목 패턴 다양화
    patterns = [
        f"[제주 국비지원] {core_keyword} | 자부담 10% 특화훈련",
        f"{year} 제주 {seo_keyword} 추천 - {core_keyword} (자부담 10%)",
        f"제주 {core_keyword} 무료교육 | 국민내일배움카드 자부담 10%로 배우기",
    ]

    # 해시를 이용해 과정마다 다른 패턴 선택 (같은 과정은 항상 같은 패턴)
    pattern_index = hash(title) % len(patterns)
    return patterns[pattern_index]


def generate_empathy_intro(course_data):
    """
    독자 공감형 도입부를 생성합니다.

    네이버 블로그 알고리즘 반영 포인트:
    - 도입부 200자 이상 → 체류 시간 증가
    - 과정별 차별화된 문장 → 중복 콘텐츠 페널티 회피
    - 검색 키워드 자연스럽게 포함

    Returns:
        str: 공감형 도입부 텍스트
    """
    title = course_data.get("title", "")
    field = detect_course_field(title)
    institution = course_data.get("institution", "")
    period = course_data.get("period", "")

    # 분야별 도입부 선택
    intros = EMPATHY_INTROS.get(field, EMPATHY_INTROS["default"])
    intro_index = hash(title) % len(intros)
    base_intro = intros[intro_index]

    # 과정 정보로 커스터마이징
    year = datetime.now().year
    extra = f"\n\n{year}년, **{institution}**에서 진행하는 이 과정은 국민내일배움카드만 있으면 **자부담 10%**로 참여할 수 있어요."

    if period:
        extra += f" 교육 기간은 {period}이니, 일정 확인하고 서둘러 신청해보세요!"
    else:
        extra += " 모집 기간이 정해져 있으니, 관심 있다면 서둘러 확인해보세요!"

    return base_intro + extra


def generate_blog_hashtags(course_data):
    """
    네이버 블로그용 해시태그를 생성합니다.

    Returns:
        str: 해시태그 문자열
    """
    title = course_data.get("title", "")
    field = detect_course_field(title)
    year = datetime.now().year

    tags = set()

    # 기본 태그
    tags.update([
        f"#제주무료교육", "#국민내일배움카드", "#제주취업", "#제주특화훈련",
        f"#국비지원무료교육", f"#제주국비지원", f"#{year}국민내일배움카드",
        f"#제주교육", "#제주직업훈련", "#자부담10퍼센트",
    ])

    # 과정명 태그
    safe_title = title.replace(" ", "")
    tags.add(f"#{safe_title}")

    # 분야별 태그
    field_tags = {
        "AI": ["#AI교육", "#인공지능교육", "#AI활용교육", "#제주AI"],
        "영상": ["#영상편집교육", "#영상제작교육", "#유튜브교육", "#제주영상"],
        "디자인": ["#디자인교육", "#UIUX교육", "#디지털디자인", "#제주디자인"],
        "출판": ["#출판교육", "#편집디자인", "#인디자인교육"],
        "콘텐츠": ["#콘텐츠제작", "#크리에이터교육"],
        "마케팅": ["#마케팅교육", "#디지털마케팅"],
        "데이터": ["#데이터분석교육", "#빅데이터교육"],
        "코딩": ["#코딩교육", "#프로그래밍교육"],
    }
    tags.update(field_tags.get(field, ["#직업교육", "#기술교육"]))

    return " ".join(sorted(tags))


def generate_instagram_hashtags(course_data, max_count=20):
    """
    인스타그램용 해시태그 세트를 생성합니다.

    전략: 대형(5~7) + 중소형(5~7) + 지역(3~5) + 분야(3~5) = 15~20개

    Returns:
        str: 인스타그램 해시태그 문자열
    """
    title = course_data.get("title", "")
    field = detect_course_field(title)

    tags = []

    # 대형 해시태그 (5개)
    tags.extend(INSTAGRAM_HASHTAGS["large"][:5])

    # 중소형 해시태그 (5개)
    tags.extend(INSTAGRAM_HASHTAGS["medium"][:5])

    # 지역 태그 (4개)
    tags.extend(INSTAGRAM_HASHTAGS["local"][:4])

    # 분야별 태그 (3~4개)
    field_tags = FIELD_HASHTAGS.get(field, [])
    tags.extend(field_tags[:4])

    # 연도 태그
    year = datetime.now().year
    tags.append(f"#{year}교육")

    # 중복 제거 후 최대 개수 제한
    seen = set()
    unique_tags = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)
    unique_tags = unique_tags[:max_count]

    return "\n.\n.\n.\n" + " ".join(unique_tags)


def generate_instagram_caption(course_data):
    """
    인스타그램 게시물 캡션을 자동 생성합니다.

    포인트:
    - 첫 줄에서 주목 (이모지 + 핵심 메시지)
    - 혜택 요약
    - CTA (프로필 링크 유도)
    - 해시태그 분리 배치

    Returns:
        str: 인스타그램 캡션 전체 텍스트
    """
    from benefits_helper import get_benefits_text, get_course_type, get_total_hours

    title = course_data.get("title", "")
    institution = course_data.get("institution", "")
    period = course_data.get("period", "")
    course_cost = course_data.get("courseCost", "")
    self_cost = course_data.get("selfCost", "")
    benefits = get_benefits_text(course_data)
    field = detect_course_field(title)
    ctype = get_course_type(course_data)
    hours = get_total_hours(course_data)

    # 분야별 이모지
    field_emoji = {
        "AI": "🤖", "영상": "🎬", "디자인": "🎨", "출판": "📚",
        "멀티미디어": "🖥️", "콘텐츠": "📱", "마케팅": "📊",
        "데이터": "📈", "코딩": "💻",
    }
    emoji = field_emoji.get(field, "📌")

    # 첫 줄: 주목
    hook_lines = {
        "AI": "AI 시대, 배우는 사람이 기회를 잡아요",
        "영상": "영상 하나로 인생이 바뀔 수 있어요",
        "디자인": "디자인 스킬, 지금 시작해도 늦지 않았어요",
        "출판": "내 책을 만들 수 있는 기회",
        "default": "새로운 기술, 지금 배워보세요",
    }
    hook = hook_lines.get(field, hook_lines["default"])

    # 캡션 본문
    caption = f"""{emoji} {hook}

📍 {title}
🏫 {institution}"""

    if period:
        caption += f"\n🗓️ {period}"
    if self_cost:
        caption += f"\n💰 자부담금 {self_cost} (수강비 {course_cost})"
    elif course_cost:
        caption += f"\n💰 수강비 {course_cost}"

    # 혜택 라인 (과정 유형별 맞춤)
    if ctype == "long":
        benefit_emoji_line = f"🎁 {hours}시간 장기과정! 장려금+수당 월 최대 40만원"
    elif ctype == "general":
        benefit_emoji_line = f"🎁 {hours}시간 과정! 훈련장려금 월 최대 20만원"
    elif ctype == "short":
        benefit_emoji_line = f"🎁 {hours}시간 단기과정! 자부담 10%로 부담 없이"
    else:
        benefit_emoji_line = "🎁 특화훈련 혜택으로 부담 없이 배울 수 있어요"

    if hours > 0:
        caption += f"\n⏱️ 총 {hours}시간"

    caption += f"""

✅ 국민내일배움카드 있으면 누구나 신청 가능!
{benefit_emoji_line}
"""

    caption += """
👉 신청 방법이 궁금하다면?
프로필 링크에서 바로 확인하세요!

💬 궁금한 점은 DM 또는 댓글로 물어봐 주세요"""

    # 훈련목표 요약 (있을 때만)
    training_goal = course_data.get("trainingGoal", "")
    if training_goal:
        # 첫 문장만 추출하여 간결하게
        goal_sentences = [s.strip() for s in training_goal.replace("\n", ".").split(".") if s.strip()]
        goal_short = goal_sentences[0] if goal_sentences else ""
        if len(goal_short) > 80:
            goal_short = goal_short[:77] + "..."
        if goal_short:
            caption = caption.replace(
                "👉 신청 방법이 궁금하다면?",
                f"📋 이 과정을 배우면?\n→ {goal_short}\n\n👉 신청 방법이 궁금하다면?"
            )

    # 해시태그 (본문과 분리)
    hashtags = generate_instagram_hashtags(course_data)
    caption += hashtags

    return caption


def generate_reels_script(course_data):
    """
    인스타그램 릴스(숏폼) 대본을 생성합니다.

    차별화 요소:
    - 분야별 다중 훅 (같은 분야도 과정마다 다른 훅)
    - 과정 유형(단기/일반/장기)별 스토리라인 분기
    - NCS직종명, 훈련시간, 기관명 등 과정 고유 정보 반영
    - SEO 키워드 자연스럽게 포함
    - 3가지 릴스 포맷 제안 (슬라이드형 / 자막 중심형 / 인터뷰형)

    Returns:
        str: 릴스 대본 텍스트
    """
    title = course_data.get("title", "")
    field = detect_course_field(title)
    institution = course_data.get("institution", "")
    period = course_data.get("period", "")
    ncs_name = course_data.get("ncsName", "")
    self_cost = course_data.get("selfCost", "")
    capacity = course_data.get("capacity", "")

    from benefits_helper import get_course_type, get_total_hours
    ctype = get_course_type(course_data)
    hours = get_total_hours(course_data)
    seo_keywords = extract_seo_keywords(course_data)

    field_display = field if field != "default" else "전문 기술"

    # ── 분야별 다중 훅 (과정명 해시로 선택 → 같은 과정은 항상 같은 훅) ──
    hook_pool = {
        "AI": [
            "AI 배우고 싶은데 어디서 시작하지? 🤔",
            "ChatGPT만 쓰지 말고, AI를 제대로 배워보자 🤖",
            "AI 시대, 가만히 있으면 뒤처져요 ⚡",
            "연봉 올리는 가장 빠른 방법? AI 스킬 📈",
        ],
        "영상": [
            "영상 편집, 독학으로는 한계 있지 않나요? 🎬",
            "유튜브 시작하고 싶은데 편집이 막막하다면 📹",
            "릴스 하나로 인생이 바뀔 수 있어요 ✨",
            "내 콘텐츠, 이제 내가 직접 만들어보자 🎥",
        ],
        "디자인": [
            "디자인 스킬, 이직에 날개를 달아줄 거예요 🎨",
            "비전공자도 디자이너 될 수 있을까? 💡",
            "포트폴리오 하나면 취업이 달라져요 🖌️",
            "피그마? 포토샵? 뭐부터 배워야 할지 모르겠다면 🤔",
        ],
        "출판": [
            "내 책을 만드는 게 꿈이었다면 📚",
            "출판 디자인, 생각보다 진입장벽이 낮아요 📖",
            "전자책 시대, 출판 스킬이 무기가 됩니다 💻",
        ],
        "마케팅": [
            "마케팅, 감이 아니라 데이터로 하는 시대 📊",
            "SNS 마케팅 제대로 배우면 매출이 달라져요 📱",
            "콘텐츠 마케팅, 아직도 감으로 하시나요? 🎯",
        ],
        "데이터": [
            "데이터 분석, 모든 직무의 필수 스킬 📈",
            "엑셀 말고 파이썬으로 데이터를 다뤄보자 🐍",
            "데이터 리터러시, 이제 선택이 아니라 필수 💡",
        ],
        "코딩": [
            "코딩, 비전공자도 시작할 수 있어요 💻",
            "개발자 부족 시대, 지금이 기회입니다 🚀",
            "코딩 배워서 커리어를 바꿔보세요 ⌨️",
        ],
        "default": [
            "새로운 기술, 배우고 싶었죠? 📌",
            "이직 준비 중이라면 꼭 봐야 할 영상 👀",
            "국비로 배우는 전문 기술, 아직 모르셨나요? 🎓",
            "커리어 전환, 생각만 하지 말고 시작하세요 🔥",
        ],
    }
    hooks = hook_pool.get(field, hook_pool["default"])
    hook = hooks[hash(title) % len(hooks)]

    # ── 과정 유형별 혜택 강조 문구 ──
    if ctype == "long":
        benefit_line = f"자부담 10% + 월 최대 40만원 지원!"
        benefit_detail = f"💰 {hours}시간 장기과정이라\n  훈련장려금 20만 + 특별수당 20만\n  = 매달 최대 40만원 받으며 배워요"
        urgency = "장기과정이라 TO가 빨리 마감돼요!"
    elif ctype == "general":
        benefit_line = f"자부담 10% + 훈련장려금 월 20만원!"
        benefit_detail = f"💰 {hours}시간 과정, 출석 80% 이상이면\n  매달 훈련장려금 최대 20만원 지급!"
        urgency = f"모집 인원 {capacity}뿐이에요, 서두르세요!"
    elif ctype == "short":
        benefit_line = f"자부담 10%로 부담 없이 참여 가능!"
        benefit_detail = f"💰 {hours}시간 단기과정이라\n  부담 없이 빠르게 배울 수 있어요\n  ※ 동일 과정 재수강은 불가, 다른 과정은 횟수 무관"
        urgency = "단기라서 금방 마감될 수 있어요!"
    else:
        benefit_line = "자부담 10%로 부담 없이!"
        benefit_detail = "💰 국비지원으로 자부담 10%만 내면 돼요"
        urgency = "모집 기간이 정해져 있으니 서둘러 확인하세요!"

    # ── NCS직종 활용 ──
    ncs_line = f"📋 NCS직종: {ncs_name}" if ncs_name else ""
    ncs_intro = f"{ncs_name} 분야 전문가가 되고 싶다면?" if ncs_name else f"{field_display} 전문가가 되고 싶다면?"

    # ── 훈련목표 활용 ──
    training_goal = course_data.get("trainingGoal", "")
    goal_short = ""
    if training_goal:
        sentences = [s.strip() for s in training_goal.replace("\n", ".").split(".") if s.strip()]
        goal_short = sentences[0] if sentences else ""
        if len(goal_short) > 60:
            goal_short = goal_short[:57] + "..."
    goal_line = f"📋 \"{goal_short}\"" if goal_short else ""

    # ── SEO 키워드 해시태그 (상위 5개) ──
    seo_tags = " ".join([f"#{kw}" for kw in seo_keywords[:5]])

    # ── 포맷 A: 슬라이드형 (카드뉴스 활용) ──
    script_a = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 포맷 A: 슬라이드형 (카드뉴스 활용, 15~25초)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

0~3초 [훅]
  화면: 텍스트 오버레이 "{hook}"
  음악: 트렌디한 BGM 시작 (CapCut 내장 추천)

3~7초 [과정 소개]
  화면: 카드뉴스 커버 이미지
  자막: "제주에서 {field_display} 배울 수 있는 곳!"
  텍스트: "{title}"

7~14초 [혜택 강조]
  화면: 카드뉴스 상세 이미지 or 텍스트 애니메이션
  자막:
  - 📍 {institution}
  {f'- ⏱️ 총 {hours}시간' if hours > 0 else ''}
  {f'- {ncs_line}' if ncs_line else ''}
  {f'- {goal_line}' if goal_line else ''}
  - {benefit_line}
  - ✅ 국민내일배움카드만 있으면 OK

14~18초 [긴급성 + CTA]
  화면: 카드뉴스 신청방법 이미지
  자막: "⚠️ {urgency}"
  텍스트: "신청 방법은 프로필 링크에서 확인 👆"

게시 설정:
  커버: 카드뉴스 커버 이미지 (텍스트 오버레이 추가)
  캡션: instagram_caption.txt 사용
  해시태그: {seo_tags}"""

    # ── 포맷 B: 자막 중심형 (촬영 없이 제작 가능, 20~30초) ──
    script_b = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 포맷 B: 자막 중심형 (촬영 없이 제작, 20~30초)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

0~3초 [질문 훅]
  배경: 단색 or 그라데이션
  중앙 텍스트 (큰 글씨): "{ncs_intro}"

3~6초 [문제 공감]
  텍스트 전환 (타이핑 효과):
  "독학은 한계가 있고..."
  "학원비는 부담되고..."

6~10초 [해결책 제시]
  배경 전환 (밝은 톤)
  텍스트: "제주에서 국비로 배울 수 있어요!"
  서브: "{title}"

10~18초 [핵심 정보 나열]
  한 줄씩 등장하는 애니메이션:
  ✅ {institution}에서 진행
  {f'✅ 총 {hours}시간 과정' if hours > 0 else ''}
  {f'✅ {goal_short}' if goal_short else ''}
  {benefit_detail}
  ✅ 국민내일배움카드만 있으면 신청 가능

18~22초 [비용 강조]
  큰 텍스트: "자부담금"
  더 큰 텍스트: "{self_cost if self_cost else '수강비의 10%만!'}"
  서브: "나머지는 국비 지원"

22~25초 [CTA]
  텍스트: "신청 마감 전에 확인하세요! 👆"
  서브: "프로필 링크 → work24.go.kr"

게시 설정:
  BGM: 잔잔하지만 리듬감 있는 곡
  캡션: instagram_caption.txt 사용"""

    # ── 포맷 C: 인터뷰/나레이션형 (직접 촬영, 25~35초) ──
    script_c = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 포맷 C: 나레이션형 (직접 촬영/음성, 25~35초)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

0~5초 [훅 - 카메라 보며]
  나레이션: "{hook.replace('🤔', '').replace('🎬', '').replace('🎨', '').replace('📚', '').replace('📌', '').strip()}"
  자막 동기화: 핵심 키워드 강조

5~10초 [과정 소개]
  나레이션: "제주에서 {field_display} 과정이 열렸는데요,
    {institution}에서 진행하는 '{title[:25]}' 과정이에요.{f' ' + goal_short + '을 목표로 하는 과정이에요.' if goal_short and len(goal_short) < 40 else ''}"
  화면: 카드뉴스 커버 이미지 or 기관 외관

10~18초 [혜택 설명]
  나레이션: "{_build_narration_benefit(ctype, hours, self_cost)}"
  화면: 카드뉴스 상세 이미지 or 혜택 텍스트 오버레이

18~25초 [차별점 강조]
  나레이션: "{_build_narration_diff(field, ncs_name, ctype, hours, training_goal)}"
  화면: 관련 이미지 or 텍스트 애니메이션

25~30초 [CTA]
  나레이션: "관심 있으시면 프로필 링크에서 바로 확인하실 수 있어요.
    {urgency}"
  화면: 신청 방법 카드뉴스 + 프로필 링크 안내

게시 설정:
  BGM: 나레이션 방해하지 않는 잔잔한 곡 (볼륨 20~30%)
  캡션: instagram_caption.txt 사용"""

    # ── 공통 제작 팁 ──
    tips = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 제작 팁
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

추천 포맷: {'포맷 B (자막 중심)' if ctype == 'short' else '포맷 A (슬라이드)' if ctype == 'general' else '포맷 C (나레이션)'}
  → {'단기과정은 빠르게 핵심만 전달하는 자막형이 효과적' if ctype == 'short' else '일반과정은 카드뉴스 활용 슬라이드가 제작 부담 적음' if ctype == 'general' else '장기과정은 혜택이 큰 만큼 상세 설명하는 나레이션형 추천'}

영상 길이: {f'{hours}시간 과정 → ' if hours > 0 else ''}{'15~20초 (단기과정은 짧고 임팩트 있게)' if ctype == 'short' else '20~25초 (정보량과 집중도 균형)' if ctype == 'general' else '25~35초 (혜택 상세 설명 필요)'}

핵심 SEO 키워드 (자막/캡션에 포함):
  {', '.join(seo_keywords[:8])}

BGM 추천:
  - CapCut 내장 BGM (저작권 프리)
  - Artlist, Epidemic Sound (유료, 고퀄리티)
  - 유튜브 오디오 라이브러리 (무료)

해시태그: {seo_tags}
"""

    script = f"""[릴스 대본 - {title}]
{'=' * 50}
과정 정보: {institution} | {f'{hours}시간' if hours > 0 else ''} | {f'NCS: {ncs_name}' if ncs_name else ''} | {ctype}과정
혜택 요약: {benefit_line}
{'=' * 50}

{script_a}

{script_b}

{script_c}

{tips}"""

    return script


def _build_narration_benefit(ctype, hours, self_cost):
    """나레이션형 릴스의 혜택 설명 문구"""
    cost_mention = f"자부담금은 {self_cost}뿐이고요," if self_cost else "자부담금은 수강비의 10%뿐이고요,"

    if ctype == "long":
        return (f"이 과정이 좋은 게, 총 {hours}시간 장기과정이라 "
                f"훈련장려금이랑 특별수당 합쳐서 매달 최대 40만원까지 받을 수 있어요. "
                f"{cost_mention} 배우면서 돈도 벌 수 있는 거죠.")
    elif ctype == "general":
        return (f"{cost_mention} 거기에 출석 80% 이상이면 "
                f"매달 훈련장려금 최대 20만원도 받을 수 있어요. "
                f"배우면서 용돈까지 생기는 거죠.")
    elif ctype == "short":
        return (f"이 과정은 {hours}시간 단기과정이라 부담 없이 빠르게 배울 수 있고요, "
                f"{cost_mention} 단기과정이라 자부담 10%로 부담 없이 참여할 수 있어요. "
                f"다만 같은 과정을 다시 듣는 건 안 되고, 다른 단기과정은 계속 수강 가능합니다.")
    else:
        return f"{cost_mention} 나머지는 전부 국비로 지원받을 수 있어요."


def _build_narration_diff(field, ncs_name, ctype, hours, training_goal=""):
    """나레이션형 릴스의 차별점 강조 문구"""
    ncs_mention = f"{ncs_name} 분야 " if ncs_name else ""

    # 훈련목표가 있으면 구체적인 차별점 생성
    if training_goal:
        goal_sentences = [s.strip() for s in training_goal.replace("\n", ".").split(".") if s.strip()]
        goal_core = goal_sentences[0] if goal_sentences else ""
        if len(goal_core) > 50:
            goal_core = goal_core[:47] + "..."

        if goal_core:
            diff = f"이 과정은 {ncs_mention}{goal_core}을 목표로 하고 있어요. 실무에서 바로 활용할 수 있는 역량을 키울 수 있죠."
            if ctype == "long" and hours >= 350:
                diff += f" 총 {hours}시간이라 정말 깊이 있게 배울 수 있고요."
            elif ctype == "short" and hours > 0:
                diff += f" {hours}시간이면 부담 없이 끝낼 수 있는 분량이에요."
            return diff

    diff_pool = {
        "AI": [
            f"요즘 어디서든 AI 얘기하잖아요. 이 과정은 {ncs_mention}실무 중심이라, 배우고 바로 현업에 쓸 수 있어요.",
            f"단순히 AI 이론만 배우는 게 아니라, {ncs_mention}실제 프로젝트를 해볼 수 있는 실습 과정이에요.",
        ],
        "영상": [
            f"유튜브나 릴스 만들고 싶은 분들에게 딱인 과정이에요. {ncs_mention}편집부터 기획까지 체계적으로 배울 수 있어요.",
            f"요즘 영상 못 만들면 마케팅도 취업도 불리하잖아요. {ncs_mention}이 과정에서 확실하게 배울 수 있어요.",
        ],
        "디자인": [
            f"비전공자도 포트폴리오 만들 수 있도록 {ncs_mention}기초부터 실무까지 알려주는 과정이에요.",
            f"요즘 디자인 못하면 기획서도 제대로 못 만들잖아요. {ncs_mention}현업에서 바로 쓸 수 있는 스킬을 배워요.",
        ],
        "출판": [
            f"내 책을 만들거나 출판 분야로 취업하고 싶다면, {ncs_mention}이 과정이 좋은 시작점이 될 거예요.",
        ],
        "마케팅": [
            f"감이 아니라 데이터로 마케팅하는 법을 배울 수 있어요. {ncs_mention}실무 툴까지 다뤄요.",
        ],
        "데이터": [
            f"엑셀에서 벗어나서 {ncs_mention}제대로 된 데이터 분석 역량을 키울 수 있는 과정이에요.",
        ],
        "코딩": [
            f"비전공자도 코딩 시작할 수 있어요. {ncs_mention}기초부터 차근차근 가르쳐주는 과정이에요.",
        ],
        "default": [
            f"제주 지역 특화훈련이라 {ncs_mention}지역 수요에 맞춘 커리큘럼으로 구성되어 있어요.",
        ],
    }

    diffs = diff_pool.get(field, diff_pool["default"])
    diff = diffs[hash(ncs_name + field) % len(diffs)]

    if ctype == "long" and hours >= 350:
        diff += f" 총 {hours}시간이라 정말 깊이 있게 배울 수 있고요."
    elif ctype == "short" and hours > 0:
        diff += f" {hours}시간이면 부담 없이 끝낼 수 있는 분량이에요."

    return diff


def generate_posting_guide(course_data):
    """
    게시 타이밍 및 시리즈 전략 가이드를 생성합니다.

    Returns:
        str: 게시 가이드 텍스트
    """
    title = course_data.get("title", "")
    period = course_data.get("period", "")

    # 모집 시작일 추정
    start_date_str = course_data.get("traStartDate", "")
    if start_date_str and len(start_date_str) >= 8:
        try:
            start_date = datetime.strptime(start_date_str[:8], "%Y%m%d")
        except ValueError:
            start_date = None
    else:
        start_date = None

    guide = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 게시 가이드 - {title}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 권장 게시 일정
"""

    if start_date:
        d1 = start_date - timedelta(days=21)
        d2 = start_date - timedelta(days=14)
        d3 = start_date - timedelta(days=7)
        d4 = start_date - timedelta(days=3)

        guide += f"""
  1차 (D-21, {d1.strftime('%m/%d')}): 블로그 "혜택 정리편" + 인스타 카드뉴스
  2차 (D-14, {d2.strftime('%m/%d')}): 블로그 "커리큘럼 상세편" + 릴스 영상
  3차 (D-7,  {d3.strftime('%m/%d')}): 인스타 스토리 "마감 D-7" 긴급성 강조
  4차 (D-3,  {d4.strftime('%m/%d')}): 블로그+인스타 "마감 임박" 리마인드
"""
    else:
        guide += """
  1차: 과정 공개 후 즉시 → 블로그 "혜택 정리편" + 인스타 카드뉴스
  2차: 1주일 후 → 블로그 "커리큘럼 상세편" + 릴스 영상
  3차: 마감 7일 전 → 인스타 스토리 "마감 D-7" 긴급성 강조
  4차: 마감 3일 전 → 블로그+인스타 "마감 임박" 리마인드
"""

    guide += """
⏰ 권장 게시 시간
  - 네이버 블로그: 오전 8~9시 (출근길 검색) 또는 오후 1시 (점심시간)
  - 인스타그램 피드: 오후 12~1시 (점심) 또는 오후 6~9시 (퇴근 후)
  - 인스타그램 릴스: 오후 7~9시 (최대 도달)
  - 인스타그램 스토리: 오전 8시, 오후 12시, 오후 8시 (3회)
  - 최적 요일: 월~수 (교육/자기계발 콘텐츠 반응 우수)

📊 게시 후 체크리스트
  □ 블로그: 발행 후 24시간 내 네이버 서치어드바이저에서 색인 요청
  □ 인스타: 게시 후 1시간 내 댓글에 직접 답글 달기 (알고리즘 부스트)
  □ 인스타: 스토리에 게시물 공유 + "자세히 보기" 유도
  □ 릴스: 첫 3초 이탈 방지를 위해 훅 문장 확인
  □ 관련 커뮤니티/카페에 링크 공유 (제주 지역 커뮤니티 우선)

🔑 인스타그램 프로필 설정
  - 프로필 링크: 고용24 과정 신청 페이지 또는 링크트리
  - 프로필 소개: "제주 무료교육·국비지원 과정 안내 | 국민내일배움카드"
  - 하이라이트: "신청방법", "모집중", "수강후기" 카테고리 생성
"""

    return guide
