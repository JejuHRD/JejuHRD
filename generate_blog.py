"""
블로그 포스트 자동 생성기 - 제주지역인적자원개발위원회 특화훈련 홍보용
네이버 스마트에디터 복사-붙여넣기 최적화 텍스트를 생성합니다.

v3 개선사항 (스마트에디터 최적화):
- 네이버 스마트에디터 ONE에 바로 붙여넣기 가능한 텍스트 생성
- [소제목], [구분선], [이미지] 등 에디터 작업 가이드 태그 포함
- 테이블 대신 줄바꿈 기반 정보 나열 (에디터 호환성 확보)
- 마크다운/HTML 출력 제거 → 단일 .txt 파일로 통합
- 상단에 포스팅 작업 가이드 포함
- 인스타그램 캡션 + 해시태그 동시 생성
- 릴스 대본 자동 생성
- 게시 타이밍 가이드 출력
"""

import os
import re
from datetime import datetime
from benefits_helper import (
    is_long_course,
    get_benefits_detail_lines,
    get_cost_info_text,
    parse_course_hours,
)
from seo_helper import (
    generate_seo_title,
    generate_empathy_intro,
    generate_blog_hashtags,
    generate_instagram_caption,
    generate_instagram_hashtags,
    generate_reels_script,
    generate_posting_guide,
    extract_seo_keywords,
    detect_course_field,
)


