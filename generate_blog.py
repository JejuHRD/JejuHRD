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
    get_overlap_report,
)

try:
    from seo_helper import get_display_label
except ImportError:
    # seo_helper.py가 구버전으로 남아 있어도 파이프라인이 멈추지 않도록 (라벨 없이 동작)
    def get_display_label(field, title):
        return field


def generate_blog_post(course_data, output_dir="output"):
    """
    과정 데이터를 받아 네이버 스마트에디터용 텍스트를 생성합니다.
    SEO 최적화 + 인스타그램 캡션 + 릴스 대본 + 게시 가이드를 함께 출력합니다.

    Returns:
        (blog_txt_path, None) - HTML은 더 이상 생성하지 않으므로 None 반환
    """
    os.makedirs(output_dir, exist_ok=True)

    # v6: '왜 지금' 버전 판정이 이번 호출의 output_dir을 보도록 (직전 블로그 파일 위치)
    try:
        from field_research_helper import set_output_dir
        set_output_dir(output_dir)
    except ImportError:
        pass

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

    # ── STEP3 문구 (중복 제거 v2: 금액은 '혜택' 섹션이 전담) ──
    if ctype in ("general", "long"):
        allowance_step3 = "출석률(80% 이상)만 지키면 훈련장려금이 매달 들어와요. 위에서 안내한 금액 그대로예요."
    else:
        allowance_step3 = "부담 없는 자부담으로 새로운 기술을 배울 수 있어요."

    # ── 표시 라벨 (v6): 같은 리서치 데이터라도 제목·소제목·추천 대상은 과정에 맞게 ──
    #   예) AI 유튜브 크리에이터 → 데이터는 '마케팅', 표시는 'AI유튜브'
    label = get_display_label(field, title)

    # ── '왜 배워야 할까요?' 섹션 (산업동향 + 훈련필요성) ──
    seo_section = _build_seo_section(course_data, field, year, label).strip()

    # ── 누구에게 추천하나요 섹션 ──
    recommend_section = _build_recommend_section(field, ctype, label).strip()

    # ── 공감형 도입부에서 마크다운 볼드(**) 제거 ──
    empathy_clean = empathy_intro.replace("**", "")

    # ── 구조 다양화를 위한 해시 (과정별 미세 변형) ──
    title_hash = abs(hash(title))
    sec_intro = get_varied_section_title("intro", title_hash + 1)
    sec_overview = get_varied_section_title("overview", title_hash)
    sec_benefits = get_varied_section_title("benefits", title_hash)
    sec_curriculum = get_varied_section_title("curriculum", title_hash + 2)
    sec_apply = get_varied_section_title("apply", title_hash + 3)
    closing = get_varied_closing(title_hash)

    # ── 무엇을 배울 수 있나요 섹션 (v5: 훈련목표 × 리서치 자체 해설) ──
    # sec_curriculum이 정의된 뒤에 호출해야 합니다.
    curriculum_section = _build_curriculum_section(course_data, field, sec_curriculum).strip()

    # ════════════════════════════════════════
    #  스마트에디터용 본문 텍스트 생성 (SEO v4)
    # ════════════════════════════════════════

    post_content = f"""[제목] {blog_title}

[이미지 삽입] 직접 촬영한 대표 이미지 또는 카드뉴스 커버 (1번)

[소제목] {sec_intro}

[✍️ 직접 작성] 아래 도입부를 참고하되, 반드시 본인의 말로 고쳐 쓰세요.
예시: "제주에서 살면서 늘 느끼는 건데, 수도권에 비해 교육 기회가 정말 적잖아요..."
→ 이 구간은 '공감과 문제의식'만 다룹니다. 산업 통계·수치는 다음 섹션에서 다루니 여기서 미리 쓰지 마세요.

{empathy_clean}

[구분선]

{seo_section}

[구분선]

[소제목] {sec_overview}

📌 과정명: {title}
🏫 교육기관: {institution}
📅 훈련 기간: {period}
⏰ 총 훈련시간: {time_info}
👥 모집 인원: {capacity}
🎯 수강 자격: {target}

[구분선]

[소제목] {sec_benefits}

{benefit_text}

💰 실제로 얼마를 내나요?
{cost_info}

[구분선]

{recommend_section}

[구분선]

{curriculum_section}

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
    # ── 도입부 ↔ SEO 섹션 중복 진단 (v5) ──
    overlap_report = get_overlap_report(empathy_clean, seo_section)

    # ── '왜 지금' 섹션 버전 (v6): 재생성 때마다 바뀌는 본문 버전을 작업 가이드에 기록 ──
    #   이 표식은 다음 생성 때 '직전 버전'을 판정하는 근거로도 쓰입니다 (지우지 마세요).
    variant_report = _build_variant_report(field, title)

    work_guide = _build_work_guide(blog_title, char_count, keyword_report, overlap_report,
                                   variant_report)

    final_content = work_guide + "\n" + post_content

    # ── 파일 저장 ──
    # NTFS 금지 문자(< > : " / \ | ? * 줄바꿈) 모두 제거
    # 다른 파일(pipeline.py, generate_cardnews.py, generate_cardnews_v2.py)과
    # 동일한 re.sub 방식으로 통일하여 같은 과정의 산출물 파일명 일치 보장
    # → 카드뉴스·블로그·인스타·가이드 모두 동일한 safe_name prefix 사용
    safe_name = re.sub(r'[<>:"/\\|?*\r\n\t]', "_", title[:30]).replace(" ", "_")
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


def _build_variant_report(field, title):
    """작업 가이드용 '왜 지금' 섹션 버전 안내 (v6).

    첫 줄의 표식(🔄 '왜 지금' 섹션 버전 i/n …)은 field_research_helper가
    다음 생성 때 직전 버전을 읽는 근거이므로 형식을 바꾸지 마세요.
    """
    try:
        from field_research_helper import get_variant_info
    except ImportError:
        return "  (버전 정보 없음 — field_research_helper 구버전)"
    info = get_variant_info(field, title)
    if not info:
        return "  (이 분야는 리서치 데이터가 없어 기본 문구를 사용합니다)"
    lines = [f"  {info['marker']}"]
    if info["total"] > 1:
        nxt = info["index"] % info["total"] + 1
        lines.append(f"  → 같은 과정이 다시 생성되면 버전 {nxt}/{info['total']}로 자동 교체돼요.")
        lines.append("  → '들어가며' 맥락 단락·'왜 지금' 본문·인스타 키워드 문장이 같은 버전으로 바뀝니다.")
    else:
        lines.append("  → 이 분야는 아직 대체 버전이 없어 재생성해도 '왜 지금' 본문이 같아요.")
        lines.append("    발행 전 지난 글과 겹치는 문단은 직접 고쳐 쓰세요.")
    return "\n".join(lines)


def _build_work_guide(blog_title, char_count=0, keyword_report="", overlap_report="",
                      variant_report=""):
    """
    파일 상단에 포함할 스마트에디터 작업 가이드 (SEO v4).
    인간화 편집 체크리스트, 키워드 밀도 리포트, 저품질 방지 가이드 포함.
    v6: '왜 지금' 섹션 버전 안내(variant_report) 추가.
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
🔁 도입부 ↔ '왜 배워야 할까요?' 중복 진단
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{overlap_report if overlap_report else "  (측정 생략)"}

  ※ 역할 분리 원칙
     · 들어가며      → 독자의 상황·경험에 공감 (수치·기관명 금지)
     · 왜 배워야 할까요 → 산업 통계·정책·기업사례로 근거 제시

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 '왜 지금' 섹션 버전
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{variant_report if variant_report else "  (버전 정보 없음)"}

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


