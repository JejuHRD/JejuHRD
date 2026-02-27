"""
SEO 및 마케팅 헬퍼 - 제주지역인적자원개발위원회 특화훈련 홍보용

기능:
- 과정 분야 자동 감지 및 SEO 키워드 추출
- 네이버 블로그 SEO 최적화 제목 생성
- 공감형 도입부 생성
- 인스타그램 해시태그/캡션 생성
- Sora AI용 15초 릴스 가이드 생성 (v3: 훈련목표 키워드 요약 포함)
- 게시 타이밍 가이드 생성

v3 변경사항:
- generate_reels_script(): 최대 15초 Sora AI 영상 가이드로 변경
- summarize_training_goal(): 훈련목표 크롤링 텍스트를 핵심 키워드 3개로 요약
"""

import re
import random
from datetime import datetime, timedelta


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEO 키워드 매핑
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KEYWORD_MAP = {
    "AI": ["AI교육", "인공지능교육", "AI활용", "ChatGPT교육"],
    "영상": ["영상편집교육", "영상제작", "유튜브교육", "프리미어프로"],
    "디자인": ["디자인교육", "UI교육", "UX교육", "피그마교육", "웹디자인"],
    "출판": ["출판교육", "인디자인교육", "전자책제작", "편집디자인"],
    "멀티미디어": ["멀티미디어교육", "디지털콘텐츠"],
    "콘텐츠": ["콘텐츠제작", "크리에이터교육", "SNS콘텐츠"],
    "마케팅": ["디지털마케팅", "SNS마케팅교육", "마케팅교육"],
    "데이터": ["데이터분석교육", "빅데이터", "파이썬교육"],
    "코딩": ["코딩교육", "프로그래밍교육", "개발자교육"],
}

