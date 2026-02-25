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

    # ── NCS직종명 (태그-뱃지 사이 중앙, 태그 스타일) ──
    ncs_name = course_data.get("ncsName", "")
    if ncs_name:
        font_ncs = get_font(FONT_BOLD, 22)
        ncs_label = f"NCS {ncs_name}"
        ncs_bbox = draw.textbbox((0, 0), ncs_label, font=font_ncs)
        ncs_text_w = ncs_bbox[2] - ncs_bbox[0]
        ncs_text_h = ncs_bbox[3] - ncs_bbox[1]
        ncs_pad_x, ncs_pad_y = 16, 10
        ncs_pill_w = ncs_text_w + ncs_pad_x * 2
        ncs_pill_h = ncs_text_h + ncs_pad_y * 2
        # 태그 오른쪽 ~ 뱃지 왼쪽 사이 중앙
        gap_left = tag_x + tag_w
        gap_right = badge_x
        ncs_pill_x = gap_left + (gap_right - gap_left - ncs_pill_w) // 2
        ncs_pill_y = tag_y + (tag_h - ncs_pill_h) // 2
        draw_rounded_rect(draw,
                           (ncs_pill_x, ncs_pill_y,
                            ncs_pill_x + ncs_pill_w, ncs_pill_y + ncs_pill_h),
                           radius=14, fill=hex_to_rgb("#1A3A5C"), outline=hex_to_rgb("#FFFFFF"), width=2)
        draw.text((ncs_pill_x + ncs_pad_x, ncs_pill_y + ncs_pad_y), ncs_label,
                  font=font_ncs, fill=hex_to_rgb("#FFFFFF"))

    # ── 과정명 (메인 타이틀) ──
    font_title = get_font(FONT_BLACK, 55)
    title_lines = wrap_text_to_lines(course_data["title"], font_title, W - 140, draw)

    # 최대 3줄로 제한
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

    # ── 하단 정보 카드 영역 ──
    card_y = 545
    card_margin = 50
    card_padding = 30

    # 정보 항목들
    info_items = []
    if course_data.get("period"):
        info_items.append(("배움 기간", course_data["period"]))
    hours = get_total_hours(course_data)
    if hours > 0:
        info_items.append(("배움 시간", f"{hours}시간"))
    if course_data.get("capacity"):
        info_items.append(("모집 인원", course_data["capacity"]))

    font_label = get_font(FONT_BOLD, 27)
    font_value = get_font(FONT_REGULAR, 27)

    item_y = card_y + 10
    for idx, (label, value) in enumerate(info_items):
        draw.text((card_margin + card_padding, item_y), label,
                  font=font_label, fill=hex_to_rgb(COLORS["primary"]))
        draw.text((card_margin + card_padding + 180, item_y), value,
                  font=font_value, fill=hex_to_rgb(COLORS["text_dark"]))
        item_y += 48
        if idx < len(info_items) - 1:
            draw.line((card_margin + card_padding, item_y - 8,
                       W - card_margin - card_padding, item_y - 8),
                      fill=hex_to_rgb("#E8E8E8"), width=1)

    # ── 비용 강조 영역 ──
    self_cost = course_data.get("selfCost", "")
    course_cost = course_data.get("courseCost", "")
    if self_cost or course_cost:
        cost_y = item_y + 8
        cost_box_h = 120
        draw_rounded_rect(draw,
                           (card_margin, cost_y, W - card_margin, cost_y + cost_box_h),
                           radius=15, fill=hex_to_rgb("#EBF5FB"))
        font_cost_label = get_font(FONT_BOLD, 27)
        font_cost_prefix = get_font(FONT_BOLD, 29)
        font_cost_big = get_font(FONT_BLACK, 42)
        font_cost_small = get_font(FONT_REGULAR, 21)

        draw.text((card_margin + 22, cost_y + 12), "자부담금",
                  font=font_cost_label, fill=hex_to_rgb(COLORS["primary"]))
        if self_cost:
            # "단," 접두어
            prefix_text = "단,"
            cost_row_y = cost_y + 60
            draw.text((card_margin + 22, cost_row_y), prefix_text,
                      font=font_cost_prefix, fill=hex_to_rgb(COLORS["text_dark"]))
            prefix_bbox = draw.textbbox((0, 0), prefix_text, font=font_cost_prefix)
            prefix_w = prefix_bbox[2] - prefix_bbox[0]

            # 금액 (큰 글씨)
            draw.text((card_margin + 22 + prefix_w + 10, cost_row_y - 4), self_cost,
                      font=font_cost_big, fill=hex_to_rgb(COLORS["accent"]))

            # (수강비 XXX원) 작은 글씨
            if course_cost:
                cost_bbox = draw.textbbox((0, 0), self_cost, font=font_cost_big)
                cost_w = cost_bbox[2] - cost_bbox[0]
                small_x = card_margin + 22 + prefix_w + 10 + cost_w + 12
                draw.text((small_x, cost_row_y + 10),
                          f"(수강비 {course_cost})",
                          font=font_cost_small, fill=hex_to_rgb("#888888"))
        elif course_cost:
            draw.text((card_margin + 22, cost_y + 60), course_cost,
                      font=font_cost_big, fill=hex_to_rgb(COLORS["accent"]))
        item_y = cost_y + cost_box_h + 8

    # ── 혜택 하이라이트 박스 ──
    benefit_y = item_y + 5
    benefits = course_data.get("benefits", "") or get_benefits_text(course_data)
    benefit_lines = benefits.split('\n')
    benefit_box_h = 55 + len(benefit_lines) * 32
    draw_rounded_rect(draw,
                       (card_margin, benefit_y, W - card_margin, benefit_y + benefit_box_h),
                       radius=15, fill=hex_to_rgb("#FEF9E7"))

    font_benefit_title = get_font(FONT_BOLD, 27)
    font_benefit = get_font(FONT_REGULAR, 23)

    draw.text((card_margin + 22, benefit_y + 10), "이런 혜택이!",
              font=font_benefit_title, fill=hex_to_rgb(COLORS["accent"]))
    for bi, bline in enumerate(benefit_lines):
        draw.text((card_margin + 22, benefit_y + 45 + bi * 32), bline,
                  font=font_benefit, fill=hex_to_rgb(COLORS["text_dark"]))

    # ── 하단 ※ 주석 ──
    footer_y = H - 100
    font_footnote = get_font(FONT_REGULAR, 20)
    footnote = get_benefits_footnote(course_data)
    draw.text((60, footer_y - 28), footnote,
              font=font_footnote, fill=hex_to_rgb("#888888"))

    # ── 하단 바 (기관명 + CTA) ──
    footer_bar_h = H - footer_y  # 100px
    draw.rectangle((0, footer_y, W, H), fill=hex_to_rgb(COLORS["primary"]))
    font_footer = get_font(FONT_REGULAR, 23)
    font_cta = get_font(FONT_BOLD, 25)

    # 기관명 수직 중앙
    org_text = "제주지역인적자원개발위원회"
    org_bbox = draw.textbbox((0, 0), org_text, font=font_footer)
    org_h = org_bbox[3] - org_bbox[1]
    org_text_y = footer_y + (footer_bar_h - org_h) // 2
    draw.text((60, org_text_y), org_text,
              font=font_footer, fill=hex_to_rgb("#AED6F1"))

    # CTA 수직 중앙
    cta_text = "신청 ▸ work24.go.kr"
    cta_bbox = draw.textbbox((0, 0), cta_text, font=font_cta)
    cta_w = cta_bbox[2] - cta_bbox[0]
    cta_h = cta_bbox[3] - cta_bbox[1]
    cta_text_y = footer_y + (footer_bar_h - cta_h) // 2
    draw.text((W - cta_w - 60, cta_text_y), cta_text,
              font=font_cta, fill=hex_to_rgb(COLORS["accent_bright"]))

    # ── 좌측 액센트 라인 ──
    draw.rectangle((0, 520, 6, footer_y), fill=hex_to_rgb(COLORS["accent"]))

    img.save(output_path, quality=95)
    return output_path