def _get_seo_section_title(field, year, label=None):
    """목차에 표시할 SEO 섹션 제목을 반환합니다.

    v6: 표시 라벨(AI유튜브·드론영상·드론배송)이 있으면 라벨 제목을 먼저 씁니다.
    """
    label_titles = {
        "AI유튜브": "왜 지금 AI 유튜브를 배워야 할까요?",
        "유튜브": "왜 지금 유튜브를 배워야 할까요?",
        "AI마케팅": "왜 지금 AI 마케팅 자동화를 배워야 할까요?",
        "드론영상": "왜 지금 드론 영상을 배워야 할까요?",
        "드론배송": "왜 지금 드론 배송 운영을 배워야 할까요?",
    }
    if label and label in label_titles:
        return label_titles[label]
    titles = {
        "제과제빵": f"왜 지금 AI 활용 디저트를 배워야 할까요?",
        "드론정비": f"왜 지금 드론 정비를 배워야 할까요?",
        "AI커머스": f"왜 지금 AI 판매페이지를 배워야 할까요?",
        "디지털콘텐츠": f"왜 지금 AI 디지털콘텐츠를 배워야 할까요?",
        "관광데이터": f"왜 지금 관광 데이터 분석을 배워야 할까요?",
        "AI": f"왜 지금 AI를 배워야 할까요?",
        "영상": f"왜 지금 영상 제작을 배워야 할까요?",
        "디자인": f"왜 지금 디자인을 배워야 할까요?",
        "출판": f"왜 지금 출판 제작을 배워야 할까요?",
        "이커머스": f"왜 지금 온라인 판매를 배워야 할까요?",
        "산업안전": f"왜 지금 산업안전을 배워야 할까요?",
        "마케팅": f"왜 지금 AI 마케팅을 배워야 할까요?",
        "물류/운송": f"왜 지금 지게차 자격증을 따야 할까요?",
        "건축/설계": f"왜 지금 건축설계·디자인을 배워야 할까요?",
        "건축AI": f"왜 지금 건축CAD+AI를 배워야 할까요?",
        "드론": f"왜 지금 드론 전문가가 되어야 할까요?",
        "조경": f"왜 지금 조경기능사를 따야 할까요?",
        "에너지/시설관리": f"왜 지금 에너지관리기능사를 따야 할까요?",
    }
    return titles.get(field, "왜 이 과정을 추천할까요?")


