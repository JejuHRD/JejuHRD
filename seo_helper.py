"""
SEO 및 마케팅 헬퍼 - 제주지역인적자원개발위원회 특화훈련 홍보용

v4 전면 개편 (과정별 차별화):
  1) 훈련목표 키워드 → Sora 장면 자동 매핑
  2) 과정 제목/목표에서 동적 훅 문장 생성
  3) 혜택 구간을 과정 시간·비용에 맞게 세분화
  4) 모집 D-day 기반 CTA 동적 변경
  5) 분야+키워드별 Sora 색상 팔레트·무드 차별화
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
# [아이디어 1] 키워드 → Sora 장면 매핑 테이블
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
    """추출된 키워드에서 Sora 장면을 매핑합니다."""
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
        return "자부담 10% + 장려금·수당 월 최대 40만원 💰"
    elif ctype == "general":
        if months > 0:
            return f"{months}개월 과정, 월 20만원 장려금 + 자부담 10% 💰"
        return "자부담 10% + 훈련장려금 월 최대 20만원 💰"
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
    if len(seo_title) > 60:
        short_title = title[:25] + "..." if len(title) > 25 else title
        seo_title = f"[제주 국비지원] {short_title} | {benefit_tag}"
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
        f"#{year}국비지원", "#내일배움카드", "#제주무료교육",
        "#제주취업", "#제주직업훈련", "#제주특화훈련",
        "#국비지원무료교육", "#내일배움카드추천",
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
    hashtags = generate_instagram_hashtags(course_data)
    caption += hashtags
    return caption


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Sora 컷 시나리오 빌더 (영상만, 텍스트/자막 지시 없음)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _build_sora_cuts_short(scenes, mood):
    """단기과정: 속도감 빠른 컷 전환 (영상만)."""
    cuts = []
    cuts.append({
        "time": "0~2초", "label": "임팩트 오프닝",
        "scene": "작업 화면 빠른 줌인 클로즈업. 마우스 클릭하는 손, 모니터 화면 빠르게 스크롤.",
        "camera": "빠른 줌인 → 0.5초 홀드",
        "mood": "글리치 효과, 에너지 넘치는 시작",
    })
    for i, s in enumerate(scenes):
        start = 2.0 + i * 1.7
        end = start + 1.5
        cuts.append({
            "time": f"{start:.0f}~{end:.0f}초", "label": f"빠른 컷 #{i+1}: {s['keyword']}",
            "scene": s["scene"],
            "camera": "빠른 줌인 → 0.3초 홀드 → 스위시 전환",
            "mood": "비트에 맞춘 빠른 컷 체인지",
        })
    cuts.append({
        "time": "7~11초", "label": "혜택 강조",
        "scene": "밝은 배경의 교실/작업 공간. 한국인 수강생이 웃으며 동료와 대화하는 모습.",
        "camera": "미디엄 샷 → 천천히 줌인",
        "mood": "밝은 톤, 따뜻한 조명으로 전환",
    })
    cuts.append({
        "time": "11~15초", "label": "엔딩",
        "scene": "밝아지는 화면, 깨끗한 배경. 로고/기관명이 들어갈 여백이 있는 정리된 엔딩 프레임.",
        "camera": "정면 고정 → 화면 서서히 밝아짐",
        "mood": "클린 마무리, 밝은 화이트 톤",
    })
    return cuts


def _build_sora_cuts_long(scenes, mood):
    """장기과정: Before→After 성장 서사 (영상만)."""
    main_scene = scenes[0] if scenes else {"keyword": "", "scene": ""}
    return [
        {
            "time": "0~3초", "label": "Before — 고민",
            "scene": "어두운 방, 노트북 앞에서 한숨 쉬는 한국인의 실루엣. 데스크 위에 빈 이력서, 어두운 톤.",
            "camera": "슬로우 줌인, 한국인 뒷모습에서 시작",
            "mood": "어두운 그레이딩, 블루 톤, 고민의 무게감",
        },
        {
            "time": "3~4.5초", "label": "학습 시작",
            "scene": "밝은 강의실, 한국인이 문을 열고 들어와 자리에 앉으며 노트북을 펼침.",
            "camera": "팔로우 샷 → 자리에 앉으면서 미디엄 샷",
            "mood": "톤이 살짝 밝아지기 시작, 희망의 조짐",
        },
        {
            "time": "4.5~6초", "label": "실습",
            "scene": main_scene["scene"],
            "camera": "화면 위 작업물 클로즈업 → 집중하는 손과 표정",
            "mood": "따뜻한 조명, 몰입감 있는 중간톤",
        },
        {
            "time": "6~8초", "label": "협업/성장",
            "scene": "한국인 팀원들과 모니터를 함께 보며 토론. 표정이 점점 밝아지고, 서로 고개를 끄덕이는 장면.",
            "camera": "그룹 미디엄 샷, 약간의 핸드헬드 느낌",
            "mood": "확실하게 밝아진 색감, warm 톤 전환",
        },
        {
            "time": "8~12초", "label": "After — 달라진 나",
            "scene": "자신감 있는 표정으로 완성된 작업물/포트폴리오를 보여주는 한국인. 환한 조명, 모니터에 결과물.",
            "camera": "한국인 → 작업물 클로즈업 → 다시 미소",
            "mood": "밝고 따뜻한 golden hour 톤, 성취감",
        },
        {
            "time": "12~15초", "label": "엔딩",
            "scene": "수료식 혹은 한국인 동료와의 하이파이브. 이어서 깨끗한 배경으로 전환, 로고/기관명 여백.",
            "camera": "미디엄 → 정면 고정, 화면 밝아짐",
            "mood": "따뜻한 블러 전환 → 선명한 엔딩",
        },
    ]


def _build_sora_cuts_general(scenes, mood):
    """일반과정: 밸런스형 (영상만)."""
    cuts = [
        {
            "time": "0~3초", "label": "오프닝",
            "scene": "한국인이 카메라를 향해 걸어오며 현대적인 작업 공간에 진입. 문을 열고 들어서는 동작.",
            "camera": "다이나믹 줌인, 한국인 팔로우",
            "mood": "활기찬 시작, 밝은 자연광",
        },
    ]
    for i, s in enumerate(scenes[:2]):
        start = 3 + i * 2.5
        end = start + 2.5
        cuts.append({
            "time": f"{start:.0f}~{end:.0f}초", "label": f"실무 장면: {s['keyword']}",
            "scene": s["scene"],
            "camera": "부드러운 크로스 디졸브 전환",
            "mood": "집중과 몰입의 분위기",
        })
    cuts.append({
        "time": "8~12초", "label": "밝은 분위기",
        "scene": "밝은 표정의 한국인 수강생, 동료와 화면을 함께 보며 대화. 웃는 얼굴 클로즈업.",
        "camera": "미디엄 → 클로즈업 전환",
        "mood": "따뜻하고 긍정적인 톤",
    })
    cuts.append({
        "time": "12~15초", "label": "엔딩",
        "scene": "깨끗한 배경, 밝아지는 화면. 로고/기관명이 들어갈 여백 확보.",
        "camera": "정면 고정, 화면 밝아짐",
        "mood": "클린 마무리",
    })
    return cuts


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [통합] 릴스 3종 패키지 생성 (대본 + Sora 컷 + Vrew 자막)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_reels_package(course_data):
    """
    릴스 제작에 필요한 3종 패키지를 생성합니다.

    Returns:
        dict | str:
            성공 시 {"script": str, "sora": str, "vrew": str}
            만료 과정이면 "[SKIP] ..." 문자열
    """
    from benefits_helper import get_course_type, get_total_hours

    title = course_data.get("title", "")
    ncs_cd = course_data.get("ncsCd", "")
    field = detect_course_field(title, ncs_cd)
    ncs_sub = _get_ncs_sub_keyword(ncs_cd)
    ctype = get_course_type(course_data)
    hours = get_total_hours(course_data)
    institution = course_data.get("institution", "")
    period = course_data.get("period", "")

    # 훈련목표 키워드
    training_goal = (course_data.get("traingGoal", "")
                     or course_data.get("training_goal", "")
                     or course_data.get("trainingGoal", ""))
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

    scenes = _get_sora_scenes(goal_summary, field, ncs_sub)
    mood = VISUAL_MOOD.get(field, VISUAL_MOOD["default"])

    # 타임라인 구조 선택
    if ctype == "long":
        structure_label = "성장 서사형 (Before→After)"
        sora_cuts = _build_sora_cuts_long(scenes, mood)
    elif ctype == "short":
        structure_label = "빠른 컷 몽타주형 (속도감)"
        sora_cuts = _build_sora_cuts_short(scenes, mood)
    else:
        structure_label = "밸런스형 (실무 중심)"
        sora_cuts = _build_sora_cuts_general(scenes, mood)

    # ═══════════════════════════════════════════════════
    # 1. 릴스 대본 (기본)
    # ═══════════════════════════════════════════════════
    script = f"""[릴스 대본] {title}