def generate_blog_post(course_data, output_dir="output"):
    """
    과정 데이터를 받아 네이버 스마트에디터용 텍스트를 생성합니다.
    SEO 최적화 + 인스타그램 캡션 + 릴스 대본 + 게시 가이드를 함께 출력합니다.

    Returns:
        (blog_txt_path, None) - HTML은 더 이상 생성하지 않으므로 None 반환
    """
    os.makedirs(output_dir, exist_ok=True)

    title = course_data["title"]
    institution = course_data.get("institution", "")
    period = course_data.get("period", "")
    time_info = course_data.get("time", "")
    capacity = course_data.get("capacity", "")
    target = course_data.get("target", "내일배움카드 있으면 누구나")
    curriculum = course_data.get("curriculum", [])
    outcome = course_data.get("outcome", "")
    contact = course_data.get("contact", "")
    hrd_url = course_data.get("hrd_url", "https://www.hrd.go.kr")

    # ── 혜택 문구 (과정 시간 기반 자동 결정) ──
    benefit_lines = get_benefits_detail_lines(course_data)
    benefit_text = "\n".join(line.replace("- ", "✔ ") for line in benefit_lines)
    cost_info = get_cost_info_text(course_data)
    hours = parse_course_hours(course_data)
    long = is_long_course(course_data)

    # ── SEO 최적화 ──
    blog_title = generate_seo_title(course_data)
    empathy_intro = generate_empathy_intro(course_data)
    seo_keywords = extract_seo_keywords(course_data)
    field = detect_course_field(title)
    hashtags_raw = generate_blog_hashtags(course_data)
    year = datetime.now().year
    today = datetime.now().strftime("%Y년 %m월 %d일")

    # 해시태그에서 마크다운 볼드(**) 제거
    hashtags = hashtags_raw.replace("**", "")

    # ── 커리큘럼 텍스트 ──
    curriculum_text = ""
    if curriculum:
        curriculum_text = "\n[소제목] 이런 걸 배워요\n\n"
        for i, item in enumerate(curriculum, 1):
            if isinstance(item, dict):
                curriculum_text += f"{i}. {item.get('title', '')}\n"
                if item.get("desc"):
                    curriculum_text += f"   → {item['desc']}\n"
            else:
                curriculum_text += f"{i}. {item}\n"
            curriculum_text += "\n"

    # ── 훈련장려금 관련 문구 (140시간 이상일 때만) ──
    if long is True:
        allowance_step3 = "열심히 다니면 (출석 80% 이상) 매달 훈련장려금이 들어와요."
    else:
        allowance_step3 = "자부담 10%로 부담 없이 새로운 기술을 배울 수 있어요."

    # ── SEO 키워드 자연 삽입 섹션 ──
    seo_section = _build_seo_section(course_data, field, year)

    # ── 누구에게 추천하나요 섹션 ──
    recommend_section = _build_recommend_section(field, long)

    # ── 공감형 도입부에서 마크다운 볼드(**) 제거 ──
    empathy_clean = empathy_intro.replace("**", "")

    # ════════════════════════════════════════
    #  스마트에디터용 본문 텍스트 생성
    # ════════════════════════════════════════

    post_content = f"""[제목] {blog_title}

[이미지 삽입] 카드뉴스 커버 이미지 (1번)

{empathy_clean}

[구분선]

[소제목] 한눈에 보기

📌 과정명: {title}
🏫 어디서 배우나요: {institution}
📅 배움 기간: {period}
⏰ 총 시간: {time_info}
👥 모집 인원: {capacity}
🎯 누가 들을 수 있나요: {target}

[구분선]

[소제목] 이런 혜택이 있어요

{benefit_text}

💰 비용이 궁금하시죠?
{cost_info}

[이미지 삽입] 카드뉴스 상세 이미지 (2번)

{seo_section}

[구분선]
{curriculum_text}
[구분선]

{recommend_section}

[구분선]

[소제목] 배우고 나면

{outcome}

[구분선]

[소제목] 이렇게 신청하세요

STEP 1. 내일배움카드 만들기
아직 카드가 없다면, 고용24(hrd.go.kr)에서 온라인으로 신청하거나
가까운 고용센터에 방문하면 돼요. 발급까지 약 1~2주 걸리니 서둘러 신청하세요!

💡 꿀팁: 고용24 앱을 설치하면 스마트폰으로도 간편하게 신청할 수 있어요.

STEP 2. 원하는 과정 찾아서 신청하기
고용24에서 과정명을 검색하거나, 아래 링크에서 바로 확인하세요.

[링크] 고용24에서 이 과정 찾아보기: {hrd_url}

💡 꿀팁: "{title}" 전체를 검색하기 어려우면, 핵심 키워드 + "제주"로 검색해보세요.

STEP 3. 배우면서 혜택도 받기
{allowance_step3}

[이미지 삽입] 카드뉴스 신청방법 이미지 (3번)

[구분선]

[소제목] 궁금하신 점은

{contact}

편하게 전화 주시면 친절하게 안내해드려요!

[구분선]

이 과정은 {year}년 제주지역인적자원개발위원회에서 안내하는 특화훈련입니다.
제주 지역의 산업 수요에 맞춰 기획된 과정이니, 제주에서 새로운 커리어를 준비하시는 분들에게 특히 추천드려요.

최종 수정일: {today}

[구분선]

{hashtags}
"""

    # ── 작업 가이드 (파일 상단에 추가) ──
    work_guide = _build_work_guide(blog_title)

    final_content = work_guide + "\n" + post_content

    # ── 파일 저장 ──
    safe_name = title[:30].replace(" ", "_").replace("/", "_")
    filepath = os.path.join(output_dir, f"{safe_name}_blog_naver.txt")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_content)

    print(f"  📝 네이버 블로그용 텍스트 생성: {filepath}")

    # ── 인스타그램 캡션 생성 ──
    caption_filepath = os.path.join(output_dir, f"{safe_name}_instagram_caption.txt")
    caption = generate_instagram_caption(course_data)
    with open(caption_filepath, "w", encoding="utf-8") as f:
        f.write(caption)

    print(f"  📸 인스타그램 캡션 생성: {caption_filepath}")

    # ── 릴스 대본 생성 ──
    reels_filepath = os.path.join(output_dir, f"{safe_name}_reels_script.txt")
    reels_script = generate_reels_script(course_data)
    with open(reels_filepath, "w", encoding="utf-8") as f:
        f.write(reels_script)

    print(f"  🎬 릴스 대본 생성: {reels_filepath}")

    # ── 게시 가이드 생성 ──
    guide_filepath = os.path.join(output_dir, f"{safe_name}_posting_guide.txt")
    guide = generate_posting_guide(course_data)
    with open(guide_filepath, "w", encoding="utf-8") as f:
        f.write(guide)

    print(f"  📋 게시 가이드 생성: {guide_filepath}")

    # HTML은 더 이상 생성하지 않음 (None 반환으로 pipeline 호환성 유지)
    return filepath, None


