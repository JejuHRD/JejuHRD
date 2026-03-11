"""
Pexels 무료 스톡 이미지 API 연동 모듈

환경변수: PEXELS_API_KEY (Pexels API Key)
훈련과정 주제/NCS직종에 맞는 배경 이미지를 자동으로 검색/다운로드합니다.
"""

import os
import hashlib
from io import BytesIO


# ── 과정 키워드 → 영문 검색어 매핑 ──
KEYWORD_MAP = {
    "AI": "artificial intelligence technology",
    "인공지능": "artificial intelligence",
    "프로그래밍": "programming code computer",
    "코딩": "coding laptop developer",
    "빅데이터": "data analytics technology",
    "클라우드": "cloud computing server",
    "웹": "web development design",
    "디지털": "digital technology modern",
    "드론": "drone aerial photography",
    "항공": "drone aerial landscape",
    "촬영": "camera photography professional",
    "관광": "tourism travel beautiful destination",
    "바리스타": "coffee barista cafe",
    "커피": "coffee beans cafe",
    "디자인": "design creative studio",
    "미용": "beauty salon hairstyle",
    "건설": "construction building architecture",
    "요리": "cooking chef kitchen",
    "농업": "agriculture farming green",
    "전기": "electrical engineering power",
    "용접": "welding industrial manufacturing",
    "자동차": "automotive car mechanic",
    "물류": "logistics warehouse shipping",
    "간호": "healthcare nursing hospital",
    "3D": "3d modeling technology",
    "모델링": "3d modeling digital",
    "영상": "video production camera",
    "편집": "video editing creative",
    "마케팅": "digital marketing business",
    "SNS": "social media marketing",
    "콘텐츠": "content creation digital",
    "출판": "publishing books design",
    "데이터": "data science analytics",
    "정비": "maintenance repair technical",
}

# ── NCS 직종명 → 영문 검색어 매핑 ──
NCS_KEYWORD_MAP = {
    "소형무인기운용": "drone pilot aerial",
    "소형무인기정비": "drone repair maintenance",
    "영상촬영": "video camera filming",
    "영상편집": "video editing production",
    "멀티미디어": "multimedia design creative",
    "웹디자인": "web design ui ux",
    "시각디자인": "graphic design creative",
    "광고": "advertising marketing creative",
    "커피": "coffee barista latte art",
    "조리": "cooking chef professional",
    "건축설계": "architecture blueprint design",
    "전기설비": "electrical installation engineering",
    "용접": "welding metal industrial",
    "자동차정비": "automotive mechanic repair",
    "네트워크": "network server technology",
    "정보보안": "cybersecurity technology",
    "빅데이터분석": "data analytics dashboard",
    "인공지능": "artificial intelligence robot",
    "응용SW": "software development coding",
    "디지털마케팅": "digital marketing analytics",
    "관광기획": "tourism planning travel",
    "3D모델링": "3d modeling rendering",
}

FALLBACK_QUERIES = [
    "modern office workspace",
    "learning education technology",
    "professional development training",
    "career growth success",
    "creative workspace design",
    "technology innovation",
    "teamwork collaboration",
]


def _stable_hash_index(text, mod):
    """실행마다 동일한 인덱스를 보장하는 해시 함수"""
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()
    return int(digest, 16) % mod


def extract_search_query(course_data):
    """
    과정 데이터에서 가장 적합한 Pexels 검색어를 추출합니다.
    우선순위: NCS직종명 → 과정제목 키워드 → 폴백
    """
    if isinstance(course_data, str):
        # 하위호환: 문자열(제목)만 전달된 경우
        title = course_data
        ncs_name = ""
    else:
        title = course_data.get("title", "")
        ncs_name = course_data.get("ncsName", "")

    # 1순위: NCS 직종명 매칭
    if ncs_name:
        for ncs_keyword, english_query in NCS_KEYWORD_MAP.items():
            if ncs_keyword in ncs_name:
                return english_query

    # 2순위: 과정 제목 키워드 매칭
    matched_queries = []
    for korean_keyword, english_query in KEYWORD_MAP.items():
        if korean_keyword in title:
            matched_queries.append(english_query)

    if matched_queries:
        return matched_queries[0]

    # 3순위: 폴백
    idx = _stable_hash_index(title, len(FALLBACK_QUERIES))
    return FALLBACK_QUERIES[idx]