총 길이: 15초 | 구조: {structure_label}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
필수 요소
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  훅:           {hook}
  과정명:       {title}
  핵심 키워드:  {goal_summary}
  혜택:         {benefit_line}
  CTA:          {cta_text}
  긴급도:       {urgency}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
타임라인 구성
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [0~3초]  훅          → {hook}
  [3~8초]  과정 소개   → {title}
                         {goal_summary}
                         {institution}{(' | ' + period) if period else ''}
  [8~12초] 혜택        → {benefit_line}
                         내일배움카드 있으면 누구나 신청 가능
  [12~15초] CTA        → {cta_text}
                         {cta_sub}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
제작 워크플로
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1) Sora에서 영상+BGM+나레이션 생성  →  *_reels_sora.txt 참고
  2) Vrew에서 영상 불러오기 → 음성 인식 자동 자막 생성
  3) *_reels_vrew.txt 나레이션 원고와 대조하여 자막 교정
  4) 자막 스타일 적용 (폰트/크기/색상)
  5) 인스타그램 릴스 업로드 (캡션: *_instagram_caption.txt)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
게시 설정
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  화면 비율:    9:16 (세로형)
  커버 이미지:  3~8초 구간 캡처 권장
  게시 우선순위: {'높음 🔴 (마감 임박)' if urgency == 'urgent' else '보통 🟢'}
