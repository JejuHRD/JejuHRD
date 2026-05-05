"""
Grok (xAI) 이미지 생성 모듈

환경변수: XAI_API_KEY
모델: grok-imagine-image
엔드포인트: https://api.x.ai/v1/images/generations
훈련과정명을 기반으로 배경 이미지를 AI 생성합니다.
"""

import os
from io import BytesIO


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 분야별 시각 가이드 (v3)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _get_field_visual_guide(clean_title, training_goal=""):
    """과정명·훈련목표에서 분야를 감지해 시각 가이드를 반환합니다.

    우선순위 (memory 기준): 복합 분야 → 우선 분야(드론/건축/물류/조경/에너지)
    → 일반 분야(영상/AI/코딩/디자인/마케팅/이커머스/안전) → 기본값.

    반환 dict:
      - subject: 메인 비주얼 묘사 (사물·환경·결과물 중심, 사람 ❌)
      - human_policy: 인물 등장 정책
      - monitor_content: 화면이 등장할 때 표시할 내용 (없으면 빈 문자열)
    """
    haystack = (clean_title + " " + training_goal).lower()
    t_pad = " " + clean_title.lower() + " "

    has_drone = any(k in haystack for k in ["드론", "uav", "무인기", "무인항공"])
    has_video = any(k in haystack for k in ["영상", "촬영", "편집", "비디오", "유튜브"])
    has_delivery = any(k in haystack for k in ["배송", "택배", "물류"])
    has_ai = (" ai " in t_pad) or any(k in haystack for k in [
        "인공지능", "머신러닝", "딥러닝", "chatgpt", "생성형", "프롬프트엔지니어", "llm"
    ])

    # ── 복합 분야 (가장 구체적 매칭 우선) ──
    if has_drone and has_video:
        return {
            "subject": (
                "A professional aerial drone hovering in mid-air with its gimbal camera "
                "tilted toward a stunning Jeju coastal landscape below — volcanic black "
                "coastline, blue ocean waves, green fields. The drone is the central focal "
                "subject, its rotors in soft motion-blur, capturing the scene below."
            ),
            "human_policy": "no people visible in the frame",
            "monitor_content": "",
        }

    if has_drone and has_delivery:
        return {
            "subject": (
                "A delivery drone with a small parcel attached underneath, mid-flight above "
                "a Jeju coastal landscape, approaching a marked landing pad on the ground "
                "below. The drone and package are the central subject."
            ),
            "human_policy": "no people visible",
            "monitor_content": "",
        }

    # ── 우선 분야 ──
    if has_drone:
        return {
            "subject": (
                "A modern professional drone in mid-flight, propellers in soft motion-blur, "
                "gimbal camera mounted underneath, set against a vivid Jeju sky and "
                "landscape backdrop. The drone itself is the central subject."
            ),
            "human_policy": "no people visible",
            "monitor_content": "",
        }

    if any(k in haystack for k in ["건축", "설계", "cad", "bim", "도면"]):
        return {
            "subject": (
                "An architect's empty workspace: large monitors displaying CAD floor plans "
                "and 3D building models, blueprint prints spread on the desk, a small "
                "physical architectural model nearby. Drawings, instruments, and the model "
                "are the focus."
            ),
            "human_policy": "no people visible — empty workspace style",
            "monitor_content": (
                "Monitors display architectural CAD output: clean line floor plans, "
                "isometric 3D building wireframes, technical sections — all rendered as "
                "pure line graphics with NO text annotations, NO dimension numbers, "
                "NO labels."
            ),
        }

    if any(k in haystack for k in ["지게차", "포크리프트", "물류", "창고", "운송", "하역"]):
        return {
            "subject": (
                "An industrial warehouse interior: a forklift mid-operation lifting wooden "
                "pallets stacked with goods, multi-tier shelving units lining the aisles, "
                "polished concrete floor with directional line markings. Industrial overhead "
                "lighting."
            ),
            "human_policy": (
                "no operator visible — show the forklift mid-action with the cabin empty "
                "or driver entirely obscured behind cabin frame"
            ),
            "monitor_content": "",
        }

    if any(k in haystack for k in ["조경", "정원", "원예", "가드닝", "식재"]):
        return {
            "subject": (
                "A beautifully designed Jeju garden landscape: volcanic basalt stone walls, "
                "stepping-stone pathways winding through subtropical plants (palm trees, "
                "hydrangeas, ornamental grasses), pruned ornamental trees, and a small "
                "reflecting pond. Natural daylight, lush greenery."
            ),
            "human_policy": "no people visible",
            "monitor_content": "",
        }

    if any(k in haystack for k in ["에너지", "시설관리", "보일러", "냉난방", "공조", "전기설비"]):
        return {
            "subject": (
                "A clean mechanical room interior: industrial boiler systems, pressure "
                "gauges with analog dials (no numerals), valve manifolds, and parallel "
                "pipe networks of varying diameters. Polished metal surfaces, subtle warm "
                "under-lighting."
            ),
            "human_policy": "no people visible — empty mechanical room",
            "monitor_content": "",
        }

    # ── 일반 분야 ──
    if has_video:
        return {
            "subject": (
                "A professional video editing workstation: two large monitors on a desk, a "
                "cinema camera and headphones beside the keyboard, soft warm room lighting. "
                "The equipment and screens carry the subject."
            ),
            "human_policy": "no people visible — empty editor's station",
            "monitor_content": (
                "Primary monitor shows a video editing timeline: stacked horizontal clip "
                "strips in different colors (video tracks in blue, audio tracks in green "
                "with waveforms), a vertical playhead line, and transport controls. "
                "Secondary monitor shows the preview of a Jeju landscape clip with "
                "cinematic color grading. NO text, NO file names, NO labels visible — "
                "only the visual structure of editing."
            ),
        }

    if has_ai:
        return {
            "subject": (
                "A modern AI development workstation: multiple monitors displaying neural "
                "network architectures and data visualizations, soft blue ambient lighting, "
                "sleek minimalist hardware setup."
            ),
            "human_policy": "no people visible — empty workstation",
            "monitor_content": (
                "Monitors show AI-themed visualizations specific to AI tooling: a neural "
                "network node graph (rows of connected dots arranged in layers, with "
                "glowing blue connecting lines between layers), a heatmap matrix in "
                "red-to-blue gradient, and a data flow diagram with rectangular nodes "
                "linked by directional arrows. NO code text, NO interface labels, "
                "NO numbers — only the visual structures themselves."
            ),
        }

    if any(k in haystack for k in ["코딩", "개발", "프로그래밍", "웹개발", "앱개발", "파이썬", "자바", "백엔드", "프론트엔드"]):
        return {
            "subject": (
                "A developer's workstation: a wide curved monitor and mechanical keyboard, "
                "subtle RGB ambient lighting, a small plant on the desk. Dark theme "
                "aesthetic, no operator present."
            ),
            "human_policy": "no people visible",
            "monitor_content": (
                "Monitor shows a code-like visual rhythm: indented horizontal colored bars "
                "of varying lengths arranged like syntax-highlighted code blocks — but "
                "rendered as abstract solid-color shapes with absolutely NO actual letters, "
                "characters, or readable text. Only the visual cadence of code structure."
            ),
        }

    if any(k in haystack for k in ["디자인", "그래픽", "ui", "ux", "포토샵", "일러스트", "브랜딩"]):
        return {
            "subject": (
                "A designer's clean studio: a large monitor showing a design canvas, color "
                "palette swatches arranged on the desk, a graphics tablet and stylus, "
                "natural daylight from a side window."
            ),
            "human_policy": "no people visible",
            "monitor_content": (
                "Monitor displays a design canvas with: geometric shapes (circles, "
                "rectangles, polygons) in vibrant brand colors, a horizontal row of color "
                "palette swatches, layout grid guides. NO text, NO letter-form logos."
            ),
        }

    if any(k in haystack for k in ["마케팅", "광고", "sns", "소셜", "퍼포먼스마케팅", "콘텐츠마케팅"]):
        return {
            "subject": (
                "A marketing analytics workspace: multiple monitors showing dashboard-style "
                "data visualizations, sticky notes on the wall behind, a tablet on the desk."
            ),
            "human_policy": "no people visible",
            "monitor_content": (
                "Monitors display marketing dashboard visualizations: a line graph trending "
                "upward, colorful bar charts side-by-side, a donut chart with multiple "
                "color segments, rectangular metric widgets in a grid. NO text labels, "
                "NO numerical values — only the visual shape of data."
            ),
        }

    if any(k in haystack for k in ["이커머스", "쇼핑몰", "스마트스토어", "온라인판매", "오픈마켓", "셀러"]):
        return {
            "subject": (
                "A clean product photography setup: a tabletop product on a white seamless "
                "backdrop, softbox lighting equipment, a laptop and DSLR camera nearby on "
                "the workbench."
            ),
            "human_policy": "no people visible",
            "monitor_content": (
                "Laptop monitor shows an e-commerce product grid: rectangular product "
                "image tiles arranged in a 3x3 grid layout, a sidebar with simple category "
                "icons, a small upward-trend chart in the corner. NO text, NO product "
                "names, NO price labels."
            ),
        }

    if any(k in haystack for k in ["산업안전", "안전관리", "안전보건"]):
        return {
            "subject": (
                "An industrial work site with safety equipment as the focus: a hard hat on "
                "a workbench, safety goggles beside it, a hi-vis vest hanging nearby, and "
                "tools laid out neatly on polished concrete."
            ),
            "human_policy": "no people visible",
            "monitor_content": "",
        }

    # ── 기본값 (분야 미감지) ──
    return {
        "subject": (
            f"A clean professional workspace specifically illustrating the concept of: "
            f"{clean_title}. The tools, equipment, materials, and environment specific to "
            f"this profession are arranged thoughtfully — these objects ARE the subject."
        ),
        "human_policy": (
            "no people visible — the equipment and environment carry the subject"
        ),
        "monitor_content": "",
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 프롬프트 빌더
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _build_image_prompt(course_data):
    """이미지 생성 프롬프트 빌더 (v3).

    v3 변경점:
      1. 분야별 시각 가이드 (`_get_field_visual_guide`) 도입
         → 사람 대신 사물·환경 중심 묘사, 분야별 모니터 콘텐츠 차별화
      2. trainingGoal을 보조 컨셉으로 활용 (한글이 그려지지 않도록 명시)
      3. 인물 정책 강화: "no people / focus on equipment" 우선

    유지 원칙 (v2):
      · 한글 입력 차단 — title/goal은 컨셉 설명일 뿐, 그려넣지 마라
      · 상단 1/3 구도 — 카드뉴스 텍스트 박스와 겹치지 않도록
      · NO TEXT 정책 — 부정문 + 긍정 대체 지시 병행
    """
    if isinstance(course_data, str):
        title = course_data
        training_goal = ""
    else:
        title = course_data.get("title", "")
        training_goal = (
            course_data.get("trainingGoal", "")
            or course_data.get("traingGoal", "")  # API 오타 케이스
            or course_data.get("training_goal", "")
        )

    # (산대특) 접두사 제거
    clean_title = title.replace("(산대특)", "").replace("산대특", "").strip()

    # 분야별 시각 가이드
    guide = _get_field_visual_guide(clean_title, training_goal)

    # 훈련목표 보조 컨셉 (짧게 자르고, 한글 렌더링 방지 명시)
    goal_hint = ""
    if training_goal:
        goal_short = training_goal.replace("\n", " ").strip()[:120]
        goal_hint = (
            f" Training goal context (interpret semantically, must NOT be rendered as "
            f"visible text): {goal_short}."
        )

    # 모니터 콘텐츠 (분야에 따라 있을 수도, 없을 수도)
    monitor_clause = ""
    if guide["monitor_content"]:
        monitor_clause = f"SCREEN CONTENT: {guide['monitor_content']} "

    prompt = (
        # ── 1. 메인 컨셉 + 한글 차단 ──
        f"A photorealistic cinematic image illustrating the concept of: {clean_title}.{goal_hint} "
        f"(All Korean text above is concept description for the AI — it must NOT appear "
        f"as visible hangul, characters, or any writing in the rendered image.) "

        # ── 2. 분야별 비주얼 (사물·환경 중심) ──
        f"VISUAL FOCUS: {guide['subject']} "
        f"{monitor_clause}"

        # ── 3. 인물 정책 (사람 최소화) ──
        f"PEOPLE POLICY: {guide['human_policy']}. The composition prioritizes equipment, "
        f"tools, environment, results of the work, and the subject of the training — "
        f"NOT human figures. If a person is truly unavoidable for the scene, show only "
        f"hands at work or a silhouetted shoulder from behind, never a centered face or "
        f"a full-body figure in the foreground. "

        # ── 4. 구도 가이드 (상단 1/3) ──
        f"COMPOSITION (critical): Place the main subject in the UPPER THIRD of the frame "
        f"(top 30–40% of vertical space). Equipment, tools, and any focal point must sit "
        f"above the vertical midline. The lower two-thirds is intentionally simpler — "
        f"atmospheric negative space, soft out-of-focus background, smooth surfaces, or "
        f"gentle bokeh — leaving a clean area for text overlay. Do NOT place important "
        f"visual details below the vertical center. "

        # ── 5. NO TEXT 정책 ──
        f"NO TEXT POLICY (strict): Zero readable characters of any writing system — "
        f"no Korean hangul, no Latin alphabet, no Chinese characters, no numerals, "
        f"no logos with letters, no watermarks. "
        f"Books and papers are closed, edge-on, or fully blurred. "
        f"Signs, posters, whiteboards, name tags, and product labels are cropped, "
        f"out of focus, or rendered as blank surfaces. "
        f"Keyboards and control panels show no key markings. "
        f"Clocks, if present, are analog with no numerals on the face. "

        # ── 6. 스타일 ──
        f"STYLE: professional cinematic photography, soft directional lighting, shallow "
        f"depth of field, refined color grading. This image serves as a background — "
        f"Korean text overlay will be composited on top in a separate step."
    )

    return prompt


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Grok API 호출
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
