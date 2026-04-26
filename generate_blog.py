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
    generate_posting_guide,
    extract_seo_keywords,
    detect_course_field,
    get_varied_section_title,
    get_varied_closing,
    estimate_char_count,
    get_keyword_density_report,
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
    field = detect_course_field(title, course_data.get("ncsCd"))
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

    # ── 구조 다양화를 위한 해시 (과정별 미세 변형) ──
    title_hash = abs(hash(title))
    sec_overview = get_varied_section_title("overview", title_hash)
    sec_benefits = get_varied_section_title("benefits", title_hash)
    sec_curriculum = get_varied_section_title("curriculum", title_hash + 2)
    sec_apply = get_varied_section_title("apply", title_hash + 3)
    closing = get_varied_closing(title_hash)

    # ════════════════════════════════════════
    #  스마트에디터용 본문 텍스트 생성 (SEO v4)
    # ════════════════════════════════════════

    post_content = f"""[제목] {blog_title}

[이미지 삽입] 직접 촬영한 대표 이미지 또는 카드뉴스 커버 (1번)

[✍️ 직접 작성] 아래 공감형 도입부를 참고하되, 반드시 본인의 말로 고쳐 쓰세요.
예시: "제주에서 살면서 늘 느끼는 건데, 수도권에 비해 교육 기회가 정말 적잖아요..."

{empathy_clean}

[구분선]

[소제목] {sec_overview}

📌 과정명: {title}
🏫 교육기관: {institution}
📅 훈련 기간: {period}
⏰ 총 훈련시간: {time_info}
👥 모집 인원: {capacity}
🎯 수강 자격: {target}

[이미지 삽입] 교육기관 외관/내부 또는 카드뉴스 상세 이미지 (2번)

[구분선]

[소제목] {sec_benefits}

{benefit_text}

💰 비용이 궁금하시죠?
{cost_info}

{seo_section}

[구분선]

{recommend_section}

[구분선]

[소제목] {sec_curriculum}

{outcome if outcome else "상세 커리큘럼은 고용24에서 확인해주세요."}

[✍️ 직접 작성] 커리큘럼에 대한 본인의 생각이나 기대를 1~2문장 추가하세요.
예시: "개인적으로 이 과정에서 가장 기대되는 건 ○○ 파트예요. 실무에서 바로 쓸 수 있거든요."

[구분선]

[소제목] {sec_apply}

STEP 1. 내일배움카드 만들기
아직 카드가 없다면, 고용24(hrd.go.kr)에서 온라인으로 신청하거나
가까운 고용센터에 방문하면 돼요. 발급까지 약 1~2주 걸리니 서둘러 신청하세요!

💡 고용24 앱을 설치하면 스마트폰으로도 간편하게 신청할 수 있어요.

STEP 2. 원하는 과정 찾아서 신청하기
고용24에서 과정명을 검색하거나, 아래 링크에서 바로 확인하세요.

[링크] 고용24에서 이 과정 확인하기: {hrd_url}

💡 "{title}" 전체를 검색하기 어려우면, 핵심 키워드 + "제주"로 검색해보세요.

STEP 3. 배우면서 혜택도 받기
{allowance_step3}

[이미지 삽입] 카드뉴스 신청방법 이미지 또는 고용24 화면 캡처 (3번)

[구분선]

{institution + chr(10) if institution and institution not in contact else ''}{contact}
{('📍 ' + course_data.get('address', '')) if course_data.get('address') else ''}

[✍️ 직접 작성] 교육기관까지 가는 방법, 주변 환경 등 제주 현지 정보를 추가하세요.
예시: "제주시에서 버스 ○○번 타면 ○○ 정류장에서 도보 5분이에요. 근처에 주차장도 있어요."

편하게 전화 주시면 친절하게 안내해드려요!

[구분선]

[내부링크 영역]
👉 이 글이 도움이 되셨다면, 다른 훈련 과정도 확인해보세요!
(여기에 블로그 내 관련 글 2~3개의 제목과 링크를 추가하세요)
→ 내부링크를 꼭 넣어야 체류시간이 늘어나고 검색 노출에 유리해요!

[구분선]

{closing}

이 과정은 {year}년 제주지역인적자원개발위원회에서 안내하는 특화훈련이에요.
제주 지역 산업 수요에 맞춰 기획되었으니, 제주에서 새로운 커리어를 준비하시는 분들께 추천드려요.

최종 수정일: {today}

{hashtags}
"""

    # ── 글자 수 측정 및 키워드 밀도 리포트 ──
    char_count = estimate_char_count(post_content)
    keyword_report = get_keyword_density_report(
        post_content, "제주",
        ["국비지원", "내일배움카드", field if field != "default" else "직업훈련"],
    )

    # ── 작업 가이드 (파일 상단에 추가) ──
    work_guide = _build_work_guide(blog_title, char_count, keyword_report)

    final_content = work_guide + "\n" + post_content

    # ── 파일 저장 ──
    safe_name = title[:30].translate(str.maketrans(" /", "__", ':"<>|*?\r\n'))
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

    # ── 게시 가이드 생성 ──
    guide_filepath = os.path.join(output_dir, f"{safe_name}_posting_guide.txt")
    guide = generate_posting_guide(course_data)
    with open(guide_filepath, "w", encoding="utf-8") as f:
        f.write(guide)

    print(f"  📋 게시 가이드 생성: {guide_filepath}")

    # HTML은 더 이상 생성하지 않음 (None 반환으로 pipeline 호환성 유지)
    return filepath, None