"""

    # ═══════════════════════════════════════════════════
    # 나레이션 원고 생성 (Sora + Vrew 공통 기반)
    # ═══════════════════════════════════════════════════

    # 자막용 짧은 텍스트 → 나레이션용 자연스러운 말투로 변환
    title_short = title.replace("(산대특) ", "").replace("(산대특)", "")

    # benefit_line에서 이모지/장식 제거한 짧은 버전
    benefit_short = (benefit_line
                     .replace(" 💰", "")
                     .replace("받으며 배우기", "지원")
                     .replace("부담 없이 배우기", "만 부담")
                     .rstrip("!."))
    cta_short = (cta_text
                 .replace(" 🔥", "").replace(" 👆", "")
                 .replace("!", "").replace("📢", "")
                 .strip())

    if ctype == "long":
        narration_blocks = [
            ("00:00.0", "00:03.0", hook),
            ("00:03.0", "00:07.0", f"{title_short}."),
            ("00:07.0", "00:11.0", f"{benefit_short}. 내일배움카드로 신청하세요."),
            ("00:11.0", "00:15.0", f"{cta_short}."),
        ]
    elif ctype == "short":
        narration_blocks = [
            ("00:00.0", "00:02.0", hook),
            ("00:02.0", "00:06.0", f"{title_short}."),
            ("00:06.0", "00:10.0", f"{benefit_short}. 내일배움카드로 신청하세요."),
            ("00:10.0", "00:15.0", f"{cta_short}. 놓치지 마세요."),
        ]
    else:
        narration_blocks = [
            ("00:00.0", "00:03.0", hook),
            ("00:03.0", "00:07.0", f"{title_short}."),
            ("00:07.0", "00:11.0", f"{benefit_short}. 내일배움카드로 신청하세요."),
            ("00:11.0", "00:15.0", f"{cta_short}."),
        ]

    # 나레이션 전체 텍스트 (Sora 프롬프트용)
    narration_full = " ".join(text for _, _, text in narration_blocks)

    # 기관명+기간 보조 자막 (3~8초 구간 하단)
    sub_info = institution
    if period:
        sub_info += f" | {period}"

    # ═══════════════════════════════════════════════════
    # 2. Sora 컷 시나리오 (영상 + BGM + 나레이션)
    # ═══════════════════════════════════════════════════
    cuts_text = ""
    for cut in sora_cuts:
        cuts_text += f"""
[{cut['time']}] {cut['label']}
  장면: {cut['scene']}
  카메라: {cut['camera']}
  분위기: {cut['mood']}
"""

    # Sora 프롬프트 (텍스트/자막 지시 제거, 나레이션 포함)
    scene_prompt_lines = []
    for cut in sora_cuts:
        scene_prompt_lines.append(f"[{cut['time']}] {cut['scene']}")
    scene_prompt_block = "\n".join(scene_prompt_lines)

    urgency_ending_visual = {
        "urgent": "The final 3 seconds: screen flashes briefly, then fades to a clean bright frame.",
        "soon": "The final 3 seconds: warm amber tones gradually brighten to a clean ending frame.",
        "open": "The final 3 seconds: smooth transition to a bright, clean ending frame.",
        "normal": "The final 3 seconds: screen gradually brightens to a clean white ending frame.",
    }

    # 나레이션 타임코드별 텍스트 (Sora 프롬프트용)
    narration_prompt_lines = []
    for start_tc, end_tc, text in narration_blocks:
        narration_prompt_lines.append(f"[{start_tc}~{end_tc}] \"{text}\"")
    narration_prompt_block = "\n".join(narration_prompt_lines)

    sora_prompt = f"""A 15-second vertical (9:16) cinematic video. NO TEXT, NO SUBTITLES, NO OVERLAYS — video footage only.

Visual Style:
  Color palette: {mood['palette']}
  Mood: {mood['mood']}
  Lighting: {mood['lighting']}
  Textures: {mood['texture']}

Scene flow ({structure_label}):
{scene_prompt_block}

