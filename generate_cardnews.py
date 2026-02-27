"""
카드뉴스 자동 생성기 - 제주지역인적자원개발위원회 특화훈련 홍보용
Instagram용 1080x1080 이미지를 생성합니다.
"""

from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import math
from benefits_helper import get_badge_text, get_benefits_text, get_benefits_footnote, get_step3_text, get_total_hours

# ── 브랜드 컬러 ──
COLORS = {
    "primary": "#1B4F72",       # 딥 블루 (신뢰감)
    "primary_light": "#2E86C1", # 밝은 블루
    "accent": "#E67E22",        # 오렌지 (주목)
    "accent_bright": "#F39C12", # 밝은 오렌지
    "white": "#FFFFFF",
    "bg_light": "#F8F9FA",      # 밝은 배경
    "text_dark": "#2C3E50",     # 본문 텍스트
    "text_gray": "#7F8C8D",     # 보조 텍스트
    "success": "#27AE60",       # 초록 (무료/혜택 강조)
    "tag_bg": "#EBF5FB",        # 태그 배경
}

# ── 폰트 설정 ──
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_REGULAR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_BLACK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_font(path, size, index=1):
    """한국어 폰트 로드 (index=1 = KR)"""
    try:
        return ImageFont.truetype(path, size, index=index)
    except:
        return ImageFont.truetype(path, size, index=0)

def draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    """둥근 모서리 사각형"""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def wrap_text_to_lines(text, font, max_width, draw):
    """텍스트를 최대 너비에 맞게 어절(공백) 단위로 줄바꿈"""
    lines = []
    for paragraph in text.split('\n'):
        if not paragraph.strip():
            lines.append('')
            continue
        words = paragraph.split(' ')
        current_line = ''
        for word in words:
            test_line = (current_line + ' ' + word).strip() if current_line else word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] > max_width:
                if current_line:
                    lines.append(current_line)
                # 단어 자체가 max_width보다 넓으면 글자 단위로 분할
                bbox_word = draw.textbbox((0, 0), word, font=font)
                if bbox_word[2] - bbox_word[0] > max_width:
                    sub = ''
                    for ch in word:
                        test_sub = sub + ch
                        bbox_sub = draw.textbbox((0, 0), test_sub, font=font)
                        if bbox_sub[2] - bbox_sub[0] > max_width and sub:
                            lines.append(sub)
                            sub = ch
                        else:
                            sub = test_sub
                    current_line = sub
                else:
                    current_line = word
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)
    return lines


