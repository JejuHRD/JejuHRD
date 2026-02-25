"""
카드뉴스 v2 - 배경 이미지 지원 버전
Pexels API 또는 그라데이션 배경 위에 텍스트를 오버레이합니다.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
from benefits_helper import get_badge_text, get_benefits_text, get_benefits_footnote

# ── 폰트 ──
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_REGULAR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_BLACK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"

# ── 컬러 ──
ACCENT = "#E67E22"
ACCENT_BRIGHT = "#F39C12"
SUCCESS = "#27AE60"
PRIMARY = "#1B4F72"

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def get_font(path, size, index=1):
    try:
        return ImageFont.truetype(path, size, index=index)
    except:
        return ImageFont.truetype(path, size, index=0)

def draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def wrap_text(text, font, max_width, draw):
    lines = []
    for para in text.split('\n'):
        if not para.strip():
            lines.append('')
            continue
        words = para.split(' ')
        cur = ''
        for word in words:
            test = (cur + ' ' + word).strip() if cur else word
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > max_width:
                if cur:
                    lines.append(cur)
                bbox_w = draw.textbbox((0, 0), word, font=font)
                if bbox_w[2] - bbox_w[0] > max_width:
                    sub = ''
                    for ch in word:
                        test_sub = sub + ch
                        bbox_sub = draw.textbbox((0, 0), test_sub, font=font)
                        if bbox_sub[2] - bbox_sub[0] > max_width and sub:
                            lines.append(sub)
                            sub = ch
                        else:
                            sub = test_sub
                    cur = sub
                else:
                    cur = word
            else:
                cur = test
        if cur:
            lines.append(cur)
    return lines


def apply_dark_overlay(img, opacity=140):
    """이미지 위에 반투명 어두운 오버레이 적용"""
    overlay = Image.new('RGBA', img.size, (0, 0, 0, opacity))
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    result = Image.alpha_composite(img, overlay)
    return result.convert('RGB')


def apply_gradient_overlay(img, direction="bottom"):
    """하단 또는 상단에서 점점 어두워지는 그라데이션 오버레이"""
    w, h = img.size
    gradient = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)

    for y in range(h):
        if direction == "bottom":
            if y < h * 0.35:
                alpha = 0
            else:
                progress = (y - h * 0.35) / (h * 0.65)
                alpha = int(200 * progress)
        else:
            if y > h * 0.65:
                alpha = 0
            else:
                progress = 1 - (y / (h * 0.65))
                alpha = int(200 * progress)
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))

    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    result = Image.alpha_composite(img, gradient)
    return result.convert('RGB')


def generate_cover_v2(course_data, bg_image, credit, output_path):
    """커버 이미지 v2: 배경 이미지 + 텍스트 오버레이"""
    W, H = 1080, 1080

    bg = bg_image.copy().resize((W, H), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=2))
    img = apply_gradient_overlay(bg, direction="bottom")

    # 상단 추가 오버레이
    overlay_top = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_top = ImageDraw.Draw(overlay_top)
    draw_top.rectangle((0, 0, W, 200), fill=(0, 0, 0, 100))
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, overlay_top).convert('RGB')

    draw = ImageDraw.Draw(img)

    # ── 상단 액센트 라인 ──
    draw.rectangle((0, 0, W, 6), fill=hex_to_rgb(ACCENT))

    # ── 상단 태그 ──
    font_tag = get_font(FONT_BOLD, 29)
    tag_text = "제주지역 특화훈련"
    tag_bbox = draw.textbbox((0, 0), tag_text, font=font_tag)
    tag_w = tag_bbox[2] - tag_bbox[0] + 40
    tag_h = tag_bbox[3] - tag_bbox[1] + 22
    draw_rounded_rect(draw, (50, 38, 50 + tag_w, 38 + tag_h),
                       radius=18, fill=hex_to_rgb(ACCENT))
    draw.text((70, 44), tag_text, font=font_tag, fill=(255, 255, 255))

    # ── 상단 뱃지 ──
    font_badge = get_font(FONT_BOLD, 27)
    badge_text = get_badge_text(course_data)
    badge_bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    badge_w = badge_bbox[2] - badge_bbox[0] + 40
    badge_h = badge_bbox[3] - badge_bbox[1] + 22
    badge_x = W - badge_w - 50
    draw_rounded_rect(draw, (badge_x, 38, badge_x + badge_w, 38 + badge_h),
                       radius=18, fill=hex_to_rgb(SUCCESS))
    draw.text((badge_x + 20, 44), badge_text, font=font_badge, fill=(255, 255, 255))

    # ── 하단 콘텐츠 영역 (반투명 카드) ──
    card_y = 440
    card_img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card_img)

    card_draw.rounded_rectangle(
        (30, card_y, W - 30, H - 30),
        radius=20,
        fill=(255, 255, 255, 230)
    )

    img = img.convert('RGBA')
    img = Image.alpha_composite(img, card_img).convert('RGB')
    draw = ImageDraw.Draw(img)

    # ── 과정명 ──
    font_title = get_font(FONT_BLACK, 49)
    title_lines = wrap_text(course_data["title"], font_title, W - 120, draw)
    if len(title_lines) > 3:
        title_lines = title_lines[:3]
        title_lines[-1] = title_lines[-1][:-1] + "..."

    title_y = card_y + 28
    for line in title_lines:
        draw.text((60, title_y), line, font=font_title, fill=hex_to_rgb(PRIMARY))
        title_y += 65

    # ── 기관명 ──
    font_inst = get_font(FONT_REGULAR, 27)
    inst_y = title_y + 6
    draw.text((60, inst_y), course_data["institution"],
              font=font_inst, fill=(100, 100, 100))

    # ── 구분선 ──
    line_y = inst_y + 48
    draw.line((60, line_y, W - 60, line_y), fill=(220, 220, 220), width=2)

    # ── 정보 항목 ──
    font_label = get_font(FONT_BOLD, 25)
    font_value = get_font(FONT_REGULAR, 25)

    info_items = []
    if course_data.get("period"):
        info_items.append(("배움 기간", course_data["period"]))
    if course_data.get("capacity"):
        info_items.append(("모집 인원", course_data["capacity"]))

    item_y = line_y + 14
    for label, value in info_items:
        draw.text((60, item_y), label, font=font_label, fill=hex_to_rgb(PRIMARY))
        draw.text((220, item_y), value, font=font_value, fill=(60, 60, 60))
        item_y += 42

    # ── 비용 강조 영역 ──
    self_cost = course_data.get("selfCost", "")
    course_cost = course_data.get("courseCost", "")
    if self_cost or course_cost:
        cost_y = item_y + 6
        cost_box_h = 110
        draw_rounded_rect(draw,
                           (50, cost_y, W - 50, cost_y + cost_box_h),
                           radius=12, fill=(235, 245, 251))
        font_cost_label = get_font(FONT_BOLD, 25)
        font_cost_prefix = get_font(FONT_BOLD, 27)
        font_cost_big = get_font(FONT_BLACK, 40)
        font_cost_small = get_font(FONT_REGULAR, 19)

        draw.text((72, cost_y + 10), "자부담금",
                  font=font_cost_label, fill=hex_to_rgb(PRIMARY))
        if self_cost:
            prefix_text = "단,"
            cost_row_y = cost_y + 55
            draw.text((72, cost_row_y), prefix_text,
                      font=font_cost_prefix, fill=(44, 62, 80))
            prefix_bbox = draw.textbbox((0, 0), prefix_text, font=font_cost_prefix)
            prefix_w = prefix_bbox[2] - prefix_bbox[0]

            draw.text((72 + prefix_w + 8, cost_row_y - 4), self_cost,
                      font=font_cost_big, fill=hex_to_rgb(ACCENT))

            if course_cost:
                cost_bbox = draw.textbbox((0, 0), self_cost, font=font_cost_big)
                cost_w = cost_bbox[2] - cost_bbox[0]
                small_x = 72 + prefix_w + 8 + cost_w + 10
                draw.text((small_x, cost_row_y + 8),
                          f"(수강비 {course_cost})",
                          font=font_cost_small, fill=(136, 136, 136))
        elif course_cost:
            draw.text((72, cost_y + 55), course_cost,
                      font=font_cost_big, fill=hex_to_rgb(ACCENT))
        item_y = cost_y + cost_box_h + 6

    # ── 혜택 하이라이트 ──
    benefit_y = item_y + 6
    benefit_box_h = 72
    draw_rounded_rect(draw,
                       (50, benefit_y, W - 50, benefit_y + benefit_box_h),
                       radius=12, fill=(255, 248, 230))

    font_benefit_title = get_font(FONT_BOLD, 25)
    font_benefit = get_font(FONT_REGULAR, 22)

    draw.text((72, benefit_y + 8), "이런 혜택이!",
              font=font_benefit_title, fill=hex_to_rgb(ACCENT))
    benefits = course_data.get("benefits", "") or get_benefits_text(course_data)
    draw.text((72, benefit_y + 40), benefits,
              font=font_benefit, fill=(60, 60, 60))

    # ── 하단 ※ 주석 ──
    footer_y = H - 75
    font_footnote = get_font(FONT_REGULAR, 19)
    footnote = get_benefits_footnote()
    draw.text((50, footer_y - 26), footnote,
              font=font_footnote, fill=(136, 136, 136))

    # ── 하단 바 ──
    footer_bar_bottom = H - 30
    footer_bar_h = footer_bar_bottom - footer_y
    draw.rectangle((30, footer_y, W - 30, footer_bar_bottom), fill=hex_to_rgb(PRIMARY))
    font_footer = get_font(FONT_REGULAR, 21)
    font_cta = get_font(FONT_BOLD, 23)

    # 기관명 수직 중앙
    org_text = "제주지역인적자원개발위원회"
    org_bbox = draw.textbbox((0, 0), org_text, font=font_footer)
    org_h = org_bbox[3] - org_bbox[1]
    org_y = footer_y + (footer_bar_h - org_h) // 2
    draw.text((55, org_y), org_text, font=font_footer, fill=(174, 214, 241))

    # CTA 수직 중앙
    cta_text = "신청은 hrd.go.kr"
    cta_bbox = draw.textbbox((0, 0), cta_text, font=font_cta)
    cta_w = cta_bbox[2] - cta_bbox[0]
    cta_h = cta_bbox[3] - cta_bbox[1]
    cta_y = footer_y + (footer_bar_h - cta_h) // 2
    draw.text((W - cta_w - 55, cta_y), cta_text,
              font=font_cta, fill=hex_to_rgb(ACCENT_BRIGHT))

    # ── Pexels 크레딧 ──
    if credit:
        font_credit = get_font(FONT_REGULAR, 17)
        credit_text = f"Photo: {credit['photographer']} / Pexels"
        draw.text((50, card_y - 25), credit_text,
                  font=font_credit, fill=(200, 200, 200, 180))

    img.save(output_path, quality=95)
    return output_path


def generate_detail_v2(course_data, bg_image, output_path):
    """상세 슬라이드 v2: 배경 이미지 상단 + 하단 콘텐츠"""
    W, H = 1080, 1080

    header_h = 280
    bg = bg_image.copy().resize((W, int(W * bg_image.size[1] / bg_image.size[0])), Image.LANCZOS)

    if bg.size[1] >= header_h:
        bg_crop = bg.crop((0, 0, W, header_h))
    else:
        bg_crop = bg.resize((W, header_h), Image.LANCZOS)

    bg_crop = apply_dark_overlay(bg_crop, opacity=150)

    img = Image.new('RGB', (W, H), (248, 249, 250))
    img.paste(bg_crop, (0, 0))

    draw = ImageDraw.Draw(img)

    draw.rectangle((0, 0, W, 5), fill=hex_to_rgb(ACCENT))

    font_header = get_font(FONT_BOLD, 39)
    draw.text((60, 38), "이런 걸 배워요", font=font_header, fill=(255, 255, 255))

    font_subtitle = get_font(FONT_REGULAR, 27)
    title_short = course_data["title"][:40] + ("..." if len(course_data["title"]) > 40 else "")
    draw.text((60, 88), title_short, font=font_subtitle, fill=(200, 210, 220))

    # ── 커리큘럼 카드 영역 ──
    font_item_title = get_font(FONT_BOLD, 29)
    font_item_desc = get_font(FONT_REGULAR, 25)

    curriculum = course_data.get("curriculum", [])
    y = header_h + 22

    for i, item in enumerate(curriculum[:5]):
        card_h = 115
        draw_rounded_rect(draw, (40, y, W - 40, y + card_h),
                           radius=12, fill=(255, 255, 255))

        draw_rounded_rect(draw, (40, y, 48, y + card_h), radius=0,
                           fill=hex_to_rgb(ACCENT))

        # 번호 원
        cx, cy = 80, y + 30
        cr = 20
        draw_rounded_rect(draw, (cx - cr, cy - cr, cx + cr, cy + cr),
                           radius=cr, fill=hex_to_rgb(PRIMARY))
        font_num = get_font(FONT_BOLD, 23)
        num_bbox = draw.textbbox((0, 0), str(i + 1), font=font_num)
        num_w = num_bbox[2] - num_bbox[0]
        draw.text((cx - num_w // 2, cy - 13), str(i + 1),
                  font=font_num, fill=(255, 255, 255))

        if isinstance(item, dict):
            title_text = item.get("title", "")
            desc_text = item.get("desc", "")
        else:
            title_text = str(item)
            desc_text = ""

        draw.text((115, y + 14), title_text,
                  font=font_item_title, fill=(44, 62, 80))
        if desc_text:
            desc_lines = wrap_text(desc_text, font_item_desc, W - 190, draw)
            for j, dl in enumerate(desc_lines[:2]):
                draw.text((115, y + 52 + j * 30), dl,
                          font=font_item_desc, fill=(127, 140, 141))

        y += card_h + 12

    # ── 수료 후 박스 ──
    outcome_y = max(y + 10, H - 175)
    draw_rounded_rect(draw, (40, outcome_y, W - 40, outcome_y + 108),
                       radius=12, fill=hex_to_rgb(PRIMARY))

    font_outcome_title = get_font(FONT_BOLD, 27)
    font_outcome = get_font(FONT_REGULAR, 25)

    draw.text((65, outcome_y + 14), "배우고 나면",
              font=font_outcome_title, fill=hex_to_rgb(ACCENT_BRIGHT))
    outcome = course_data.get("outcome", "관련 분야 취업 연계")
    outcome_lines = wrap_text(outcome, font_outcome, W - 150, draw)
    for i, line in enumerate(outcome_lines[:2]):
        draw.text((65, outcome_y + 50 + i * 32), line,
                  font=font_outcome, fill=(255, 255, 255))

    # ── 하단 ※ 주석 ──
    footer_y = H - 60
    font_footnote = get_font(FONT_REGULAR, 19)
    footnote = get_benefits_footnote()
    draw.text((50, footer_y - 25), footnote,
              font=font_footnote, fill=(136, 136, 136))

    # ── 하단 바 ──
    footer_bar_h = H - footer_y
    draw.rectangle((0, footer_y, W, H), fill=hex_to_rgb(PRIMARY))
    font_footer = get_font(FONT_REGULAR, 21)
    ft_text = "제주지역인적자원개발위원회  |  신청: hrd.go.kr"
    ft_bbox = draw.textbbox((0, 0), ft_text, font=font_footer)
    ft_h = ft_bbox[3] - ft_bbox[1]
    ft_y = footer_y + (footer_bar_h - ft_h) // 2
    draw.text((50, ft_y), ft_text,
              font=font_footer, fill=(174, 214, 241))

    img.save(output_path, quality=95)
    return output_path


def generate_cardnews_v2(course_data, output_dir="output"):
    """이미지 포함 카드뉴스 생성 (v2)"""
    from fetch_images import get_course_image
    from generate_cardnews import generate_slide_howto

    os.makedirs(output_dir, exist_ok=True)
    safe_name = course_data["title"][:30].replace(" ", "_").replace("/", "_")

    bg_image, credit = get_course_image(course_data["title"])

    paths = []

    p1 = os.path.join(output_dir, f"{safe_name}_v2_1_cover.png")
    generate_cover_v2(course_data, bg_image, credit, p1)
    paths.append(p1)
    print(f"  [v2] 커버 생성: {p1}")

    if course_data.get("curriculum"):
        p2 = os.path.join(output_dir, f"{safe_name}_v2_2_detail.png")
        generate_detail_v2(course_data, bg_image, p2)
        paths.append(p2)
        print(f"  [v2] 상세 생성: {p2}")

    p3 = os.path.join(output_dir, f"{safe_name}_v2_3_howto.png")
    generate_slide_howto(course_data, p3)
    paths.append(p3)
    print(f"  [v2] 신청방법 생성: {p3}")

    return paths