def _build_work_guide(blog_title):
    """
    파일 상단에 포함할 스마트에디터 작업 가이드를 생성합니다.
    실제 본문에 포함하지 않고, 작업자가 참고하는 용도입니다.
    """
    return f"""{'=' * 60}
📋 네이버 블로그 포스팅 작업 가이드
{'=' * 60}

아래 본문을 네이버 스마트에디터에 붙여넣은 뒤,
태그 표시를 보고 서식을 적용해주세요.

✅ 작업 순서:
  1. 아래 [===== 여기부터 본문 =====] 이후의 텍스트를 전체 복사
  2. 네이버 블로그 > 글쓰기 > 스마트에디터에 붙여넣기
  3. 아래 태그들을 찾아서 서식 적용:

  [제목]       → 삭제하고, 블로그 제목란에 입력
  [소제목]     → 해당 텍스트를 드래그 → 에디터 "제목2" 적용
  [구분선]     → 삭제 후 에디터 구분선(―) 삽입
  [이미지 삽입] → 삭제 후 해당 위치에 카드뉴스 이미지 업로드
  [링크]       → 텍스트에 하이퍼링크 걸기
  💡, ✔, 📌 등 → 이모지는 그대로 유지 (에디터에서 정상 표시됨)

  4. 이미지 최소 3장 삽입 (네이버 검색 노출에 유리)
  5. 미리보기로 확인 후 발행

{'=' * 60}
===== 여기부터 본문 =====
{'=' * 60}
"""


def _build_seo_section(course_data, field, year):
    """
    SEO 키워드를 자연스럽게 녹인 추가 섹션을 생성합니다.
    네이버 검색에 잡히는 키워드를 본문에 포함시킵니다.
    """
    sections = {
        "AI": f"""
[소제목] 왜 지금 AI를 배워야 할까요?

{year}년 현재, AI는 더 이상 먼 미래의 이야기가 아닙니다. 채용 공고에서도 "AI 활용 능력"을 요구하는 곳이 빠르게 늘고 있어요. 제주에서도 관광, 서비스, 미디어 등 다양한 산업에서 AI를 활용하는 인재를 필요로 하고 있습니다.

이 과정은 단순히 AI 도구 사용법만 알려주는 게 아니라, 기획 → 생성 → 검증 → 최적화까지 실무에서 바로 쓸 수 있는 업무 흐름을 배웁니다. 제주 지역에서 국비지원으로 AI 교육을 받을 수 있는 기회는 많지 않으니, 이번 과정을 꼭 확인해보세요.
""",
        "영상": f"""
[소제목] 왜 지금 영상 제작을 배워야 할까요?

유튜브, 릴스, 틱톡... {year}년에도 영상 콘텐츠의 영향력은 계속 커지고 있어요. 개인 크리에이터뿐 아니라, 기업 홍보 담당자, 프리랜서, 소상공인까지 영상 제작 능력이 필수가 되고 있습니다.

이 과정에서는 촬영 기초부터 AI를 활용한 영상 생성, 전문 편집까지 체계적으로 배울 수 있어요. 제주에서 국비지원으로 영상 편집 교육을 받을 수 있는 기회, 놓치지 마세요.
""",
        "디자인": f"""
[소제목] 왜 지금 디자인을 배워야 할까요?

디지털 전환이 가속화되면서, 디자인 역량은 디자이너만의 것이 아니게 되었어요. 마케터, 기획자, 스타트업 창업자까지 UI/UX와 디지털 디자인 기초를 알아야 하는 시대입니다.

이 과정은 피그마(Figma) 같은 현업 필수 도구부터 AI를 활용한 디자인 워크플로우까지 다루고 있어서, {year}년 취업 시장에서 경쟁력을 갖추는 데 도움이 될 거예요.
""",
        "출판": f"""
[소제목] 왜 지금 출판 제작을 배워야 할까요?

전자책, 독립출판, POD(주문형 출판)... 출판의 문턱이 낮아지고 있습니다. AI 도구를 활용하면 삽화 생성, 조판, 전자책 변환까지 한 사람이 해낼 수 있는 시대가 됐어요.

이 과정에서는 인디자인을 중심으로 기획부터 제작, 유통까지 출판 전 과정을 배울 수 있습니다. 제주에서 출판 제작 교육을 국비지원으로 받을 수 있는 흔치 않은 기회예요.
""",
    }

    return sections.get(field, f"""
[소제목] 왜 이 과정을 추천할까요?

{year}년, 기술 변화가 빠르게 진행되면서 새로운 역량을 갖춘 인재에 대한 수요가 높아지고 있어요. 제주에서도 관련 분야의 전문 인력이 필요한 상황이고, 이 과정은 제주 지역의 산업 수요에 맞춰 기획되었습니다.

내일배움카드로 자부담 10%만 내고 체계적으로 배울 수 있으니, 새로운 도전을 준비하고 계시다면 이 기회를 활용해보세요.
""")


