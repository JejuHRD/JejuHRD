"""
Pexels 무료 스톡 이미지 API 연동 모듈

Pexels API Key 발급: https://www.pexels.com/api/ (무료, 월 20,000건)
환경변수: PEXELS_API_KEY

훈련과정 주제에 맞는 고품질 배경 이미지를 자동으로 검색/다운로드합니다.
"""

import os
import hashlib
from io import BytesIO

# ── 과정 키워드 → 영문 검색어 매핑 ──
# 훈련과정 제목에 포함된 한국어 키워드를 Pexels 영문 검색어로 변환
KEYWORD_MAP = {
    # IT / 디지털
    "AI": "artificial intelligence technology",
    "인공지능": "artificial intelligence",
    "프로그래밍": "programming code computer",
    "코딩": "coding laptop developer",
    "빅데이터": "data analytics technology",
    "클라우드": "cloud computing server",
    "웹": "web development design",
    "앱": "mobile app development",
    "디지털": "digital technology modern",
    "SW": "software development",
    "소프트웨어": "software development",
    "정보보안": "cybersecurity technology",
    "사이버보안": "cybersecurity",
    "블록체인": "blockchain technology",
    "메타버스": "virtual reality technology",
    "IoT": "internet of things smart",
    "사물인터넷": "internet of things",
    "로봇": "robotics automation",
    "3D프린팅": "3d printing manufacturing",

    # 드론 / 항공
    "드론": "drone aerial photography",
    "항공": "drone aerial landscape",
    "촬영": "camera photography professional",

    # 관광 / 서비스
    "관광": "tourism travel beautiful destination",
    "여행": "travel adventure tourism",
    "호텔": "hotel hospitality luxury",
    "숙박": "hotel resort accommodation",
    "외식": "restaurant food service",
    "바리스타": "coffee barista cafe",
    "커피": "coffee roasting cafe",
    "조리": "cooking chef kitchen professional",
    "요리": "cooking chef culinary",
    "제과제빵": "bakery pastry chef",
    "베이커리": "bakery bread artisan",
    "관광가이드": "tour guide travel",
    "컨벤션": "convention conference business",
    "카지노": "casino gaming entertainment",

    # 농업 / 환경
    "스마트팜": "smart farm agriculture technology",
    "농업": "agriculture farming field",
    "수산": "fishing ocean marine",
    "해양": "ocean marine coastal",
    "환경": "environment nature green",
    "신재생에너지": "renewable energy solar wind",
    "태양광": "solar panel energy",
    "전기차": "electric vehicle charging",

    # 건설 / 제조
    "건축": "architecture construction building",
    "건설": "construction site building",
    "인테리어": "interior design modern",
    "용접": "welding manufacturing industrial",
    "기계": "mechanical engineering factory",
    "자동차": "automotive car maintenance",
    "전기": "electrical engineering wiring",
    "설비": "industrial facility maintenance",
    "배관": "plumbing pipe industrial",

    # 미용 / 패션
    "미용": "beauty salon hairstyle",
    "헤어": "hairstyling salon professional",
    "네일": "nail art beauty salon",
    "메이크업": "makeup beauty cosmetics",
    "피부관리": "skincare beauty spa",
    "패션": "fashion design clothing",

    # 디자인 / 콘텐츠
    "디자인": "graphic design creative workspace",
    "영상": "video production filming",
    "콘텐츠": "content creation digital media",
    "SNS": "social media marketing",
    "마케팅": "digital marketing business",
    "광고": "advertising marketing creative",
    "유튜브": "youtube video creator",
    "편집": "video editing production",

    # 의료 / 복지
    "간호": "nursing healthcare hospital",
    "간병": "elderly care nursing",
    "요양": "elderly care facility",
    "사회복지": "social welfare community",
    "보육": "childcare education",
    "상담": "counseling therapy office",

    # 사무 / 경영
    "회계": "accounting finance business",
    "경영": "business management office",
    "무역": "international trade business",
    "물류": "logistics warehouse supply chain",
    "유통": "retail distribution business",

    # 제주 특화
    "제주": "Jeju island nature",
    "감귤": "citrus orange farm",
    "해녀": "ocean diving traditional",
    "올레": "nature trail hiking path",
}

# 폴백 검색어 (키워드 매칭 실패 시)
FALLBACK_QUERIES = [
    "professional training education",
    "career development learning",
    "modern classroom workshop",
    "technology education future",
]


def _stable_hash_index(text, mod):
    """
    실행 환경에 관계없이 동일한 인덱스를 반환하는 해시 함수.

    Python 내장 hash()는 PYTHONHASHSEED에 의해 실행마다 값이 달라질 수 있어
    GitHub Actions처럼 매번 새 프로세스에서 실행되는 환경에서는
    같은 입력에도 다른 결과를 낼 수 있습니다.
    hashlib.md5는 항상 동일한 값을 보장합니다.
    """
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()
    return int(digest, 16) % mod