def _build_seo_section(course_data, field, year, label=None):
    """
    '왜 OOO를 배워야 할까요?' 섹션을 생성합니다.

    v5 개선 (분량 확대 + 도입부와 역할 분리):
      · 도입부(들어가며)는 공감·문제의식만 담당
      · 이 섹션은 [산업 동향] + [훈련 필요성] 두 블록으로 구성해 분량을 확대
      · training_need_body가 있으면 소제목을 나눠 두 번째 블록으로 붙입니다.
    v6: 본문은 field_research_helper가 고른 '이번 차례 버전'을 씁니다 (재생성 시 자동 교체).
    """
    title = course_data.get("title", "")

    # 1순위: field_research.json 캐시에서 연구 기반 섹션 로드
    try:
        from field_research_helper import get_seo_section, get_training_need
        cached_section = get_seo_section(field, year, title=title)
        if cached_section:
            section_title = _get_seo_section_title(field, year, label)
            block = f"\n[소제목] {section_title}\n\n{cached_section}\n"

            # 훈련 필요성 블록 (있는 분야만) — 섹션 분량 확대
            need = get_training_need(field, year, title=title)
            if need:
                block += (
                    f"\n[소제목] 그래서 왜 이 훈련일까요?\n\n{need}\n"
                    f"\n[✍️ 직접 작성] 위 내용 중 본인이 실제로 겪은 경험이나 주변 사례를 1~2문장 덧붙이면 "
                    f"체류시간과 신뢰도가 함께 올라갑니다.\n"
                )
            return block
    except ImportError:
        pass

    # 2순위: 하드코딩 데이터
    sections = {
        "AI": f"""
[소제목] 왜 지금 AI를 배워야 할까요?

제주도는 2026년 AI·디지털 분야에 1,015억 원을 투입하기로 했어요. 도민과 소상공인이 AI를 써 볼 수 있도록 디지털배움터의 AI 전환 교육도 함께 추진하고 있고요.

일하는 방식도 이미 바뀌고 있어요. 한국은행이 취업자를 조사했더니 51.8%가 업무에 생성형 AI를 써 본 적이 있었지만, 정기적으로 활용하는 비율은 17.1%였어요(2025년 조사). 써 본 사람은 많아도 업무에 제대로 붙여 쓰는 사람은 아직 많지 않다는 뜻이에요.

정부도 5년간 100만 명 이상에게 AI 직업능력개발을 지원하겠다는 계획을 내놨어요(고용노동부, 2025년 12월). 도구 사용법을 아는 것과 내 업무에 붙여 쓰는 것은 다른 문제라, 국비지원 과정으로 내 일에 맞는 활용법을 익혀 두면 출발선이 달라집니다.
""",
        "영상": f"""
[소제목] 왜 지금 영상 제작을 배워야 할까요?

가게 홍보도, 회사 소식도, 여행지 소개도 이제 짧은 영상으로 먼저 전해지는 경우가 많아요. 영상 한 편을 직접 기획하고 편집할 수 있으면 외주를 기다리지 않고 필요한 때 바로 콘텐츠를 낼 수 있죠.

제주를 담은 영상 수요도 분명해요. 제주특별자치도관광협회는 2026년 도외 유튜버가 제주에 머물며 영상을 만들도록 팀당 100만~200만 원 지원에 나섰어요. 밖에서 사람을 불러 찍을 만큼 제주 영상이 필요하다는 뜻이고, 제주에 사는 사람은 그 풍경을 언제든 다시 찍을 수 있어요.

제주는 콘텐츠기업지원센터 조성을 추진하는 등 콘텐츠 산업 지원을 넓히고 있고, 드론특별자유화구역도 운영하고 있어요. 관광 홍보영상, 소상공인 숏폼, 지역 브랜딩 콘텐츠 등 제주만의 영상 수요도 꾸준합니다.
""",
        "디자인": f"""
[소제목] 왜 지금 디자인을 배워야 할까요?

디자인은 이제 디자인 회사만의 일이 아니에요. 한국디자인진흥원 '2025 디자인산업통계'(2024년 기준)에 따르면 국내 디자인 인력 29만 8,144명 가운데 88.4%가 디자인 전문회사가 아니라 디자인을 활용하는 일반 기업에 속해 있어요. 프리랜서 디자이너도 5만 3,219명으로 1년 새 8.5% 늘었고요.

제주에도 카페·숙박·특산품처럼 브랜드와 패키지가 곧 경쟁력인 업종이 많아요. 감귤·한라봉·녹차 같은 특산품도 어떻게 보여 주느냐에 따라 전혀 다르게 팔리죠.

디자인 도구를 다룰 줄 아는 데서 그치지 않고, 내 작업을 결과물로 보여 줄 수 있는 사람이 결국 일을 맡게 돼요. 국비지원 과정으로 그 첫 결과물을 만들어 보세요.
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

제주도는 로컬크리에이터 육성 조례를 만들고 지역 브랜드 지원을 넓히고 있어요. 라이브커머스와 숏폼 커머스가 커지는 지금, 온라인 판매 스킬은 제주에서 가장 실용적인 무기가 됩니다.
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

기술이 바뀌는 속도가 빨라지면서, 일하면서 새 역량을 더하는 사람과 그렇지 않은 사람의 차이가 커지고 있어요. 제주도도 2026년 AI·디지털 분야에 1,015억 원을 투입하는 등 지역 산업의 디지털 전환을 지원하고 있습니다.

이 과정은 제주 지역의 산업 수요에 맞춰 기획되었고, 내일배움카드로 자부담 10%만 내고 체계적으로 배울 수 있어요. 새로운 도전을 준비하고 계시다면 이 기회를 활용해보세요.

이런 국비지원 과정은 제주 지역의 고용 상황과 산업 트렌드를 반영하여 매년 새롭게 기획됩니다. 올해 열리는 과정이 내년에도 열린다는 보장이 없으니, 관심이 있다면 지금 신청하는 것을 추천드려요.
""")


