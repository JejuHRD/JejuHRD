"""
SEO 및 마케팅 헬퍼 - 제주지역인적자원개발위원회 특화훈련 홍보용

v4 전면 개편 (과정별 차별화):
  1) 훈련목표 키워드 → Grok 장면 자동 매핑
  2) 과정 제목/목표에서 동적 훅 문장 생성
  3) 혜택 구간을 과정 시간·비용에 맞게 세분화
  4) 모집 D-day 기반 CTA 동적 변경
  5) 분야+키워드별 Grok 색상 팔레트·무드 차별화
  6) 과정 기간에 따른 타임라인 구조 변형 (단기 빠른 컷 / 장기 성장 서사)
  7) NCS 직무분류 코드 기반 정밀 분야 감지
"""

import re
import random
from datetime import datetime, timedelta


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [아이디어 7] NCS 코드 기반 분야 감지
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

NCS_FIELD_MAP = {
    "08": "디자인",       # 문화/예술/디자인/방송
    "20": "코딩",         # 정보통신
    "02": "마케팅",       # 경영/회계/사무
    "10": "이커머스",     # 영업판매 → 이커머스로 변경
    "0802": "디자인",     # 디자인
    "0803": "영상",       # 방송
    "0801": "콘텐츠",     # 문화콘텐츠
    "2001": "코딩",       # 정보기술
    "2002": "데이터",     # 통신기술
    "24": "산업안전",     # 안전관리
    "1001": "이커머스",   # 유통/판매
    "0201": "마케팅",     # 경영기획 (마케팅 유지)
}

NCS_SUB_KEYWORDS = {
    "080301": "영상촬영",
    "080302": "영상편집",
    "080201": "시각디자인",
    "080202": "UX디자인",
    "080203": "제품디자인",
    "080204": "패션디자인",
    "080205": "실내디자인",
    "200101": "SW개발",
    "200102": "DB개발",
    "200104": "보안",
}


def _detect_field_by_ncs(ncs_cd):
    """NCS 코드에서 분야를 감지합니다."""
    if not ncs_cd or len(str(ncs_cd).strip()) < 2:
        return None, None
    ncs_cd = str(ncs_cd).strip()
    sub_keyword = None
    if len(ncs_cd) >= 6:
        sub_keyword = NCS_SUB_KEYWORDS.get(ncs_cd[:6])
    for length in (4, 2):
        prefix = ncs_cd[:length]
        if prefix in NCS_FIELD_MAP:
            return NCS_FIELD_MAP[prefix], sub_keyword
    return None, sub_keyword


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 분야 감지 (NCS 우선 + 제목 키워드 폴백)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TITLE_FIELD_KEYWORDS = {
    "AI": ["AI", "인공지능", "챗GPT", "CHATGPT", "머신러닝", "딥러닝", "생성형"],
    "영상": ["영상", "비디오", "유튜브", "숏폼", "프리미어", "에프터이펙트", "촬영", "릴스"],
    "디자인": ["디자인", "UI", "UX", "피그마", "FIGMA", "웹디자인", "그래픽"],
    "출판": ["출판", "인디자인", "편집디자인", "전자책", "EPUB", "오디오북"],
    "이커머스": ["스마트스토어", "이커머스", "쇼핑몰", "온라인판매", "라이브커머스", "셀러", "전자상거래"],
    "산업안전": ["산업안전", "안전관리", "안전보건", "중대재해", "위험성평가", "건설안전"],
    "멀티미디어": ["멀티미디어"],
    "콘텐츠": ["콘텐츠", "크리에이터"],
    "마케팅": ["마케팅", "퍼포먼스", "광고"],
    "데이터": ["데이터", "빅데이터", "분석", "시각화"],
    "코딩": ["코딩", "프로그래밍", "파이썬", "개발", "자바", "웹개발"],
}


def detect_course_field(title, ncs_cd=None):
    """과정 분야를 감지합니다. NCS 코드 우선, 없으면 제목 키워드 폴백."""
    ncs_field, _ = _detect_field_by_ncs(ncs_cd)
    if ncs_field:
        return ncs_field
    title_upper = title.upper()
    for field, keywords in TITLE_FIELD_KEYWORDS.items():
        for kw in keywords:
            if kw in title_upper:
                return field
    return "default"


def _get_ncs_sub_keyword(ncs_cd):
    """NCS 세분류 키워드를 반환합니다."""
    _, sub = _detect_field_by_ncs(ncs_cd)
    return sub


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [아이디어 1] 키워드 → Grok 장면 매핑 테이블
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TOOL_SCENE_MAP = {
    "프리미어 프로": "a widescreen monitor showing Adobe Premiere Pro timeline with colorful video clips, editing room with soft warm lighting",
    "에프터 이펙트": "a monitor displaying After Effects motion graphics workspace with animated text layers and particle effects",
    "다빈치 리졸브": "a color grading suite with DaVinci Resolve interface showing color wheels on an ultrawide monitor",
    "피그마": "dual monitors showing Figma prototype with colorful UI components, modern bright workspace with sticky notes",
    "인디자인": "a designer's desk with Adobe InDesign layout on screen, printed booklet samples and color swatches nearby",
    "포토샵": "a creative workspace with Photoshop open showing photo retouching, Wacom tablet and stylus on desk",
    "일러스트레이터": "Adobe Illustrator workspace with vector artwork on screen, clean minimalist desk setup",
    "파이썬": "a developer's setup with Python code on a dark-themed IDE, dual monitors, coffee cup beside keyboard",
    "블렌더": "a 3D modeling workspace with Blender showing a detailed 3D model, high-spec workstation setup",
    "ChatGPT": "a modern workspace with ChatGPT conversation on screen, Korean person typing prompt, futuristic blue ambient light",
    "미드저니": "a creative studio with Midjourney AI-generated art displayed on a large monitor, colorful and artistic atmosphere",
    "영상 편집": "a professional video editing suite with multiple monitors showing timeline and preview, headphones on desk",
    "영상촬영": "a studio with professional camera on tripod, ring light, and green screen setup",
    "영상 제작": "a content creation studio with camera, microphone, lighting equipment, and editing station",
    "숏폼 제작": "a mobile content creation setup with smartphone on gimbal, ring light, and vertical format on screen",
    "UI/UX 디자인": "a UX designer's workspace with wireframes on screen, user journey maps on wall, post-it notes by color",
    "편집디자인": "a publishing workspace with InDesign layout on screen, printed magazine spreads fanned out on desk",
    "웹디자인": "a web designer's desk with responsive website mockup on screen, code editor on second monitor",
    "전자책 제작": "a cozy home office with e-book formatting software on screen, tablet showing finished e-book, bookshelf background",
    "콘텐츠 기획": "a brainstorming workspace with content calendar on whiteboard, laptop showing social media analytics",
    "콘텐츠 제작": "a versatile content studio with camera, microphone, laptop showing social media dashboard",
    "데이터 분석": "a data analyst's workspace with charts and dashboards on dual monitors, spreadsheet with colorful graphs",
    "디지털 마케팅": "a marketing workspace with social media analytics dashboard on screen, campaign performance graphs",
    "포트폴리오 완성": "a designer presenting portfolio on laptop screen, printed portfolio book open on desk",
    "실무 프로젝트": "a collaborative workspace with team members at laptops, whiteboard with project timeline",
    "AI 활용": "a futuristic workspace with multiple AI tool interfaces on screens, neural network visualization in background",
    "생성형 AI": "a creative tech workspace with AI image generation on one screen and AI text on another, neon blue accents",
    "시각디자인": "a graphic designer's studio with typography work on screen, pantone color books and printed samples",
    "UX디자인": "a UX research lab with usability testing setup, wireframe sketches on desk, monitor showing user flow diagram",
    "SW개발": "a software development environment with multiple IDE windows, Git terminal, agile board in background",
}

FIELD_DEFAULT_SCENES = {
    "AI": "a futuristic tech workspace with AI interfaces on screens, holographic data visualization, cool blue neon ambient lighting",
    "영상": "a professional video production studio with camera, monitors showing editing timeline, warm studio lighting",
    "디자인": "a designer's bright studio with large monitor showing design work, color swatches and sketches on desk",
    "출판": "a warm publishing studio with books, printed layouts, InDesign on screen, amber desk lamp lighting",
    "콘텐츠": "a modern content creator's studio with camera, ring light, laptop showing social media feeds",
    "마케팅": "a marketing team workspace with analytics dashboards, campaign metrics on screens, collaborative atmosphere",
    "데이터": "a data science workspace with complex visualizations and code on dual monitors, organized desk setup",
    "코딩": "a developer workspace with code on dark-themed screens, mechanical keyboard, minimalist desk with plants",
    "default": "a bright modern classroom with laptops, students engaged in learning, natural light through large windows",
}