COMMON_SEARCH_KEYWORDS = [
    "제주무료교육", "제주국비지원", "내일배움카드",
    "제주취업", "제주직업훈련", "제주특화훈련",
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 공감형 도입부 (분야별)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EMPATHY_INTROS = {
    "AI": [
        "\"나도 AI를 배워야 하나?\" 고민만 하다가 시간이 흘러가고 있다면, 지금이 딱 시작할 타이밍이에요.",
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
        "새로운 기술을 배우고 싶은데, 어디서 시작해야 할지 막막하셨나요? 내일배움카드만 있으면 자부담 10%로 바로 시작할 수 있는 과정이 열렸어요.",
        "이직을 고민하거나, 새로운 분야에 도전하고 싶은 마음... 누구나 한번쯤 있죠. 제주에서 부담 없이 새로운 기술을 배울 수 있는 기회를 소개합니다.",
        "경력을 쌓고 싶은데 교육비가 부담이셨나요? 내일배움카드로 자부담 10%만 내고 전문 기술을 배울 수 있어요. 제주에서 만나는 특화훈련을 확인해보세요.",
    ],
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 분야 감지
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def detect_course_field(title):
    """과정 제목에서 분야를 감지합니다."""
    title_upper = title.upper()

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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEO 키워드 / 제목 / 도입부
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def extract_seo_keywords(course_data):
    """과정 데이터에서 SEO 키워드를 추출합니다."""
    title = course_data.get("title", "")
    keywords = set()

    for trigger, mapped in KEYWORD_MAP.items():
        if trigger.upper() in title.upper():
            keywords.update(mapped)

    keywords.update(COMMON_SEARCH_KEYWORDS)

    year = datetime.now().year
    keywords.add(f"{year}국비지원")
    keywords.add(f"{year}내일배움카드")

    return sorted(keywords)


def generate_seo_title(course_data):
    """네이버 블로그 SEO에 최적화된 제목을 생성합니다."""
    from benefits_helper import is_long_course

    title = course_data.get("title", "")
    long = is_long_course(course_data)

    benefit_tag = "자부담 10% + 훈련장려금" if long else "자부담 10%"
    seo_title = f"[제주 국비지원] {title} | {benefit_tag}"

    if len(seo_title) > 60:
        short_title = title[:25] + "..." if len(title) > 25 else title
        seo_title = f"[제주 국비지원] {short_title} | {benefit_tag}"

    return seo_title


def generate_empathy_intro(course_data):
    """과정별로 차별화된 공감형 도입부를 생성합니다."""
    title = course_data.get("title", "")
    field = detect_course_field(title)
    intros = EMPATHY_INTROS.get(field, EMPATHY_INTROS["default"])
    return random.choice(intros)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 인스타그램 해시태그 / 캡션
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_instagram_hashtags(course_data):
    """인스타그램 해시태그 20개를 대형+중소형+지역+분야별로 믹스합니다."""
    title = course_data.get("title", "")
    field = detect_course_field(title)

    big_tags = ["#국비지원", "#무료교육", "#내일배움카드", "#직업훈련", "#자기계발"]
    mid_tags = ["#제주교육", "#제주취업", "#제주취업준비", "#제주직업훈련", "#내일배움카드신청"]
    local_tags = ["#제주", "#제주시", "#제주도생활", "#제주이직", "#제주살이"]

    field_tags = {
        "AI": ["#AI교육", "#인공지능", "#ChatGPT", "#AI활용", "#생성형AI"],
        "영상": ["#영상편집", "#영상제작", "#프리미어프로", "#유튜브교육", "#숏폼"],
        "디자인": ["#디자인교육", "#UIUX", "#피그마", "#웹디자인", "#디지털디자인"],
        "출판": ["#출판교육", "#인디자인", "#전자책", "#편집디자인", "#독립출판"],
        "콘텐츠": ["#콘텐츠제작", "#크리에이터", "#SNS마케팅", "#디지털콘텐츠"],
        "마케팅": ["#디지털마케팅", "#SNS마케팅", "#마케팅교육", "#퍼포먼스마케팅"],
        "데이터": ["#데이터분석", "#빅데이터", "#파이썬", "#데이터사이언스"],
        "코딩": ["#코딩교육", "#프로그래밍", "#개발자", "#파이썬"],
        "default": ["#스킬업", "#커리어전환", "#신기술교육", "#역량강화"],
    }

    specific = field_tags.get(field, field_tags["default"])

    all_tags = []
    all_tags.extend(random.sample(big_tags, min(3, len(big_tags))))
    all_tags.extend(random.sample(mid_tags, min(4, len(mid_tags))))
    all_tags.extend(random.sample(local_tags, min(4, len(local_tags))))
    all_tags.extend(random.sample(specific, min(4, len(specific))))

    year = datetime.now().year
    all_tags.append(f"#{year}국비지원")
    all_tags.append("#제주특화훈련")

    seen = set()
    unique_tags = []
    for tag in all_tags:
        if tag not in seen:
            unique_tags.append(tag)
            seen.add(tag)

    return "\n\n.\n.\n.\n" + " ".join(unique_tags[:20])


def generate_instagram_caption(course_data):
    """인스타그램 캡션을 생성합니다."""
    from benefits_helper import is_long_course, get_benefits_text

    title = course_data.get("title", "")
    institution = course_data.get("institution", "")
    period = course_data.get("period", "")
    time_info = course_data.get("time", "")
    long = is_long_course(course_data)
    benefits = get_benefits_text(course_data)
    field = detect_course_field(title)

    field_emoji = {
        "AI": "🤖", "영상": "🎬", "디자인": "🎨", "출판": "📚",
        "멀티미디어": "🖥️", "콘텐츠": "📱", "마케팅": "📊",
        "데이터": "📈", "코딩": "💻",
    }
    emoji = field_emoji.get(field, "📌")

    hook_lines = {
        "AI": "AI 시대, 배우는 사람이 기회를 잡아요",
        "영상": "영상 하나로 인생이 바뀔 수 있어요",
        "디자인": "디자인 스킬, 지금 시작해도 늦지 않았어요",
        "출판": "내 책을 만들 수 있는 기회",
        "default": "새로운 기술, 지금 배워보세요",
    }
    hook = hook_lines.get(field, hook_lines["default"])

    caption = f"""{emoji} {hook}

📍 {title}
🏫 {institution}"""

    if period:
        caption += f"\n🗓️ {period}"
    if time_info:
        caption += f"\n⏰ {time_info}"

    caption += f"""

💰 {benefits}
✅ 내일배움카드 있으면 누구나 신청 가능!
"""

    if long is True:
        caption += "🎁 훈련장려금 월 최대 20만원까지 받을 수 있어요\n"

    caption += """
👉 신청 방법이 궁금하다면?
프로필 링크에서 바로 확인하세요!

💬 궁금한 점은 DM 또는 댓글로 물어봐 주세요"""

    hashtags = generate_instagram_hashtags(course_data)
    caption += hashtags

    return caption


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [NEW] 훈련목표 핵심 키워드 요약
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def summarize_training_goal(training_goal, max_keywords=3):
    """
    훈련목표 텍스트에서 핵심 키워드를 추출하여 짧은 요약문을 생성합니다.
    Sora AI 릴스(15초)에서 텍스트 오버레이 자막으로 사용됩니다.

    Args:
        training_goal: L02 API의 traingGoal 필드 원문
        max_keywords: 추출할 핵심 키워드 최대 개수

    Returns:
        str: "프리미어 프로 · 에프터 이펙트 · AI 활용" 형식의 요약
             훈련목표가 없으면 빈 문자열 반환

    사용 예시:
        goal = api_response.get("traingGoal", "")
        summary = summarize_training_goal(goal)
        # → "프리미어 프로 · 에프터 이펙트 · AI 활용"
    """
    if not training_goal or not training_goal.strip():
        return ""

    text = training_goal.strip()

    # 그룹별 키워드 패턴 (구체적 도구 → AI → 분야/직무 → 성과 순서)
    keyword_groups = [
        # 1) 구체적 소프트웨어/도구 (가장 눈에 띄는 정보)
        {"patterns": [
            (r'프리미어\s*프로|Premiere\s*Pro', "프리미어 프로"),
            (r'에프터\s*이펙트|After\s*Effects', "에프터 이펙트"),
            (r'다빈치\s*리졸브', "다빈치 리졸브"),
            (r'피그마|Figma', "피그마"),
            (r'인디자인|InDesign', "인디자인"),
            (r'포토샵|Photoshop', "포토샵"),
            (r'일러스트레이터|Illustrator', "일러스트레이터"),
            (r'파이썬|Python', "파이썬"),
            (r'블렌더|Blender', "블렌더"),
            (r'유니티|Unity', "유니티"),
        ], "max": 2},
        # 2) AI/기술 키워드 (구체적 도구 다음 우선순위)
        {"patterns": [
            (r'생성형\s*AI', "생성형 AI"),
            (r'ChatGPT|챗GPT', "ChatGPT"),
            (r'미드저니|Midjourney', "미드저니"),
            (r'Stable\s*Diffusion', "Stable Diffusion"),
            (r'머신러닝', "머신러닝"),
            (r'딥러닝', "딥러닝"),
            (r'AI|인공지능', "AI 활용"),
        ], "max": 1},
        # 3) 분야/직무 키워드
        {"patterns": [
            (r'영상\s*편집', "영상 편집"),
            (r'영상\s*제작|영상\s*촬영', "영상 제작"),
            (r'숏폼', "숏폼 제작"),
            (r'UI/?UX\s*디자인|UI\s*설계', "UI/UX 디자인"),
            (r'편집\s*디자인|편집디자인', "편집디자인"),
            (r'웹\s*디자인', "웹디자인"),
            (r'전자책|e-?book|EPUB', "전자책 제작"),
            (r'콘텐츠\s*제작', "콘텐츠 제작"),
            (r'콘텐츠\s*기획', "콘텐츠 기획"),
            (r'빅데이터|데이터\s*분석', "데이터 분석"),
            (r'디지털\s*마케팅|SNS\s*마케팅', "디지털 마케팅"),
        ], "max": 2},
        # 4) 성과/아웃풋 (남은 슬롯 채우기)
        {"patterns": [
            (r'포트폴리오', "포트폴리오 완성"),
            (r'실무\s*프로젝트|현장\s*실습', "실무 프로젝트"),
            (r'취업', "취업 연계"),
            (r'자격증', "자격증 취득"),
            (r'창업', "창업 준비"),
        ], "max": 1},
    ]

    found = []
    labels = set()

    for group in keyword_groups:
        cnt = 0
        for pattern, label in group["patterns"]:
            if cnt >= group["max"] or len(found) >= max_keywords:
                break
            if label not in labels and re.search(pattern, text, re.IGNORECASE):
                found.append(label)
                labels.add(label)
                cnt += 1

    return " · ".join(found[:max_keywords]) if found else ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [MODIFIED] Sora AI용 15초 릴스 가이드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_reels_script(course_data):
    """
    Sora AI로 생성할 15초 릴스 영상 가이드를 생성합니다.

    변경사항 (v3):
    - 재생시간: 최대 20초 → 최대 15초로 압축
    - 훈련목표(traingGoal)를 핵심 키워드로 요약하여 3~8초 구간에 표시
    - 각 구간에 Sora AI 프롬프트용 장면 설명 추가
    - 훈련목표가 없는 경우 분야 기반 폴백 키워드 사용

    구간 설계 (15초):
      0~3초: 훅 (주목 끌기)
      3~8초: 배우는 내용 (훈련목표 키워드 요약)
      8~12초: 혜택 핵심
      12~15초: CTA (행동 유도)

    Returns:
        str: Sora AI 릴스 가이드 텍스트
    """
    from benefits_helper import is_long_course

    title = course_data.get("title", "")
    field = detect_course_field(title)
    long = is_long_course(course_data)
    institution = course_data.get("institution", "")
    time_info = course_data.get("time", "")

    # ── 훈련목표 키워드 요약 ──
    training_goal = course_data.get("traingGoal", "") or course_data.get("training_goal", "")
    goal_summary = summarize_training_goal(training_goal)

    # 훈련목표가 없으면 분야 기반 폴백 키워드
    if not goal_summary:
        fallback_keywords = {
            "AI": "AI 활용 · 실무 프로젝트",
            "영상": "영상 편집 · 콘텐츠 제작",
            "디자인": "UI/UX 디자인 · 실무 포트폴리오",
            "출판": "편집디자인 · 전자책 제작",
            "콘텐츠": "콘텐츠 기획 · 제작 실무",
            "마케팅": "디지털 마케팅 · SNS 운영",
            "데이터": "데이터 분석 · 시각화",
            "코딩": "프로그래밍 · 개발 실무",
            "default": "전문 기술 · 실무 역량",
        }
        goal_summary = fallback_keywords.get(field, fallback_keywords["default"])

    # ── 분야별 훅 ──
    hooks = {
        "AI": "AI, 배우면 기회가 달라져요",
        "영상": "영상 편집, 제대로 배워보자",
        "디자인": "디자인, 지금 시작해도 늦지 않아요",
        "출판": "내 책을 만드는 첫걸음",
        "콘텐츠": "콘텐츠 크리에이터 되는 법",
        "마케팅": "디지털 마케팅, 실전 스킬 업",
        "데이터": "데이터로 일하는 시대",
        "코딩": "코딩, 이제 필수 스킬이에요",
        "default": "새로운 기술, 제주에서 배워요",
    }
    hook = hooks.get(field, hooks["default"])

    # ── 혜택 한 줄 ──
    if long is True:
        benefit_line = "자부담 10% + 훈련장려금 월 최대 20만원"
    else:
        benefit_line = "자부담 10%로 부담 없이"

    # ── Sora AI 장면 분위기 ──
    scene_moods = {
        "AI": "미래지향적이고 깔끔한 테크 오피스 공간, 모니터에 AI 인터페이스가 보이는 밝은 분위기",
        "영상": "카메라와 편집 장비가 있는 스튜디오, 모니터에 타임라인이 보이는 크리에이티브한 공간",
        "디자인": "넓은 모니터에 디자인 작업물이 보이는 깔끔한 워크스페이스, 밝고 세련된 분위기",
        "출판": "책과 디자인 작업물이 있는 아늑한 작업실, 따뜻한 조명",
        "default": "밝고 현대적인 교육 공간, 노트북과 학습 자료가 보이는 활기찬 분위기",
    }
    scene_mood = scene_moods.get(field, scene_moods["default"])

    # ── 릴스 가이드 생성 ──
    script = f"""[Sora AI 릴스 가이드 - {title}]
총 재생시간: 15초 | Sora AI 영상 생성용

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 장면 분위기 (Sora 프롬프트 참고)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{scene_mood}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ 0~3초 (훅 - 주목 끌기)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
텍스트 오버레이: "{hook}"
장면: 인물이 카메라를 향해 걸어오거나, 작업 화면이 클로즈업되는 동적인 시작
효과: 텍스트 페이드인 + 약간의 줌인

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ 3~8초 (배우는 내용 - 훈련목표 핵심키워드)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
텍스트 오버레이: "✨ {goal_summary}"
보조 텍스트: "{institution} | {time_info}"
장면: 실제 수업/작업 장면 - 모니터에서 소프트웨어를 다루는 손, 집중하는 표정
효과: 키워드가 하나씩 나타나는 타이핑 애니메이션

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ 8~12초 (혜택 핵심)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
텍스트 오버레이: "💰 {benefit_line}"
보조 텍스트: "내일배움카드만 있으면 OK ✅"
장면: 밝은 표정의 수강생, 수료증을 들고 있거나 동료와 하이파이브
효과: 혜택 금액 부분 강조 (볼드 또는 색상 변화)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ 12~15초 (CTA - 행동 유도)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
텍스트 오버레이: "지금 바로 신청하세요! 👆"
보조 텍스트: "프로필 링크에서 확인"
장면: 로고/기관명 + CTA 버튼 느낌의 그래픽 엔딩
효과: 텍스트 확대 + 화면 밝아짐"""

    # ── 훈련목표 키워드 상세 정보 ──
    script += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 훈련목표 키워드 요약
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
추출된 키워드: {goal_summary}"""

    if training_goal:
        # 원문이 길면 앞부분만 표시
        goal_preview = training_goal[:150] + "..." if len(training_goal) > 150 else training_goal
        script += f"""
원문 (참고용): {goal_preview}"""
    else:
        script += """
원문: (훈련목표 데이터 없음 - 분야 기반 폴백 키워드 사용)"""

    # ── Sora AI 프롬프트 제안 ──
    script += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Sora AI 프롬프트 예시
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A 15-second promotional video for a vocational training course.
Scene: {scene_mood}
The video starts with a dynamic zoom-in on a workspace,
then shows text overlay "{hook}" fading in.
At 3 seconds, keywords "{goal_summary}" appear one by one with typing animation.
At 8 seconds, benefit text "{benefit_line}" appears with emphasis.
The video ends with a call-to-action "지금 바로 신청하세요!" with the screen brightening.
Style: Modern, clean, professional, warm lighting, Korean text overlays.
Aspect ratio: 9:16 (vertical/portrait for Instagram Reels)
Duration: 15 seconds

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 게시 설정
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 화면 비율: 9:16 (세로형)
- 캡션: instagram_caption.txt 파일 내용 사용
- 커버: 3~8초 구간 캡처 (핵심키워드가 보이는 장면)
- 음악: Sora AI 생성 영상에 별도 BGM 추가 권장 (저작권 프리)
"""

    return script


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 게시 가이드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_posting_guide(course_data):
    """게시 타이밍 및 시리즈 전략 가이드를 생성합니다."""
    title = course_data.get("title", "")
    period = course_data.get("period", "")

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
  2차 (D-14, {d2.strftime('%m/%d')}): 블로그 "커리큘럼 상세편" + Sora AI 릴스 영상
  3차 (D-7,  {d3.strftime('%m/%d')}): 인스타 스토리 "마감 D-7" 긴급성 강조
  4차 (D-3,  {d4.strftime('%m/%d')}): 블로그+인스타 "마감 임박" 리마인드
"""
    else:
        guide += """
  1차: 과정 공개 후 즉시 → 블로그 "혜택 정리편" + 인스타 카드뉴스
  2차: 1주일 후 → 블로그 "커리큘럼 상세편" + Sora AI 릴스 영상
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
  - 프로필 소개: "제주 무료교육·국비지원 과정 안내 | 내일배움카드"
  - 하이라이트: "신청방법", "모집중", "수강후기" 카테고리 생성
"""

    return guide