def _build_goal_explanation(training_goal, field, title):
    """훈련목표 원문에서 키워드를 뽑아 리서치 기반 자체 해설을 생성합니다.

    동작 (v5):
      1) field_research.json의 skill_explanations에서 키워드를 매칭
         (긴 키워드 우선 — "상세페이지"가 "페이지"보다 먼저 잡히도록)
      2) 최대 3개까지 해설을 이어붙임
      3) 매칭이 없으면 key_skills 기반 일반 해설로 폴백

    Work24에서 파싱한 trainingGoal은 행정 문구라 딱딱합니다.
    이 함수가 그 원문을 독자 언어로 풀어주는 역할을 합니다.
    """
    if not training_goal:
        return ""

    haystack = training_goal.upper().replace(" ", "")

    try:
        from field_research_helper import get_skill_explanations, get_education_trends
    except ImportError:
        return ""

    expl_map = get_skill_explanations(field, title=title) or {}

    matched = []
    # 긴 키워드 우선 매칭 (부분 문자열 충돌 방지)
    for kw in sorted(expl_map.keys(), key=len, reverse=True):
        if kw.upper().replace(" ", "") in haystack:
            # 이미 채택된 해설과 중복이면 건너뜀
            if expl_map[kw] not in matched:
                matched.append(expl_map[kw])
        if len(matched) >= 3:
            break

    if matched:
        return "\n\n".join(matched)

    # 폴백: key_skills 상위 3개로 일반 해설 구성
    skills = get_education_trends(field, "key_skills", title=title)
    if skills:
        # v8: 훈련목표에 없는 스킬을 '이 과정에서 다룬다'고 단정하지 않도록 분야 일반 설명으로
        top = ", ".join(skills[:3])
        return (
            f"훈련목표를 실무 언어로 옮기면, 배운 내용을 실제 업무에 바로 써 볼 수 있는 상태가 "
            f"목표라는 뜻이에요. 이 분야 현장에서는 {top} 같은 역량이 함께 쓰여요."
        )
    return ""


# 훈련목표 대조에서 제외할 범용 단어 (이 단어만 겹쳐서는 '직접 명시'로 보지 않음)
#   v8: 관련·위한·대한·필요·통한·따른 추가 — "배송 운영 관련 실무"의 '관련'이
#       "드론 관련 법규·특구 제도"에 ✔를 붙이던 문제
_GENERIC_SKILL_TOKENS = {"AI", "제작", "작성", "기획", "활용", "실무", "기초", "기본",
                         "이해", "실습", "능력", "역량", "수행", "방법", "도구", "교육",
                         "제주", "생성형", "개발", "관리", "운영", "기반",
                         "관련", "위한", "대한", "필요", "통한", "따른"}

_SKILL_SPLIT_RE = r"[\s·,()'\"‘’“”/]+"


def _strip_particle(tok):
    """조사 떼기 — 단, 남는 말이 한 글자면 원래 낱말(경로·결과·효과·자료 등)이므로 그대로 둠."""
    stem = re.sub(r"(으로|에서|과|와|을|를|의|로|및|에)$", "", tok)
    return stem if len(stem) >= 2 else tok


def _raw_skill_tokens(skill):
    toks = []
    for tok in re.split(_SKILL_SPLIT_RE, skill):
        tok = _strip_particle(tok)
        if len(tok) >= 2 and tok.upper() not in _GENERIC_SKILL_TOKENS:
            toks.append(tok)
    return toks


