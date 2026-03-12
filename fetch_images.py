"""
Gemini API 이미지 생성 모듈

환경변수: GEMINI_API_KEY
모델: gemini-2.5-flash (무료 티어, 하루 500장)
훈련과정명을 기반으로 배경 이미지를 AI 생성합니다.
"""

import os
import hashlib
from io import BytesIO


def _build_image_prompt(course_data):
    """
    과정 데이터에서 Gemini 이미지 생성 프롬프트를 만듭니다.
    과정명에서 핵심 키워드를 추출하여 장면을 구성합니다.
    """
    if isinstance(course_data, str):
        title = course_data
    else:
        title = course_data.get("title", "")

    KEYWORD_SCENES = {
        "드론": "a professional drone flying over a beautiful landscape, aerial photography, cinematic lighting",
        "3D": "3D modeling workspace with digital holographic display, futuristic technology, blue glow",
        "모델링": "3D digital modeling with wireframe objects floating in space, tech aesthetic",
        "바리스타": "elegant coffee shop interior, barista pouring latte art, warm cozy lighting",
        "커피": "artisan coffee beans and espresso machine, warm cafe atmosphere",
        "인공지능": "abstract AI neural network visualization, glowing nodes and connections, dark blue background",
        "AI": "modern AI technology workspace, holographic data displays, futuristic blue tones",
        "프로그래밍": "clean coding workspace with multiple monitors showing colorful code, dark theme",
        "코딩": "developer workspace with code on screen, modern minimal desk setup",
        "빅데이터": "data visualization dashboard with flowing charts and graphs, dark tech aesthetic",
        "클라우드": "cloud computing concept with server racks and glowing connections",
        "영상": "professional video production studio with camera equipment and monitors",
        "편집": "video editing timeline on ultrawide monitor, creative studio setup",
        "촬영": "professional camera setup with studio lighting, cinematic equipment",
        "마케팅": "digital marketing analytics dashboard on screen, modern office, business growth charts",
        "SNS": "social media content creation workspace with multiple screens showing platforms",
        "콘텐츠": "creative content studio with camera, ring light, and editing setup",
        "디자인": "modern design studio with large display showing UI mockups, creative workspace",
        "출판": "elegant bookshelf with open books and manuscript pages, warm library lighting",
        "데이터": "data science workspace with visualizations and charts on dark screens",
        "미용": "modern beauty salon interior with elegant mirrors and professional equipment",
        "건설": "architectural blueprint with modern building under construction, golden hour",
        "요리": "professional kitchen with chef preparing food, warm dramatic lighting",
        "농업": "smart agriculture technology, green farm with modern monitoring equipment",
        "전기": "electrical engineering workspace with circuit boards and testing equipment",
        "용접": "industrial welding workshop with sparks, dramatic professional lighting",
        "자동차": "automotive repair workshop with modern diagnostic equipment",
        "물류": "modern logistics warehouse with organized shelving and automation",
        "간호": "modern healthcare facility, clean medical workspace with technology",
        "정비": "professional maintenance workshop with technical equipment and tools",
        "관광": "beautiful travel destination landscape, scenic tourism photography",
        "웹": "web development workspace with responsive design on multiple devices",
        "디지털": "digital transformation concept, modern technology workspace with screens",
    }

    scene = None
    for keyword, scene_desc in KEYWORD_SCENES.items():
        if keyword in title:
            scene = scene_desc
            break

    if not scene:
        scene = "modern professional training classroom with laptops and bright natural lighting"

    prompt = (
        f"A high-quality photorealistic background image for an educational course card. "
        f"Scene: {scene}. "
        f"Style: professional, clean, slightly blurred background suitable for text overlay. "
        f"No text, no words, no letters, no watermarks. "
        f"Square format 1080x1080. Soft lighting, professional color grading."
    )

    return prompt


def generate_image_with_gemini(course_data):
    """
    Gemini API로 과정에 맞는 배경 이미지를 생성합니다.

    Returns:
        tuple(PIL.Image, dict|None) - (이미지, 크레딧 정보)
    """
    from PIL import Image

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("  ⚠️  GEMINI_API_KEY가 설정되지 않았습니다. 그라데이션 배경을 사용합니다.")
        return None, None

    try:
        from google import genai
    except ImportError:
        print("  ⚠️  google-genai 미설치 — pip install google-genai 필요")
        return None, None

    prompt = _build_image_prompt(course_data)
    title = course_data.get("title", "") if isinstance(course_data, dict) else str(course_data)
    print(f"  🎨 Gemini 이미지 생성 중... ({title[:30]})")

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-04-17",
            contents=[prompt],
            config=genai.types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                img_data = part.inline_data.data
                img = Image.open(BytesIO(img_data))

                credit = {
                    "photographer": "AI Generated",
                    "source": "Google Gemini",
                }

                print(f"  ✅ 이미지 생성 완료 ({img.size[0]}x{img.size[1]})")
                return img, credit

        print("  ⚠️  Gemini 응답에 이미지가 없습니다.")
        return None, None

    except Exception as e:
        print(f"  ⚠️  Gemini API 오류: {e}")
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
    """과정 주제에 따른 그라데이션 배경 생성 (Gemini 실패 시 폴백)"""
    import numpy as np
    from PIL import Image, ImageDraw

    title = course_data.get("title", "") if isinstance(course_data, dict) else str(course_data)
    w, h = size

    color_themes = {
        "AI": [(25, 55, 100), (50, 100, 180)],
        "드론": [(44, 62, 80), (52, 152, 219)],
        "관광": [(22, 160, 133), (44, 62, 80)],
        "바리스타": [(62, 39, 35), (141, 110, 99)],
        "디자인": [(142, 68, 173), (44, 62, 80)],
        "영상": [(30, 45, 80), (70, 120, 180)],
        "마케팅": [(40, 70, 120), (80, 140, 200)],
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
    for cx, cy, radius, alpha in [(w*0.8, h*0.2, 200, 30), (w*0.1, h*0.7, 150, 20), (w*0.6, h*0.8, 100, 15)]:
        overlay_draw.ellipse([cx-radius, cy-radius, cx+radius, cy+radius], fill=(255, 255, 255, alpha))

    img = img.convert('RGBA')
    img = Image.alpha_composite(img, overlay)
    return img.convert('RGB')


def get_course_image(course_data, target_size=(1080, 1080)):
    """
    과정 데이터에 맞는 배경 이미지를 Gemini로 생성합니다.
    Gemini 실패 시 그라데이션으로 폴백합니다.
    """
    from PIL import Image

    img, credit = generate_image_with_gemini(course_data)

    if img:
        img = crop_center(img, target_size)
        return img, credit

    print("  🔄 그라데이션 배경으로 폴백")
    img = generate_gradient_background(course_data, target_size)
    return img, None