def generate_slide_detail(course_data, output_path):
    """
    슬라이드 2: 상세 정보 (교육 내용, 커리큘럼 요약)
    """
    W, H = 1080, 1080
    img = Image.new('RGB', (W, H), hex_to_rgb(COLORS["bg_light"]))
    draw = ImageDraw.Draw(img)

    # 상단 컬러 바
    draw.rectangle((0, 0, W, 8), fill=hex_to_rgb(COLORS["accent"]))
    draw.rectangle((0, 8, W, 12), fill=hex_to_rgb(COLORS["primary"]))

    # ── 헤더 ──
    font_header = get_font(FONT_BOLD, 39)
    draw.text((60, 45), "이런 걸 배워요", font=font_header, fill=hex_to_rgb(COLORS["primary"]))

    # 과정명 (소제목)
    font_subtitle = get_font(FONT_REGULAR, 27)
    title_short = course_data["title"][:35] + ("…" if len(course_data["title"]) > 35 else "")
    draw.text((60, 95), title_short, font=font_subtitle, fill=hex_to_rgb(COLORS["text_gray"]))

    # 구분선
    draw.line((60, 142, W - 60, 142), fill=hex_to_rgb("#D5D8DC"), width=2)

    # ── 커리큘럼 / 교육 내용 ──
    font_item_title = get_font(FONT_BOLD, 29)
    font_item_desc = get_font(FONT_REGULAR, 25)

    curriculum = course_data.get("curriculum", [])
    y = 170

    for i, item in enumerate(curriculum[:6]):  # 최대 6개 항목
        # 번호 원
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

        # 항목 텍스트
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

        # 구분선 (마지막 항목 제외)
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