def _get_sora_scenes(goal_keywords, field, ncs_sub=None):
    """추출된 키워드에서 Grok 장면을 매핑합니다."""
    scenes = []
    used = set()
    if ncs_sub and ncs_sub in TOOL_SCENE_MAP:
        scenes.append({"keyword": ncs_sub, "scene": TOOL_SCENE_MAP[ncs_sub]})
        used.add(ncs_sub)
    if goal_keywords:
        for kw in goal_keywords.split(" · "):
            kw = kw.strip()
            if kw and kw not in used:
                scene = TOOL_SCENE_MAP.get(kw)
                if scene:
                    scenes.append({"keyword": kw, "scene": scene})
                    used.add(kw)
    if not scenes:
        scenes.append({
            "keyword": field,
            "scene": FIELD_DEFAULT_SCENES.get(field, FIELD_DEFAULT_SCENES["default"]),
        })
    return scenes[:3]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [아이디어 5] 분야+키워드별 색상 팔레트 & 무드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VISUAL_MOOD = {
    "AI": {
        "palette": "neon blue (#00D4FF) and dark navy (#0A1628) with electric purple accents (#7B61FF)",
        "mood": "futuristic, high-tech, sleek",
        "lighting": "cool ambient neon glow with subtle lens flare",
        "texture": "glass and holographic surfaces, floating UI elements",
    },
    "영상": {
        "palette": "warm orange (#FF6B35) and deep charcoal (#2D2D2D) with golden highlight (#FFD93D)",
        "mood": "cinematic, dynamic, creative",
        "lighting": "warm studio lighting with dramatic shadows, slight film grain",
        "texture": "camera lens bokeh, film strip textures, timeline interface elements",
    },
    "디자인": {
        "palette": "vibrant coral (#FF6F61) and clean white (#FFFFFF) with mint green (#98DFAF)",
        "mood": "clean, modern, inspiring",
        "lighting": "bright natural light from large windows, soft shadows",
        "texture": "grid patterns, clean geometric shapes, gradient overlays",
    },
    "출판": {
        "palette": "warm amber (#F4A261) and cream (#FAF3E0) with deep brown (#5C3D2E)",
        "mood": "warm, cozy, intellectual",
        "lighting": "warm desk lamp glow, golden hour tones",
        "texture": "paper textures, book spines, elegant serif typography",
    },
    "콘텐츠": {
        "palette": "hot pink (#FF1493) and bright yellow (#FFE600) with electric blue (#00BFFF)",
        "mood": "energetic, trendy, social-media-native",
        "lighting": "bright ring light with colorful RGB backlight",
        "texture": "social media UI elements, emoji overlays, notification badges",
    },
    "마케팅": {
        "palette": "bold red (#E63946) and navy (#1D3557) with clean white (#F1FAEE)",
        "mood": "professional, data-driven, strategic",
        "lighting": "clean office lighting with screen glow on face",
        "texture": "chart elements, growth arrows, dashboard cards",
    },
    "데이터": {
        "palette": "teal (#2EC4B6) and dark slate (#1A1A2E) with bright green (#00FF87)",
        "mood": "analytical, precise, intelligent",
        "lighting": "monitor glow in dim room, matrix-style ambience",
        "texture": "data visualization elements, scatter plots, neural network nodes",
    },
    "코딩": {
        "palette": "VS Code blue (#007ACC) and dark (#1E1E1E) with green (#4EC9B0) accents",
        "mood": "focused, technical, hacker-chic",
        "lighting": "dark room with multiple monitor glow, RGB keyboard lighting",
        "texture": "code syntax highlighting, terminal text, bracket patterns",
    },
    "이커머스": {
        "palette": "warm orange (#FF6B00) and clean white (#FFFFFF) with green (#2DB400) accents",
        "mood": "entrepreneurial, dynamic, commercial",
        "lighting": "bright product photography lighting, clean white background",
        "texture": "product packaging, shopping cart icons, order notification badges",
    },
    "산업안전": {
        "palette": "safety yellow (#FFD100) and industrial gray (#4A4A4A) with alert red (#E53E3E)",
        "mood": "professional, authoritative, safety-focused",
        "lighting": "industrial overhead lighting, construction site ambient",
        "texture": "safety signage, hard hat textures, checklist patterns",
    },
    "default": {
        "palette": "sky blue (#4A90D9) and warm gray (#F5F5F5) with accent yellow (#FFC107)",
        "mood": "friendly, approachable, professional",
        "lighting": "bright and welcoming, natural classroom light",
        "texture": "notebook textures, clean rounded UI elements",
    },
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [아이디어 2] 과정 제목/목표에서 동적 훅 생성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _extract_title_core(title):
    """제목에서 핵심 명사구를 추출합니다."""
    clean = re.sub(r'\([^)]*\)', '', title).strip()
    clean = re.sub(r'^[\[\]【】\s]+|[\[\]【】\s]+$', '', clean)
    core = re.sub(r'\s*(양성|전문가|실무|입문|심화|기초|마스터|스페셜리스트|전문)\s*과정.*$', '', clean)
    return core.strip() if core.strip() else clean


def _generate_dynamic_hook(title, field, goal_summary=""):
    """과정 제목과 훈련목표에서 동적 훅 문장을 생성합니다."""
    core = _extract_title_core(title)

    dynamic_templates = [
        f"{core}, 지금 시작할 타이밍이에요",
        f"{core} 배우고 싶었다면 주목!",
        f"제주에서 {core} 전문가로 성장하세요",
        f"{core}, 국비로 배울 수 있어요",
    ]

    goal_hooks = []
    if goal_summary:
        first_kw = goal_summary.split(" · ")[0]
        goal_hooks = [
            f"{first_kw}부터 실무까지 한 번에",
            f"{first_kw} 마스터하는 가장 빠른 길",
        ]

    field_hooks = {
        "AI": ["AI 시대, 쓰는 사람이 기회를 잡아요", "AI가 내 일을 도와주는 세상, 준비됐나요?"],
        "영상": ["영상 하나로 세상과 소통하는 법", "촬영부터 편집까지, 내 손으로 만드는 영상"],
        "디자인": ["디자인 감각, 배우면 달라져요", "비전공자도 시작할 수 있는 디자인"],
        "출판": ["내 이름으로 책을 만드는 첫걸음", "전자책부터 오디오북까지, 1인 출판 시대"],
        "콘텐츠": ["콘텐츠로 나만의 커리어를 만드세요", "SNS 콘텐츠, 기획부터 배워야 다르죠"],
        "마케팅": ["데이터로 성과를 만드는 마케팅", "디지털 마케팅, 실전이 답이에요"],
        "데이터": ["데이터로 말하는 시대, 분석 스킬 UP", "숫자 속에서 인사이트를 찾아내는 법"],
        "코딩": ["코딩, 이제 선택이 아니라 필수예요", "개발자의 첫걸음, 제주에서 시작하세요"],
        "이커머스": ["내 가게를 온라인에 여는 가장 빠른 길", "스마트스토어, 제대로 배우면 달라요"],
        "산업안전": ["안전관리, 이제 선택이 아니라 법적 의무예요", "산업안전기사, 국가자격 1위의 이유"],
        "default": ["새로운 기술, 제주에서 배워요", "국비지원으로 부담 없이 스킬업!"],
    }

    # 짧은 훅 우선: field_hooks → goal_hooks → dynamic_templates
    # 나레이션에서 잘리지 않도록 완전한 문장만 사용
    short_candidates = field_hooks.get(field, field_hooks["default"]) + goal_hooks
    long_candidates = dynamic_templates

    idx = hash(title) % max(len(short_candidates), 1)
    if short_candidates:
        hook = short_candidates[idx % len(short_candidates)]
    else:
        hook = long_candidates[idx % len(long_candidates)]
    return hook


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [아이디어 4] D-day 기반 CTA 동적 생성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _generate_cta(course_data):
    """훈련시작일까지 남은 기간에 따라 CTA 문구와 긴급도를 결정합니다."""
    start_str = course_data.get("traStartDate", "")
    if not start_str or len(start_str) < 8:
        return "지금 바로 신청하세요! 👆", "프로필 링크에서 확인", "normal"
    try:
        start_date = datetime.strptime(start_str[:8], "%Y%m%d")
        d_day = (start_date - datetime.now()).days
    except ValueError:
        return "지금 바로 신청하세요! 👆", "프로필 링크에서 확인", "normal"

    if d_day <= 0:
        return None, None, "expired"
    elif d_day <= 7:
        return f"마감 D-{d_day}! 서두르세요 🔥", "마감 임박! 프로필 링크에서 바로 신청", "urgent"
    elif d_day <= 14:
        return f"D-{d_day}, 놓치면 아까워요!", "선착순 마감 · 프로필 링크에서 확인", "soon"
    elif d_day <= 30:
        return "모집 중! 선착순 마감 📢", "지금 신청하면 자리 확보", "open"
    else:
        return "지금 바로 신청하세요! 👆", "프로필 링크에서 확인", "normal"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [아이디어 3] 과정 특성 맞춤 혜택 문구
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _generate_benefit_line(course_data, ctype, hours):
    """과정 시간·비용·기간을 조합하여 구체적인 혜택 한 줄을 생성합니다."""
    start_str = course_data.get("traStartDate", "")
    end_str = course_data.get("traEndDate", "")
    months = 0
    if start_str and end_str and len(start_str) >= 8 and len(end_str) >= 8:
        try:
            s = datetime.strptime(start_str[:8], "%Y%m%d")
            e = datetime.strptime(end_str[:8], "%Y%m%d")
            months = max(1, round((e - s).days / 30))
        except ValueError:
            pass

    if ctype == "long":
        if months > 0:
            return f"{months}개월간 월 최대 40만원 받으며 배우기 💰"
        return "자부담 10%, 장려금·수당 월 최대 40만원 💰"
    elif ctype == "general":
        if months > 0:
            return f"{months}개월 과정, 월 20만원 장려금, 자부담 10% 💰"
        return "자부담 10%, 훈련장려금 월 최대 20만원 💰"
    else:
        if hours > 0:
            weeks = max(1, round(hours / 40))
            if weeks <= 4:
                return f"약 {weeks}주 만에 실무 스킬 완성, 자부담 10%만! 💰"
            return f"자부담 10%로 {hours}시간 알차게 배우기 💰"
        return "자부담 10%로 부담 없이 배우기 💰"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 훈련목표 핵심 키워드 요약
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def summarize_training_goal(training_goal, max_keywords=3):
    """훈련목표 텍스트에서 핵심 키워드를 추출합니다."""
    if not training_goal or not training_goal.strip():
        return ""
    text = training_goal.strip()

    keyword_groups = [
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
        {"patterns": [
            (r'생성형\s*AI', "생성형 AI"),
            (r'ChatGPT|챗GPT', "ChatGPT"),
            (r'미드저니|Midjourney', "미드저니"),
            (r'Stable\s*Diffusion', "Stable Diffusion"),
            (r'머신러닝', "머신러닝"),
            (r'딥러닝', "딥러닝"),
            (r'AI|인공지능', "AI 활용"),
        ], "max": 1},
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
# SEO 키워드 매핑
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KEYWORD_MAP = {
    "AI": ["AI교육", "인공지능교육", "AI활용", "ChatGPT교육",
           "생성형AI활용", "AI챗봇교육", "AI영상제작"],
    "영상": ["영상편집교육", "영상제작", "유튜브교육", "프리미어프로",
            "숏폼콘텐츠제작", "드론촬영교육", "릴스편집"],
    "디자인": ["디자인교육", "UI교육", "UX교육", "피그마교육", "웹디자인",
              "브랜딩디자인교육", "패키지디자인"],
    "출판": ["출판교육", "인디자인교육", "전자책제작", "편집디자인"],
    "멀티미디어": ["멀티미디어교육", "디지털콘텐츠"],
    "콘텐츠": ["콘텐츠제작", "크리에이터교육", "SNS콘텐츠", "숏폼제작"],
    "마케팅": ["디지털마케팅", "SNS마케팅교육", "마케팅교육"],
    "데이터": ["데이터분석교육", "빅데이터", "파이썬교육"],
    "코딩": ["코딩교육", "프로그래밍교육", "개발자교육"],
    "이커머스": ["스마트스토어교육", "이커머스교육", "온라인쇼핑몰창업",
                "라이브커머스교육", "상세페이지제작"],
    "산업안전": ["산업안전교육", "안전관리자교육", "산업안전기사",
                "중대재해처벌법교육", "위험성평가교육"],
}

COMMON_SEARCH_KEYWORDS = [
    "제주무료교육", "제주국비지원", "내일배움카드",
    "제주취업", "제주직업훈련", "제주특화훈련",
    "제주디지털전환", "제주AI교육",
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 공감형 도입부
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EMPATHY_INTROS = {
    "AI": [
        "\"나도 AI를 배워야 하나?\" 고민만 하다가 시간이 흘러가고 있다면, 지금이 딱 시작할 타이밍이에요.",
        "ChatGPT, 미드저니, AI 영상 생성... 세상은 빠르게 바뀌고 있는데, 어디서부터 배워야 할지 막막하셨죠? 제주에서 체계적으로 배울 수 있는 기회가 열렸어요.",
        "\"AI가 내 일자리를 대체한다\"는 뉴스, 불안하기만 하셨나요? AI를 활용하는 쪽에 서면 오히려 기회가 됩니다.",
        "AI 시대에 뒤처질까 불안하다면? 지금 배우는 사람과 안 배우는 사람의 격차는 1년 뒤 엄청나게 벌어집니다.",
        "AI 개발자 부족률이 57.6%이고, 기업 69%가 채용할 때 AI 역량을 본다는 사실 아셨나요? 지금 AI를 배우면 취업 시장에서 확실한 경쟁력이 됩니다.",
        "제주도가 AI·디지털 대전환에 918억 원을 투자하고, ETRI·네이버클라우드와 제주 특화 AI를 개발하고 있어요. 제주에서 AI 인력 수요가 폭발적으로 늘어나는 중입니다.",
    ],
    "영상": [
        "유튜브, 릴스, 숏폼... 영상이 대세인 건 알겠는데, 혼자 독학하기엔 너무 막막하셨죠? 촬영부터 편집, AI 활용까지 한번에 배울 수 있는 과정이 있어요.",
        "\"나도 영상 하나 만들어볼까?\" 한번쯤 생각해보셨을 거예요. 스마트폰 하나로 시작해서 프로 수준까지, 제주에서 제대로 배워보세요.",
        "영상 편집 배우고 싶었는데 비용이 걱정이었다면, 좋은 소식이에요. 자부담 10%로 전문 영상 제작 기술을 배울 수 있는 과정이 제주에서 열려요.",
        "영상 편집 독학하다 포기한 경험, 있지 않으세요? 체계적으로 배우면 완전히 다릅니다.",
        "숏폼 이용률 70.7%, 크리에이터 산업 5.5조 원 시대인데, 제주 크리에이터 비율은 겨우 1.7%예요. 지금 제주에서 영상을 배우면 기회가 열립니다.",
        "제주는 전국 최대 드론특별자유화구역(1,283km²)에, 콘텐츠진흥원 121억 원 투자까지. 영상 제작을 배우기에 제주만큼 좋은 환경이 없어요.",
    ],
    "디자인": [
        "피그마, 포토샵, UI/UX... 디자인 도구는 많은데 뭘 어떻게 배워야 할지 막막하셨나요? 현업에서 바로 쓸 수 있는 스킬을 체계적으로 알려드려요.",
        "이직을 준비하면서 \"디자인 스킬이 있으면 좋겠다\" 생각해보신 적 있나요? 비전공자도 부담 없이 시작할 수 있는 과정이 제주에서 열립니다.",
        "디지털 시대에 디자인 감각은 모든 직군에서 필요해지고 있어요. 제주에서 체계적으로 디자인 역량을 키워보세요.",
        "포트폴리오 하나 없이 디자인 직군에 지원하고 계시진 않나요? 이 과정이면 수료와 동시에 실무 포트폴리오가 완성됩니다.",
        "글로벌 UI/UX 시장이 매년 32%씩 성장하고, Fortune 500 기업 95%가 피그마를 쓰는 시대예요. 지금 디자인을 배우면 일감이 넘칩니다.",
        "제주 카페·숙박·특산품 브랜딩 수요는 폭발적인데, 현지 디자인 업체는 대부분 5인 미만이에요. 디자인을 배우면 제주에서 바로 일할 수 있습니다.",
    ],
    "출판": [
        "\"내 책을 한 번 만들어보고 싶다\"는 꿈, 생각보다 가까이 있어요. AI와 전문 편집 도구를 활용하면 누구나 출판제작자가 될 수 있습니다.",
        "전자책, 오디오북, 독립출판... 출판의 세계가 달라지고 있어요. 기획부터 제작, 유통까지 한번에 배울 수 있는 기회를 놓치지 마세요.",
        "1인 출판 시대, 기획부터 편집까지 혼자 할 수 있다면? 생각보다 문턱이 낮아졌어요.",
    ],
    "이커머스": [
        "242조 원 이커머스 시장에서 제주 감귤이 날개를 달고 있어요. 온라인 직거래로 유통비를 절반 가까이 줄인 제주 농가, 서귀포 온라인몰은 누적 362억 원을 돌파했거든요.",
        "스마트스토어 연매출 1억 원 이상 셀러가 4만 5,000명을 넘었다는 사실 아셨나요? 라이브커머스 3.5조 원, AI 커머스까지 합쳐지면서 1인 셀러에게 역대급 기회가 열리고 있어요.",
        "제주 감귤 농가가 스마트스토어로 유통비를 58%에서 32%로 줄이고, 수취가를 60% 이상 올렸다는 거 알고 계셨나요? 온라인 판매, 이제 선택이 아니라 필수예요.",
        "소상공인 디지털 활용률이 아직 15.4%라는 건 뒤집어 보면, 지금 시작하는 사람에게 압도적인 선점 효과가 있다는 뜻이에요. 제주에서 스마트스토어를 배울 수 있는 국비지원 과정이 열렸어요.",
        "네이버가 AI 추천 기반 '발견형 쇼핑'을 도입하면서 구매 전환율이 2배 이상 뛰었어요. 숏폼·라이브·AI가 바꾸는 이커머스 시대, 제주에서 국비지원으로 배울 수 있는 기회를 소개해요.",
        "제주도가 전국 최초로 크리에이터 전담부서를 만들고 50억 원 규모 펀드를 조성한 이유가 뭘까요? 온라인 판매가 제주 경제의 핵심이 되고 있기 때문이에요.",
    ],
    "산업안전": [
        "산업안전기사 응시자 연 19.6만 명, 국가기술자격 기사 등급 1위라는 사실 아셨나요? 지금 가장 뜨거운 자격증입니다.",
        "중대재해처벌법이 5인 이상 전 사업장으로 확대되면서, 안전관리자 수요가 폭발하고 있어요. 자격증만 있으면 취업 기회가 넘칩니다.",
        "50인 미만 기업의 77%가 아직 법 준수를 못 한 상태예요. 안전관리를 배우면 어디서든 필요한 인재가 됩니다.",
        "건설업 사망사고의 46.9%가 안전관리 부실에서 시작돼요. 안전관리 전문가는 생명을 살리는 직업입니다.",
        "제주는 풍력발전 2,345MW 확대, 건설·관광 인프라 투자가 이어지면서 안전관리 전문인력 수요가 급증하고 있어요.",
    ],
    "default": [
        "새로운 기술을 배우고 싶은데, 어디서 시작해야 할지 막막하셨나요? 내일배움카드만 있으면 자부담 10%로 바로 시작할 수 있는 과정이 열렸어요.",
        "이직을 고민하거나, 새로운 분야에 도전하고 싶은 마음... 누구나 한번쯤 있죠. 제주에서 부담 없이 새로운 기술을 배울 수 있는 기회를 소개합니다.",
        "경력을 쌓고 싶은데 교육비가 부담이셨나요? 내일배움카드로 자부담 10%만 내고 전문 기술을 배울 수 있어요.",
        "국비지원 교육, 잘못 선택하면 같은 과정은 다시 들을 수 없다는 사실 아셨나요? 그래서 첫 선택이 중요합니다.",
        "\"배우고 싶은 건 많은데 시간도 돈도 없다\"는 말, 더 이상 핑계가 안 돼요. 국비지원이면 가능하거든요.",
    ],
}


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
    """
    네이버 블로그 SEO에 최적화된 제목을 생성합니다.

    전략:
    - 롱테일 키워드를 제목 앞쪽에 배치
    - 25자 이내 목표 (검색 결과에서 잘리지 않도록)
    - 연도 포함으로 최신성 확보
    - 예: "제주 AI영상편집 국비교육 2026"
    """
    from benefits_helper import get_course_type
    title = course_data.get("title", "")
    ctype = get_course_type(course_data)
    year = datetime.now().year
    field = detect_course_field(title, course_data.get("ncsCd"))

    # 과정명에서 핵심 키워드 추출 (괄호, 접두사 제거)
    core = _extract_title_core(title)

    # 과정명에서 구체적 도구/스킬 키워드 추출
    TOOL_KEYWORDS = [
        "프리미어프로", "프리미어 프로", "에프터이펙트", "에프터 이펙트",
        "다빈치리졸브", "피그마", "인디자인", "포토샵", "일러스트레이터",
        "파이썬", "블렌더", "ChatGPT", "챗GPT", "미드저니",
        "드론", "바리스타", "3D모델링", "AI",
        "스마트스토어", "산업안전기사", "건설안전기사",
    ]
    found_tool = ""
    for tool in TOOL_KEYWORDS:
        if tool.upper() in core.upper().replace(" ", ""):
            found_tool = tool.replace(" ", "")
            break

    # 분야 축약명
    field_short = {
        "AI": "AI", "영상": "영상편집", "디자인": "디자인",
        "출판": "출판편집", "콘텐츠": "콘텐츠제작", "마케팅": "디지털마케팅",
        "데이터": "데이터분석", "코딩": "코딩", "멀티미디어": "멀티미디어",
        "이커머스": "스마트스토어", "산업안전": "산업안전",
    }
    short = field_short.get(field, "직업훈련")

    # 핵심 키워드 조합
    # - 도구명이 분야와 관련 있으면 조합 (AI + 영상편집 → AI영상편집)
    # - 도구명이 분야와 무관하면 도구명만 사용 (드론 ≠ 영상편집)
    TOOL_FIELD_COMPAT = {
        "AI": ["영상편집", "디자인", "디지털마케팅", "콘텐츠제작", "데이터분석", "코딩"],
        "ChatGPT": ["디지털마케팅", "콘텐츠제작", "코딩"],
        "챗GPT": ["디지털마케팅", "콘텐츠제작", "코딩"],
        "미드저니": ["디자인", "콘텐츠제작"],
    }
    if found_tool and found_tool != short:
        compat_fields = TOOL_FIELD_COMPAT.get(found_tool, [])
        if short in found_tool or found_tool in short:
            # 도구와 분야가 겹치면 도구만 사용
            core_keyword = found_tool
        elif short in compat_fields:
            # AI + 영상편집처럼 의미상 호환되면 조합
            core_keyword = f"{found_tool}{short}"
        else:
            # 드론 + 영상편집처럼 호환 안 되면 도구만 사용
            core_keyword = found_tool
    elif len(core) <= 12:
        core_keyword = core
    else:
        core_keyword = short

    # 혜택 태그 (짧게)
    if ctype == "long":
        benefit_tag = "장려금+수당"
    elif ctype == "general":
        benefit_tag = "장려금지원"
    else:
        benefit_tag = "국비지원"

    # 제목 조합: "제주 {핵심} {benefit_tag} {연도}" (25자 이내 목표)
    seo_title = f"제주 {core_keyword} {benefit_tag} {year}"

    # 25자 초과 시 순차 축약
    if len(seo_title) > 25:
        seo_title = f"제주 {core_keyword} 국비 {year}"
    if len(seo_title) > 25:
        seo_title = f"제주 {core_keyword[:8]} 국비 {year}"
    if len(seo_title) > 25:
        seo_title = f"제주 {short} 국비 {year}"

    return seo_title


def generate_empathy_intro(course_data):
    """
    과정별로 차별화된 공감형 도입부를 생성합니다.

    SEO v4 개선:
    - field_research.json 캐시가 있으면 연구 기반 도입부 우선 사용
    - 첫 200자 안에 핵심 키워드(제주, 국비지원, 분야) 반드시 포함
    - 대화체(~거든요, ~이에요) 혼용으로 AI 패턴 회피
    """
    from benefits_helper import get_course_type, get_total_hours

    title = course_data.get("title", "")
    field = detect_course_field(title, course_data.get("ncsCd"))
    ctype = get_course_type(course_data)
    hours = get_total_hours(course_data)
    self_cost = course_data.get("selfCost", "")

    # 1순위: field_research.json 캐시에서 연구 기반 도입부 로드
    try:
        from field_research_helper import get_empathy_hooks
        cached_hooks = get_empathy_hooks(field)
        if cached_hooks:
            intro = random.choice(cached_hooks)
        else:
            intros = EMPATHY_INTROS.get(field, EMPATHY_INTROS["default"])
            intro = random.choice(intros)
    except ImportError:
        intros = EMPATHY_INTROS.get(field, EMPATHY_INTROS["default"])
        intro = random.choice(intros)

    # 과정 데이터 기반 추가 후킹 문장 (2번째 문단)
    data_hook = ""
    if self_cost and self_cost != "0":
        data_hook = f"자부담 {self_cost}이면 시작할 수 있어요."
    elif ctype == "long" and hours > 0:
        months = max(1, round(hours / 160))
        data_hook = f"{months}개월 과정인데, 매달 최대 40만원까지 받으면서 배울 수 있어요."
    elif ctype == "general" and hours > 0:
        data_hook = f"총 {hours}시간 과정이고, 매달 최대 20만원 훈련장려금도 받을 수 있어요."

    if data_hook:
        intro += f"\n\n{data_hook}"

    # SEO: 첫 200자 안에 "제주"와 "국비" 키워드가 없으면 보강
    first_200 = intro[:200]
    if "제주" not in first_200:
        intro += "\n\n제주에서 진행되는 이 과정, 지금 바로 알아보세요."

    return intro


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 인스타그램 해시태그 / 캡션
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_blog_hashtags(course_data):
    """네이버 블로그용 해시태그를 생성합니다."""
    title = course_data.get("title", "")
    field = detect_course_field(title, course_data.get("ncsCd"))
    year = datetime.now().year
    common = [
        f"#{year}국비지원", "#내일배움카드", "#제주국비지원교육",
        "#제주취업", "#제주직업훈련", "#제주특화훈련",
        "#국비지원교육추천", "#내일배움카드추천",
    ]
    field_tags = {
        "AI": ["#AI교육", "#인공지능교육", "#ChatGPT교육", "#생성형AI", "#AI활용교육", "#제주AI교육"],
        "영상": ["#영상편집교육", "#영상제작", "#프리미어프로", "#숏폼콘텐츠", "#드론촬영", "#제주영상제작"],
        "디자인": ["#디자인교육", "#UIUX교육", "#피그마", "#브랜딩디자인", "#제주브랜딩", "#웹디자인교육"],
        "출판": ["#출판교육", "#인디자인", "#전자책제작", "#편집디자인"],
        "콘텐츠": ["#콘텐츠제작교육", "#크리에이터교육", "#SNS콘텐츠", "#숏폼제작"],
        "마케팅": ["#디지털마케팅교육", "#SNS마케팅", "#마케팅교육"],
        "데이터": ["#데이터분석교육", "#빅데이터", "#파이썬교육"],
        "코딩": ["#코딩교육", "#프로그래밍교육", "#개발자교육"],
        "이커머스": ["#스마트스토어교육", "#온라인쇼핑몰창업", "#이커머스교육", "#라이브커머스", "#제주특산품판매"],
        "산업안전": ["#산업안전기사", "#안전관리자교육", "#중대재해처벌법", "#산업안전교육", "#위험성평가"],
        "default": ["#직업훈련", "#스킬업", "#자기계발", "#커리어전환", "#제주디지털전환"],
    }
    specific = field_tags.get(field, field_tags["default"])
    all_tags = common + specific
    seen = set()
    unique = []
    for t in all_tags:
        if t not in seen:
            unique.append(t)
            seen.add(t)
    # SEO 연구: 태그 5~10개가 최적, 과도한 태그는 어뷰징 의심
    return " ".join(unique[:10])


def generate_instagram_hashtags(course_data):
    """
    인스타그램 해시태그 5~8개를 선별합니다.

    2025년 해시태그 팔로우 폐지 이후, 소수 정예 해시태그가 더 효과적.
    대형 1~2개 + 중소형(지역+분야) 4~5개 = 총 5~8개
    """
    title = course_data.get("title", "")
    field = detect_course_field(title, course_data.get("ncsCd"))
    year = datetime.now().year

    # 대형 태그 (1~2개)
    big_tags = [f"#{year}국비지원", "#내일배움카드"]

    # 지역 태그 (1~2개)
    local_tags = ["#제주국비지원", "#제주직업훈련"]

    # 분야별 태그 (2~3개)
    field_tags = {
        "AI": ["#AI교육", "#인공지능교육", "#ChatGPT"],
        "영상": ["#영상편집교육", "#영상제작", "#프리미어프로"],
        "디자인": ["#디자인교육", "#UIUX", "#피그마"],
        "출판": ["#출판교육", "#인디자인", "#편집디자인"],
        "콘텐츠": ["#콘텐츠제작", "#크리에이터교육"],
        "마케팅": ["#디지털마케팅", "#SNS마케팅"],
        "데이터": ["#데이터분석", "#파이썬"],
        "코딩": ["#코딩교육", "#프로그래밍"],
        "이커머스": ["#스마트스토어", "#온라인창업", "#제주특산품"],
        "산업안전": ["#산업안전기사", "#안전관리자", "#중대재해처벌법"],
        "default": ["#스킬업", "#자기계발"],
    }
    specific = field_tags.get(field, field_tags["default"])

    # 조합: 대형 1~2 + 지역 1~2 + 분야 2~3 = 5~7개
    all_tags = []
    all_tags.extend(random.sample(big_tags, min(1, len(big_tags))))
    all_tags.extend(random.sample(local_tags, min(2, len(local_tags))))
    all_tags.extend(random.sample(specific, min(3, len(specific))))
    all_tags.append("#제주특화훈련")

    # 중복 제거
    seen = set()
    unique_tags = []
    for tag in all_tags:
        if tag not in seen:
            unique_tags.append(tag)
            seen.add(tag)

    return "\n\n.\n.\n.\n" + " ".join(unique_tags[:8])


def generate_instagram_caption(course_data):
    """
    인스타그램 캡션을 생성합니다.

    개선사항:
    - 첫 문단에 자연어 키워드 삽입 (해시태그 팔로우 폐지 대응)
    - 저장·공유 유도 CTA 추가 (알고리즘 최우선 신호)
    - 캡션 키워드: 제주 + 분야 + 국비지원 + 연도
    """
    from benefits_helper import get_course_type, get_benefits_text
    title = course_data.get("title", "")
    institution = course_data.get("institution", "")
    period = course_data.get("period", "")
    time_info = course_data.get("time", "")
    ctype = get_course_type(course_data)
    benefits = get_benefits_text(course_data)
    field = detect_course_field(title, course_data.get("ncsCd"))
    year = datetime.now().year
    field_emoji = {
        "AI": "🤖", "영상": "🎬", "디자인": "🎨", "출판": "📚",
        "멀티미디어": "🖥️", "콘텐츠": "📱", "마케팅": "📊",
        "데이터": "📈", "코딩": "💻",
        "이커머스": "🛒", "산업안전": "🦺",
    }
    emoji = field_emoji.get(field, "📌")
    hook = _generate_dynamic_hook(title, field)

    # 자연어 키워드 문장 (검색·추천 알고리즘용, 분야별 트렌드 반영)
    # 1순위: field_research.json 캐시, 2순위: 하드코딩
    keyword_sentence = None
    try:
        from field_research_helper import get_instagram_keyword_sentence
        keyword_sentence = get_instagram_keyword_sentence(field, year)
    except ImportError:
        pass

    if not keyword_sentence:
        field_keyword_sentence = {
            "AI": f"{year}년 제주도가 AI·디지털 대전환에 918억 원을 투자하는 지금, 제주에서 국비지원으로 AI 활용 교육을 배울 수 있는 과정을 소개합니다.",
            "영상": f"숏폼 이용률 70.7% 시대, 제주 크리에이터 비율은 겨우 1.7%. {year}년 제주에서 국비지원으로 영상편집을 배울 수 있는 과정을 소개합니다.",
            "디자인": f"제주 카페·숙박 브랜딩 수요는 폭발적인데 디자인 인력은 부족. {year}년 제주에서 국비지원으로 디자인을 배울 수 있는 과정을 소개합니다.",
            "출판": f"{year}년 제주에서 국비지원으로 출판편집 교육을 배울 수 있는 과정을 소개합니다.",
            "콘텐츠": f"{year}년 제주에서 국비지원으로 콘텐츠 제작을 배울 수 있는 과정을 소개합니다.",
            "마케팅": f"{year}년 제주에서 국비지원으로 디지털마케팅을 배울 수 있는 과정을 소개합니다.",
            "데이터": f"{year}년 제주에서 국비지원으로 데이터분석을 배울 수 있는 과정을 소개합니다.",
            "코딩": f"{year}년 제주에서 국비지원으로 코딩을 배울 수 있는 과정을 소개합니다.",
            "이커머스": f"{year}년 온라인쇼핑 242조 원 시대, 제주 농가는 스마트스토어로 유통비를 절반으로 줄이고 있어요. 제주에서 국비지원으로 스마트스토어·라이브커머스를 배울 수 있는 과정을 소개합니다.",
            "산업안전": f"산업안전기사 응시자 연 19.6만 명, 국가자격 1위. {year}년 제주에서 국비지원으로 산업안전 교육을 받을 수 있는 과정을 소개합니다.",
        }
        keyword_sentence = field_keyword_sentence.get(field,
            f"{year}년 제주에서 국비지원으로 배울 수 있는 직업훈련 과정을 소개합니다.")

    caption = f"""{emoji} {hook}

{keyword_sentence}

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
    if ctype in ("general", "long"):
        caption += "🎁 훈련장려금 월 최대 20만원까지 받을 수 있어요\n"

    cta_text, cta_sub, urgency = _generate_cta(course_data)
    if urgency == "urgent":
        caption += f"\n🔥 {cta_text}\n"
    elif urgency == "soon":
        caption += f"\n⏰ {cta_text}\n"

    caption += """
👉 신청 방법이 궁금하다면?
프로필 링크에서 바로 확인하세요!"""

    # 훈련목표 요약 (있을 때만)
    training_goal = course_data.get("trainingGoal", "")
    if training_goal:
        import re
        text = re.sub(r'\d+\.\s*', '', training_goal)
        goal_sentences = [s.strip() for s in text.replace("\n", ".").split(".")
                          if s.strip() and len(s.strip()) > 15]
        if goal_sentences:
            caption += "\n\n📋 이 과정을 배우면?"
            for s in goal_sentences[:2]:
                caption += f"\n→ {s}"

    # 저장·공유 유도 CTA (알고리즘 최우선 신호)
    caption += "\n\n💾 나중에 신청하려면 이 게시물을 저장해두세요!"
    caption += "\n📩 제주에서 교육 찾는 친구에게 공유해주세요"

    hashtags = generate_instagram_hashtags(course_data)
    caption += hashtags
    return caption


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 릴스 영상 시스템 v3
# 원칙: 세그먼트당 장면 1개, 짧은 나레이션(1~2문장/세그먼트), Vrew 음성인식 자막
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 분야별 배경 장소 (30초 내내 동일 공간 유지)
def _clean_title(title):
    """(산대특) 접두사 제거한 깨끗한 과정명"""
    return title.replace("(산대특)", "").replace("산대특", "").strip()


def _goal_to_actions_kr(training_goal):
    """
    훈련목표에서 한국어 핵심 동작 2개를 추출합니다.
    나레이션/action_kr 표시용 (장면 묘사에는 사용하지 않음)
    """
    if not training_goal:
        return "", ""

    import re
    text = re.sub(r'\d+\.\s*', '', training_goal)
    sentences = [s.strip() for s in text.replace('\n', '.').split('.')
                 if s.strip() and len(s.strip()) > 5]

    if len(sentences) >= 2:
        return sentences[0], sentences[1]
    elif len(sentences) == 1:
        return sentences[0], ""
    else:
        return "", ""


# 과정 키워드 → (배경, 복장) 매핑 (seg1 전용)
FIELD_SETTING = {
    "드론정비": (
        "an outdoor drone test field with workbenches, spare parts, and a landed drone on the ground",
        "wearing a hard hat, work coveralls, and holding a toolkit",
    ),
    "드론촬영": (
        "an open outdoor landscape with a drone landing pad and portable monitors on a folding table",
        "wearing an outdoor vest with pockets, cap, and holding a drone controller",
    ),
    "3D모델링": (
        "a high-tech studio with a large curved monitor displaying 3D wireframe models and a graphics tablet on the desk",
        "wearing a collared shirt and glasses, with a stylus pen in hand",
    ),
    "드론": (
        "an open airfield with a drone on the ground, flight controller, and a tablet showing aerial maps",
        "wearing a reflective safety vest and cap, holding a drone controller",
    ),
    "3D": (
        "a digital design studio with dual large monitors showing 3D rendered objects and modeling software",
        "wearing a collared shirt, with a stylus pen in hand",
    ),
    "마케팅": (
        "a bright co-working cafe space with a laptop showing SNS analytics dashboards and a smartphone on the table",
        "wearing smart casual business attire",
    ),
    "AI": (
        "a modern tech office with dual monitors showing AI dashboards, code, and neural network visualizations",
        "wearing a neat business casual shirt",
    ),
    "영상편집": (
        "a video editing studio with an ultrawide monitor showing a timeline, color grading panels, and studio monitors",
        "wearing a casual creative outfit with headphones around the neck",
    ),
    "영상": (
        "a video production studio with a professional camera on a tripod, lighting rigs, and a director's monitor",
        "wearing a casual creative outfit with a lanyard badge",
    ),
    "콘텐츠": (
        "a content creation studio with a ring light, camera on tripod, and a laptop showing social media feeds",
        "wearing a casual outfit with a small microphone clipped on",
    ),
    "디자인": (
        "a bright design studio with a large display showing UI mockups, a pen tablet, and color swatches on the wall",
        "wearing a turtleneck and neat trousers",
    ),
    "출판": (
        "a cozy publishing workspace with bookshelves, manuscript pages spread on the desk, and a laptop showing page layouts",
        "wearing smart glasses and a cardigan",
    ),
    "바리스타": (
        "a stylish cafe behind the counter with an espresso machine, coffee grinder, and cups lined up",
        "wearing a barista apron over a neat shirt",
    ),
    "데이터": (
        "an analytics office with multiple monitors showing data charts, graphs, and dark-themed dashboards",
        "wearing business casual with rolled-up sleeves",
    ),
    "코딩": (
        "a developer workspace with dual monitors showing syntax-highlighted code, a mechanical keyboard, and a plant on the desk",
        "wearing a hoodie and glasses",
    ),
    "관광": (
        "an outdoor scenic Jeju landscape with a laptop on a portable table and camera equipment nearby",
        "wearing outdoor casual clothes with a camera bag",
    ),
    "정비": (
        "a professional maintenance workshop with diagnostic tools, parts shelves, and equipment on the workbench",
        "wearing work coveralls and safety gloves",
    ),
    "스마트스토어": (
        "a bright home office with a laptop showing an online store dashboard, product packages neatly stacked on a shelf",
        "wearing a casual smart outfit",
    ),
    "이커머스": (
        "a product photography studio with a laptop showing an e-commerce dashboard, packaged goods and shipping boxes nearby",
        "wearing a casual smart outfit with an apron",
    ),
    "산업안전": (
        "a safety training room with PPE equipment on display, safety posters on walls, and a monitor showing risk assessment software",
        "wearing a safety helmet, reflective vest, and holding a clipboard",
    ),
    "안전관리": (
        "a construction site office with safety inspection checklists on desk, a hard hat, and a monitor showing safety dashboards",
        "wearing a hard hat and reflective safety vest",
    ),
    "default": (
        "a bright modern classroom with laptops on desks, a whiteboard, and large windows with natural light",
        "wearing smart casual attire",
    ),
}


def _get_setting(title):
    """과정명에서 키워드 매칭하여 (배경, 복장) 반환."""
    for keyword in FIELD_SETTING:
        if keyword == "default":
            continue
        if keyword in title:
            return FIELD_SETTING[keyword]
    return FIELD_SETTING["default"]


# 과정 키워드 → 영문 행동 묘사 (seg2, seg3)
FIELD_ACTIONS_EN = {
    "드론정비": (
        "inspects and repairs drone components, checking propellers and rotors with tools",
        "tests the repaired drone, reviewing maintenance checklist on a tablet",
    ),
    "드론촬영": (
        "operates a drone controller, launching the drone for aerial photography",
        "reviews captured aerial footage on a monitor and adjusts flight path",
    ),
    "3D모델링": (
        "works on 3D modeling software, rotating digital objects on a large monitor",
        "reviews a rendered 3D terrain model and adjusts textures on screen",
    ),
    "드론": (
        "operates drone control equipment in an open field, monitoring flight on a tablet",
        "inspects drone hardware and reviews aerial data on screen",
    ),
    "3D": (
        "creates 3D digital content on a large screen with modeling software",
        "reviews and refines a 3D rendered model on monitor",
    ),
    "마케팅": (
        "creates brand marketing content on a laptop using AI-powered tools",
        "analyzes campaign performance metrics and charts on screen",
    ),
    "AI": (
        "works with an AI dashboard on screen, adjusting parameters and reviewing outputs",
        "tests AI-generated content results and fine-tunes the model on laptop",
    ),
    "영상편집": (
        "edits video footage on a timeline with professional editing software",
        "color-grades and reviews the final cut on a large monitor",
    ),
    "영상": (
        "operates a professional video camera, adjusting angles and lighting",
        "edits video clips on editing software with multiple monitors",
    ),
    "콘텐츠": (
        "creates digital content with a camera setup and ring light",
        "reviews content analytics and engagement metrics on a laptop",
    ),
    "디자인": (
        "designs UI mockups on a large monitor with a pen tablet",
        "reviews design iterations and adjusts layout details on screen",
    ),
    "출판": (
        "works on book layout design with publishing software on screen",
        "reviews printed manuscript pages and adjusts typography on laptop",
    ),
    "바리스타": (
        "operates an espresso machine and prepares coffee with precise technique",
        "pours latte art into a cup with careful hand movements",
    ),
    "데이터": (
        "analyzes data visualizations and charts on multiple dark-themed screens",
        "builds a dashboard with pivot tables and filtered data views",
    ),
    "코딩": (
        "writes code on dual monitors with syntax-highlighted editor",
        "runs and tests the program, reviewing output in terminal",
    ),
    "관광": (
        "photographs scenic spots with professional camera equipment",
        "reviews tourism content on a laptop in an outdoor setting",
    ),
    "정비": (
        "inspects mechanical components with diagnostic tools and equipment",
        "repairs and reassembles parts, then tests the system operation",
    ),
    "스마트스토어": (
        "photographs products with a smartphone and edits listing images on laptop",
        "reviews online store sales dashboard and packs shipping boxes",
    ),
    "이커머스": (
        "creates product detail pages on a laptop with e-commerce platform open",
        "reviews order management dashboard and prepares packages for shipping",
    ),
    "산업안전": (
        "conducts safety inspection with a checklist, examining equipment and signage",
        "reviews risk assessment documents on screen and marks safety zones on a map",
    ),
    "안전관리": (
        "inspects a construction site with a clipboard, checking guardrails and signage",
        "reviews safety training materials and updates risk assessment on laptop",
    ),
    "default": (
        "works on practical training exercises with professional equipment",
        "reviews completed work results on screen and takes notes",
    ),
}


def _get_actions_en(title):
    """과정명에서 구체적 키워드를 먼저 매칭하여 영문 행동 2개를 반환."""
    for keyword in FIELD_ACTIONS_EN:
        if keyword == "default":
            continue
        if keyword in title:
            return FIELD_ACTIONS_EN[keyword]
    return FIELD_ACTIONS_EN["default"]


def _build_segments(course_data, ctype):
    """
    3세그먼트 장면을 생성합니다.
    seg1: 배경+복장 상세 설정 + 나레이션 (훅+과정명)
    seg2: 훈련목표 실습 장면 1개, 나레이션 없음
    seg3: 마무리 (카메라 보며 CTA) + 나레이션
    """
    title = course_data.get("title", "")
    clean = _clean_title(title)
    training_goal = (course_data.get("trainingGoal", "")
                     or course_data.get("traingGoal", "")
                     or course_data.get("training_goal", ""))
    kr1, _ = _goal_to_actions_kr(training_goal)
    en1, _ = _get_actions_en(clean)
    bg, outfit = _get_setting(clean)

    if ctype == "long":
        return [
            {
                "scene_en": f"A Korean professional {outfit}, in {bg}. They look at the camera and begin speaking. Medium shot, warm lighting.",
                "action_kr": "작업 현장 → 카메라 보며 이야기",
            },
            {
                "scene_en": f"The same person {en1}.",
                "action_kr": f"실습: {kr1[:45] if kr1 else en1[:45]}",
            },
            {
                "scene_en": "The same person looks at the camera and speaks confidently with a warm smile.",
                "action_kr": "카메라 보며 자신있게 마무리",
            },
        ]
    elif ctype == "short":
        return [
            {
                "scene_en": f"A Korean professional {outfit}, walks into {bg} and speaks to the camera with energy. Bright lighting, handheld camera.",
                "action_kr": "활기차게 입장 → 카메라에 말하기",
            },
            {
                "scene_en": f"The same person {en1}.",
                "action_kr": f"실습: {kr1[:45] if kr1 else en1[:45]}",
            },
            {
                "scene_en": "The same person gives a thumbs up and speaks to the camera with energy.",
                "action_kr": "엄지척하며 밝게 마무리",
            },
        ]
    else:  # general
        return [
            {
                "scene_en": f"A Korean professional {outfit}, in {bg}. They smile at the camera and begin speaking. Medium shot, bright natural lighting.",
                "action_kr": "작업 공간 → 카메라 보며 인사",
            },
            {
                "scene_en": f"The same person {en1}.",
                "action_kr": f"실습: {kr1[:45] if kr1 else en1[:45]}",
            },
            {
                "scene_en": "The same person smiles at the camera and speaks warmly.",
                "action_kr": "카메라 보며 따뜻하게 마무리",
            },
        ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [통합] 릴스 패키지 생성 (Grok 영상 가이드)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_reels_package(course_data):
    """
    릴스 제작에 필요한 2종 패키지를 생성합니다.

    Returns:
        dict | str:
            성공 시 {"grok": str}
            만료 과정이면 "[SKIP] ..." 문자열
    """
    from benefits_helper import get_course_type, get_total_hours

    title = course_data.get("title", "")
    ncs_cd = course_data.get("ncsCd", "")
    field = detect_course_field(title, ncs_cd)
    ctype = get_course_type(course_data)
    hours = get_total_hours(course_data)
    institution = course_data.get("institution", "")
    period = course_data.get("period", "")

    # 훈련목표 키워드
    training_goal = (course_data.get("trainingGoal", "")
                     or course_data.get("training_goal", ""))
    goal_summary = summarize_training_goal(training_goal)
    if not goal_summary:
        fallback = {
            "AI": "AI 활용 · 실무 프로젝트", "영상": "영상 편집 · 콘텐츠 제작",
            "디자인": "UI/UX 디자인 · 실무 포트폴리오", "출판": "편집디자인 · 전자책 제작",
            "콘텐츠": "콘텐츠 기획 · 제작 실무", "마케팅": "디지털 마케팅 · SNS 운영",
            "데이터": "데이터 분석 · 시각화", "코딩": "프로그래밍 · 개발 실무",
            "이커머스": "스마트스토어 운영 · 온라인 판매", "산업안전": "안전관리 · 위험성평가",
            "default": "전문 기술 · 실무 역량",
        }
        goal_summary = fallback.get(field, fallback["default"])

    hook = _generate_dynamic_hook(title, field, goal_summary)
    benefit_line = _generate_benefit_line(course_data, ctype, hours)

    cta_text, cta_sub, urgency = _generate_cta(course_data)
    if urgency == "expired":
        return f"[SKIP] {title} - 이미 시작된 과정 (릴스 생성 건너뜀)"

    mood = VISUAL_MOOD.get(field, VISUAL_MOOD["default"])

    # 타임라인 구조 라벨
    structure_labels = {
        "long": "성장 서사형 (Before→After)",
        "short": "빠른 전개형 (에너지)",
        "general": "밸런스형 (실무 중심)",
    }
    structure_label = structure_labels.get(ctype, structure_labels["general"])

    # 3세그먼트 장면 생성 (과정명+훈련목표 기반)
    segments = _build_segments(course_data, ctype)

    # ═══════════════════════════════════════════════════
    # 나레이션 원고 (Vrew TTS용, 30초)
    # ═══════════════════════════════════════════════════

    title_short = title.replace("(산대특) ", "").replace("(산대특)", "")

    benefit_short = (benefit_line
                     .replace(" 💰", "")
                     .replace("받으며 배우기", "지원")
                     .replace("부담 없이 배우기", "만 부담")
                     .rstrip("!."))
    cta_short = (cta_text
                 .replace(" 🔥", "").replace(" 👆", "")
                 .replace("!", "").replace("📢", "")
                 .strip())

    # 훈련기간 짧은 표현 (나레이션용)
    period_narr_short = ""
    start_str = course_data.get("traStartDate", "")
    end_str = course_data.get("traEndDate", "")
    if start_str and end_str and len(start_str) >= 8 and len(end_str) >= 8:
        try:
            s_m = int(start_str[4:6])
            e_m = int(end_str[4:6])
            if s_m == e_m:
                period_narr_short = f"{s_m}월에 시작해요."
            else:
                period_narr_short = f"{s_m}월에 시작해요."
        except ValueError:
            period_narr_short = ""

    # 훈련기간 상세 (Vrew 자막용)
    period_narr_full = ""
    if start_str and end_str and len(start_str) >= 8 and len(end_str) >= 8:
        try:
            s_m, s_d = int(start_str[4:6]), int(start_str[6:8])
            e_m, e_d = int(end_str[4:6]), int(end_str[6:8])
            period_narr_full = f"{s_m}월 {s_d}일부터 {e_m}월 {e_d}일까지"
        except ValueError:
            period_narr_full = ""

    # 나레이션용: '·' 제거, 첫 번째 키워드만 추출
    goal_narr = goal_summary.replace(" · ", "과 ")
    goal_first = goal_summary.split(" · ")[0] if " · " in goal_summary else goal_summary

    # ═══════════════════════════════════════════════════
    # 세그먼트별 나레이션 (쉼표로 호흡 구분)
    # ═══════════════════════════════════════════════════
    seg_narrations = {
        1: f"{hook}, {title_short}.",
        2: f"{goal_narr}을, 배울 수 있어요.",
        3: f"지금 바로 신청하세요, {period_narr_full}." if period_narr_full else f"지금 바로 신청하세요.",
    }

    # ═══════════════════════════════════════════════════
    # Grok 영상 가이드 (영상 + 나레이션)
    # ═══════════════════════════════════════════════════

    # 세그먼트별 Grok 프롬프트
    def _grok_prompt(seg_num, seg, narr_text):
        if seg_num == 1:
            return f"""The person speaks clearly in Korean with natural lip-sync: "{narr_text}"

A cinematic video. {seg['scene_en']}
No background music, no BGM."""
        elif seg_num == 2:
            # 나레이션 없이 장면만
            return f"""{seg['scene_en']}"""
        else:
            return f"""The person speaks clearly in Korean with natural lip-sync: "{narr_text}"

{seg['scene_en']}"""

    seg1_prompt = _grok_prompt(1, segments[0], seg_narrations[1])
    seg2_prompt = _grok_prompt(2, segments[1], seg_narrations[2])
    seg3_prompt = _grok_prompt(3, segments[2], seg_narrations[3])

    urgency_label = {
        "urgent": "높음 🔴 (마감 임박)",
        "soon": "보통 🟡",
        "open": "보통 🟢",
        "normal": "보통 🟢",
    }

    grok = f"""[Grok 영상 가이드] {title}
영상 + 나레이션 생성
구조: {structure_label} | 30초 (10초×3) | 9:16 세로형

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 제작 워크플로
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1) Grok에서 세그먼트 1 (0~10초) 영상 생성
  2) 세그먼트 1 영상을 기반으로 +10초 연장 → 세그먼트 2 (10~20초)
  3) 세그먼트 2 영상을 기반으로 +10초 연장 → 세그먼트 3 (20~30초)
  4) 완성된 30초 영상 편집 (자막은 Vrew 자동 생성 활용)
  5) 인스타그램 릴스 업로드 (캡션: *_instagram_caption.txt)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ 핵심 원칙
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • 세그먼트당 장면 1개 (장면 전환 없음)
  • 동일 인물 · 동일 공간 · 동일 조명 유지
  • 나레이션은 쉼표(,)로 호흡 단위 구분
  • 연장 프롬프트는 이전 장면을 구체적으로 언급

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 세그먼트 1 — 처음 생성 (0~10초)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  장면: {segments[0]['action_kr']}
  나레이션: {seg_narrations[1]}

