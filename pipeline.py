"""
메인 파이프라인 - 고용24 API에서 과정 데이터를 가져와 콘텐츠를 자동 생성합니다.

사용법:
  python pipeline.py                    # 전체 실행 (API 호출 + 콘텐츠 생성)
  python pipeline.py --json data.json   # JSON 파일에서 데이터 로드

v3 개선사항 (스마트에디터 최적화):
- 블로그 포스트: 네이버 스마트에디터 복사-붙여넣기 최적화 텍스트 (.txt)
- 마크다운/HTML 출력 제거 → 에디터 작업 가이드 포함 단일 텍스트
- 인스타그램: 캡션 + 해시태그(20개) 자동 생성
- 릴스: 15~30초 숏폼 대본 자동 생성
- 게시 가이드: 타이밍, 시리즈 전략, 체크리스트
"""

import json
import os
import sys
from datetime import datetime

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


def _get_field(item, *keys):
    """API 응답에서 여러 가능한 키 이름을 시도하여 값을 가져옵니다."""
    for key in keys:
        val = item.get(key, "")
        if val not in ("", None):
            return val
    return ""


def format_cost(raw_value):
    """숫자 문자열을 '1,077,960원' 형태로 포맷합니다."""
    if not raw_value:
        return ""
    try:
        return f"{int(raw_value):,}원"
    except (ValueError, TypeError):
        return f"{raw_value}원"


def format_date(raw):
    """YYYYMMDD → YYYY.MM.DD 변환"""
    raw = str(raw).replace("-", "").replace(".", "").replace(" ", "")
    if len(raw) >= 8:
        return f"{raw[:4]}.{raw[4:6]}.{raw[6:8]}"
    return str(raw) if raw else ""


def fetch_course_detail(course, api_key):
    """
    L02 API로 과정 상세 정보를 조회하여 course dict에 업데이트합니다.
    totalHours, trainingGoal, ncsName, address 등 L01에 없는 필드를 보완합니다.
    """
    import requests

    url = "https://www.work24.go.kr/cm/openApi/call/hr/callOpenApiSvcInfo310L02.do"
    trpr_id = course.get("trprId", "")
    trpr_degr = course.get("trprDegr", "")
    torg_id = course.get("instCd", "") or course.get("trainstCstId", "")

    params = {
        "authKey": api_key,
        "returnType": "JSON",
        "outType": "2",
        "srchTrprId": trpr_id,
        "srchTrprDegr": trpr_degr,
    }
    if torg_id:
        params["srchTorgId"] = torg_id

    try:
        resp = requests.get(url, params=params, timeout=30)
        raw = resp.text.strip()

        if not raw or raw.startswith("<"):
            print(f"    ⚠️ L02 응답 오류 (HTML 또는 빈 응답)")
            return

        data = resp.json()

        # L02 응답 키: inst_base_info 또는 inst_det_info
        base_info = data.get("inst_base_info", data.get("instBaseInfo", data.get("inst_det_info", {})))
        if isinstance(base_info, list):
            base_info = base_info[0] if base_info else {}
        if not base_info:
            base_info = data

        # 훈련시간 (다중 키 시도)
        raw_hours = _get_field(base_info, "trtm", "TRTM", "totTraingHr", "teTm")
        try:
            total_hours = int(raw_hours)
        except (ValueError, TypeError):
            total_hours = 0
        if total_hours > 0:
            course["totalHours"] = total_hours
            course["time"] = f"총 {total_hours}시간"

        # NCS 직종명
        ncs_name = _get_field(base_info, "ncsNm", "NCS_NM", "ncsCdNm")
        if ncs_name:
            course["ncsName"] = ncs_name

        # 기관명
        inst_name = _get_field(base_info, "inoNm", "INO_NM", "instNm")
        if inst_name:
            course["institution"] = inst_name

        # 훈련목표
        training_goal = _get_field(base_info, "traingGoal", "trainingGoal")
        if training_goal:
            course["trainingGoal"] = training_goal

        # 연락처
        tel = _get_field(base_info, "hpNo", "telNo", "HP_NO", "TEL_NO")
        if tel:
            course["contact"] = f"{course.get('institution', '')} Tel: {tel}"

        # 주소
        addr = _get_field(base_info, "addr1", "ADDR1", "address")
        if addr:
            course["address"] = addr

        # 자부담금 / 수강비 (L02에서 보완)
        per_trco = _get_field(base_info, "perTrco", "PER_TRCO")
        tot_trco = _get_field(base_info, "totTrco", "TOT_TRCO")
        if per_trco and not course.get("selfCost"):
            course["selfCost"] = format_cost(per_trco)
        if tot_trco and not course.get("courseCost"):
            course["courseCost"] = format_cost(tot_trco)

        print(f"    ✅ L02 상세: {total_hours}h, NCS={ncs_name or '없음'}, 목표={'있음' if training_goal else '없음'}")

    except Exception as e:
        print(f"    ⚠️ L02 조회 실패: {e}")