def _compact(text):
    """비교용으로 글자·숫자만 남깁니다 (공백·가운뎃점·쉼표·기호 제거, 대문자)."""
    return re.sub(r"[^0-9A-Za-z가-힣]", "", text or "").upper()


def _phrase_hay(text):
    """훈련목표를 앞 두 낱말 대조용으로 압축합니다.
    낱말마다 조사를 떼고 붙인 것까지 함께 둬서 "영상을 편집하여"도 '영상 편집'으로 잡힙니다."""
    words = re.split(_SKILL_SPLIT_RE, text or "")
    return _compact(text) + " " + _compact("".join(_strip_particle(w) for w in words))


def _skill_head_phrase(skill, title_c=""):
    """스킬 문장의 앞 두 낱말을 붙인 말 (예: '조경 설계 도면 읽기' → '조경설계').
    두 낱말이 모두 범용어('AI 활용', '생성형 AI' 등)이거나 과정명에 이미 든 말
    (예: 호텔디저트 과정의 '호텔 디저트')이면 근거가 못 되므로 빈 문자열."""
    words = [w for w in (_strip_particle(t) for t in re.split(_SKILL_SPLIT_RE, skill)) if len(w) >= 2]
    if len(words) < 2:
        return ""
    a, b = words[0].upper(), words[1].upper()

    def weak(w):
        return w in _GENERIC_SKILL_TOKENS or (title_c and _compact(w) in title_c)

    if weak(a) and weak(b):
        return ""
    return _compact(a + b)


def _common_skill_tokens(skills):
    """그 분야 스킬 3개 이상에 공통으로 나오는 단어 (예: 조경 분야의 '조경').
    이런 단어 하나만 훈련목표와 겹쳐서는 '직접 명시'로 보지 않습니다."""
    from collections import Counter
    cnt = Counter(t.upper() for s in skills for t in set(_raw_skill_tokens(s)))
    return {t for t, n in cnt.items() if n >= 3}


def _skill_tokens(skill, common=frozenset()):
    """핵심 스킬 문장을 훈련목표 대조용 단어로 쪼갭니다 (조사 제거·범용어·분야 공통어 제외)."""
    return [t for t in _raw_skill_tokens(skill) if t.upper() not in common]


# v7: 훈련목표에 흔히 들어가는 넓은 단어 — 이 단어 '하나만' 겹쳐서는 ✔하지 않음
#     (예: 목표의 "마케팅 콘텐츠"가 "유튜브·숏폼 채널 기획과 콘텐츠 캘린더"에 ✔를 붙이던 문제)
_BROAD_SKILL_TOKENS = {"광고", "콘텐츠", "자동화", "생성", "영상", "마케팅", "데이터", "분석",
                       "고객", "성과", "채널", "디자인", "판매", "상품", "업무", "서비스",
                       "전략", "설계", "시스템", "프로그램", "기술", "규정", "편집", "촬영",
                       "절차", "SNS"}


def _course_broad_tokens(skills, title):
    """넓은 단어 + 과정명에 이미 들어 있는 단어(예: 드론배송 과정의 '드론').
    과정명 단어는 훈련목표에도 거의 늘 나오므로 그 단어 하나만으로는 ✔하지 않습니다."""
    title_hay = (title or "").upper().replace(" ", "")
    in_title = {t.upper() for s in skills for t in _raw_skill_tokens(s) if t.upper() in title_hay}
    return _BROAD_SKILL_TOKENS | in_title


def _skill_hit(skill, hay, common=frozenset(), broad=None, hay_compact=None, title_c=""):
    """스킬이 훈련목표에 '직접 명시'됐는지 판단합니다.
    ✔ 조건 (하나라도 맞으면):
      ① 스킬의 앞 두 낱말이 붙은 그대로 훈련목표에 있음 — 조사는 무시
         (예: '광고 성과' → "광고 성과를 분석", '영상 편집' → "영상을 편집하여")
      ② 넓지 않은 단어(랜딩페이지·송출·응대 등)가 하나라도 겹침
      ③ 스킬의 단어가 모두 겹침 (단어가 하나뿐이면 그 단어가 넓은 단어가 아닐 때만)
    v8: 넓은 단어 두 개가 훈련목표의 서로 다른 곳에 따로 나오는 것만으로는 ✔하지 않습니다
        (예: 목표의 "광고 문구"와 "성과 분석"이 '네이버·카카오… 광고 설정과 성과 해석'에 ✔를 붙이던 문제)."""
    broad = _BROAD_SKILL_TOKENS if broad is None else broad
    if hay_compact is None:
        hay_compact = _phrase_hay(hay)
    phrase = _skill_head_phrase(skill, title_c)
    if phrase and phrase in hay_compact:
        return True
    toks = {t.upper() for t in _skill_tokens(skill, common)}
    matched = {t for t in toks if t in hay}
    if not matched:
        return False
    if matched == toks and (len(toks) >= 2 or not (toks & _BROAD_SKILL_TOKENS)):
        return True
    return any(t not in broad for t in matched)