{urgency_ending_visual.get(urgency, urgency_ending_visual['normal'])}

Audio:
  Include upbeat background music suitable for a promotional video.
  Include Korean female voice-over narration reading the following script naturally and clearly:

Narration script (Korean):
{narration_prompt_block}

IMPORTANT: Do NOT generate any text, titles, subtitles, or captions in the video.
All text will be added separately in post-production.
All people appearing in the video must be Korean.
Duration: exactly 15 seconds. Korean workplace setting with Korean people."""

    sora = f"""[Sora 컷 시나리오] {title}
영상 + BGM + 나레이션 생성 — 자막은 Vrew에서 음성인식으로 자동 생성
구조: {structure_label} | 15초 | 9:16 세로형

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎨 비주얼 무드 (분야: {field})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  팔레트: {mood['palette']}
  분위기: {mood['mood']}
  조명:   {mood['lighting']}
  질감:   {mood['texture']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 컷별 장면 (Sora → 영상만 생성, 텍스트 없음)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{cuts_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎤 나레이션 원고 (Sora가 한국어 음성으로 생성)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    for start_tc, end_tc, text in narration_blocks:
        sora += f"[{start_tc} → {end_tc}]  {text}\n"

    sora += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔊 오디오 설정
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  나레이션: 한국어 여성 음성, 밝고 또렷한 톤
  BGM: 업비트 프로모션용 배경음악
  BGM 볼륨: 나레이션 대비 30~40% (나레이션이 또렷하게 들리도록)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Sora 프롬프트 (복사용)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{sora_prompt}
"""

    # ═══════════════════════════════════════════════════
    # 3. Vrew 자막 원고 (나레이션 음성인식 → 자동 자막 → 교정)
    # ═══════════════════════════════════════════════════

    vrew_text = f"""[Vrew 자막 원고] {title}
Sora 나레이션 음성을 Vrew 음성인식으로 자동 자막 생성 후, 아래 원고와 대조하여 교정합니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 작업 순서
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1) Sora에서 생성된 영상(나레이션 포함)을 Vrew에 불러오기
  2) Vrew '음성 인식' 기능으로 자동 자막 생성 (언어: 한국어)
  3) 아래 나레이션 원고와 대조하여 인식 오류 교정
  4) 자막 스타일(폰트/크기/색상/위치) 적용
  5) 보조 자막 수동 추가 (기관명, CTA 안내)
  6) 내보내기 (MP4, 1080x1920)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎤 나레이션 원고 (교정용 — 자동 자막과 대조)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    for start_tc, end_tc, text in narration_blocks:
        vrew_text += f"[{start_tc} → {end_tc}]  {text}\n"

    vrew_text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 보조 자막 (수동 추가)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[00:03.0 → 00:08.0]  {sub_info}
[00:12.0 → 00:15.0]  {cta_sub}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 음성인식 자막 교정 체크리스트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  □ 과정명이 정확한지 확인 (띄어쓰기, 약어)
  □ 금액/숫자 표기 확인 (40만원, 10% 등)
  □ 전문 용어 오인식 교정 (예: '에프터이펙트' → '에프터 이펙트')
  □ 자막 줄바꿈 위치 조정 (한 줄 15자 이내 권장)
  □ 나레이션과 자막 타이밍 싱크 확인

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎨 자막 스타일 가이드
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  메인 자막 (나레이션 자동 자막):
    폰트: Pretendard Bold (또는 노토산스 Bold)
    크기: 화면 너비의 70~80%
    색상: 흰색 (#FFFFFF), 검은 그림자 또는 반투명 배경 박스
    위치: 화면 중앙~상단 1/3
    애니메이션: 페이드인 (0.2초)

  보조 자막 (수동 추가):
    폰트: Pretendard Regular
    크기: 메인의 50~60%
    색상: 연한 흰색 (#E0E0E0)
    위치: 화면 하단
    애니메이션: 없음 (고정)

  혜택 구간 (8~12초):
    숫자/금액 부분만 강조색 적용 (노란색 #FFD93D 또는 분야 포인트색)
"""

    return {
        "script": script,
        "sora": sora,
        "vrew": vrew_text,
    }


def generate_reels_script(course_data):
    """하위 호환용 래퍼. 기존 코드에서 단일 문자열 반환이 필요한 경우."""
    result = generate_reels_package(course_data)
    if isinstance(result, str):
        return result  # "[SKIP] ..."
    return result["script"]


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
  - 네이버 블로그: 오전 8~9시 또는 오후 1시
  - 인스타그램 피드: 오후 12~1시 또는 오후 6~9시
  - 인스타그램 릴스: 오후 7~9시
  - 인스타그램 스토리: 오전 8시, 오후 12시, 오후 8시 (3회)
  - 최적 요일: 월~수

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