def fetch_pexels_image(query, orientation="square", size="large"):
    """Pexels API에서 이미지를 검색하고 다운로드합니다."""
    import requests
    from PIL import Image

    api_key = os.environ.get("PEXELS_API_KEY", "")
    if not api_key:
        print("  ⚠️  PEXELS_API_KEY가 설정되지 않았습니다. 그라데이션 배경을 사용합니다.")
        return None, None

    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": api_key}
    params = {
        "query": query,
        "orientation": orientation,
        "size": size,
        "per_page": 5,
        "page": 1,
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        photos = data.get("photos", [])
        if not photos:
            print(f"  ⚠️  '{query}' 검색 결과가 없습니다.")
            return None, None

        photo_idx = _stable_hash_index(query, len(photos))
        photo = photos[photo_idx]

        img_url = photo["src"].get("large2x", photo["src"].get("large", photo["src"]["original"]))
        img_response = requests.get(img_url, timeout=30)
        img_response.raise_for_status()

        img = Image.open(BytesIO(img_response.content))

        credit = {
            "photographer": photo.get("photographer", "Unknown"),
            "photographer_url": photo.get("photographer_url", ""),
            "pexels_url": photo.get("url", ""),
            "photo_id": photo.get("id", ""),
        }

        print(f"  📸 이미지 다운로드 완료: {photo['photographer']} (Pexels)")
        return img, credit

    except Exception as e:
        print(f"  ⚠️  Pexels API 오류: {e}")
        return None, None


def crop_center(img, target_size):
    """이미지를 중앙 기준으로 크롭하여 target_size에 맞춤"""
    from PIL import Image

    tw, th = target_size
    target_ratio = tw / th
    iw, ih = img.size
    img_ratio = iw / ih

    if img_ratio > target_ratio:
        new_h = th
        new_w = int(iw * (th / ih))
    else:
        new_w = tw
        new_h = int(ih * (tw / iw))

    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - tw) // 2
    top = (new_h - th) // 2
    img = img.crop((left, top, left + tw, top + th))
    return img


def generate_gradient_background(course_data, size=(1080, 1080)):
    """과정 주제에 따른 그라데이션 배경 생성 (Pexels 실패 시 폴백)"""
    import numpy as np
    from PIL import Image, ImageDraw

    if isinstance(course_data, str):
        title = course_data
    else:
        title = course_data.get("title", "")

    w, h = size

    color_themes = {
        "IT": [(30, 60, 114), (42, 82, 152)],
        "AI": [(25, 55, 100), (50, 100, 180)],
        "드론": [(44, 62, 80), (52, 152, 219)],
        "관광": [(22, 160, 133), (44, 62, 80)],
        "바리스타": [(62, 39, 35), (141, 110, 99)],
        "커피": [(62, 39, 35), (141, 110, 99)],
        "디자인": [(142, 68, 173), (44, 62, 80)],
        "미용": [(232, 67, 147), (200, 80, 120)],
        "건설": [(44, 62, 80), (127, 140, 141)],
        "농업": [(39, 174, 96), (46, 64, 83)],
        "요리": [(211, 84, 0), (243, 156, 18)],
        "영상": [(30, 45, 80), (70, 120, 180)],
        "마케팅": [(40, 70, 120), (80, 140, 200)],
        "3D": [(50, 50, 90), (90, 130, 180)],
        "정비": [(50, 60, 70), (90, 110, 130)],
    }

    colors = [(27, 79, 114), (46, 134, 193)]
    for keyword, theme_colors in color_themes.items():
        if keyword in title:
            colors = theme_colors
            break

    c1 = np.array(colors[0], dtype=np.float64)
    c2 = np.array(colors[1], dtype=np.float64)

    y_ratio = np.linspace(0, 1, h).reshape(h, 1)
    x_ratio = np.linspace(0, 1, w).reshape(1, w)
    t = (x_ratio * 0.5 + y_ratio * 0.5)

    gradient = c1 + (c2 - c1) * t[:, :, np.newaxis]
    gradient = np.clip(gradient, 0, 255).astype(np.uint8)

    img = Image.fromarray(gradient, mode="RGB")

    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    circles = [
        (w * 0.8, h * 0.2, 200, 30),
        (w * 0.1, h * 0.7, 150, 20),
        (w * 0.6, h * 0.8, 100, 15),
    ]
    for cx, cy, radius, alpha in circles:
        overlay_draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=(255, 255, 255, alpha)
        )

    img = img.convert('RGBA')
    img = Image.alpha_composite(img, overlay)
    img = img.convert('RGB')

    return img


def get_course_image(course_data, target_size=(1080, 1080)):
    """
    과정 데이터에 맞는 배경 이미지를 가져옵니다.
    Pexels API 실패 시 그라데이션으로 폴백합니다.

    Args:
        course_data: dict (과정 데이터) 또는 str (과정 제목, 하위호환)
        target_size: tuple - (width, height)

    Returns:
        tuple(PIL.Image, dict|None) - (이미지, 크레딧 정보)
    """
    from PIL import Image

    query = extract_search_query(course_data)
    print(f"  🔍 이미지 검색: '{query}'")

    img, credit = fetch_pexels_image(query, orientation="square")

    if img:
        img = crop_center(img, target_size)
        return img, credit

    # 폴백: 그라데이션 배경
    img = generate_gradient_background(course_data, target_size)
    return img, None
