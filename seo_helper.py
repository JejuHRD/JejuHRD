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
    "10": "마케팅",       # 영업판매
    "0802": "디자인",     # 디자인
    "0803": "영상",       # 방송
    "0801": "콘텐츠",     # 문화콘텐츠
    "2001": "코딩",       # 정보기술
    "2002": "데이터",     # 통신기술
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
# 공감형 도입부
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EMPATHY_INTROS = {
    "AI": [
        "\"나도 AI를 배워야 하나?\" 고민만 하다가 시간이 흘러가고 있다면, 지금이 딱 시작할 타이밍이에요.",
        "ChatGPT, 미드저니, AI 영상 생성... 세상은 빠르게 바뀌고 있는데, 어디서부터 배워야 할지 막막하셨죠? 제주에서 체계적으로 배울 수 있는 기회가 열렸어요.",
        "\"AI가 내 일자리를 대체한다\"는 뉴스, 불안하기만 하셨나요? AI를 활용하는 쪽에 서면 오히려 기회가 됩니다.",
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
        "경력을 쌓고 싶은데 교육비가 부담이셨나요? 내일배움카드로 자부담 10%만 내고 전문 기술을 배울 수 있어요.",
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
    """네이버 블로그 SEO에 최적화된 제목을 생성합니다."""
    from benefits_helper import get_course_type
    title = course_data.get("title", "")
    ctype = get_course_type(course_data)
    benefit_tag = "자부담 10% + 훈련장려금" if ctype in ("general", "long") else "자부담 10%"
    seo_title = f"[제주 국비지원] {title} | {benefit_tag}"
    return seo_title


def generate_empathy_intro(course_data):
    """과정별로 차별화된 공감형 도입부를 생성합니다."""
    title = course_data.get("title", "")
    field = detect_course_field(title, course_data.get("ncsCd"))
    intros = EMPATHY_INTROS.get(field, EMPATHY_INTROS["default"])
    return random.choice(intros)


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
        "AI": ["#AI교육", "#인공지능교육", "#ChatGPT교육", "#생성형AI"],
        "영상": ["#영상편집교육", "#영상제작", "#프리미어프로", "#유튜브교육"],
        "디자인": ["#디자인교육", "#UIUX교육", "#피그마", "#웹디자인교육"],
        "출판": ["#출판교육", "#인디자인", "#전자책제작", "#편집디자인"],
        "콘텐츠": ["#콘텐츠제작교육", "#크리에이터교육", "#SNS콘텐츠"],
        "마케팅": ["#디지털마케팅교육", "#SNS마케팅", "#마케팅교육"],
        "데이터": ["#데이터분석교육", "#빅데이터", "#파이썬교육"],
        "코딩": ["#코딩교육", "#프로그래밍교육", "#개발자교육"],
        "default": ["#직업훈련", "#스킬업", "#자기계발", "#커리어전환"],
    }
    specific = field_tags.get(field, field_tags["default"])
    all_tags = common + specific
    seen = set()
    unique = []
    for t in all_tags:
        if t not in seen:
            unique.append(t)
            seen.add(t)
    return " ".join(unique[:15])


def generate_instagram_hashtags(course_data):
    """인스타그램 해시태그 20개를 대형+중소형+지역+분야별로 믹스합니다."""
    title = course_data.get("title", "")
    field = detect_course_field(title, course_data.get("ncsCd"))
    big_tags = ["#국비지원", "#국비지원교육", "#내일배움카드", "#직업훈련", "#자기계발"]
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
    from benefits_helper import get_course_type, get_benefits_text
    title = course_data.get("title", "")
    institution = course_data.get("institution", "")
    period = course_data.get("period", "")
    time_info = course_data.get("time", "")
    ctype = get_course_type(course_data)
    benefits = get_benefits_text(course_data)
    field = detect_course_field(title, course_data.get("ncsCd"))
    field_emoji = {
        "AI": "🤖", "영상": "🎬", "디자인": "🎨", "출판": "📚",
        "멀티미디어": "🖥️", "콘텐츠": "📱", "마케팅": "📊",
        "데이터": "📈", "코딩": "💻",
    }
    emoji = field_emoji.get(field, "📌")
    hook = _generate_dynamic_hook(title, field)

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
    if ctype in ("general", "long"):
        caption += "🎁 훈련장려금 월 최대 20만원까지 받을 수 있어요\n"

    cta_text, cta_sub, urgency = _generate_cta(course_data)
    if urgency == "urgent":
        caption += f"\n🔥 {cta_text}\n"
    elif urgency == "soon":
        caption += f"\n⏰ {cta_text}\n"

    caption += """
👉 신청 방법이 궁금하다면?
프로필 링크에서 바로 확인하세요!

💬 궁금한 점은 DM 또는 댓글로 물어봐 주세요"""

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
⏰ 권장 게시 시간
  - 네이버 블로그: 오전 8~9시 또는 오후 1시
  - 인스타그램 피드: 오후 12~1시 또는 오후 6~9시
  - 인스타그램 릴스: 오후 7~9시
  - 인스타그램 스토리: 오전 8시, 오후 12시, 오후 8시 (3회)
  - 최적 요일: 월~수

📊 게시 후 체크리스트
  □ 블로그: 발행 후 네이버 검색에서 제목 검색 → 노출 여부 확인 (보통 수 시간 내 자동 색인)
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
