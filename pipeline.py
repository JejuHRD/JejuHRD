"""
메인 파이프라인 - 고용24 API에서 과정 데이터를 가져와 콘텐츠를 자동 생성합니다.

사용법:
  python pipeline.py                    # 전체 실행 (API 호출 + 콘텐츠 생성)
  python pipeline.py --json data.json   # JSON 파일에서 데이터 로드

v2 개선사항 (SEO/마케팅 최적화):
- 블로그 포스트: SEO 최적화 제목, 공감형 도입부, 확장된 본문
- 인스타그램: 캡션 + 해시태그(20개) 자동 생성
- 릴스: 15~30초 숏폼 대본 자동 생성
- 게시 가이드: 타이밍, 시리즈 전략, 체크리스트

v3 변경사항 (API 엔드포인트 마이그레이션):
- HRD-Net → 고용24(work24.go.kr) 통합에 따라 API URL 변경
- 제주 지역코드 49 → 50 변경
- 필수 파라미터 추가: srchTraEndDt, sort, sortCol
"""

import json
import os
import sys
from datetime import datetime, timedelta

from generate_cardnews import generate_cardnews
from generate_blog import generate_blog_post

# v2 카드뉴스 (이미지 배경) 사용 가능 여부 확인
try:
    from generate_cardnews_v2 import generate_cardnews_v2
    HAS_V2 = True
except ImportError:
    HAS_V2 = False

# ── 설정 ──
OUTPUT_DIR = "output"
PROCESSED_FILE = "output/.processed_courses.json"


def load_processed_ids():
    """이미 콘텐츠를 생성한 과정 목록을 로드"""
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, "r") as f:
            return json.load(f)
    return {}


def save_processed_ids(processed):
    """처리 완료된 과정 저장"""
    os.makedirs(os.path.dirname(PROCESSED_FILE), exist_ok=True)
    with open(PROCESSED_FILE, "w") as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)


def make_course_key(course):
    """
    과정의 고유 키를 생성합니다.

    같은 과정(trprId)이라도 회차(trprDegr)나 훈련기간이 다르면
    별도의 콘텐츠로 취급합니다.

    키 구성: {과정ID}_{회차}_{훈련시작일}_{훈련종료일}
    예시: "AIG20250001_1_20260315_20260614"
    """
    parts = []

    # 과정 ID
    course_id = course.get("trprId", course.get("id", ""))
    if course_id:
        parts.append(str(course_id))

    # 회차
    degr = course.get("trprDegr", "")
    if degr:
        parts.append(str(degr))

    # 훈련기간 (시작일~종료일)
    start = course.get("traStartDate", "")
    end = course.get("traEndDate", "")
    if start:
        parts.append(start)
    if end:
        parts.append(end)

    # period 필드에서 날짜 추출 (위 필드가 없을 경우 폴백)
    if not start and not end and course.get("period"):
        period_clean = course["period"].replace(".", "").replace(" ", "")
        parts.append(period_clean[:20])

    # 아무 정보도 없으면 과정명 + 기관명으로 대체
    if not parts:
        parts.append(course.get("title", "unknown"))
        parts.append(course.get("institution", ""))

    return "_".join(parts)


