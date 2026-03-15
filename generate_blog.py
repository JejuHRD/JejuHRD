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
    get_course_type,
    get_total_hours,
    get_benefits_detail_lines,
    get_cost_info_text,
)
from seo_helper import (
    generate_seo_title,
    generate_empathy_intro,
    generate_blog_hashtags,
    generate_instagram_caption,
    generate_instagram_hashtags,
    generate_reels_package,
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
    # outcome이 비어있으면 훈련목표를 활용
    if not outcome:
        training_goal_for_outcome = course_data.get("trainingGoal", "")
        if training_goal_for_outcome:
            outcome = (
                f"이 과정을 수료하면 다음과 같은 역량을 갖출 수 있어요.\n\n"
                f"> {training_goal_for_outcome}"
            )
    contact = course_data.get("contact", "")
    hrd_url = course_data.get("hrd_url", "https://www.hrd.go.kr")

    # ── 혜택 문구 (과정 시간 기반 자동 결정) ──
    benefit_lines = get_benefits_detail_lines(course_data)
    benefit_text = "\n".join(line.replace("- ", "✔ ") for line in benefit_lines)
    cost_info = get_cost_info_text(course_data)
    hours = get_total_hours(course_data)
    ctype = get_course_type(course_data)

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

    # ── 훈련장려금 관련 문구 (140시간 이상일 때만) ──
    if ctype in ("general", "long"):
        allowance_step3 = "열심히 다니면 (출석 80% 이상) 매달 훈련장려금이 들어와요."
    else:
        allowance_step3 = "자부담 10%로 부담 없이 새로운 기술을 배울 수 있어요."

    # ── SEO 키워드 자연 삽입 섹션 ──
    seo_section = _build_seo_section(course_data, field, year)

    # ── 누구에게 추천하나요 섹션 ──
    recommend_section = _build_recommend_section(field, ctype)

    # ── 공감형 도입부에서 마크다운 볼드(**) 제거 ──
    empathy_clean = empathy_intro.replace("**", "")

    # ════════════════════════════════════════
    #  스마트에디터용 본문 텍스트 생성
    # ════════════════════════════════════════

    post_content = f"""[제목] {blog_title}

[이미지 삽입] 카드뉴스 커버 이미지 (1번)

{empathy_clean}

[구분선]

[소제목] 목차

1. 한눈에 보기
2. 이런 혜택이 있어요
3. {_get_seo_section_title(field, year)}
4. 이런 분에게 추천해요
5. 어떤 것들을 배우나요
6. 이렇게 신청하세요
7. 궁금하신 점은

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

{recommend_section}

[구분선]

[소제목] 어떤 것들을 배우나요

{outcome if outcome else "상세 내용은 고용24에서 확인해주세요."}

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

{institution + chr(10) if institution and institution not in contact else ''}{contact}
{('📍 ' + course_data.get('address', '')) if course_data.get('address') else ''}

편하게 전화 주시면 친절하게 안내해드려요!

[구분선]

[내부링크 영역]
👉 이 글이 도움이 되셨다면, 다른 훈련 과정 안내도 확인해보세요!
(여기에 블로그 내 관련 글 2~3개의 제목과 링크를 추가하세요)

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

    # ── 릴스 Grok 영상 가이드 생성 ──
    reels_result = generate_reels_package(course_data)

    if isinstance(reels_result, str):
        # "[SKIP] ..." — 이미 시작된 과정
        reels_filepath = os.path.join(output_dir, f"{safe_name}_reels_grok.txt")
        with open(reels_filepath, "w", encoding="utf-8") as f:
            f.write(reels_result)
        print(f"  ⏭️  릴스 스킵: {reels_result[:60]}")
    else:
        grok_path = os.path.join(output_dir, f"{safe_name}_reels_grok.txt")
        with open(grok_path, "w", encoding="utf-8") as f:
            f.write(reels_result["grok"])
        print(f"  🎬 Grok 영상 가이드 생성: {grok_path}")

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

  [제목]         → 삭제하고, 블로그 제목란에 입력
  [소제목]       → 해당 텍스트를 드래그 → 에디터 "제목2" 적용
  [구분선]       → 삭제 후 에디터 구분선(―) 삽입
  [이미지 삽입]   → 삭제 후 해당 위치에 카드뉴스 이미지 업로드
  [링크]         → 텍스트에 하이퍼링크 걸기
  [내부링크 영역] → 이전에 발행한 관련 과정 글 2~3개의 링크를 추가
  💡, ✔, 📌 등 → 이모지는 그대로 유지 (에디터에서 정상 표시됨)

  4. 이미지 최소 3장 삽입 (네이버 검색 노출에 유리)
  5. 미리보기로 확인 후 발행

📌 SEO 체크리스트 (검색 상위 노출을 위해 꼭 확인!):
  □ 제목이 25자 이내인지 확인
  □ 목차 섹션의 각 항목에 앵커링크(클릭 시 해당 위치로 이동)를 걸면 체류시간 ↑
  □ [내부링크 영역]에 기존 블로그 글 2~3개 링크 추가 (세션당 페이지뷰 증가)
  □ 본문이 1,500자 이상인지 확인 (정보성 글은 2,000자 이상 권장)
  □ 3~4줄마다 줄바꿈으로 가독성 확보
  □ 발행 후 1~2시간 뒤 whereispost.com에서 색인 여부 확인

{'=' * 60}
===== 여기부터 본문 =====
{'=' * 60}
"""


def _get_seo_section_title(field, year):
    """목차에 표시할 SEO 섹션 제목을 반환합니다."""
    titles = {
        "AI": f"왜 지금 AI를 배워야 할까요?",
        "영상": f"왜 지금 영상 제작을 배워야 할까요?",
        "디자인": f"왜 지금 디자인을 배워야 할까요?",
        "출판": f"왜 지금 출판 제작을 배워야 할까요?",
    }
    return titles.get(field, "왜 이 과정을 추천할까요?")


def _build_seo_section(course_data, field, year):
    """
    SEO 키워드를 자연스럽게 녹인 추가 섹션을 생성합니다.
    제주 특화 시장 트렌드 데이터를 활용하여 설득력과 체류시간을 높입니다.
    """
    sections = {
        "AI": f"""
[소제목] 왜 지금 AI를 배워야 할까요?

제주특별자치도는 'AI·디지털 대전환 로드맵'을 발표하고, {year}년 정보화사업에 918억 원(208개 사업)을 편성했어요. ETRI·네이버클라우드와 함께 제주 특화 AI를 공동 개발하고 있고, 소상공인 디지털 전환 패키지, 제주농업 디지털 전환 플랫폼 등 AI 관련 투자가 쏟아지고 있습니다.

이미 제주관광공사는 AI 챗봇으로 24시간 종합관광 안내를 운영하고, 54종 빅데이터 기반 관광 혼잡도 분석 서비스로 UNWTO 스마트관광 우수사례에 선정될 만큼 앞서가고 있어요. 관광·서비스업이 주력인 제주에서 AI를 활용할 줄 아는 인재에 대한 수요는 계속 늘어날 수밖에 없습니다.

전국적으로 AI 개발자 부족률이 57.6%에 달하고, 기업 69%가 채용 시 AI 역량을 고려한다는 조사 결과가 있어요. 정부도 5년간 100만 명 AI 교육을 목표로 대규모 투자를 진행하고 있고요. 이 과정은 단순 도구 사용법이 아닌, 기획부터 실무 적용까지 체계적으로 배울 수 있어요. 제주에서 국비지원으로 AI를 배울 수 있는 기회는 많지 않으니 꼭 확인해보세요.
""",
        "영상": f"""
[소제목] 왜 지금 영상 제작을 배워야 할까요?

한국의 숏폼 콘텐츠 이용률이 70.7%까지 치솟았어요. 전년 대비 16.4%p나 급증한 수치이고, 스마트폰으로 주 5일 이상 숏폼을 소비하는 비율도 41.8%로 1위입니다. 크리에이터 산업 규모는 5.5조 원을 넘어섰고, 광고·마케팅·커머스 분야 사업체는 전년 대비 197.7%나 폭증했어요.

그런데 크리에이터 지역 분포를 보면, 제주는 강원과 합산해도 겨우 1.7%에 불과합니다. 수도권에 73% 이상이 집중되어 있는 거죠. 이건 역으로 제주에서 영상 제작을 배우면 경쟁이 적고 기회가 많다는 뜻이에요.

제주는 콘텐츠진흥원이 121억 원을 투자하고, 98억 원 규모 콘텐츠기업지원센터를 추진 중이에요. 전국 최대 드론특별자유화구역(1,283km²)이 있어서 드론 영상 촬영·실습 환경도 전국 최고 수준이고요. 관광 홍보영상, 소상공인 숏폼, 지역 브랜딩 콘텐츠 등 제주만의 영상 수요가 풍부합니다.
""",
        "디자인": f"""
[소제목] 왜 지금 디자인을 배워야 할까요?

글로벌 UI/UX 디자인 시장이 매년 32%씩 성장하고 있어요. {year}년 19.8억 달러에서 2031년 116.6억 달러까지 커질 전망입니다. 피그마(Figma)가 시장 점유율 40%를 차지하고 Fortune 500 기업 95%가 사용할 만큼 디자인 도구의 표준이 되었어요.

제주에서는 '로컬 힙' 트렌드와 함께 카페·숙박·특산품의 브랜딩 수요가 폭발적으로 늘고 있어요. 이니스프리, 삼다수, 오설록, 제주맥주 같은 성공 사례가 쌓이면서, 중소 사업자들도 체계적인 브랜딩에 관심을 갖게 된 거죠. 감귤·한라봉·녹차·오메기떡 같은 특산품의 프리미엄 패키지 디자인 수요도 증가하고 있고요.

하지만 제주 현지 디자인 업체는 대부분 5인 미만의 극소규모예요. 디자인 인력이 구조적으로 부족한 상황이라, 디자인을 배우면 제주에서 바로 일할 수 있는 기회가 많습니다. 이 과정에서는 피그마 같은 현업 필수 도구부터 실무 포트폴리오 완성까지 체계적으로 배울 수 있어요.
""",
        "출판": f"""
[소제목] 왜 지금 출판 제작을 배워야 할까요?

전자책, 독립출판, POD(주문형 출판)... 출판의 문턱이 낮아지고 있습니다. AI 도구를 활용하면 삽화 생성, 조판, 전자책 변환까지 한 사람이 해낼 수 있는 시대가 됐어요.

이 과정에서는 인디자인을 중심으로 기획부터 제작, 유통까지 출판 전 과정을 배울 수 있습니다. 제주에서 출판 제작 교육을 국비지원으로 받을 수 있는 흔치 않은 기회예요.

1인 출판, 브랜드 북, 사보 제작, 전자책 기획까지 다양한 분야에서 활용할 수 있는 실용적인 스킬을 배울 수 있습니다.
""",
    }

    return sections.get(field, f"""
[소제목] 왜 이 과정을 추천할까요?

{year}년, 제주도는 AI·디지털 대전환에 918억 원을 투자하고, 콘텐츠진흥원 121억 원, 소상공인 디지털 전환 패키지 등 역대급 투자를 진행하고 있어요. 기술 변화가 빠르게 진행되면서 새로운 역량을 갖춘 인재에 대한 수요가 높아지고 있습니다.

이 과정은 제주 지역의 산업 수요에 맞춰 기획되었고, 내일배움카드로 자부담 10%만 내고 체계적으로 배울 수 있어요. 새로운 도전을 준비하고 계시다면 이 기회를 활용해보세요.

이런 국비지원 과정은 제주 지역의 고용 상황과 산업 트렌드를 반영하여 매년 새롭게 기획됩니다. 올해 열리는 과정이 내년에도 열린다는 보장이 없으니, 관심이 있다면 지금 신청하는 것을 추천드려요.
""")


def _build_recommend_section(field, ctype):
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

    if ctype == "long":
        section += "\n350시간 이상 장기과정이라 훈련장려금 + 특별훈련수당(월 최대 40만원)도 받을 수 있어서, 배우면서 생활비 부담도 줄일 수 있어요."
    elif ctype == "general":
        section += "\n140시간 이상 과정이라 훈련장려금(월 최대 20만원)도 받을 수 있어서, 배우면서 생활비 부담도 줄일 수 있어요."
    else:
        section += "\n단기 과정이라 빠르게 핵심만 배울 수 있어요. 바쁜 분들에게 딱 맞는 구성이에요."

    return section
