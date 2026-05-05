"""
Grok (xAI) 이미지 생성 모듈

환경변수: XAI_API_KEY
모델: grok-imagine-image
엔드포인트: https://api.x.ai/v1/images/generations
훈련과정명을 기반으로 배경 이미지를 AI 생성합니다.
"""

import os
import re
from io import BytesIO


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 분야별 시각 가이드 (v4)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _get_field_visual_guide(clean_title, training_goal=""):
    """과정명·훈련목표에서 분야를 감지해 시각 가이드를 반환합니다.

    매칭 우선순위:
      [복합] 드론+영상 / 드론+배송 / 건축+AI / AI+마케팅 / 3D모델링
      [우선] 드론 / 건축 / 물류 / 조경 / 에너지
      [일반] 영상 / 마케팅 / AI / 코딩 / 디자인 / 이커머스 / 안전
      [기본값]

    반환 dict:
      - subject: 메인 비주얼 묘사 (사물·환경·결과물 중심, 사람 ❌)
      - human_policy: 인물 등장 정책
      - monitor_content: 화면이 등장할 때 표시할 내용 (없으면 빈 문자열)
    """
    haystack = (clean_title + " " + training_goal).lower()

    # 영문 약어를 토큰 단위로 정확 매칭 (한글 인접 케이스 대응)
    # 예: "AI마케팅" → ['ai', '마케팅'], "건축CAD AI융합" → ['cad', 'ai']
    eng_tokens = set(re.findall(r'[a-z]+', haystack))

    has_drone = any(k in haystack for k in ["드론", "무인기", "무인항공"]) or 'uav' in eng_tokens
    # 영상은 명백한 영상 작업 키워드만 (콘텐츠는 광범위해서 제외 — 마케팅·디자인 콘텐츠도 있음)
    has_video = any(k in haystack for k in [
        "영상", "촬영", "편집", "비디오", "유튜브", "크리에이터"
    ])
    has_delivery = any(k in haystack for k in ["배송", "택배", "물류"])
    has_ai = ('ai' in eng_tokens) or ('llm' in eng_tokens) or any(k in haystack for k in [
        "인공지능", "머신러닝", "딥러닝", "chatgpt", "생성형", "프롬프트엔지니어"
    ])
    has_3d = any(k in haystack for k in [
        "블렌더", "3d 모델링", "3d모델링", "마야", "지브러시", "캐릭터 모델링"
    ]) or any(t in eng_tokens for t in ["blender", "maya", "zbrush"])
    has_arch = any(k in haystack for k in ["건축", "설계", "도면"]) \
               or any(t in eng_tokens for t in ["cad", "bim"])
    has_marketing = any(k in haystack for k in [
        "마케팅", "광고", "퍼포먼스마케팅", "콘텐츠마케팅", "디지털마케팅", "sns 마케팅"
    ])
    has_ecommerce = any(k in haystack for k in [
        "이커머스", "쇼핑몰", "스마트스토어", "온라인판매", "오픈마켓", "셀러", "온라인 판매"
    ])

    # ──────────────────────────────────────────────────────────────────
    # 복합 매칭 (가장 구체적 우선)
    # ──────────────────────────────────────────────────────────────────

    # 드론 + 영상/촬영/유튜브/크리에이터 → 시네마틱 드론
    if has_drone and has_video:
        return {
            "subject": (
                "A cinematic aerial photography quadcopter drone hovering in mid-air — "
                "sleek matte-grey folding body, four propeller arms unfolded with "
                "propellers in soft motion-blur, a 3-axis gimbal-stabilized camera "
                "mounted at the front underbelly. The drone is captured against a "
                "stunning Jeju coastal landscape: volcanic black coastline, emerald "
                "ocean, green oreum (volcanic cone) hills in the distance. The drone "
                "and its mounted camera are the central focal subject."
            ),
            "human_policy": "no people visible in the frame",
            "monitor_content": "",
        }

    # 드론 + 배송/물류 → 화물 드론 (헥사/옥토콥터)
    if has_drone and has_delivery:
        return {
            "subject": (
                "An industrial cargo delivery drone hovering above a coastal landing "
                "zone — a robust hexacopter or octocopter frame with six-to-eight "
                "rotors extending from a sturdy reinforced central body, a small "
                "package box suspended from short cables underneath the drone, "
                "extended landing legs. The Jeju coast and a marked circular landing "
                "pad are in the background. The cargo drone and its package are the "
                "central subject. The drone's top surface is clean and flat — no "
                "parachute, no canopy, no fabric attachments above the body."
            ),
            "human_policy": "no people visible",
            "monitor_content": "",
        }

    # 건축 + AI 융합 → CAD + AI 생성 컨셉 격자
    if has_arch and has_ai:
        return {
            "subject": (
                "A modern AI-assisted architectural design workspace: a wide split-screen "
                "monitor displaying CAD drawings on one half and AI-generated building "
                "concept renderings on the other, a small physical architectural model "
                "and a digital stylus resting on the desk. Drawings, computational "
                "design output, and the model are the focus."
            ),
            "human_policy": "no people visible — empty workspace style",
            "monitor_content": (
                "The split-screen monitor shows two coordinated views. LEFT HALF: a 3D "
                "building wireframe view with a floor plan line drawing below it. "
                "RIGHT HALF: a 3x3 grid of AI-generated building concept thumbnails in "
                "diverse architectural styles (curved organic forms, angular modular, "
                "biomorphic, parametric facades) — each thumbnail a small rendered "
                "building image. NO text, NO labels, NO numbers — only the visual "
                "language of computational architectural design."
            ),
        }

    # AI + 마케팅 → AI 마케팅 자동화 (워크플로우 + 광고 variations)
    if has_ai and has_marketing:
        return {
            "subject": (
                "An AI-powered marketing automation workspace: multiple monitors showing "
                "automated campaign workflows alongside AI-generated ad creative "
                "variations, a tablet with stylus on the desk, modern minimal aesthetic, "
                "soft cool ambient lighting."
            ),
            "human_policy": "no people visible",
            "monitor_content": (
                "Monitors display AI marketing automation. LEFT: a workflow node "
                "diagram (rectangular nodes connected by directional arrows showing "
                "automation steps in a flowchart). MIDDLE: a 3x3 grid of AI-generated "
                "ad creative variations (each tile a different colored composition with "
                "abstract product shapes). RIGHT: a performance analytics dashboard with "
                "line graphs trending upward and small KPI metric tiles. NO text, "
                "NO ad copy, NO labels — only the visual structure of automated "
                "marketing."
            ),
        }

    # 3D 모델링 / 블렌더 → 3D 뷰포트 + 폴리곤 메시
    if has_3d:
        return {
            "subject": (
                "A 3D modeling artist's workstation: a large monitor displaying a 3D "
                "modeling viewport with a partially-completed character or product "
                "model in mid-creation, a graphics tablet with stylus on the desk, "
                "soft cool-toned ambient lighting. No operator present."
            ),
            "human_policy": "no people visible",
            "monitor_content": (
                "Monitor shows a 3D modeling interface (Blender-style viewport): a "
                "perspective viewport with a colorful 3D character or product model in "
                "mid-creation, a polygon mesh wireframe overlaid on the shaded surface, "
                "a transform gizmo (red/green/blue arrow handles) visible on the model, "
                "a small material preview sphere at the corner, an outliner panel on "
                "the side as plain rectangular bars. NO text, NO menu labels, NO panel "
                "titles — only the visual language of 3D modeling."
            ),
        }

    # 이커머스 + 마케팅 → 제품 카탈로그 + 광고 대시보드 분할 화면
    if has_ecommerce and has_marketing:
        return {
            "subject": (
                "An e-commerce marketing operations workspace: a primary monitor "
                "displaying an online product catalog dashboard, a secondary monitor "
                "showing an ad performance dashboard, product samples on the desk "
                "(a small box, fabric swatches), a tablet with stylus, modern minimal "
                "aesthetic, soft natural daylight."
            ),
            "human_policy": "no people visible",
            "monitor_content": (
                "Monitors display an e-commerce + advertising combination. PRIMARY "
                "monitor: a product catalog grid — a 3x3 or 4x3 layout of rectangular "
                "product image tiles, each with a small colored badge in the corner, "
                "a sidebar with simple category icons. SECONDARY monitor: an ad "
                "performance dashboard with line graphs trending upward, donut charts, "
                "and rectangular campaign cards arranged in a grid. NO text, NO "
                "product names, NO prices, NO ad copy — only the visual structure of "
                "e-commerce marketing."
            ),
        }

    # ──────────────────────────────────────────────────────────────────
    # 우선 분야
    # ──────────────────────────────────────────────────────────────────

    # 드론 단독 → 시네마틱 드론 (배송 키워드 없으면 영상 드론으로 디폴트)
    if has_drone:
        return {
            "subject": (
                "A cinematic quadcopter drone in mid-flight — sleek matte-grey folding "
                "body, four unfolded propeller arms with propellers in soft motion-blur, "
                "a 3-axis gimbal camera mounted at the front underbelly, sturdy landing "
                "gear retracted. Set against a vivid Jeju sky and coastal landscape "
                "backdrop. The drone itself is the central subject."
            ),
            "human_policy": "no people visible",
            "monitor_content": "",
        }

    # 건축/설계/CAD (단독)
    if has_arch:
        return {
            "subject": (
                "An architect's empty workspace: large monitors displaying CAD floor "
                "plans and 3D building models, blueprint prints spread on the desk, a "
                "small physical architectural model nearby. Drawings, instruments, and "
                "the model are the focus."
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
                "An industrial warehouse interior: a forklift mid-operation lifting "
                "wooden pallets stacked with goods, multi-tier shelving units lining "
                "the aisles, polished concrete floor with directional line markings. "
                "Industrial overhead lighting."
            ),
            "human_policy": (
                "no operator visible — show the forklift mid-action with the cabin "
                "empty or driver entirely obscured behind cabin frame"
            ),
            "monitor_content": "",
        }

    if any(k in haystack for k in ["조경", "정원", "원예", "가드닝", "식재"]):
        return {
            "subject": (
                "A beautifully designed Jeju garden landscape: volcanic basalt stone "
                "walls, stepping-stone pathways winding through subtropical plants "
                "(palm trees, hydrangeas, ornamental grasses), pruned ornamental trees, "
                "and a small reflecting pond. Natural daylight, lush greenery."
            ),
            "human_policy": "no people visible",
            "monitor_content": "",
        }

    if any(k in haystack for k in ["에너지", "시설관리", "보일러", "냉난방", "공조", "전기설비"]):
        return {
            "subject": (
                "A clean mechanical room interior: industrial boiler systems, pressure "
                "gauges with analog dials (no numerals), valve manifolds, and parallel "
                "pipe networks of varying diameters. Polished metal surfaces, subtle "
                "warm under-lighting."
            ),
            "human_policy": "no people visible — empty mechanical room",
            "monitor_content": "",
        }

    # ──────────────────────────────────────────────────────────────────
    # 일반 분야 (우선순위: 이커머스/마케팅 → 영상 → AI → 코딩 → 디자인 → 안전)
    # 이커머스·마케팅이 영상보다 위 — trainingGoal에 영상 키워드 섞여도 명시 의도가 우선
    # ──────────────────────────────────────────────────────────────────

    # 이커머스 단독 (마케팅 없는 케이스)
    if has_ecommerce:
        return {
            "subject": (
                "A clean product photography setup: a tabletop product on a white "
                "seamless backdrop, softbox lighting equipment, a laptop showing an "
                "e-commerce product catalog and a DSLR camera nearby on the workbench."
            ),
            "human_policy": "no people visible",
            "monitor_content": (
                "Laptop monitor shows an e-commerce product catalog dashboard: "
                "rectangular product image tiles arranged in a 3x3 grid layout, a "
                "sidebar with simple category icons, a small upward-trend chart in "
                "the corner. NO text, NO product names, NO price labels."
            ),
        }

    # 마케팅 단독 (AI+마케팅, 이커머스+마케팅 매칭에서 빠진 케이스)
    if has_marketing:
        return {
            "subject": (
                "A marketing operations workspace: multiple monitors showing campaign "
                "dashboards and analytics, sticky notes and printed campaign mockups "
                "on the wall behind, a tablet with stylus on the desk, modern minimal "
                "aesthetic."
            ),
            "human_policy": "no people visible",
            "monitor_content": (
                "Monitors display marketing campaign dashboards (Google Ads / Meta Ads "
                "manager style): rectangular campaign cards arranged in a grid layout, "
                "line graphs trending upward, donut charts with multiple color "
                "segments, small KPI metric tiles, and a funnel visualization on one "
                "screen. NO text, NO numerical values, NO campaign names — only the "
                "visual shape of marketing data."
            ),
        }

    # 영상/편집/촬영/유튜브/크리에이터 — monitor_content 시각화 강화 (v5)
    if has_video:
        return {
            "subject": (
                "A professional video editor's workstation: a wide primary monitor "
                "actively displaying a video editing application interface, a smaller "
                "secondary monitor beside it showing color-graded footage preview, a "
                "cinema camera with mounted gimbal and a clapper slate on the desk, "
                "headphones on a stand. Soft warm key light from the side, subtle "
                "blue-purple monitor glow."
            ),
            "human_policy": "no people visible — empty editor's station",
            "monitor_content": (
                "Primary monitor displays a dark-themed video editing interface with "
                "a very specific visual structure. BOTTOM HALF of the screen is "
                "dominated by a multi-track timeline: five to seven horizontal "
                "stacked colored bars (red, blue, purple, green) of varying lengths, "
                "layered like horizontal bricks across the full width, with a "
                "vertical playhead line crossing through them; the green bars (audio "
                "tracks) contain small triangular waveform shapes inside. TOP HALF: "
                "a video preview window on the right showing a color-graded Jeju "
                "coastal aerial shot, and a media bin on the left with thumbnail "
                "clips arranged in a 3x2 grid. This is NOT an architectural drawing, "
                "NOT a 3D model, NOT a CAD floor plan — it is a video editing "
                "timeline with horizontal colored clip bars. NO text, NO file names, "
                "NO panel labels."
            ),
        }

    # AI 단독 (마케팅·영상·건축에 흡수되지 않은 순수 AI 과정)
    if has_ai:
        return {
            "subject": (
                "A modern AI development workstation: multiple monitors displaying "
                "neural network architectures and data visualizations, soft blue "
                "ambient lighting, sleek minimalist hardware setup."
            ),
            "human_policy": "no people visible — empty workstation",
            "monitor_content": (
                "Monitors show AI-themed visualizations specific to AI tooling: a "
                "neural network node graph (rows of connected dots arranged in layers, "
                "with glowing blue connecting lines between layers), a heatmap matrix "
                "in red-to-blue gradient, and a data flow diagram with rectangular "
                "nodes linked by directional arrows. NO code text, NO interface "
                "labels, NO numbers — only the visual structures themselves."
            ),
        }

    if any(k in haystack for k in [
        "코딩", "개발", "프로그래밍", "웹개발", "앱개발", "파이썬", "자바",
        "백엔드", "프론트엔드"
    ]):
        return {
            "subject": (
                "A developer's workstation: a wide curved monitor and mechanical "
                "keyboard, subtle RGB ambient lighting, a small plant on the desk. "
                "Dark theme aesthetic, no operator present."
            ),
            "human_policy": "no people visible",
            "monitor_content": (
                "Monitor shows a code-like visual rhythm: indented horizontal colored "
                "bars of varying lengths arranged like syntax-highlighted code blocks "
                "— but rendered as abstract solid-color shapes with absolutely NO "
                "actual letters, characters, or readable text. Only the visual "
                "cadence of code structure."
            ),
        }

    if any(k in haystack for k in [
        "디자인", "그래픽", "ui", "ux", "포토샵", "일러스트", "브랜딩"
    ]):
        return {
            "subject": (
                "A designer's clean studio: a large monitor showing a design canvas, "
                "color palette swatches arranged on the desk, a graphics tablet and "
                "stylus, natural daylight from a side window."
            ),
            "human_policy": "no people visible",
            "monitor_content": (
                "Monitor displays a design canvas with: geometric shapes (circles, "
                "rectangles, polygons) in vibrant brand colors, a horizontal row of "
                "color palette swatches, layout grid guides. NO text, NO letter-form "
                "logos."
            ),
        }

    if any(k in haystack for k in ["산업안전", "안전관리", "안전보건"]):
        return {
            "subject": (
                "An industrial work site with safety equipment as the focus: a hard "
                "hat on a workbench, safety goggles beside it, a hi-vis vest hanging "
                "nearby, and tools laid out neatly on polished concrete."
            ),
            "human_policy": "no people visible",
            "monitor_content": "",
        }

    # 기본값
    return {
        "subject": (
            f"A clean professional workspace specifically illustrating the concept of: "
            f"{clean_title}. The tools, equipment, materials, and environment specific "
            f"to this profession are arranged thoughtfully — these objects ARE the "
            f"subject."
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
    """이미지 생성 프롬프트 빌더 (v5).

    v5 변경점 (이전 피드백 대응):
      1. 영상편집 monitor_content 시각화 강화
         · 추상적 묘사("editing application interface") → 시각 패턴 직설 묘사
         · "5-7개 가로 색깔 막대, 벽돌처럼 층층이, 수직 플레이헤드"
         · 도면/3D와 명백히 구별되는 시각적 큐로 모델 무시 방지
      2. 일반 분야 우선순위 재조정 (이커머스/마케팅 → 영상)
         · trainingGoal에 영상 키워드 섞여도 마케팅·이커머스 의도가 우선
         · "스마트스토어 마케팅"이 영상편집으로 매칭되는 문제 차단
      3. 이커머스+마케팅 복합 매칭 신설
         · 분할 화면: 제품 카탈로그 + 광고 퍼포먼스 대시보드
      4. has_video 키워드에서 "콘텐츠 제작" 제거 (광범위해서 마케팅·디자인 콘텐츠도 포함)
      5. 드론배송 subject에서 낙하산 묘사 제거 (펼친 낙하산으로 그려지는 문제)

    v4 유지: 복합 매칭 (드론+영상, 드론+배송, 건축+AI, AI+마케팅, 3D),
             드론 형태 구체화, 영문 토큰 정확 매칭

    유지 원칙 (v3): 인물 정책, 한글 차단, 상단 1/3 구도, NO TEXT
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

    # 모니터 콘텐츠
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
        f"no logos with letters, no watermarks, no brand names. "
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