def _build_work_guide(blog_title, char_count=0, keyword_report=""):
    """
    파일 상단에 포함할 스마트에디터 작업 가이드 (SEO v4).
    인간화 편집 체크리스트, 키워드 밀도 리포트, 저품질 방지 가이드 포함.
    """
    return f"""{'=' * 60}
📋 네이버 블로그 포스팅 작업 가이드 (SEO v4)
{'=' * 60}

⚠️ 중요: AI 생성 콘텐츠를 그대로 게시하지 마세요!
아래 인간화 편집을 반드시 거쳐야 네이버 저품질을 피할 수 있습니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔑 인간화 편집 필수 체크리스트 (가장 중요!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  □ [✍️ 직접 작성] 영역을 반드시 본인 경험/관점으로 채우기
    → "저도 처음엔..." / "실제로 알아봤는데..." 등 개인적 도입
  □ 직접 촬영한 사진 6~13장 삽입 (교육기관 외관, 주변 환경, 교재 등)
    → AI 생성 이미지, 다른 블로그에서 가져온 이미지 절대 금지
    → 파일명에 키워드 포함 (예: jeju-gukbi-smartstore-2026.jpg)
  □ "~합니다/됩니다" → "~거든요/이에요/잖아요" 대화체로 3~5곳 변환
  □ 1분 이상 동영상 1개 삽입 (직접 촬영 권장)
  □ 제주 현지 정보 추가 (교육기관까지 교통편, 주변 식당, 주차 등)
  □ 개인적 견해/감상 2~3문장 추가
  □ 이모지 3~5개 자연스럽게 활용

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ SEO 체크리스트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  □ 제목 15~25자 (현재: {len(blog_title)}자) → {blog_title}
  □ 본문 공백 제외 2,000자 이상 (현재: 약 {char_count}자)
    → 2,000자 미만이면 제주 현지 정보, 경험담을 추가하세요
  □ 첫 200자 안에 핵심 키워드 포함 확인
  □ 소제목 3~5개 (현재 구조에 맞게 조정됨)
  □ [내부링크 영역]에 기존 글 2~3개 링크 반드시 추가 (체류시간 ↑)
  □ 3~4줄마다 줄바꿈으로 가독성 확보

📊 키워드 밀도 (본문 5~6회가 안전선):
{keyword_report if keyword_report else "  (생성 후 자동 측정됩니다)"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⛔ 저품질 방지 주의사항
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ✗ 동일 키워드 7회 이상 반복 금지
  ✗ 여러 포스팅에 같은 외부 링크 반복 삽입 금지
  ✗ 같은 이미지를 여러 포스팅에 재사용 금지
  ✗ 게시 후 제목/핵심 키워드 전면 수정 금지
  ✗ 매일 정확히 같은 시간에 게시 금지 (1~3시간 변동 필요)
  ✗ 하루 2개 이상 게시 시 최소 2~3시간 간격 유지

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 스마트에디터 작업 순서
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. [===== 여기부터 본문 =====] 이후의 텍스트를 전체 복사
  2. 네이버 블로그 > 글쓰기 > 스마트에디터에 붙여넣기
  3. 태그를 찾아서 서식 적용:
     [제목]          → 삭제하고, 블로그 제목란에 입력
     [소제목]        → 해당 텍스트 드래그 → 에디터 "제목2" 적용
     [구분선]        → 삭제 후 에디터 구분선(―) 삽입
     [이미지 삽입]    → 삭제 후 해당 위치에 직접 촬영한 이미지 업로드
     [링크]          → 텍스트에 하이퍼링크 걸기
     [내부링크 영역]  → 기존 블로그 글 2~3개의 제목과 링크 추가
     [✍️ 직접 작성]  → 반드시 본인의 말로 직접 작성
     💡, ✔, 📌 등  → 이모지는 그대로 유지
  4. 직접 촬영 이미지 6~13장 삽입
  5. 동영상 1개 삽입 (1분 이상)
  6. 미리보기로 확인 후 발행
  7. 발행 후 1~2시간 뒤 whereispost.com에서 색인 확인

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
        "이커머스": f"왜 지금 온라인 판매를 배워야 할까요?",
        "산업안전": f"왜 지금 산업안전을 배워야 할까요?",
    }
    return titles.get(field, "왜 이 과정을 추천할까요?")


def _build_seo_section(course_data, field, year):
    """
    SEO 키워드를 자연스럽게 녹인 추가 섹션을 생성합니다.
    
    v4 개선: field_research.json 캐시가 있으면 연구 기반 데이터 우선 사용.
    title 키워드로 서브필드(예: "드론영상")를 자동 매칭합니다.
    """
    title = course_data.get("title", "")
    
    # 1순위: field_research.json 캐시에서 연구 기반 섹션 로드
    try:
        from field_research_helper import get_seo_section
        cached_section = get_seo_section(field, year, title=title)
        if cached_section:
            section_title = _get_seo_section_title(field, year)
            return f"\n[소제목] {section_title}\n\n{cached_section}\n"
    except ImportError:
        pass

    # 2순위: 하드코딩 데이터
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
        "이커머스": f"""