def _build_curriculum_section(course_data, field, sec_title):
    """'무엇을 배울 수 있나요' 섹션을 생성합니다 (v5 신설).

    구조:
      [소제목] 무엇을 배울 수 있나요
      [이미지] 카드뉴스 2번          ← 소제목 바로 아래 인접 배치
      ▸ 기관이 밝힌 훈련목표          ← Work24 파싱 원문 (그대로 인용)
      ▸ 풀어서 설명하면 이런 거예요    ← 훈련목표 키워드 × 리서치 자체 해설
      ▸ 구체적으로 배우는 것들        ← key_skills 중 훈련목표에 직접 명시된 항목(✔)
      ▸ 이 분야에서 함께 알아 두면 좋은 역량 ← 나머지 key_skills(·)
        (✔가 하나도 없으면 '이 분야에서 주로 다루는 역량' 한 묶음으로)
      ▸ 수료 후 이런 길이 열려요      ← career_paths
      certification_note
    """
    title = course_data.get("title", "")
    goal = (course_data.get("trainingGoal", "") or "").strip()
    outcome = (course_data.get("outcome", "") or "").strip()

    block = f"[소제목] {sec_title}\n\n"
    block += "[이미지 삽입] 카드뉴스 커리큘럼 이미지 (2번) — 이 소제목 바로 아래에 배치하세요\n\n"

    # ── ① 기관이 밝힌 훈련목표 (원문 유지) ──
    if goal:
        block += "▸ 기관이 밝힌 훈련목표\n\n"
        block += f"> {goal}\n\n"
    elif outcome:
        block += f"{outcome}\n\n"

    # ── ② 자체 해설 (훈련목표 × 리서치 연계) ──
    explanation = _build_goal_explanation(goal or outcome, field, title)
    if explanation:
        block += "▸ 풀어서 설명하면 이런 거예요\n\n"
        block += f"{explanation}\n\n"

    try:
        from field_research_helper import get_education_trends
    except ImportError:
        get_education_trends = None

    if get_education_trends:
        # ── ③ 구체적으로 배우는 것들 ──
        skills = get_education_trends(field, "key_skills", title=title)
        if skills:
            hay = (goal + " " + outcome).upper().replace(" ", "")
            # 훈련목표에 언급된 스킬을 상단으로 끌어올림
            # v6: 'AI'·'제작'처럼 어디에나 있는 단어 하나로 ✔가 붙어
            #     훈련목표에 없는 항목까지 '직접 명시'로 표시되던 문제 수정
            #     (조사 '과/와/을/를…'도 떼고 비교 → "송출과"가 "송출"로 잡힘)
            common = _common_skill_tokens(skills)
            broad = _course_broad_tokens(skills, title)
            hay_compact = _phrase_hay(goal + " " + outcome)
            title_c = _compact(title)
            hit = [s for s in skills if _skill_hit(s, hay, common, broad, hay_compact, title_c)]
            rest = [s for s in skills if s not in hit]
            # 나머지는 과정명 단어가 든 항목을 앞으로 (예: 마케팅 데이터를 함께 쓰는 AI 유튜브 과정은 유튜브 항목부터)
            rest.sort(key=lambda s: not any(t.upper() in title_c for t in _raw_skill_tokens(s)))
            ordered = (hit + rest)[:7]
            shown_hit = [s for s in ordered if s in hit]
            shown_rest = [s for s in ordered if s not in hit]
            # v8: 훈련목표에 없는 항목(·)이 '구체적으로 배우는 것들' 아래에 함께 나가
            #     과정에서 다루지 않을 수도 있는 내용까지 배우는 것처럼 읽히던 문제 → 묶음 분리
            if shown_hit:
                block += "▸ 구체적으로 배우는 것들\n\n"
                for s in shown_hit:
                    block += f"✔ {s}\n"
                block += "\n(✔ 표시는 이 과정의 훈련목표에 직접 명시된 항목이에요)\n\n"
                if shown_rest:
                    block += "▸ 이 분야에서 함께 알아 두면 좋은 역량\n\n"
                    for s in shown_rest:
                        block += f"· {s}\n"
                    block += "\n"
            else:
                block += "▸ 이 분야에서 주로 다루는 역량\n\n"
                for s in shown_rest:
                    block += f"· {s}\n"
                block += "\n(실제 수업 내용은 고용24 과정 상세에서 확인해 주세요)\n\n"

        # ── ④ 수료 후 진로 ──
        paths = get_education_trends(field, "career_paths", title=title)
        if paths:
            block += "▸ 수료 후 이런 길이 열려요\n\n"
            for p in paths[:6]:
                block += f"→ {p}\n"
            block += "\n"

        # ── ⑤ 자격 관련 메모 ──
        note = get_education_trends(field, "certification_note", title=title)
        if note:
            block += f"💡 {note}\n\n"

    if not goal and not outcome and not explanation:
        block += "상세 커리큘럼은 고용24에서 확인해주세요.\n\n"

    block += (
        "[✍️ 직접 작성] 커리큘럼에 대한 본인의 생각이나 기대를 1~2문장 추가하세요.\n"
        "예시: \"개인적으로 이 과정에서 가장 기대되는 건 ○○ 파트예요. 실무에서 바로 쓸 수 있거든요.\""
    )
    return block