def _build_recommend_section(field, long):
    """
    '이런 분에게 추천해요' 섹션을 생성합니다.
    체류 시간 증가 + 독자 공감 유도.
    """
    field_recommends = {
        "AI": [
            "AI에 관심은 있지만 어디서부터 시작해야 할지 모르겠는 분",
            "현재 직무에 AI를 접목해서 업무 효율을 높이고 싶은 분",
            "AI 관련 직종으로 이직이나 전직을 준비하시는 분",
            "프리랜서로 AI 활용 능력을 포트폴리오에 추가하고 싶은 분",
        ],
        "영상": [
            "유튜브나 인스타 릴스를 시작하고 싶지만 편집이 어려운 분",
            "회사에서 영상 콘텐츠 제작 업무를 맡게 된 분",
            "영상 제작 프리랜서로 활동하고 싶은 분",
            "개인 브랜딩을 위해 영상 스킬이 필요한 분",
        ],
        "디자인": [
            "비전공자지만 디자인 역량을 키우고 싶은 분",
            "UI/UX 디자이너로 커리어를 시작하고 싶은 분",
            "기획이나 마케팅 업무에 디자인 감각을 더하고 싶은 분",
            "포트폴리오를 만들어서 취업 경쟁력을 높이고 싶은 분",
        ],
        "출판": [
            "내 책을 직접 만들어보고 싶은 분",
            "출판 편집 디자이너로 취업을 준비하시는 분",
            "전자책이나 독립출판에 관심이 있는 분",
            "인디자인 등 편집 도구를 배우고 싶은 분",
        ],
    }

    recommends = field_recommends.get(field, [
        "새로운 분야에 도전하고 싶은 분",
        "취업이나 이직을 준비하시는 분",
        "현재 직무 역량을 업그레이드하고 싶은 분",
        "부담 없이 새로운 기술을 배워보고 싶은 분",
    ])

    section = "[소제목] 이런 분에게 추천해요\n\n"
    for r in recommends:
        section += f"✅ {r}\n"

    if long is True:
        section += "\n140시간 이상 과정이라 훈련장려금(월 최대 20만원)도 받을 수 있어서, 배우면서 생활비 부담도 줄일 수 있어요."
    else:
        section += "\n단기 과정이라 빠르게 핵심만 배울 수 있어요. 바쁜 분들에게 딱 맞는 구성이에요."

    return section
