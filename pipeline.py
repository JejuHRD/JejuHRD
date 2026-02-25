"""
메인 파이프라인 - 고용24 API에서 과정 데이터를 가져와 콘텐츠를 자동 생성합니다.

사용법:
  python pipeline.py                    # 전체 실행 (API 호출 + 콘텐츠 생성)
  python pipeline.py --json data.json   # JSON 파일에서 데이터 로드

v3 변경사항:
- HRD-Net → 고용24(work24.go.kr) API 엔드포인트 마이그레이션
- 산업구조변화대응 등 특화훈련(C0102) 과정만 조회
- 제주 지역코드 49 → 50 변경
- 날짜 파싱 강화 (다양한 형식 대응)
"""

import json
import os
import re
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
    """
    parts = []

    course_id = course.get("trprId", course.get("id", ""))
    if course_id:
        parts.append(str(course_id))

    degr = course.get("trprDegr", "")
    if degr:
        parts.append(str(degr))

    start = course.get("traStartDate", "")
    end = course.get("traEndDate", "")
    if start:
        parts.append(start)
    if end:
        parts.append(end)

    if not start and not end and course.get("period"):
        period_clean = course["period"].replace(".", "").replace(" ", "")
        parts.append(period_clean[:20])

    if not parts:
        parts.append(course.get("title", "unknown"))
        parts.append(course.get("institution", ""))

    return "_".join(parts)


def format_date(raw):
    """
    API 응답의 날짜 문자열을 YYYY.MM.DD 형식으로 변환합니다.

    다양한 입력 형식 대응:
    - '20260315'        → '2026.03.15'
    - '2026-03-15'      → '2026.03.15'
    - '2026.03.15'      → '2026.03.15' (그대로)
    - 그 외 / 빈값      → 원본 반환
    """
    if not raw:
        return ""
    raw = str(raw).strip()

    # YYYYMMDD (8자리 숫자)
    if re.match(r"^\d{8}$", raw):
        return f"{raw[:4]}.{raw[4:6]}.{raw[6:8]}"

    # YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}", raw):
        return raw[:10].replace("-", ".")

    # 이미 YYYY.MM.DD 형식이거나 기타
    return raw


def fetch_courses_from_api():
    """
    고용24 API에서 제주지역 특화훈련 과정을 2단계로 조회합니다.

    1단계: L01(목록 API) → 과정 리스트 + trprId, trprDegr, instCd 확보
    2단계: L02(과정/기관정보 API) → 과정별 trtm(총훈련시간), ncsNm(NCS직종명) 등 상세

    - 훈련유형: C0102 (산업구조변화대응 등 특화훈련)
    - 지역: 50 (제주)
    """
    import requests
    import time

    api_key = os.environ.get("HRD_API_KEY", "")
    if not api_key:
        print("  ❌ HRD_API_KEY 환경변수가 설정되지 않았습니다.")
        return []

    # ═══════════════════════════════════════════════════
    # 1단계: L01 목록 API
    # ═══════════════════════════════════════════════════
    url_list = "https://www.work24.go.kr/cm/openApi/call/hr/callOpenApiSvcInfo310L01.do"

    today = datetime.now()
    end_date = today + timedelta(days=180)

    params_list = {
        "authKey": api_key,
        "returnType": "JSON",
        "outType": "1",
        "pageNum": "1",
        "pageSize": "100",
        "srchTraStDt": today.strftime("%Y%m%d"),
        "srchTraEndDt": end_date.strftime("%Y%m%d"),
        "srchTraArea1": "50",
        "crseTracseSe": "C0102",
        "sort": "ASC",
        "sortCol": "2",
    }

    try:
        print("  [1단계] L01 목록 API 호출 중...")
        response = requests.get(url_list, params=params_list, timeout=30)
        print(f"  응답 코드: {response.status_code}")

        content_type = response.headers.get("Content-Type", "")
        if "text/html" in content_type:
            print(f"  ⚠️  HTML 응답 수신 — API URL이 변경되었거나 인증키가 유효하지 않습니다.")
            print(f"  응답 앞 300자:\n{response.text[:300]}")
            return []

        data = response.json()

        srch_list = data.get("srchList", [])
        if not srch_list:
            srch_list = data.get("scn_list", data.get("returnList", []))

        if not srch_list:
            print("  ⚠️  목록 API 결과 0건")
            return []

        # 첫 번째 아이템 키 덤프 (디버그)
        first = srch_list[0]
        print(f"\n  ┌─ [DEBUG] L01 목록 API 필드 ({len(first)}개) ─┐")
        for k, v in first.items():
            val_str = str(v)[:60] if v else "(빈값)"
            print(f"  │  {k:25s} = {val_str}")
        print(f"  └────────────────────────────────────────────┘")

        print(f"  L01에서 {len(srch_list)}개 과정 조회 완료\n")

        # ═══════════════════════════════════════════════════
        # 2단계: L02 과정/기관정보 API (과정별 상세)
        # ═══════════════════════════════════════════════════
        url_detail = "https://www.work24.go.kr/cm/openApi/call/hr/callOpenApiSvcInfo310L02.do"
        print("  [2단계] L02 상세 API로 훈련시간/NCS직종 조회 중...")

        courses = []
        for idx, item in enumerate(srch_list):
            # L01에서 기본 데이터 파싱
            course = _parse_list_item(item)
            if not course:
                continue

            # L02 상세 호출에 필요한 ID들
            trpr_id = course["trprId"]
            trpr_degr = course["trprDegr"]
            # 훈련기관ID: L01 응답에서 가능한 키들 시도
            torg_id = _get_field(item, "instCd", "trainstCstId", "torgId",
                                  "INST_CD", "TRAINST_CST_ID", "TORG_ID",
                                  "instIno", "INST_INO")

            if trpr_id and trpr_degr and torg_id:
                detail = _fetch_course_detail(
                    api_key, url_detail, trpr_id, trpr_degr, torg_id,
                    is_first=(idx == 0)
                )
                if detail:
                    course["totalHours"] = detail.get("totalHours", 0)
                    course["ncsName"] = detail.get("ncsName", "")

                # API 부하 방지 (0.3초 간격)
                time.sleep(0.3)
            else:
                if idx == 0:
                    print(f"  ⚠️  훈련기관ID를 찾을 수 없음 — L01 키 목록에서 기관ID 필드를 확인해주세요")

            courses.append(course)

        # 결과 요약
        has_hours = sum(1 for c in courses if c.get("totalHours", 0) > 0)
        has_ncs = sum(1 for c in courses if c.get("ncsName", ""))
        print(f"\n  ✅ 총 {len(courses)}개 과정 (훈련시간 {has_hours}건, NCS직종 {has_ncs}건 확보)")

        return courses

    except requests.exceptions.JSONDecodeError:
        print(f"  ⚠️  JSON 파싱 실패 — API 응답이 JSON이 아닙니다.")
        print(f"  응답 앞 500자:\n{response.text[:500]}")
        return []
    except Exception as e:
        print(f"  API 호출 실패: {e}")
        import traceback
        traceback.print_exc()
        return []


def _fetch_course_detail(api_key, url, trpr_id, trpr_degr, torg_id, is_first=False):
    """
    L02 과정/기관정보 API로 상세 정보를 가져옵니다.

    반환값: {"totalHours": int, "ncsName": str} 또는 None
    """
    import requests

    params = {
        "authKey": api_key,
        "returnType": "JSON",
        "outType": "2",
        "srchTrprId": trpr_id,
        "srchTrprDegr": trpr_degr,
        "srchTorgId": torg_id,
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            return None

        data = resp.json()

        # L02 응답 구조: inst_base_info 안에 상세 필드
        base_info = data.get("inst_base_info", data.get("instBaseInfo", {}))

        # 응답이 리스트인 경우 첫 번째 아이템
        if isinstance(base_info, list):
            base_info = base_info[0] if base_info else {}

        # 첫 번째 과정일 때 L02 응답 키 덤프
        if is_first and base_info:
            print(f"\n  ┌─ [DEBUG] L02 상세 API inst_base_info 필드 ({len(base_info)}개) ─┐")
            for k, v in base_info.items():
                val_str = str(v)[:60] if v else "(빈값)"
                print(f"  │  {k:25s} = {val_str}")
            print(f"  └──────────────────────────────────────────────────────────┘")

        # inst_base_info가 비어있으면 최상위에서 시도
        if not base_info:
            base_info = data

        # trtm 추출
        raw_trtm = _get_field(base_info, "trtm", "TRTM", "tRtM")
        try:
            total_hours = int(raw_trtm)
        except (ValueError, TypeError):
            total_hours = 0

        # ncsNm 추출
        ncs_name = _get_field(base_info, "ncsNm", "NCS_NM", "ncsNM", "ncsnm")

        if is_first:
            print(f"  [DEBUG] L02 → 훈련시간: {total_hours}, NCS직종: {ncs_name}")
            print()

        return {"totalHours": total_hours, "ncsName": ncs_name}

    except Exception as e:
        return None


def format_cost(raw_value):
    """숫자 문자열을 '1,077,960원' 형태로 포맷합니다."""
    if not raw_value:
        return ""
    try:
        return f"{int(raw_value):,}원"
    except (ValueError, TypeError):
        return f"{raw_value}원"


def _get_field(item, *keys):
    """API 응답에서 여러 가능한 키 이름을 시도하여 값을 가져옵니다."""
    for key in keys:
        val = item.get(key, "")
        if val not in ("", None):
            return val
    return ""


def _parse_list_item(api_item):
    """
    L01 목록 API 아이템을 파싱합니다.
    (trtm, ncsNm은 L02에서 별도 채움)
    """
    try:
        start_raw = _get_field(api_item, "traStartDate", "TRA_START_DATE")
        end_raw = _get_field(api_item, "traEndDate", "TRA_END_DATE")

        start_fmt = format_date(start_raw)
        end_fmt = format_date(end_raw)
        period = f"{start_fmt} ~ {end_fmt}" if start_fmt and end_fmt else ""

        institution = _get_field(api_item, "subTitle", "SUB_TITLE", "instNm", "INST_NM", "inoNm", "INO_NM")
        trpr_id = _get_field(api_item, "trprId", "TRPR_ID")
        trpr_degr = _get_field(api_item, "trprDegr", "TRPR_DEGR")

        raw_course_man = _get_field(api_item, "courseMan", "COURSE_MAN")
        course_cost = format_cost(raw_course_man)

        try:
            self_cost = format_cost(str(round(int(raw_course_man) * 0.1)))
        except (ValueError, TypeError):
            self_cost = ""

        return {
            "trprId": trpr_id,
            "trprDegr": trpr_degr,
            "traStartDate": str(start_raw),
            "traEndDate": str(end_raw),
            "title": _get_field(api_item, "title", "TITLE", "trprNm", "TRPR_NM"),
            "ncsName": "",          # L02에서 채워짐
            "institution": institution,
            "period": period,
            "courseCost": course_cost,
            "selfCost": self_cost,
            "totalHours": 0,        # L02에서 채워짐
            "capacity": f"{_get_field(api_item, 'yardMan', 'YARD_MAN') or '?'}명",
            "target": "국민내일배움카드 있으면 누구나",
            "benefits": "",
            "curriculum": [],
            "outcome": "",
            "contact": f"{institution} Tel: {_get_field(api_item, 'telNo', 'TEL_NO', 'trprChapTel', 'TRPR_CHAP_TEL')}",
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

    use_v2 = HAS_V2 and os.environ.get("PEXELS_API_KEY", "")
    if use_v2:
        cardnews_paths = generate_cardnews_v2(course, output_dir)
    else:
        cardnews_paths = generate_cardnews(course, output_dir)

    blog_md, blog_html = generate_blog_post(course, output_dir)

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
    if skip_count > 0:
        print(f"  💡 스킵된 과정을 재생성하려면: python pipeline.py --force")
    print(f"{'=' * 60}")

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
    print("  🎯 대상: 산업구조변화대응 등 특화훈련 (C0102) / 제주")
    print("=" * 60)

    # --force: 캐시 초기화 후 전체 재생성
    if "--force" in sys.argv:
        cache_file = os.path.join(OUTPUT_DIR, "processed_ids.json")
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print("\n  🔄 --force: 캐시 초기화 완료 → 전체 과정 재생성합니다")
        else:
            print("\n  🔄 --force: 캐시 없음 → 전체 과정 새로 생성합니다")

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
        # 첫 번째 과정 파싱 결과 요약
        c = courses[0]
        print(f"  ── 첫 번째 과정 파싱 결과 확인 ──")
        print(f"  과정명:     {c.get('title', '?')}")
        print(f"  NCS직종명:  {c.get('ncsName') or '❌ 비어있음 (API 필드명 확인 필요)'}")
        print(f"  훈련시간:   {c.get('totalHours') or '❌ 0 (API 필드명 확인 필요)'}")
        print(f"  기관명:     {c.get('institution', '?')}")
        print(f"  수강비:     {c.get('courseCost', '?')}")
        print()
        run_pipeline(courses)
    else:
        print("  생성할 과정이 없습니다.")