def _build_recommend_section(field, ctype, label=None):
    """
    '이런 분에게 추천해요' 섹션을 생성합니다.
    체류 시간 증가 + 독자 공감 유도.
    v6: 표시 라벨 우선 + 누락 분야(마케팅·조경·드론·에너지·물류) 추가
        — 기존엔 기본 문구("새로운 분야에 도전하고 싶은 분" 등)로 빠졌음
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
        "건축AI": [
            "AutoCAD는 익숙한데 AI 도구는 손도 못 대본 건축 실무자",
            "시안 뽑는 시간을 줄여 야근을 덜고 싶은 설계사",
            "건축주 설득용 렌더링을 빠르게 만들고 싶은 분",
            "리모델링·빈집재생 설계로 방향을 넓히려는 분",
        ],
        "건축/설계": [
            "도면을 읽고 그릴 줄 아는 기본기를 갖추고 싶은 분",
            "인테리어·실내건축 분야로 전직을 준비하시는 분",
            "현장에서 도면 때문에 답답했던 시공·감리 실무자",
            "공공공사 BIM 의무화에 대비하려는 분",
        ],
        "제과제빵": [
            "호텔·리조트 F&B나 베이커리에서 일하고 계신 재직자",
            "카페를 운영하며 디저트로 차별화하고 싶은 분",
            "제과기능사·제빵기능사 실기를 제대로 준비하고 싶은 분",
            "제주 특산물을 활용한 디저트 브랜드를 만들고 싶은 분",
        ],
        "드론정비": [
            "드론 조종 자격은 있지만 정비 역량을 더하고 싶은 분",
            "공공기관·지자체에서 드론 운용·점검을 담당하는 재직자",
            "드론 촬영·방제 현장에서 기체 관리를 맡고 계신 분",
            "드론 제작·활용업체 A/S 직무로 취업을 준비하시는 분",
        ],
        "AI커머스": [
            "제주 특산품을 판매하지만 상세페이지가 늘 아쉬운 농가·소상공인",
            "나만의 브랜드를 만들어 온라인으로 팔고 싶은 분",
            "상세페이지 외주 비용을 줄이고 직접 제작하고 싶은 분",
            "이커머스 콘텐츠 기획자로 커리어를 넓히고 싶은 분",
        ],
        "디지털콘텐츠": [
            "디자이너는 아니지만 회사에서 디자인 업무를 맡게 된 분",
            "SNS·홍보 콘텐츠를 직접 만들어야 하는 마케팅 담당자",
            "AI 도구를 쓰고는 있지만 결과물이 늘 어정쩡한 분",
            "제주에서 UI/UX·디지털디자인 입문 과정을 찾고 계셨던 분",
        ],
        "관광데이터": [
            "관광사업체에서 데이터를 근거로 의사결정하고 싶은 재직자",
            "코딩을 몰라도 데이터 분석을 시작하고 싶은 분",
            "제주 관광 데이터로 실무 포트폴리오를 만들고 싶은 분",
            "공공기관·지자체에서 데이터 업무를 맡게 된 분",
        ],
        # ── v6 추가 ──
        "마케팅": [
            "광고·SNS 운영을 혼자 맡아 매일 시간에 쫓기는 마케팅 담당자",
            "ChatGPT·Gemini를 써 봤지만 업무에 제대로 붙이지 못한 분",
            "반복되는 콘텐츠 작성·보고서 정리를 자동화하고 싶은 소상공인·실무자",
            "데이터를 보고 광고 예산을 판단하는 힘을 기르고 싶은 분",
        ],
        "AI유튜브": [
            "유튜브 채널을 열었지만 기획과 꾸준한 업로드가 막막한 분",
            "가게·브랜드 홍보를 위해 직접 영상 채널을 운영하고 싶은 소상공인",
            "AI 도구로 대본·썸네일·편집 시간을 줄이고 싶은 분",
            "조회수·구독 데이터를 읽고 채널 성장 전략을 세우고 싶은 분",
        ],
        "조경": [
            "정원·녹지 관리 현장으로 취업을 준비하시는 분",
            "호텔·골프장·리조트 등 조경 관리 직무에 관심 있는 분",
            "정원 가꾸기를 취미에서 직업으로 넓혀 보고 싶은 분",
            "전직을 앞두고 현장에서 바로 쓰는 기술을 찾는 분",
        ],
        "조경기능사": [
            "조경기능사 필기·실기를 체계적으로 준비하고 싶은 분",
            "호텔·골프장·리조트 등 조경 관리 현장으로 취업을 준비하시는 분",
            "정원 가꾸기를 취미에서 직업으로 넓혀 보고 싶은 분",
            "전직을 앞두고 현장에서 바로 쓰는 기술 자격을 찾는 분",
        ],
        "드론": [
            "드론 조종 자격은 있지만 배송·물류 운영 경험을 더하고 싶은 분",
            "물류·유통 현장에서 새로운 배송 방식을 준비하는 재직자",
            "비행 계획·관제 등 드론 운영 직무로 취업을 준비하시는 분",
            "드론 산업으로 진로를 넓히려는 분",
        ],
        "드론영상": [
            "드론으로 제주 풍경을 담고 싶었지만 촬영·편집이 막막했던 분",
            "숙소·카페·관광지 홍보 영상을 직접 만들고 싶은 소상공인",
            "영상 제작 프리랜서로 일감을 넓히고 싶은 분",
            "드론 자격을 딴 뒤 실제로 활용할 분야를 찾고 계신 분",
        ],
        "에너지/시설관리": [
            "호텔·리조트·대형 건물 시설관리직으로 취업을 준비하시는 분",
            "에너지관리기능사 등 설비 자격 취득을 준비하시는 분",
            "보일러·냉난방 설비를 다뤄 본 경험을 자격으로 증명하고 싶은 분",
            "기술 하나로 오래 일할 수 있는 직무를 찾는 분",
        ],
        "물류/운송": [
            "물류센터·항만·농산물 유통 현장으로 취업을 준비하시는 분",
            "장비 운전·하역 등 현장 자격을 준비하시는 분",
            "나이·학력과 상관없이 현장에서 바로 쓰는 기술을 찾는 분",
            "경력 단절 후 다시 일을 시작하려는 분",
        ],
        "지게차": [
            "지게차운전기능사 자격을 제주에서 준비하고 싶은 분",
            "물류센터·항만·농산물 유통 현장으로 취업을 준비하시는 분",
            "나이·학력과 상관없이 현장에서 바로 쓰는 자격을 찾는 분",
            "경력 단절 후 다시 일을 시작하려는 분",
        ],
    }
    field_recommends["드론배송"] = field_recommends["드론"]
    # 호텔디저트(AI 메뉴개발 향상과정): 자격증 대비 문구 대신 현직자 기준
    field_recommends["호텔디저트"] = [
        "호텔·리조트 페이스트리 주방에서 시즌 메뉴를 맡고 있는 재직자",
        "카페·베이커리를 운영하며 디저트로 차별화하고 싶은 분",
        "제주 재료로 우리 가게만의 시그니처 디저트를 만들고 싶은 분",
        "메뉴 아이디어·원가 계산·홍보 사진을 AI로 덜어내고 싶은 분",
    ]
    field_recommends["AI마케팅"] = field_recommends["마케팅"]
    field_recommends["유튜브"] = [
        "유튜브 채널을 열었지만 기획과 꾸준한 업로드가 막막한 분",
        "가게·브랜드 홍보를 위해 직접 영상 채널을 운영하고 싶은 소상공인",
        "촬영·편집을 독학하다 막혀서 체계적으로 배우고 싶은 분",
        "조회수·구독 데이터를 읽고 채널 성장 전략을 세우고 싶은 분",
    ]

    recommends = field_recommends.get(label) or field_recommends.get(field, [
        "새로운 분야에 도전하고 싶은 분",
        "취업이나 이직을 준비하시는 분",
        "현재 직무 역량을 업그레이드하고 싶은 분",
        "부담 없이 새로운 기술을 배워보고 싶은 분",
    ])

    section = "[소제목] 이런 분에게 추천해요\n\n"
    for r in recommends:
        section += f"✅ {r}\n"

    # 중복 제거 (v2): 훈련장려금·수당 금액은 '이런 혜택이 있어요' 섹션이 전담합니다.
    # 여기서는 금액을 반복하지 않고 과정 성격만 한 줄로 덧붙입니다.
    if ctype == "long":
        section += "\n장기과정이라 기초부터 실무 포트폴리오까지 차근차근 쌓을 수 있어요."
    elif ctype == "general":
        section += "\n실습 비중이 높은 구성이라 배운 걸 바로 현장에 적용해볼 수 있어요."
    else:
        section += "\n단기 과정이라 빠르게 핵심만 배울 수 있어요. 바쁜 분들에게 딱 맞는 구성이에요."

    return section