def extract_search_query(course_title):
    """
    과정 제목에서 가장 적합한 Pexels 검색어를 추출합니다.

    Args:
        course_title: str - 훈련과정 제목

    Returns:
        str - Pexels API 검색용 영문 쿼리
    """
    matched_queries = []

    for korean_keyword, english_query in KEYWORD_MAP.items():
        if korean_keyword in course_title:
            matched_queries.append(english_query)

    if matched_queries:
        # 가장 구체적인 매칭을 우선 (긴 키워드가 더 구체적)
        return matched_queries[0]

    # 매칭 실패 시 폴백 (안정적 해시 사용)
    idx = _stable_hash_index(course_title, len(FALLBACK_QUERIES))
    return FALLBACK_QUERIES[idx]


def fetch_pexels_image(query, orientation="square", size="large"):
    """
    Pexels API에서 이미지를 검색하고 다운로드합니다.

    Args:
        query: str - 검색어
        orientation: str - "landscape" | "portrait" | "square"
        size: str - "large" | "medium" | "small"

    Returns:
        tuple(PIL.Image, dict) - (이미지 객체, 크레딧 정보) 또는 (None, None)
    """
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

        # 안정적 해시로 일관된 이미지 선택 (같은 과정은 항상 같은 이미지)
        photo_idx = _stable_hash_index(query, len(photos))
        photo = photos[photo_idx]

        # 이미지 다운로드 (large2x 또는 large)
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


def get_course_image(course_title, target_size=(1080, 1080)):
    """
    과정 제목에 맞는 배경 이미지를 가져옵니다.
    Pexels API 실패 시 프로그래매틱 그라데이션으로 폴백합니다.

    Args:
        course_title: str - 과정 제목
        target_size: tuple - (width, height)

    Returns:
        tuple(PIL.Image, dict|None) - (이미지, 크레딧 정보)
    """
    from PIL import Image

    query = extract_search_query(course_title)
    print(f"  🔍 이미지 검색: '{query}'")

    img, credit = fetch_pexels_image(query, orientation="square")

    if img:
        # 이미지를 target_size에 맞게 크롭 (center crop)
        img = crop_center(img, target_size)
        return img, credit

    # 폴백: 그라데이션 배경
    img = generate_gradient_background(course_title, target_size)
    return img, None


def crop_center(img, target_size):
    """이미지를 중앙 기준으로 크롭하여 target_size에 맞춤"""
    from PIL import Image

    tw, th = target_size
    target_ratio = tw / th

    iw, ih = img.size
    img_ratio = iw / ih

    if img_ratio > target_ratio:
        # 이미지가 더 넓음 → 높이 기준으로 리사이즈 후 좌우 크롭
        new_h = th
        new_w = int(iw * (th / ih))
    else:
        # 이미지가 더 좁음 → 너비 기준으로 리사이즈 후 상하 크롭
        new_w = tw
        new_h = int(ih * (tw / iw))

    img = img.resize((new_w, new_h), Image.LANCZOS)

    # 중앙 크롭
    left = (new_w - tw) // 2
    top = (new_h - th) // 2
    img = img.crop((left, top, left + tw, top + th))

    return img


def generate_gradient_background(course_title, size=(1080, 1080)):
    """
    과정 주제에 따른 그라데이션 배경 생성 (Pexels 실패 시 폴백)

    numpy 배열 연산으로 1초 이내에 생성합니다.
    (기존 draw.point 방식은 116만 픽셀을 하나씩 찍어 수십 초 소요)
    """
    import numpy as np
    from PIL import Image, ImageDraw

    w, h = size

    # 과정 주제별 색상 팔레트
    color_themes = {
        "IT": [(30, 60, 114), (42, 82, 152)],        # 딥블루
        "드론": [(44, 62, 80), (52, 152, 219)],        # 하늘
        "관광": [(22, 160, 133), (44, 62, 80)],        # 청록
        "바리스타": [(62, 39, 35), (141, 110, 99)],     # 갈색
        "커피": [(62, 39, 35), (141, 110, 99)],
        "디자인": [(142, 68, 173), (44, 62, 80)],      # 보라
        "미용": [(232, 67, 147), (200, 80, 120)],      # 핑크
        "건설": [(44, 62, 80), (127, 140, 141)],       # 그레이
        "농업": [(39, 174, 96), (46, 64, 83)],         # 그린
        "요리": [(211, 84, 0), (243, 156, 18)],        # 오렌지
        "의료": [(41, 128, 185), (109, 213, 250)],     # 라이트블루
    }

    # 주제 매칭
    colors = [(27, 79, 114), (46, 134, 193)]  # 기본 (딥블루)
    for keyword, theme_colors in color_themes.items():
        if keyword in course_title:
            colors = theme_colors
            break

    c1 = np.array(colors[0], dtype=np.float64)
    c2 = np.array(colors[1], dtype=np.float64)

    # 대각선 그라데이션을 numpy 배열로 한번에 생성
    y_ratio = np.linspace(0, 1, h).reshape(h, 1)   # (h, 1)
    x_ratio = np.linspace(0, 1, w).reshape(1, w)   # (1, w)
    t = (x_ratio * 0.5 + y_ratio * 0.5)            # (h, w) 브로드캐스트

    # (h, w, 3) 배열 생성
    gradient = c1 + (c2 - c1) * t[:, :, np.newaxis]
    gradient = np.clip(gradient, 0, 255).astype(np.uint8)

    img = Image.fromarray(gradient, mode="RGB")

    # 미묘한 패턴 오버레이 (원형 장식)
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