🤖 Grok 프롬프트 (복사용)
────────────────────────────────────────────
{seg1_prompt}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 세그먼트 2 — +10초 연장 (10~20초)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  장면: {segments[1]['action_kr']}
  나레이션: {seg_narrations[2]}

🤖 Grok 프롬프트 (복사용)
────────────────────────────────────────────
{seg2_prompt}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 세그먼트 3 — +10초 연장 (20~30초)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  장면: {segments[2]['action_kr']}
  나레이션: {seg_narrations[3]}

🤖 Grok 프롬프트 (복사용)
────────────────────────────────────────────
{seg3_prompt}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 게시 설정
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  화면 비율:      9:16 (세로형)
  커버 이미지:    4~10초 구간 캡처 권장
  게시 우선순위:  {urgency_label.get(urgency, '보통 🟢')}
"""

    return {
        "grok": grok,
    }


def generate_reels_script(course_data):
    """하위 호환용 래퍼. 기존 코드에서 단일 문자열 반환이 필요한 경우."""
    result = generate_reels_package(course_data)
    if isinstance(result, str):
        return result  # "[SKIP] ..."
    return result["grok"]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 게시 가이드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_posting_guide(course_data):
    """게시 타이밍 및 시리즈 전략 가이드를 생성합니다."""
    title = course_data.get("title", "")
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
  2차 (D-14, {d2.strftime('%m/%d')}): 블로그 "커리큘럼 상세편" + Grok AI 릴스 영상
  3차 (D-7,  {d3.strftime('%m/%d')}): 인스타 스토리 "마감 D-7" 긴급성 강조
  4차 (D-3,  {d4.strftime('%m/%d')}): 블로그+인스타 "마감 임박" 리마인드
"""
    else:
        guide += """
  1차: 과정 공개 후 즉시 → 블로그 "혜택 정리편" + 인스타 카드뉴스
  2차: 1주일 후 → 블로그 "커리큘럼 상세편" + Grok AI 릴스 영상
  3차: 마감 7일 전 → 인스타 스토리 "마감 D-7" 긴급성 강조
  4차: 마감 3일 전 → 블로그+인스타 "마감 임박" 리마인드
"""
    guide += """
⏰ 권장 게시 시간 (반드시 불규칙하게!)
  ⚠️ 매일 같은 시간 게시 = 자동화(매크로) 의심 → 저품질 위험
  - 네이버 블로그: 오전 8~10시 또는 오후 12~2시 (±1~3시간 변동)
  - 인스타그램 피드/캐러셀: 오후 9시~10시
  - 인스타그램 릴스: 오후 9시~10시
  - 하루 2개 이상 게시 시: 최소 2~3시간 간격
  - 최적 요일: 목요일 > 화·수요일

📊 게시 후 체크리스트
  □ 블로그: 발행 후 1~2시간 뒤 색인 확인
    - whereispost.com 또는 네이버에서 site:blog.naver.com/[블로그ID]
    - ※ 네이버 블로그는 서치어드바이저 별도 등록 불필요 (자동 색인)
  □ 블로그: 기존 관련 글 2~3개와 내부링크 상호 연결 (체류시간 극대화)
  □ 인스타: 게시 후 1시간 내 댓글에 직접 답글 달기
  □ 인스타: 스토리에 게시물 공유 + "자세히 보기" 유도
  □ 관련 커뮤니티/카페에 정보성 글로 자연스럽게 공유
    - 제주 지역 카페, 취업/이직 카페, 내일배움카드 카페

📈 C-Rank 성장 액션 (매주 실행)
  □ 관련 블로거 서로이웃 신청: 주 10~20명
    - 국비교육, 자기계발, 제주 생활 분야 블로거 위주
  □ 관련 블로그 구체적 댓글 작성: 매일 5~10개
    - ✗ "좋은 글이네요~" 안부 댓글은 역효과
    - ✅ "저도 이 과정 관심 있었는데, ○○ 부분이 궁금했어요" 식으로 구체적으로
  □ 네이버 지식iN에서 "국비교육", "직업훈련" 관련 질문 답변: 주 3회
  □ 블로그 전체 포스팅의 80% 이상을 국비교육/직업훈련 주제로 유지
    - C-Rank Context(주제 집중도)가 가장 높은 가중치(~40%)

🔑 인스타그램 프로필 설정
  - 프로필 이름: "제주HRD위원회 | 직업훈련·취업지원" (검색 키워드 포함)
  - 프로필 링크: 고용24 과정 신청 페이지 또는 링크트리
  - 프로필 소개 (4줄 공식):
    ①제주지역인적자원개발위원회 공식 계정
    ②제주 국비지원 직업훈련 과정 안내
    ③내일배움카드로 자부담 10% · 장려금 지원
    ④아래 링크에서 과정 확인 👇
  - 하이라이트: "신청방법", "모집중", "수강후기" 카테고리 생성

📈 콘텐츠 믹스 참고 (채널 성장을 위한 다양한 콘텐츠)
  - 정보성 콘텐츠 40%: 훈련과정 안내, 자격증 정보, 취업 팁
  - 참여·소통형 20%: 퀴즈 이벤트, 수료생 후기 공유, Q&A
  - 트렌드·감성형 20%: 제주 취업시장 동향, 밈/트렌드 활용
  - 기관 소식 15%: 협약식, 신규 프로그램 론칭
  - 시즌 콘텐츠 5%: 채용 시즌, 자격증 시험 일정
  ※ 과정 안내 외에도 위 비율을 참고하여 다양한 콘텐츠를 직접 기획해주세요
"""
    return guide


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 키워드 밀도 제어 (저품질 방지)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def check_keyword_density(text, keyword, max_count=6):
    """
    본문 내 키워드 출현 횟수를 확인합니다.
    SEO 연구: 핵심 키워드 본문 5~6회가 안전선, 과도 반복은 저품질 유발.
    """
    if not keyword or not text:
        return 0, True
    count = text.upper().count(keyword.upper())
    return count, count <= max_count