def fetch_courses_from_api():
    """
    고용24 API(work24.go.kr)에서 제주지역 훈련과정을 조회합니다.

    2024년 9월 HRD-Net → 고용24 통합에 따라 API 엔드포인트 변경:
    - 기존: https://www.hrd.go.kr/hrdp/api/prmtApi.do
    - 현재: https://www.work24.go.kr/cm/openApi/call/hr/callOpenApiSvcInfo310L01.do
    """
    import requests

    api_key = os.environ.get("HRD_API_KEY", "")
    if not api_key:
        print("HRD_API_KEY 환경변수가 설정되지 않았습니다.")
        return []

    url = "https://www.work24.go.kr/cm/openApi/call/hr/callOpenApiSvcInfo310L01.do"

    # 검색 기간: 오늘부터 6개월 후까지
    today = datetime.now()
    end_date = today + timedelta(days=180)

    params = {
        "authKey": api_key,
        "returnType": "JSON",
        "outType": "1",            # 1=리스트
        "pageNum": "1",
        "pageSize": "100",
        "srchTraStDt": today.strftime("%Y%m%d"),       # 필수: 훈련시작일 From
        "srchTraEndDt": end_date.strftime("%Y%m%d"),   # 필수: 훈련시작일 To
        "srchTraArea1": "50",      # 제주 (고용24에서 50으로 변경됨)
        "sort": "ASC",             # 필수: 정렬방법
        "sortCol": "2",            # 필수: 정렬컬럼 (2=훈련시작일)
    }

    try:
        response = requests.get(url, params=params, timeout=30)

        # 디버깅: 응답 상태 확인
        print(f"  응답 코드: {response.status_code}")

        # HTML 응답 감지 (API 오류 또는 URL 변경)
        content_type = response.headers.get("Content-Type", "")
        if "text/html" in content_type:
            print(f"  ⚠️  HTML 응답 수신 — API URL이 변경되었거나 인증키가 유효하지 않습니다.")
            print(f"  응답 앞 300자:\n{response.text[:300]}")
            return []

        data = response.json()

        # 응답 구조 확인
        srch_list = data.get("srchList", [])
        if not srch_list:
            # 대체 키 확인 (API 버전에 따라 다를 수 있음)
            srch_list = data.get("scn_list", data.get("returnList", []))

        courses = []
        for item in srch_list:
            course = parse_api_course(item)
            if course:
                courses.append(course)

        print(f"  API에서 {len(courses)}개 과정 조회 완료")
        return courses

    except requests.exceptions.JSONDecodeError:
        print(f"  ⚠️  JSON 파싱 실패 — API 응답이 JSON이 아닙니다.")
        print(f"  응답 앞 500자:\n{response.text[:500]}")
        return []
    except Exception as e:
        print(f"  API 호출 실패: {e}")
        return []


def parse_api_course(api_item):
    """
    API 응답 데이터를 콘텐츠 생성기 형식으로 변환합니다.

    고용24 API 출력 필드 (camelCase):
    - trprId: 훈련과정ID
    - trprDegr: 훈련과정 순차(회차)
    - title: 제목
    - subTitle: 부제목
    - traStartDate: 훈련시작일자 (YYYYMMDD)
    - traEndDate: 훈련종료일자 (YYYYMMDD)
    - trainstCstId: 훈련기관ID
    - courseMan: 수강비
    - yardMan: 정원
    - realMan: 실제 훈련비
    - telNo: 전화번호
    - address: 주소
    - trainTargetCd: 훈련구분
    """
    try:
        start = api_item.get("traStartDate", "")
        end = api_item.get("traEndDate", "")
        if start and end:
            period = f"{start[:4]}.{start[4:6]}.{start[6:8]} ~ {end[:4]}.{end[4:6]}.{end[6:8]}"
        else:
            period = ""

        # 훈련기관명: subTitle 또는 title에서 추출
        institution = api_item.get("subTitle", "")

        course = {
            # 원본 필드 보존 (고유 키 생성에 사용)
            "trprId": api_item.get("trprId", ""),
            "trprDegr": api_item.get("trprDegr", ""),
            "traStartDate": start,
            "traEndDate": end,

            # 콘텐츠 생성용 필드
            "title": api_item.get("title", ""),
            "institution": institution,
            "period": period,
            "time": f"총 {api_item.get('courseMan', '?')}시간",
            "courseMan": api_item.get("courseMan", ""),
            "capacity": f"{api_item.get('yardMan', '?')}명",
            "target": "내일배움카드 있으면 누구나",
            "benefits": "",  # 비워두면 benefits_helper가 시간 기반으로 자동 결정
            "curriculum": [],
            "outcome": "",
            "contact": f"{institution} Tel: {api_item.get('telNo', '')}",
            "hrd_url": (
                f"https://www.work24.go.kr/cm/openApi/call/hr/callOpenApiSvcInfo310L01.do"
                f"?trprId={api_item.get('trprId', '')}"
                f"&trprDegr={api_item.get('trprDegr', '')}"
            ),
        }

        return course

    except Exception as e:
        print(f"  과정 파싱 실패: {e}")
        return None