[소제목] 왜 지금 온라인 판매를 배워야 할까요?

{year}년 한국 온라인 쇼핑 거래액이 242조 원을 돌파했어요. 특히 농축수산물 온라인 거래액이 12.7조 원으로 전년 대비 17.8%나 성장했습니다. 네이버 스마트스토어 셀러는 57만 명을 넘었고, 연 매출 1억 원 이상 판매자만 4.5만 명이에요.

제주는 이 흐름의 최대 수혜 지역이에요. 감귤·한라봉·천혜향·녹차·해산물 등 온라인 직거래가 활발하고, 이제주몰·삼다몰 같은 공식 플랫폼과 개별 농가 스마트스토어가 공존하는 다층 판매 구조가 이미 형성되어 있어요. 제주 레몬 농가는 생산량의 1/3을 온라인으로 판매해서 도매상 대비 수익률을 대폭 높인 사례도 있습니다.

제주도는 전국 최초로 크리에이터 전담부서를 신설하고 50억 원 규모의 크리에이터 전용펀드를 조성했어요. 라이브커머스 시장이 3.5조 원으로 성장하고, 숏폼 커머스가 대세가 된 지금, 온라인 판매 스킬은 제주에서 가장 실용적인 무기가 됩니다.
""",
        "산업안전": f"""
[소제목] 왜 지금 산업안전을 배워야 할까요?

중대재해처벌법이 {year}년 현재 5인 이상 전 사업장에 적용되고 있어요. 50인 미만 기업의 77%가 아직 법 준수를 완료하지 못한 상태라서, 안전관리 인력에 대한 수요는 당분간 계속 늘어날 수밖에 없습니다.

산업안전기사 접수자가 연 19.6만 명으로 국가기술자격 기사 등급 전체 1위를 기록했어요. 2018년 2.7만 명에서 7배 이상 폭증한 수치입니다. 안전관리자 채용 공고는 상시 400건 이상이 올라와 있고, 신입 연봉도 3,000만 원 이상으로 처우가 좋은 편이에요.

제주에서는 특히 건설·관광 인프라 투자가 지속되고 있고, 풍력발전 규모가 294MW에서 2,345MW로 확대될 예정이라 고소작업·해상작업 안전 전문인력 수요가 급증할 전망입니다. 제주도는 고용노동부 '지역 중대재해 예방 사각지대 해소사업'에 선정돼 국비 12억 원을 확보했어요. 제주 현지의 오프라인 실습형 안전교육은 매우 부족한 상황이라, 이 과정은 제주에서 안전관리를 배울 수 있는 소중한 기회예요.
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
        "이커머스": [
            "제주 특산품을 온라인으로 판매하고 싶은 농가·소상공인",
            "스마트스토어 창업을 준비하고 있는 분",
            "이미 가게를 운영하면서 온라인 판로를 확장하고 싶은 분",
            "라이브커머스·숏폼 커머스에 관심이 있는 분",
        ],
        "산업안전": [
            "산업안전기사·건설안전기사 자격증 취득을 준비하시는 분",
            "안전관리자로 취업·이직을 준비하시는 분",
            "중대재해처벌법 대응이 필요한 사업주·관리자",
            "건설·제조·서비스업에서 안전관리 업무를 맡게 된 분",
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