def get_keyword_density_report(text, primary_keyword, field_keywords=None):
    """키워드 밀도 리포트를 생성합니다."""
    report = []
    cnt, safe = check_keyword_density(text, primary_keyword)
    status = "✅" if safe else "⚠️ 과다"
    report.append(f"  {status} '{primary_keyword}': {cnt}회 (권장 5~6회)")
    if field_keywords:
        for kw in field_keywords[:3]:
            cnt2, _ = check_keyword_density(text, kw)
            if cnt2 > 0:
                report.append(f"  ✅ '{kw}': {cnt2}회")
    return "\n".join(report)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 블로그 구조 다양화 (유사문서 필터링 회피)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CLOSING_PATTERNS = [
    "이 글이 도움이 되셨다면, 주변에 교육을 찾고 있는 분에게 공유해주세요. 더 궁금한 점은 댓글로 남겨주시면 답변드릴게요!",
    "제주에서 새로운 시작을 준비하고 계신다면, 이 과정 놓치지 마세요. 궁금한 점은 언제든 문의해주세요!",
    "여기까지 읽어주셨다면 이미 반은 성공이에요. 나머지 반은 신청 버튼을 누르는 것뿐입니다 😊",
    "국비지원 교육은 한번 수강한 과정은 재수강이 안 되니까, 신중하게 고르되 너무 오래 고민하지는 마세요!",
    "같은 고민을 하고 있는 친구가 있다면 이 글을 공유해주세요. 함께 배우면 더 재미있잖아요!",
]

