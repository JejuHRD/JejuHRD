"""
Grok (xAI) 이미지 생성 모듈

환경변수: XAI_API_KEY
모델: grok-imagine-image
엔드포인트: https://api.x.ai/v1/images/generations
훈련과정명을 기반으로 배경 이미지를 AI 생성합니다.
"""

import os
from io import BytesIO


def _build_image_prompt(course_data):
    """이미지 생성 프롬프트 빌더.

    설계 원칙 (v2 개선):
    1. 텍스트 제거 강화 — 부정문("NO TEXT") 단독 사용은 image diffusion 모델이
       자주 무시하므로, 텍스트가 빈출하는 요소(모니터/책/간판 등)에 대해
       긍정문 형태의 "대체 지시"를 명시함.
    2. 구도 가이드 — 카드뉴스 레이아웃 분석 결과:
         · 커버 (cover_v2):  상단 다크오버레이(y=0~200) + 하단 그라데이션·흰색카드(y=440~)
                            → 클린존 y=200~378 (전체 16~35%)
         · 상세 (detail_v2): 상단 280px(26%)만 헤더 배경 + y=0~110 흰 텍스트 오버레이
                            → 클린존 y=110~280 (전체 10~26%)
       → 두 슬라이드 공통 황금구역 = **상단 1/3**. 주제를 상단에 배치하도록 지시.
    3. 한글 입력 차단 — title이 한국어이므로 "이건 컨셉 설명일 뿐, 한글을
       그려넣지 말라"고 명시하여 hallucination 방지.
    """
    if isinstance(course_data, str):
        title = course_data
    else:
        title = course_data.get("title", "")

    # (산대특) 접두사 제거
    clean_title = title.replace("(산대특)", "").replace("산대특", "").strip()

    prompt = (
        # ── 1. 메인 컨셉 (한국어 title은 컨셉 설명용임을 명시) ──
        f"A photorealistic cinematic image illustrating the concept of: {clean_title}. "
        f"(The Korean phrase above describes the subject matter only — it must NOT appear "
        f"as visible text, hangul, or any characters in the rendered image.) "

        # ── 2. 구도 가이드 (가장 중요: 상단 1/3에 주제 배치) ──
        f"COMPOSITION (critical): Place the main subject in the UPPER THIRD of the frame "
        f"(top 30–40% of vertical space). Faces, hands at work, primary equipment, and "
        f"any focal point must sit above the vertical midline. The lower two-thirds is "
        f"intentionally simpler — atmospheric negative space, soft out-of-focus background, "
        f"smooth surfaces, or gentle bokeh — leaving a clean area for text overlay. "
        f"Do NOT place important visual details below the vertical center. "

        # ── 3. 텍스트 제거 정책 (긍정문 대체 지시 위주) ──
        f"NO TEXT POLICY (strict): The image must contain zero readable characters of any "
        f"writing system — no Korean hangul, no Latin alphabet, no Chinese characters, "
        f"no numerals, no logos, no watermarks. "
        f"Monitors and screens display only abstract glowing color patterns or soft light, "
        f"never user interfaces, code, charts, or words. "
        f"Books and papers are closed, shown edge-on, or fully blurred so nothing is legible. "
        f"Signs, posters, whiteboards, name tags, and product labels are either cropped out "
        f"of frame, heavily out of focus, or rendered as smooth blank surfaces. "
        f"Keyboards and control panels show no visible key markings or labels. "
        f"Clocks, if present, are analog with no numerals on the face. "

        # ── 4. 스타일 (배경 용도임을 명시) ──
        f"STYLE: professional cinematic photography, soft directional lighting, shallow "
        f"depth of field, refined color grading. This image serves as a background — "
        f"Korean text overlay will be composited on top in a separate step."
    )

    return prompt


def generate_image_with_grok(course_data):
    """
    Grok API (grok-imagine-image)로 배경 이미지를 생성합니다.

    Returns:
        tuple(PIL.Image, dict|None) - (이미지, 크레딧 정보)
    """
    import requests
    from PIL import Image

    api_key = os.environ.get("XAI_API_KEY", "")
    if not api_key:
        print("  ⚠️  XAI_API_KEY가 설정되지 않았습니다. 그라데이션 배경을 사용합니다.")
        return None, None

    prompt = _build_image_prompt(course_data)
    title = course_data.get("title", "") if isinstance(course_data, dict) else str(course_data)
    print(f"  🎨 Grok 이미지 생성 중... ({title[:30]})")

    try:
        response = requests.post(
            "https://api.x.ai/v1/images/generations",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": "grok-imagine-image",
                "prompt": prompt,
                "response_format": "b64_json",
                "n": 1,
            },
            timeout=60,
        )

        if response.status_code != 200:
            print(f"  ⚠️  Grok API 오류: HTTP {response.status_code}")
            try:
                err = response.json()
                print(f"      {err.get('error', {}).get('message', response.text[:200])}")
            except Exception:
                print(f"      {response.text[:200]}")
            return None, None

        data = response.json()
        images = data.get("data", [])
        if not images:
            print("  ⚠️  Grok 응답에 이미지가 없습니다.")
            return None, None

        import base64
        b64_data = images[0].get("b64_json", "")
        if not b64_data:
            # URL 방식 폴백
            img_url = images[0].get("url", "")
            if img_url:
                img_resp = requests.get(img_url, timeout=30)
                img = Image.open(BytesIO(img_resp.content))
            else:
                print("  ⚠️  Grok 응답에 이미지 데이터가 없습니다.")
                return None, None
        else:
            # b64_json에서 data:image/png;base64, 접두사 제거
            if b64_data.startswith("data:"):
                b64_data = b64_data.split(",", 1)[1]
            img_bytes = base64.b64decode(b64_data)
            img = Image.open(BytesIO(img_bytes))

        credit = {
            "photographer": "AI Generated",
            "source": "Grok (xAI)",
        }

        print(f"  ✅ 이미지 생성 완료 ({img.size[0]}x{img.size[1]})")
        return img, credit

    except requests.exceptions.Timeout:
        print("  ⚠️  Grok API 타임아웃 (60초)")
        return None, None
    except Exception as e:
        print(f"  ⚠️  Grok API 오류: {e}")
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
    """과정 주제에 따른 그라데이션 배경 생성 (Grok 실패 시 폴백)"""
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

    c1, c2 = colors
    img = Image.new('RGB', (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    return img


def get_course_image(course_data, target_size=(1080, 1080)):
    """
    과정 데이터에 맞는 배경 이미지를 Grok으로 생성합니다.
    Grok 실패 시 그라데이션으로 폴백합니다.
    """
    from PIL import Image

    img, credit = generate_image_with_grok(course_data)

    if img:
        img = crop_center(img, target_size)
        return img, credit

    print("  🔄 그라데이션 배경으로 폴백")
    img = generate_gradient_background(course_data, target_size)
    return img, None