def generate_slide_howto(course_data, output_path):
    """
    슬라이드 3: 신청 방법 안내
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

    steps = [
        {
            "num": "STEP 1",
            "title": "국민내일배움카드 만들기",
            "desc": "고용24(work24.go.kr)에서 신청하거나\n가까운 고용센터에 방문하면 돼요",
        },
        {
            "num": "STEP 2",
            "title": "원하는 과정 찾아서 신청하기",
            "desc": "고용24에서 '제주' + 관심 분야로 검색하고\n마음에 드는 과정에 바로 신청!",
        },
        {
            "num": "STEP 3",
            "title": step3_title,
            "desc": step3_desc,
        }
    ]

    font_step_num = get_font(FONT_BOLD, 23)
    font_step_title = get_font(FONT_BOLD, 33)
    font_step_desc = get_font(FONT_REGULAR, 25)

    step_y = 140
    card_h = 210
    gap = 28

    for i, step in enumerate(steps):
        card_top = step_y
        card_bottom = step_y + card_h
        draw_rounded_rect(draw, (50, card_top, W - 50, card_bottom),
                           radius=15, fill=hex_to_rgb(COLORS["bg_light"]))

        # 좌측 액센트 바
        draw_rounded_rect(draw, (50, card_top, 58, card_bottom),
                           radius=0, fill=hex_to_rgb(COLORS["accent"]))

        # ── 콘텐츠 높이 계산 후 수직 중앙 배치 ──
        num_bbox = draw.textbbox((0, 0), step["num"], font=font_step_num)
        num_tag_h = num_bbox[3] - num_bbox[1] + 16
        title_bbox = draw.textbbox((0, 0), step["title"], font=font_step_title)
        title_h = title_bbox[3] - title_bbox[1]
        desc_lines = step["desc"].split('\n')
        desc_line_h = 36
        desc_total_h = len(desc_lines) * desc_line_h

        # 간격: 번호태그-제목 12px, 제목-설명 10px
        content_h = num_tag_h + 12 + title_h + 10 + desc_total_h
        content_start = card_top + (card_h - content_h) // 2

        # 스텝 번호 태그
        num_tag_w = num_bbox[2] - num_bbox[0] + 30
        draw_rounded_rect(draw, (85, content_start, 85 + num_tag_w, content_start + num_tag_h),
                           radius=15, fill=hex_to_rgb(COLORS["primary"]))
        draw.text((100, content_start + 4), step["num"],
                  font=font_step_num, fill=hex_to_rgb(COLORS["white"]))

        # 우측 장식 원
        dot_x = W - 110
        dot_y = card_top + card_h // 2
        dot_r = 25
        draw_rounded_rect(draw,
                           (dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r),
                           radius=dot_r, fill=hex_to_rgb(COLORS["accent"]))

        # 제목
        title_y_pos = content_start + num_tag_h + 12
        draw.text((85, title_y_pos), step["title"],
                  font=font_step_title, fill=hex_to_rgb(COLORS["text_dark"]))

        # 설명
        desc_start_y = title_y_pos + title_h + 10
        for j, line in enumerate(desc_lines):
            draw.text((85, desc_start_y + j * desc_line_h), line,
                      font=font_step_desc, fill=hex_to_rgb(COLORS["text_gray"]))

        step_y = card_bottom + gap

        # 화살표 (마지막 제외)
        if i < len(steps) - 1:
            arrow_x = W // 2
            arrow_y = card_bottom + gap // 2
            draw.text((arrow_x - 10, arrow_y - 12), "▼",
                      font=get_font(FONT_BOLD, 23), fill=hex_to_rgb(COLORS["accent"]))

    # ── 하단: 문의 정보 ──
    info_y = step_y + 10
    info_box_h = 105
    draw_rounded_rect(draw, (50, info_y, W - 50, info_y + info_box_h),
                       radius=15, fill=hex_to_rgb("#FEF9E7"),
                       outline=hex_to_rgb(COLORS["accent"]), width=2)

    font_info = get_font(FONT_BOLD, 27)
    font_info_detail = get_font(FONT_REGULAR, 25)

    draw.text((78, info_y + 15), "궁금하신 점은",
              font=font_info, fill=hex_to_rgb(COLORS["accent"]))

    contact = course_data.get("contact", "제주고용센터 ☎ 064-728-7201")
    draw.text((78, info_y + 58), contact,
              font=font_info_detail, fill=hex_to_rgb(COLORS["text_dark"]))

    # ── 하단 ※ 주석 ──
    footer_y = H - 80
    font_footnote = get_font(FONT_REGULAR, 20)
    footnote = get_benefits_footnote(course_data)
    draw.text((60, footer_y - 28), footnote,
              font=font_footnote, fill=hex_to_rgb("#888888"))

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

    # 슬라이드 2: 상세 (커리큘럼이 있는 경우만)
    if course_data.get("curriculum"):
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