SECTION_TITLE_VARIANTS = {
    "overview": ["한눈에 보기", "과정 요약 정보", "핵심 정보 한눈에"],
    "benefits": ["이런 혜택이 있어요", "혜택 총정리", "받을 수 있는 혜택은?"],
    "recommend": ["이런 분에게 추천해요", "이런 분이라면 꼭 들어보세요", "나한테 맞는 과정일까?"],
    "curriculum": ["어떤 것들을 배우나요", "커리큘럼 미리보기", "무엇을 배울 수 있나요"],
    "apply": ["이렇게 신청하세요", "신청 방법 3단계", "신청은 이렇게!"],
}


def get_varied_section_title(section_key, title_hash=0):
    """과정별로 소제목 스타일을 미세하게 변형합니다."""
    variants = SECTION_TITLE_VARIANTS.get(section_key, [""])
    if not variants:
        return section_key
    return variants[title_hash % len(variants)]


def get_varied_closing(title_hash=0):
    """과정별로 다른 마무리 문구를 반환합니다."""
    return CLOSING_PATTERNS[title_hash % len(CLOSING_PATTERNS)]


def estimate_char_count(text):
    """공백 제외 글자 수를 추정합니다."""
    import re
    clean = re.sub(r'\[.*?\]', '', text)
    return len(clean.replace(" ", "").replace("\n", ""))