def fetch_courses_from_api():
    """
    고용24 API에서 제주지역 특화훈련 과정을 조회합니다.
    기존 GitHub Actions 워크플로우의 API 호출 방식에 맞춰 수정해주세요.
    """
    import requests

    api_key = os.environ.get("HRD_API_KEY", "")
    if not api_key:
        print("HRD_API_KEY 환경변수가 설정되지 않았습니다.")
        return []

    # ── L01: 목록 조회 ──
    url = "https://www.work24.go.kr/cm/openApi/call/hr/callOpenApiSvcInfo310L01.do"

    # 훈련시작일 검색범위: 오늘 ~ 6개월 후
    from datetime import timedelta
    today = datetime.now()
    six_months_later = today + timedelta(days=180)

    params = {
        "authKey": api_key,
        "returnType": "JSON",
        "outType": "1",
        "pageNum": "1",
        "pageSize": "100",
        "srchTraArea1": "50",          # 제주 (기존 49 → 50으로 변경)
        "srchTraStDt": today.strftime("%Y%m%d"),
        "srchTraEndDt": six_months_later.strftime("%Y%m%d"),
        "crseTracseSe": "C0102",       # 산업구조변화대응 특화훈련
        "sort": "ASC",
        "sortCol": "2",                # 훈련시작일 순
    }

    try:
        # ── 디버깅: 요청 URL 확인 ──
        req = requests.Request("GET", url, params=params)
        prepared = req.prepare()
        # API 키는 일부만 표시
        safe_url = prepared.url.replace(api_key, api_key[:8] + "***") if api_key else prepared.url
        print(f"  요청 URL: {safe_url}")

        response = requests.get(url, params=params, timeout=30)

        # ── 디버깅: 응답 상태 확인 ──
        print(f"  API 응답 코드: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")

        # JSON 파싱 전 응답 내용 확인
        raw = response.text.strip()
        if not raw:
            print("  ⚠️ API 응답이 비어 있습니다.")
            return []

        # JSON이 아닌 응답 감지 (HTML 에러 페이지 등)
        if raw.startswith("<") or raw.startswith("<!"):
            print(f"  ⚠️ API가 HTML을 반환했습니다 (앞 200자):")
            print(f"  {raw[:200]}")
            return []

        try:
            data = response.json()
        except json.JSONDecodeError as je:
            print(f"  ⚠️ JSON 파싱 실패: {je}")
            print(f"  응답 앞 300자: {raw[:300]}")
            return []

        courses = []
        for item in data.get("srchList", []):
            course = parse_api_course(item)
            if course:
                courses.append(course)

        print(f"API에서 {len(courses)}개 과정 조회 완료")

        # ── L02: 각 과정별 상세 정보 보완 ──
        if courses:
            print(f"\n  L02 상세 정보 조회 중... ({len(courses)}건)")
            import time
            for i, course in enumerate(courses):
                print(f"  [{i+1}/{len(courses)}] {course['title'][:40]}")
                fetch_course_detail(course, api_key)
                time.sleep(0.3)  # API 부하 방지

        return courses

    except Exception as e:
        print(f"API 호출 실패: {e}")
        return []