def generate_content_for_course(course, output_dir):
    """단일 과정에 대해 카드뉴스 + 블로그 + 인스타 캡션 + 릴스 대본 + 게시 가이드를 생성"""
    print(f"\n{'─' * 50}")
    print(f"  📌 {course['title']}")
    if course.get("period"):
        print(f"  📅 ({course['period']})")
    print(f"{'─' * 50}")

    # 카드뉴스 생성 (Pexels API 키가 있으면 v2, 없으면 v1)
    use_v2 = HAS_V2 and os.environ.get("PEXELS_API_KEY", "")
    if use_v2:
        cardnews_paths = generate_cardnews_v2(course, output_dir)
    else:
        cardnews_paths = generate_cardnews(course, output_dir)

    # 블로그 포스트 생성 (인스타 캡션, 릴스 대본, 게시 가이드도 함께 생성됨)
    blog_md, blog_html = generate_blog_post(course, output_dir)

    # 생성된 부가 파일 경로 조합
    safe_name = course["title"][:30].replace(" ", "_").replace("/", "_")
    caption_path = os.path.join(output_dir, f"{safe_name}_instagram_caption.txt")
    reels_path = os.path.join(output_dir, f"{safe_name}_reels_script.txt")
    guide_path = os.path.join(output_dir, f"{safe_name}_posting_guide.txt")

    return {
        "cardnews": cardnews_paths,
        "blog_md": blog_md,
        "blog_html": blog_html,
        "instagram_caption": caption_path if os.path.exists(caption_path) else None,
        "reels_script": reels_path if os.path.exists(reels_path) else None,
        "posting_guide": guide_path if os.path.exists(guide_path) else None,
    }


def run_pipeline(courses):
    """
    메인 파이프라인 실행
    - 같은 과정이라도 회차/훈련기간이 다르면 새로 생성
    - 이미 동일 키로 처리한 과정은 건너뜀
    """
    processed = load_processed_ids()
    new_count = 0
    skip_count = 0

    for course in courses:
        course_key = make_course_key(course)

        if course_key in processed:
            print(f"  ⏭️  이미 처리됨: {course['title'][:40]} ({course.get('period', '')})")
            skip_count += 1
            continue

        result = generate_content_for_course(course, OUTPUT_DIR)

        processed[course_key] = {
            "title": course["title"],
            "period": course.get("period", ""),
            "generated_at": datetime.now().isoformat(),
            "files": result,
        }
        new_count += 1

    save_processed_ids(processed)

    print(f"\n{'=' * 60}")
    print(f"  ✅ 실행 결과: 새 과정 {new_count}건 생성, {skip_count}건 스킵")
    print(f"{'=' * 60}")

    # 생성된 파일 요약
    if new_count > 0:
        print(f"\n  📁 출력 디렉토리: {OUTPUT_DIR}/")
        print(f"  과정당 생성 파일:")
        print(f"    - *_blog.md           : 네이버 블로그 마크다운 (SEO 최적화)")
        print(f"    - *_blog_naver.html   : 네이버 블로그 HTML (복사-붙여넣기용)")
        print(f"    - *_1_cover.png       : 카드뉴스 커버 이미지")
        print(f"    - *_2_detail.png      : 카드뉴스 상세 이미지")
        print(f"    - *_3_howto.png       : 카드뉴스 신청방법 이미지")
        print(f"    - *_instagram_caption.txt : 인스타그램 캡션 + 해시태그")
        print(f"    - *_reels_script.txt  : 릴스(숏폼) 대본")
        print(f"    - *_posting_guide.txt : 게시 타이밍/시리즈 전략 가이드")

    return new_count


if __name__ == "__main__":
    print("=" * 60)
    print("  🚀 특화훈련 콘텐츠 자동 생성 파이프라인 v3")
    print(f"  📅 실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    if "--json" in sys.argv:
        json_idx = sys.argv.index("--json") + 1
        json_path = sys.argv[json_idx]
        print(f"\n  JSON 파일에서 로드: {json_path}\n")
        with open(json_path, "r", encoding="utf-8") as f:
            courses = json.load(f)
    else:
        print("\n  고용24 API에서 데이터 조회 중...\n")
        courses = fetch_courses_from_api()

    if courses:
        run_pipeline(courses)
    else:
        print("  생성할 과정이 없습니다.")