def generate_slide_cover(course_data, output_path):
    """
    슬라이드 1: 커버 이미지 (주목 유도)
    개선: 아이콘 정보카드 + 비용 임팩트 강조 + 혜택 배너 + 섹션 여백 확보
    """
    W, H = 1080, 1080
    img = Image.new('RGB', (W, H), hex_to_rgb(COLORS["white"]))
    draw = ImageDraw.Draw(img)

    # ── 상단 배경 블록 ──
    draw_rounded_rect(draw, (0, 0, W, 520), radius=0, fill=hex_to_rgb(COLORS["primary"]))

    # 상단 장식 라인
    draw.rectangle((0, 0, W, 8), fill=hex_to_rgb(COLORS["accent"]))

    # ── 상단 태그 ──
    font_tag = get_font(FONT_BOLD, 31)
    tag_text = "제주지역 특화훈련"
    tag_bbox = draw.textbbox((0, 0), tag_text, font=font_tag)
    tag_w = tag_bbox[2] - tag_bbox[0] + 44
    tag_h = tag_bbox[3] - tag_bbox[1] + 24
    tag_x = 60
    tag_y = 45
    draw_rounded_rect(draw, (tag_x, tag_y, tag_x + tag_w, tag_y + tag_h),
                       radius=22, fill=hex_to_rgb(COLORS["accent"]))
    draw.text((tag_x + 22, tag_y + 8), tag_text, font=font_tag, fill=hex_to_rgb(COLORS["white"]))

    # ── "자부담 10%" 뱃지 ──
    font_badge = get_font(FONT_BOLD, 29)
    badge_text = get_badge_text(course_data)
    badge_bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    badge_w = badge_bbox[2] - badge_bbox[0] + 44
    badge_h = badge_bbox[3] - badge_bbox[1] + 24
    badge_x = W - badge_w - 60
    badge_y = 45
    draw_rounded_rect(draw, (badge_x, badge_y, badge_x + badge_w, badge_y + badge_h),
                       radius=22, fill=hex_to_rgb(COLORS["success"]))
    draw.text((badge_x + 22, badge_y + 8), badge_text, font=font_badge, fill=hex_to_rgb(COLORS["white"]))

    # ── NCS직종명 (태그-뱃지 사이 중앙) ──
    ncs_name = course_data.get("ncsName", "")
    if ncs_name:
        font_ncs = get_font(FONT_BOLD, 33)
        ncs_label = f"NCS {ncs_name}"
        ncs_bbox = draw.textbbox((0, 0), ncs_label, font=font_ncs)
        ncs_text_w = ncs_bbox[2] - ncs_bbox[0]
        ncs_text_h = ncs_bbox[3] - ncs_bbox[1]
        ncs_pad_x, ncs_pad_y = 24, 15
        ncs_pill_w = ncs_text_w + ncs_pad_x * 2
        ncs_pill_h = ncs_text_h + ncs_pad_y * 2
        gap_left = tag_x + tag_w
        gap_right = badge_x
        ncs_pill_x = gap_left + (gap_right - gap_left - ncs_pill_w) // 2
        ncs_pill_y = tag_y + (tag_h - ncs_pill_h) // 2
        draw_rounded_rect(draw,
                           (ncs_pill_x, ncs_pill_y,
                            ncs_pill_x + ncs_pill_w, ncs_pill_y + ncs_pill_h),
                           radius=20, fill=hex_to_rgb("#1A3A5C"), outline=hex_to_rgb("#FFFFFF"), width=2)
        draw.text((ncs_pill_x + ncs_pad_x, ncs_pill_y + ncs_pad_y), ncs_label,
                  font=font_ncs, fill=hex_to_rgb("#FFFFFF"))

    # ── 과정명 (메인 타이틀) ──
    font_title = get_font(FONT_BLACK, 55)
    title_lines = wrap_text_to_lines(course_data["title"], font_title, W - 140, draw)
    if len(title_lines) > 3:
        title_lines = title_lines[:3]
        title_lines[-1] = title_lines[-1][:-1] + "…"

    title_y_start = 145
    line_height = 75
    for i, line in enumerate(title_lines):
        draw.text((70, title_y_start + i * line_height), line,
                  font=font_title, fill=hex_to_rgb(COLORS["white"]))

    # ── 훈련기관명 ──
    font_inst = get_font(FONT_REGULAR, 33)
    inst_y = title_y_start + len(title_lines) * line_height + 15
    draw.text((70, inst_y), f"{course_data['institution']}",
              font=font_inst, fill=hex_to_rgb("#AED6F1"))

    # ── 좌측 액센트 라인 ──
    draw.rectangle((0, 520, 6, H - 100), fill=hex_to_rgb(COLORS["accent"]))

    # ══════════════════════════════════════════════════
    # 하단 정보 영역 (아이콘 카드 + 비용 강조 + 혜택 배너)
    # ══════════════════════════════════════════════════

    # ── 정보 아이콘 카드 (가로 배치, 배움기간 넓게) ──
    info_items = []
    if course_data.get("period"):
        info_items.append(("▷", "배움 기간", course_data["period"], 1.4))
    hours = get_total_hours(course_data)
    if hours > 0:
        info_items.append(("▷", "배움 시간", f"{hours}시간", 0.8))
    if course_data.get("capacity"):
        info_items.append(("▷", "모집 인원", course_data["capacity"], 0.8))

    card_top = 540
    card_margin = 50
    n_items = len(info_items)

    if n_items > 0:
        gap = 16
        total_gap = gap * (n_items - 1)
        usable_w = W - card_margin * 2 - total_gap
        total_weight = sum(item[3] for item in info_items)
        card_h = 95

        font_info_label = get_font(FONT_REGULAR, 21)
        font_info_value = get_font(FONT_BOLD, 27)
        font_marker = get_font(FONT_BOLD, 22)

        cx = card_margin
        for i, (marker, label, value, weight) in enumerate(info_items):
            card_w = int(usable_w * weight / total_weight)
            # 카드 배경
            draw_rounded_rect(draw,
                              (cx, card_top, cx + card_w, card_top + card_h),
                              radius=12, fill=hex_to_rgb(COLORS["bg_light"]))
            # 마커 (작은 원형 뱃지)
            dot_r = 14
            dot_cx = cx + 24
            dot_cy = card_top + card_h // 2
            draw_rounded_rect(draw,
                              (dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r),
                              radius=dot_r, fill=hex_to_rgb(COLORS["primary"]))
            m_bbox = draw.textbbox((0, 0), marker, font=font_marker)
            m_w = m_bbox[2] - m_bbox[0]
            draw.text((dot_cx - m_w // 2, dot_cy - 10), marker,
                      font=font_marker, fill=hex_to_rgb(COLORS["white"]))
            # 라벨
            draw.text((cx + 50, card_top + 14), label, font=font_info_label,
                      fill=hex_to_rgb(COLORS["text_gray"]))
            # 값
            draw.text((cx + 50, card_top + 46), value, font=font_info_value,
                      fill=hex_to_rgb(COLORS["text_dark"]))
            cx += card_w + gap

        next_y = card_top + card_h + 18
    else:
        next_y = card_top + 10

    # ── 비용 강조 영역 (박스 확대 + 세로 중앙 정렬) ──
    self_cost = course_data.get("selfCost", "")
    course_cost = course_data.get("courseCost", "")
    if self_cost or course_cost:
        cost_box_h = 120
        cost_box_top = next_y
        cost_box_bottom = next_y + cost_box_h
        draw_rounded_rect(draw,
                           (card_margin, cost_box_top, W - card_margin, cost_box_bottom),
                           radius=15, fill=hex_to_rgb("#EBF5FB"))

        font_cost_label = get_font(FONT_BOLD, 25)
        font_cost_prefix = get_font(FONT_BOLD, 31)
        font_cost_big = get_font(FONT_BLACK, 48)
        font_cost_small = get_font(FONT_REGULAR, 21)

        # 콘텐츠 높이 계산 (라벨 + 금액행)
        label_text = "■ 자부담금"
        label_bbox = draw.textbbox((0, 0), label_text, font=font_cost_label)
        label_h = label_bbox[3] - label_bbox[1]
        cost_line_bbox = draw.textbbox((0, 0), "단, 000,000원", font=font_cost_big)
        cost_line_h = cost_line_bbox[3] - cost_line_bbox[1]
        content_gap = 12
        total_content_h = label_h + content_gap + cost_line_h
        content_top = cost_box_top + (cost_box_h - total_content_h) // 2

        # 라벨
        draw.text((card_margin + 22, content_top), label_text,
                  font=font_cost_label, fill=hex_to_rgb(COLORS["primary"]))

        cost_row_y = content_top + label_h + content_gap
        if self_cost:
            prefix_text = "단,"
            draw.text((card_margin + 22, cost_row_y), prefix_text,
                      font=font_cost_prefix, fill=hex_to_rgb(COLORS["text_dark"]))
            prefix_bbox = draw.textbbox((0, 0), prefix_text, font=font_cost_prefix)
            prefix_w = prefix_bbox[2] - prefix_bbox[0]

            draw.text((card_margin + 22 + prefix_w + 12, cost_row_y - 6), self_cost,
                      font=font_cost_big, fill=hex_to_rgb(COLORS["accent"]))

            if course_cost:
                cost_bbox = draw.textbbox((0, 0), self_cost, font=font_cost_big)
                cost_w = cost_bbox[2] - cost_bbox[0]
                small_x = card_margin + 22 + prefix_w + 12 + cost_w + 14
                draw.text((small_x, cost_row_y + 8),
                          f"(수강비 {course_cost})",
                          font=font_cost_small, fill=hex_to_rgb("#888888"))
        elif course_cost:
            draw.text((card_margin + 22, cost_row_y), course_cost,
                      font=font_cost_big, fill=hex_to_rgb(COLORS["accent"]))
        next_y += cost_box_h + 12

    # ── 혜택 배너 (세로 중앙 정렬) ──
    benefits = course_data.get("benefits", "") or get_benefits_text(course_data)
    benefit_lines = [l.strip() for l in benefits.split('\n') if l.strip()]

    if benefit_lines:
        visible_lines = benefit_lines[:3]
        line_h = 34
        banner_h = max(60, len(visible_lines) * line_h + 24)
        banner_top = next_y
        draw_rounded_rect(draw,
                           (card_margin, banner_top, W - card_margin, banner_top + banner_h),
                           radius=15, fill=hex_to_rgb("#FEF9E7"))

        font_benefit_icon = get_font(FONT_BOLD, 27)
        font_benefit = get_font(FONT_REGULAR, 24)

        # 텍스트 영역 세로 중앙
        total_text_h = len(visible_lines) * line_h
        text_start_y = banner_top + (banner_h - total_text_h) // 2

        draw.text((card_margin + 18, text_start_y), "★",
                  font=font_benefit_icon, fill=hex_to_rgb(COLORS["accent"]))
        for bi, bline in enumerate(visible_lines):
            draw.text((card_margin + 52, text_start_y + bi * line_h), bline,
                      font=font_benefit, fill=hex_to_rgb(COLORS["text_dark"]))

        next_y += banner_h + 8

    # ── 하단 ※ 주석 ──
    font_footnote = get_font(FONT_REGULAR, 23)
    footnote = get_benefits_footnote(course_data)
    draw.text((60, next_y), footnote,
              font=font_footnote, fill=hex_to_rgb(COLORS["text_dark"]))

    # ── 하단 바 ──
    footer_y = H - 80
    footer_bar_h = H - footer_y
    draw.rectangle((0, footer_y, W, H), fill=hex_to_rgb(COLORS["primary"]))
    font_footer = get_font(FONT_REGULAR, 23)
    font_cta = get_font(FONT_BOLD, 25)

    org_text = "제주지역인적자원개발위원회"
    org_bbox = draw.textbbox((0, 0), org_text, font=font_footer)
    org_h = org_bbox[3] - org_bbox[1]
    org_text_y = footer_y + (footer_bar_h - org_h) // 2
    draw.text((60, org_text_y), org_text,
              font=font_footer, fill=hex_to_rgb("#AED6F1"))

    cta_text = "신청 ▸ work24.go.kr"
    cta_bbox = draw.textbbox((0, 0), cta_text, font=font_cta)
    cta_w = cta_bbox[2] - cta_bbox[0]
    cta_h = cta_bbox[3] - cta_bbox[1]
    cta_text_y = footer_y + (footer_bar_h - cta_h) // 2
    draw.text((W - cta_w - 60, cta_text_y), cta_text,
              font=font_cta, fill=hex_to_rgb(COLORS["accent_bright"]))

    img.save(output_path, quality=95)
    return output_path


def generate_slide_detail(course_data, output_path):
    """
    슬라이드 2: 과정 상세 정보

    데이터 우선순위:
    1. trainingGoal(훈련목표)이 있으면 → 훈련목표 중심 레이아웃
    2. curriculum이 있으면 → 커리큘럼 리스트 레이아웃
    3. 둘 다 없으면 → 과정 기본정보 요약 레이아웃
    """
    W, H = 1080, 1080
    img = Image.new('RGB', (W, H), hex_to_rgb(COLORS["bg_light"]))
    draw = ImageDraw.Draw(img)

    # 상단 컬러 바
    draw.rectangle((0, 0, W, 8), fill=hex_to_rgb(COLORS["accent"]))
    draw.rectangle((0, 8, W, 12), fill=hex_to_rgb(COLORS["primary"]))

    training_goal = course_data.get("trainingGoal", "")
    curriculum = course_data.get("curriculum", [])

    if training_goal:
        _draw_slide_detail_goal(draw, W, H, course_data, training_goal)
    elif curriculum:
        _draw_slide_detail_curriculum(draw, W, H, course_data, curriculum)
    else:
        _draw_slide_detail_fallback(draw, W, H, course_data)

    # ── 하단 바 ──
    footer_y = H - 80
    footer_bar_h = H - footer_y
    draw.rectangle((0, footer_y, W, H), fill=hex_to_rgb(COLORS["primary"]))
    font_footer = get_font(FONT_REGULAR, 23)
    ft_text = "제주지역인적자원개발위원회  |  신청: work24.go.kr"
    ft_bbox = draw.textbbox((0, 0), ft_text, font=font_footer)
    ft_h = ft_bbox[3] - ft_bbox[1]
    ft_text_y = footer_y + (footer_bar_h - ft_h) // 2
    draw.text((60, ft_text_y), ft_text,
              font=font_footer, fill=hex_to_rgb("#AED6F1"))

    img.save(output_path, quality=95)
    return output_path


def _draw_slide_detail_goal(draw, W, H, course_data, training_goal):
    """훈련목표가 있을 때의 상세 슬라이드 레이아웃 (카드 UI + 과정정보 태그)"""
    from benefits_helper import get_total_hours, get_course_type

    footer_y = H - 80  # 하단 footer 시작점

    # ── 헤더 영역 ──
    font_header = get_font(FONT_BOLD, 39)
    draw.text((60, 45), "이런 걸 배워요", font=font_header, fill=hex_to_rgb(COLORS["primary"]))

    font_subtitle = get_font(FONT_REGULAR, 25)
    title_short = course_data["title"][:38] + ("…" if len(course_data["title"]) > 38 else "")
    draw.text((60, 95), title_short, font=font_subtitle, fill=hex_to_rgb(COLORS["text_gray"]))

    # 구분선
    draw.line((60, 138, W - 60, 138), fill=hex_to_rgb("#D5D8DC"), width=2)

    # ── 하단 과정정보 태그 영역 (먼저 계산하여 카드 영역 확보) ──
    hours = get_total_hours(course_data)
    institution = course_data.get("institution", "")
    ncs_name = course_data.get("ncsName", "")
    ctype = get_course_type(course_data)

    # 태그 데이터 수집
    info_tags = []
    if institution:
        info_tags.append(institution[:20])
    if hours > 0:
        info_tags.append(f"총 {hours}시간")
    if ncs_name:
        info_tags.append(ncs_name[:20])
    ctype_labels = {"short": "단기과정", "general": "일반과정", "long": "장기과정"}
    if ctype in ctype_labels:
        info_tags.append(ctype_labels[ctype])

    # 태그 영역 높이 계산
    info_area_h = 0
    if info_tags:
        info_area_h = 110  # 태그 2줄 + 여백

    # ── 훈련목표 카드 영역 ──
    card_top = 158
    card_bottom = footer_y - info_area_h - 20
    card_left = 45
    card_right = W - 45
    card_inner_w = card_right - card_left - 80  # 좌우 패딩 40씩

    # 카드 배경 (흰색 라운드 + 그림자 효과)
    # 그림자
    draw_rounded_rect(draw, (card_left + 4, card_top + 4, card_right + 4, card_bottom + 4),
                       radius=16, fill=hex_to_rgb("#E8E8E8"))
    # 카드 본체
    draw_rounded_rect(draw, (card_left, card_top, card_right, card_bottom),
                       radius=16, fill=hex_to_rgb("#FFFFFF"))
    # 좌측 악센트 바
    accent_bar_w = 6
    draw_rounded_rect(draw, (card_left, card_top, card_left + accent_bar_w, card_bottom),
                       radius=0, fill=hex_to_rgb(COLORS["accent"]))
    # 좌상단 라운딩 복원
    draw_rounded_rect(draw, (card_left, card_top, card_left + 20, card_top + 20),
                       radius=16, fill=hex_to_rgb(COLORS["accent"]))

    # 카드 내부 라벨
    label_y = card_top + 22
    font_goal_label = get_font(FONT_BOLD, 30)
    draw.text((card_left + 30, label_y), "■  훈련목표",
              font=font_goal_label, fill=hex_to_rgb(COLORS["primary"]))

    # 라벨 아래 얇은 구분선
    sep_y = label_y + 46
    draw.line((card_left + 30, sep_y, card_right - 30, sep_y),
              fill=hex_to_rgb("#EBF5FB"), width=2)

    # ── 훈련목표 본문 (자동 폰트 크기 조정) ──
    text_top = sep_y + 16
    text_bottom = card_bottom - 22
    available_h = text_bottom - text_top

    font_sizes = [32, 29, 26, 24, 21]
    line_spacings = [56, 52, 48, 44, 40]

    chosen_idx = 0
    for idx, (fsize, lspace) in enumerate(zip(font_sizes, line_spacings)):
        test_font = get_font(FONT_REGULAR, fsize)
        test_lines = wrap_text_to_lines(training_goal, test_font, card_inner_w, draw)
        total_h = len(test_lines) * lspace
        if total_h <= available_h:
            chosen_idx = idx
            break
        chosen_idx = idx

    font_size = font_sizes[chosen_idx]
    line_spacing = line_spacings[chosen_idx]
    font_goal_body = get_font(FONT_REGULAR, font_size)
    goal_lines = wrap_text_to_lines(training_goal, font_goal_body, card_inner_w, draw)

    # 텍스트 수직 중앙 정렬 (내용이 짧을 때 빈 공간 방지)
    max_visible = int(available_h / line_spacing)
    visible_lines = goal_lines[:max_visible]
    total_text_h = len(visible_lines) * line_spacing
    y = text_top + max(0, (available_h - total_text_h) // 2)

    for line in visible_lines:
        if y + line_spacing > text_bottom + 5:
            break
        draw.text((card_left + 40, y), line,
                  font=font_goal_body, fill=hex_to_rgb(COLORS["text_dark"]))
        y += line_spacing

    # ── 하단 과정정보 태그 (카드 아래) ──
    if info_tags:
        tag_y = card_bottom + 18
        font_tag = get_font(FONT_BOLD, 27)
        tag_x = card_left
        tag_h = 42
        tag_gap = 12
        tag_pad_x = 18

        for tag_label in info_tags:
            bbox = draw.textbbox((0, 0), tag_label, font=font_tag)
            tw = bbox[2] - bbox[0]
            tag_w = tw + tag_pad_x * 2

            # 줄바꿈: 오른쪽 넘어가면 다음 줄로
            if tag_x + tag_w > card_right:
                tag_x = card_left
                tag_y += tag_h + tag_gap

            # 태그 배경 (둥근 필 모양)
            draw_rounded_rect(draw,
                              (tag_x, tag_y, tag_x + tag_w, tag_y + tag_h),
                              radius=tag_h // 2,
                              fill=hex_to_rgb(COLORS["tag_bg"]))
            # 태그 텍스트
            text_y = tag_y + (tag_h - (bbox[3] - bbox[1])) // 2
            draw.text((tag_x + tag_pad_x, text_y), tag_label,
                      font=font_tag, fill=hex_to_rgb(COLORS["primary"]))

            tag_x += tag_w + tag_gap


def _draw_slide_detail_curriculum(draw, W, H, course_data, curriculum):
    """커리큘럼이 있을 때의 상세 슬라이드 레이아웃 (기존 로직)"""
    # ── 헤더 ──
    font_header = get_font(FONT_BOLD, 39)
    draw.text((60, 45), "이런 걸 배워요", font=font_header, fill=hex_to_rgb(COLORS["primary"]))

    font_subtitle = get_font(FONT_REGULAR, 27)
    title_short = course_data["title"][:35] + ("…" if len(course_data["title"]) > 35 else "")
    draw.text((60, 95), title_short, font=font_subtitle, fill=hex_to_rgb(COLORS["text_gray"]))

    draw.line((60, 142, W - 60, 142), fill=hex_to_rgb("#D5D8DC"), width=2)

    # ── 커리큘럼 항목 ──
    font_item_title = get_font(FONT_BOLD, 29)
    font_item_desc = get_font(FONT_REGULAR, 25)

    y = 170
    for i, item in enumerate(curriculum[:6]):
        circle_x, circle_y = 80, y + 18
        circle_r = 22
        draw_rounded_rect(draw,
                           (circle_x - circle_r, circle_y - circle_r,
                            circle_x + circle_r, circle_y + circle_r),
                           radius=circle_r, fill=hex_to_rgb(COLORS["primary"]))

        font_num = get_font(FONT_BOLD, 23)
        num_text = str(i + 1)
        num_bbox = draw.textbbox((0, 0), num_text, font=font_num)
        num_w = num_bbox[2] - num_bbox[0]
        draw.text((circle_x - num_w // 2, circle_y - 13), num_text,
                  font=font_num, fill=hex_to_rgb(COLORS["white"]))

        if isinstance(item, dict):
            title_text = item.get("title", "")
            desc_text = item.get("desc", "")
        else:
            title_text = str(item)
            desc_text = ""

        draw.text((120, y), title_text, font=font_item_title, fill=hex_to_rgb(COLORS["text_dark"]))
        if desc_text:
            desc_lines = wrap_text_to_lines(desc_text, font_item_desc, W - 200, draw)
            for j, dl in enumerate(desc_lines[:2]):
                draw.text((120, y + 42 + j * 34), dl,
                          font=font_item_desc, fill=hex_to_rgb(COLORS["text_gray"]))
            y += 42 + min(len(desc_lines), 2) * 34
        y += 72

        if i < len(curriculum[:6]) - 1:
            draw.line((120, y - 25, W - 60, y - 25), fill=hex_to_rgb("#EAECEE"), width=1)

    # ── 하단: 수료 후 혜택 ──
    outcome_y = max(y + 10, H - 250)
    draw_rounded_rect(draw, (40, outcome_y, W - 40, outcome_y + 130),
                       radius=15, fill=hex_to_rgb(COLORS["primary"]))

    font_outcome_title = get_font(FONT_BOLD, 27)
    font_outcome = get_font(FONT_REGULAR, 25)

    draw.text((70, outcome_y + 15), "배우고 나면",
              font=font_outcome_title, fill=hex_to_rgb(COLORS["accent_bright"]))

    outcome_text = course_data.get("outcome", "관련 분야 취업 연계 | 자격증 취득 지원")
    outcome_lines = wrap_text_to_lines(outcome_text, font_outcome, W - 160, draw)
    for i, line in enumerate(outcome_lines[:2]):
        draw.text((70, outcome_y + 55 + i * 36), line,
                  font=font_outcome, fill=hex_to_rgb(COLORS["white"]))


def _draw_slide_detail_fallback(draw, W, H, course_data):
    """훈련목표/커리큘럼 모두 없을 때 — 간결한 안내 레이아웃"""

    # ── 헤더 ──
    font_header = get_font(FONT_BOLD, 39)
    draw.text((60, 45), "이런 걸 배워요", font=font_header, fill=hex_to_rgb(COLORS["primary"]))

    font_subtitle = get_font(FONT_REGULAR, 27)
    title_short = course_data["title"][:35] + ("…" if len(course_data["title"]) > 35 else "")
    draw.text((60, 95), title_short, font=font_subtitle, fill=hex_to_rgb(COLORS["text_gray"]))

    draw.line((60, 142, W - 60, 142), fill=hex_to_rgb("#D5D8DC"), width=2)

    # ── 중앙: 상세 정보 안내 ──
    font_msg = get_font(FONT_REGULAR, 30)
    font_url = get_font(FONT_BOLD, 28)

    msg_y = H // 2 - 80
    msg_lines = [
        "훈련과정의 상세 내용은",
        "고용24에서 확인할 수 있어요.",
    ]
    for line in msg_lines:
        bbox = draw.textbbox((0, 0), line, font=font_msg)
        lw = bbox[2] - bbox[0]
        draw.text(((W - lw) // 2, msg_y), line,
                  font=font_msg, fill=hex_to_rgb(COLORS["text_gray"]))
        msg_y += 48

    msg_y += 20
    url_text = "work24.go.kr"
    url_bbox = draw.textbbox((0, 0), url_text, font=font_url)
    url_w = url_bbox[2] - url_bbox[0]
    draw.text(((W - url_w) // 2, msg_y), url_text,
              font=font_url, fill=hex_to_rgb(COLORS["accent"]))


def generate_slide_howto(course_data, output_path):
    """
    슬라이드 3: 신청 방법 안내
    개선: 타임라인 레이아웃 + 원형 넘버 뱃지 + 연결선 + 문의 정보 강화
    """
    W, H = 1080, 1080
    img = Image.new('RGB', (W, H), hex_to_rgb(COLORS["white"]))
    draw = ImageDraw.Draw(img)

    # 상단 컬러 바
    draw.rectangle((0, 0, W, 8), fill=hex_to_rgb(COLORS["accent"]))
    draw.rectangle((0, 8, W, 12), fill=hex_to_rgb(COLORS["primary"]))

    # ── 헤더 ──
    font_header = get_font(FONT_BOLD, 43)
    draw.text((60, 45), "이렇게 신청하세요", font=font_header, fill=hex_to_rgb(COLORS["primary"]))
    draw.line((60, 108, W - 60, 108), fill=hex_to_rgb("#D5D8DC"), width=2)

    # ── 3단계 프로세스 ──
    step3_title, step3_desc = get_step3_text(course_data)
    title = course_data.get("title", "")

    steps = [
        {
            "num": "1",
            "title": "국민내일배움카드 만들기",
            "desc": "고용24(work24.go.kr)에서 신청하거나\n가까운 고용센터에 방문하면 돼요",
        },
        {
            "num": "2",
            "title": "원하는 과정 찾아서 신청하기",
            "desc": f"고용24에서 '{title}'으로\n검색하고 해당 과정을 바로 신청!",
        },
        {
            "num": "3",
            "title": step3_title,
            "desc": step3_desc,
        }
    ]

    font_step_title = get_font(FONT_BOLD, 31)
    font_step_desc = get_font(FONT_REGULAR, 24)
    font_num = get_font(FONT_BLACK, 28)

    # 타임라인 레이아웃 설정
    timeline_x = 105  # 타임라인 세로선 x좌표
    circle_r = 28     # 원형 뱃지 반지름
    card_left = 155    # 카드 시작 x
    card_right = W - 55
    card_h = 175
    gap = 30

    step_y = 135

    for i, step in enumerate(steps):
        card_top = step_y
        card_bottom = step_y + card_h
        circle_cy = card_top + card_h // 2  # 원 중심 y

        # ── 타임라인 세로 연결선 (원 위/아래) ──
        line_color = hex_to_rgb("#D5E8F5")
        if i > 0:
            # 이전 카드 하단 ~ 현재 원 상단
            prev_bottom = card_top - gap
            draw.line((timeline_x, prev_bottom, timeline_x, circle_cy - circle_r),
                      fill=line_color, width=3)
        if i < len(steps) - 1:
            # 현재 원 하단 ~ 다음 카드 상단 위치
            draw.line((timeline_x, circle_cy + circle_r, timeline_x, card_bottom + gap // 2),
                      fill=line_color, width=3)

        # ── 원형 넘버 뱃지 ──
        draw_rounded_rect(draw,
                           (timeline_x - circle_r, circle_cy - circle_r,
                            timeline_x + circle_r, circle_cy + circle_r),
                           radius=circle_r, fill=hex_to_rgb(COLORS["primary"]))
        # 원 안의 숫자 중앙 정렬
        num_bbox = draw.textbbox((0, 0), step["num"], font=font_num)
        num_w = num_bbox[2] - num_bbox[0]
        num_h = num_bbox[3] - num_bbox[1]
        draw.text((timeline_x - num_w // 2, circle_cy - num_h // 2 - 2),
                  step["num"], font=font_num, fill=hex_to_rgb(COLORS["white"]))

        # ── 카드 배경 (그림자 + 본체) ──
        draw_rounded_rect(draw,
                           (card_left + 3, card_top + 3, card_right + 3, card_bottom + 3),
                           radius=14, fill=hex_to_rgb("#E8E8E8"))
        draw_rounded_rect(draw,
                           (card_left, card_top, card_right, card_bottom),
                           radius=14, fill=hex_to_rgb(COLORS["bg_light"]))

        # ── 카드 내 콘텐츠 (수직 중앙) ──
        # desc 줄바꿈 처리 (카드 폭에 맞게)
        desc_max_w = card_right - card_left - 48
        raw_desc_lines = step["desc"].split('\n')
        desc_lines = []
        for raw_line in raw_desc_lines:
            wrapped = wrap_text_to_lines(raw_line, font_step_desc, desc_max_w, draw)
            desc_lines.extend(wrapped if wrapped else [""])

        title_bbox = draw.textbbox((0, 0), step["title"], font=font_step_title)
        title_h = title_bbox[3] - title_bbox[1]
        desc_line_h = 35
        desc_total_h = len(desc_lines) * desc_line_h
        content_h = title_h + 14 + desc_total_h
        content_start = card_top + (card_h - content_h) // 2

        # STEP 라벨 + 제목 (한 줄)
        font_step_label = get_font(FONT_BOLD, 19)
        step_label = f"STEP {step['num']}"
        draw.text((card_left + 24, content_start - 2), step_label,
                  font=font_step_label, fill=hex_to_rgb(COLORS["accent"]))
        label_bbox = draw.textbbox((0, 0), step_label, font=font_step_label)
        label_w = label_bbox[2] - label_bbox[0]

        draw.text((card_left + 24 + label_w + 12, content_start - 5), step["title"],
                  font=font_step_title, fill=hex_to_rgb(COLORS["text_dark"]))

        # 설명
        desc_start_y = content_start + title_h + 14
        for j, line in enumerate(desc_lines):
            draw.text((card_left + 24, desc_start_y + j * desc_line_h), line,
                      font=font_step_desc, fill=hex_to_rgb(COLORS["text_gray"]))

        step_y = card_bottom + gap

    # ── 하단: 문의 정보 (아이콘 + URL 포함) ──
    info_y = step_y + 5
    info_box_h = 120
    draw_rounded_rect(draw, (50, info_y, W - 50, info_y + info_box_h),
                       radius=15, fill=hex_to_rgb("#FEF9E7"),
                       outline=hex_to_rgb(COLORS["accent"]), width=2)

    font_info_title = get_font(FONT_BOLD, 27)
    font_info_detail = get_font(FONT_REGULAR, 24)
    font_info_url = get_font(FONT_BOLD, 24)

    draw.text((78, info_y + 12), "■ 궁금한 점은",
              font=font_info_title, fill=hex_to_rgb(COLORS["accent"]))

    contact = course_data.get("contact", "제주고용센터 064-728-7201")
    contact = contact.replace("☎", "").replace("📞", "").replace("  ", " ").strip()
    draw.text((78, info_y + 50), f"Tel. {contact}",
              font=font_info_detail, fill=hex_to_rgb(COLORS["text_dark"]))

    draw.text((78, info_y + 84), "▸ work24.go.kr",
              font=font_info_url, fill=hex_to_rgb(COLORS["primary"]))

    # ── 하단 ※ 주석 (footer 위 충분한 여백) ──
    footer_y = H - 80
    font_footnote = get_font(FONT_REGULAR, 23)
    footnote = get_benefits_footnote(course_data)
    draw.text((60, footer_y - 42), footnote,
              font=font_footnote, fill=hex_to_rgb(COLORS["text_dark"]))

    # ── 하단 바 ──
    draw.rectangle((0, footer_y, W, H), fill=hex_to_rgb(COLORS["primary"]))
    font_footer = get_font(FONT_REGULAR, 23)
    ft_text = "제주지역인적자원개발위원회  |  국민내일배움카드 있으면 누구나 참여할 수 있어요"
    ft_bbox = draw.textbbox((0, 0), ft_text, font=font_footer)
    ft_h = ft_bbox[3] - ft_bbox[1]
    footer_bar_h = H - footer_y
    ft_text_y = footer_y + (footer_bar_h - ft_h) // 2
    draw.text((60, ft_text_y), ft_text,
              font=font_footer, fill=hex_to_rgb("#AED6F1"))

    img.save(output_path, quality=95)
    return output_path


def generate_cardnews(course_data, output_dir="output"):
    """
    과정 데이터를 받아 카드뉴스 3장 세트를 생성합니다.
    """
    os.makedirs(output_dir, exist_ok=True)

    safe_name = course_data["title"][:30].replace(" ", "_").replace("/", "_")

    paths = []

    # 슬라이드 1: 커버
    p1 = os.path.join(output_dir, f"{safe_name}_1_cover.png")
    generate_slide_cover(course_data, p1)
    paths.append(p1)
    print(f"  ✅ 커버 이미지 생성: {p1}")

    # 슬라이드 2: 훈련목표/상세 (항상 생성)
    p2 = os.path.join(output_dir, f"{safe_name}_2_detail.png")
    generate_slide_detail(course_data, p2)
    paths.append(p2)
    print(f"  ✅ 상세 이미지 생성: {p2}")

    # 슬라이드 3: 신청 방법
    p3 = os.path.join(output_dir, f"{safe_name}_3_howto.png")
    generate_slide_howto(course_data, p3)
    paths.append(p3)
    print(f"  ✅ 신청방법 이미지 생성: {p3}")

    return paths