def parse_api_course(api_item):
    """
    L01 목록 API 아이템을 파싱합니다.
    _get_field()로 다중 키 조회하여 API 버전 차이를 흡수합니다.
    """
    try:
        start_raw = _get_field(api_item, "traStartDate", "TRA_START_DATE")
        end_raw = _get_field(api_item, "traEndDate", "TRA_END_DATE")

        start_fmt = format_date(start_raw)
        end_fmt = format_date(end_raw)
        period = f"{start_fmt} ~ {end_fmt}" if start_fmt and end_fmt else ""

        institution = _get_field(api_item, "subTitle", "SUB_TITLE", "instNm", "INST_NM", "inoNm")
        trpr_id = _get_field(api_item, "trprId", "TRPR_ID")
        trpr_degr = _get_field(api_item, "trprDegr", "TRPR_DEGR")

        raw_course_man = _get_field(api_item, "courseMan", "COURSE_MAN")
        course_cost = format_cost(raw_course_man)

        # 자부담 10% 계산
        try:
            self_cost = format_cost(str(round(int(raw_course_man) * 0.1)))
        except (ValueError, TypeError):
            self_cost = ""

        return {
            "trprId": trpr_id,
            "trprDegr": trpr_degr,
            "traStartDate": str(start_raw),
            "traEndDate": str(end_raw),
            "instCd": _get_field(api_item, "instCd", "INST_CD", "trainstCstId"),
            "trainstCstId": _get_field(api_item, "trainstCstId", "TRAINST_CST_ID"),
            "ncsCd": _get_field(api_item, "ncsCd", "NCS_CD"),

            "title": _get_field(api_item, "title", "TITLE", "trprNm", "TRPR_NM"),
            "ncsName": "",                  # L02에서 채워짐
            "institution": institution,
            "period": period,
            "courseCost": course_cost,      # 전체 수강비
            "selfCost": self_cost,          # 자부담금 (10%)
            "totalHours": 0,               # L02에서 채워짐
            "time": "",                    # L02에서 채워짐
            "capacity": f"{_get_field(api_item, 'yardMan', 'YARD_MAN') or '?'}명",
            "target": "국민내일배움카드 있으면 누구나",
            "trainingGoal": "",            # L02에서 채워짐
            "address": _get_field(api_item, "addr1", "ADDR1", "address") or "",
            "benefits": "",
            "curriculum": [],
            "outcome": "",
            "contact": f"{institution} Tel: {_get_field(api_item, 'telNo', 'TEL_NO', 'trprChapTel')}",
            "hrd_url": (
                f"https://www.work24.go.kr/hr/a/a/3100/selectTracseDetl.do"
                f"?tracseId={trpr_id}"
                f"&tracseTme={trpr_degr}"
                f"&crseTracseSe=C0102"
            ),
        }

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
    blog_txt, _ = generate_blog_post(course, output_dir)

    # 생성된 부가 파일 경로 조합
    safe_name = course["title"][:30].replace(" ", "_").replace("/", "_")
    caption_path = os.path.join(output_dir, f"{safe_name}_instagram_caption.txt")
    grok_path = os.path.join(output_dir, f"{safe_name}_reels_grok.txt")
    vrew_path = os.path.join(output_dir, f"{safe_name}_reels_vrew.txt")
    guide_path = os.path.join(output_dir, f"{safe_name}_posting_guide.txt")

    return {
        "cardnews": cardnews_paths,
        "blog_txt": blog_txt,
        "instagram_caption": caption_path if os.path.exists(caption_path) else None,
        "reels_grok": grok_path if os.path.exists(grok_path) else None,
        "reels_vrew": vrew_path if os.path.exists(vrew_path) else None,
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
        print(f"    - *_blog_naver.txt    : 네이버 블로그 텍스트 (스마트에디터용)")
        print(f"    - *_1_cover.png       : 카드뉴스 커버 이미지")
        print(f"    - *_2_detail.png      : 카드뉴스 상세 이미지")
        print(f"    - *_3_howto.png       : 카드뉴스 신청방법 이미지")
        print(f"    - *_instagram_caption.txt : 인스타그램 캡션 + 해시태그")
        print(f"    - *_reels_grok.txt    : Grok 영상 가이드 (30초, 세그먼트별 프롬프트)")
        print(f"    - *_reels_vrew.txt    : Vrew 자막 원고 (나레이션 교정용)")
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
        print(f"\n  고용24 API에서 데이터 조회 중...\n")
        courses = fetch_courses_from_api()

    if courses:
        run_pipeline(courses)
    else:
        print("  생성할 과정이 없습니다.")
