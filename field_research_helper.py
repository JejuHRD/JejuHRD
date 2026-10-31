"""
분야별 리서치 캐시 헬퍼 - field_research.json에서 최신 연구 데이터를 로드합니다.

사용법:
  from field_research_helper import (
      get_field_research, get_empathy_hooks, get_seo_section,
      get_intro_context, get_training_need,
  )

  # 분야별 전체 연구 데이터 가져오기
  data = get_field_research("이커머스")

  # 공감형 도입부 후보 가져오기
  hooks = get_empathy_hooks("이커머스")

  # SEO 섹션 본문 가져오기
  section = get_seo_section("이커머스")

리서치 갱신:
  field_research.json 파일을 직접 편집하거나,
  심층연구 결과를 update_field_research() 함수로 반영하세요.

v3 (2026-10-31) — '왜 지금' 섹션 버전 로테이션:
  같은 과정이 다시 생성될 때마다 '왜 지금' 본문이 똑같이 반복되던 문제를 막습니다.
  분야 데이터에 section_variants(대체 버전 목록)가 있으면, 생성할 때마다
  기본 → 버전 2 → 버전 3 → 기본 … 순서로 자동 교체합니다.
    · 교체 대상: intro_context / seo_section_body / training_need_body /
                 instagram_keyword_sentence (버전에 없는 키는 기본값 사용)
    · 순서 판정: ① 직전 블로그 파일 작업 가이드의 버전 표식
                 → ② 없으면 .processed_courses.json에서 '리서치 갱신일 이후'
                    같은 과정명으로 생성된 횟수
    · 한 번 실행(프로세스) 안에서는 같은 과정이 항상 같은 버전을 씁니다
      (블로그·인스타 캡션·작업 가이드가 서로 어긋나지 않도록).

v3.1 (2026-10-31) — 같은 데이터를 쓰는 과정끼리 버전 엇갈리기:
  'AI 마케팅 자동화'와 'AI 유튜브 크리에이터'처럼 한 분야 데이터를 함께 쓰는 과정이
  같은 시기에 같은 버전을 받으면 '왜 지금' 문단이 통째로 같은 글이 두 개 나갑니다
  (네이버 유사문서 위험). 그래서
    · 다른 과정의 최신 블로그 글(산출물 폴더)이 쓰는 버전은 피해서 고르고
      (자기 직전 버전은 마지막 후보 — 다른 버전이 모두 쓰이고 있을 때만)
    · 처리 이력으로 셀 때는 분야 데이터의 variant_start_by_keyword
      (예: {"유튜브": 1})만큼 시작 순서를 미룹니다.
"""

import json
import os
import re
from datetime import datetime

RESEARCH_FILE = os.path.join(os.path.dirname(__file__), "field_research.json")

_cache = None


def _load_cache():
    """리서치 캐시를 로드합니다. 파일이 없으면 빈 dict 반환."""
    global _cache
    if _cache is not None:
        return _cache
    if os.path.exists(RESEARCH_FILE):
        try:
            with open(RESEARCH_FILE, "r", encoding="utf-8") as f:
                _cache = json.load(f)
        except (json.JSONDecodeError, IOError):
            _cache = {}
    else:
        _cache = {}
    return _cache


def get_field_research(field, title=None):
    """
    특정 분야의 전체 리서치 데이터를 반환합니다.
    
    title이 주어지면 서브필드(예: "드론영상")를 자동 매칭합니다.
    서브필드가 없으면 상위 분야(예: "영상")로 폴백합니다.

    Args:
        field: 분야명 (예: "이커머스", "영상" 등)
        title: 과정 제목 (서브필드 매칭용, 선택)

    Returns:
        dict 또는 None (데이터가 없으면)
    """
    cache = _load_cache()
    
    # 서브필드 매칭: title에서 키워드를 찾아 더 구체적인 분야 데이터 사용
    if title:
        resolved = _resolve_subfield(cache, field, title)
        if resolved:
            return resolved
    
    return cache.get(field)


def _resolve_subfield(cache, field, title):
    """
    과정 제목의 키워드로 서브필드를 매칭합니다.
    
    field_research.json에서 title_keywords를 가진 엔트리 중
    parent_field가 일치하고 title에 키워드가 포함된 것을 찾습니다.
    
    매칭 정책 (v2):
      · 제목과 키워드 모두 공백·괄호 제거 후 비교하여
        "에너지 관리", "냉동 공조" 같은 공백 변형도 자동 매칭
      · 원본 제목에 대한 매칭도 함께 시도하여 기존 동작 보존
    """
    if not title:
        return None
    title_upper = title.upper()
    title_normalized = title_upper.replace(" ", "").replace("(", "").replace(")", "")
    for key, data in cache.items():
        if key.startswith("_"):
            continue
        if not isinstance(data, dict):
            continue
        parent = data.get("parent_field", "")
        keywords = data.get("title_keywords", [])
        if parent == field and keywords:
            for kw in keywords:
                kw_upper = kw.upper()
                kw_normalized = kw_upper.replace(" ", "")
                if (kw_upper in title_upper) or (kw_normalized in title_normalized):
                    return data
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# '왜 지금' 섹션 버전 로테이션 (v3)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 산출물 폴더 후보 (GitHub Actions: 저장소 루트에서 실행 → "output")
OUTPUT_DIR_CANDIDATES = [
    "output",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "output"),
]
PROCESSED_FILENAME = ".processed_courses.json"

# 블로그 작업 가이드에 남기는 버전 표식 (generate_blog._build_work_guide가 출력)
#   예) 🔄 '왜 지금' 섹션 버전 2/3 · 제작 비용·도구 혁신 · 리서치 2026-10-31
VARIANT_MARKER_FORMAT = "🔄 '왜 지금' 섹션 버전 {index}/{total} · {angle} · 리서치 {updated_at}"
_VARIANT_MARKER_RE = re.compile(
    r"'왜 지금' 섹션 버전[ \t]*(\d+)[ \t]*/[ \t]*(\d+)"
    r"(?:[^\n]*?리서치[ \t]*(\d{4}-\d{2}-\d{2}))?"
)

# 다른 과정 글의 표식을 읽을 때 쓰는 전체 패턴 (번호/전체 · 앵글 · 리서치 날짜)
_VARIANT_MARKER_FULL_RE = re.compile(
    r"'왜 지금' 섹션 버전[ \t]*(\d+)[ \t]*/[ \t]*(\d+)[ \t]*·[ \t]*([^\n]*?)[ \t]*·[ \t]*"
    r"리서치[ \t]*(\d{4}-\d{2}-\d{2}|미기재)"
)

# 테스트용 강제 지정 (None이면 자동 판정). 정수 n → n번째 로테이션(0부터)
_variant_override = None

# generate_blog_post(course, output_dir)가 알려 주는 산출물 폴더 (None이면 기본 후보)
_output_dir_override = None


def set_output_dir(path):
    """버전 판정 때 볼 산출물 폴더를 지정합니다 (generate_blog_post가 호출)."""
    global _output_dir_override
    _output_dir_override = path or None


def _output_dirs():
    if _output_dir_override:
        return [_output_dir_override]
    return OUTPUT_DIR_CANDIDATES

# 한 실행 안에서 과정별 로테이션 번호 고정 {과정명: 로테이션 번호}
_rotation_memo = {}

# 이번 실행에서 데이터별로 각 과정이 고른 버전 {데이터 식별자: {과정명: 버전 번호(0부터)}}
_run_choices = {}


def reset_variant_memo():
    """로테이션 메모를 비웁니다 (테스트에서 '다음 실행'을 흉내 낼 때 사용)."""
    _rotation_memo.clear()
    _run_choices.clear()


def _norm_title(title):
    return " ".join(str(title or "").split())


def _safe_name(title):
    """pipeline.py / generate_blog.py와 같은 규칙의 파일명 접두어."""
    return re.sub(r'[<>:"/\\|?*\r\n\t]', "_", title[:30]).replace(" ", "_")


def _variants(data):
    """[기본 버전(최상위 키)] + section_variants 목록을 반환합니다."""
    out = [data]
    variants = data.get("section_variants", []) or []
    if not isinstance(variants, list):
        return out
    for v in variants:
        if isinstance(v, dict):
            out.append(v)
    return out


def _read_last_marker(title):
    """직전에 생성된 블로그 파일에서 버전 표식을 읽습니다.

    Returns:
        (직전 버전 번호(1부터), 직전 리서치 갱신일 또는 None) / 표식이 없으면 None
    """
    fname = f"{_safe_name(title)}_blog_naver.txt"
    norm = _norm_title(title)
    for d in _output_dirs():
        path = os.path.join(d, fname)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except (IOError, UnicodeDecodeError):
            continue
        # 앞 30자가 같은 다른 과정의 파일을 잘못 읽지 않도록 과정명 확인
        m_title = re.search(r"과정명:[ \t]*([^\n]+)", text)
        if not m_title or _norm_title(m_title.group(1)) != norm:
            continue
        m = _VARIANT_MARKER_RE.search(text)
        if not m:
            return None  # 구버전 코드로 만든 파일 → 처리 이력으로 폴백
        return int(m.group(1)), m.group(3)
    return None


def _count_generations_since(title, since=""):
    """처리 이력에서 같은 과정명이 리서치 갱신일(since) 이후 생성된 횟수."""
    norm = _norm_title(title)
    for d in _output_dirs():
        path = os.path.join(d, PROCESSED_FILENAME)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                processed = json.load(f)
        except (json.JSONDecodeError, IOError, UnicodeDecodeError):
            return 0
        if not isinstance(processed, dict):
            return 0
        n = 0
        for v in processed.values():
            if not isinstance(v, dict) or _norm_title(v.get("title", "")) != norm:
                continue
            # 리서치 갱신 전에 만든 글은 옛 본문을 썼으므로 로테이션 횟수에서 제외
            if since and str(v.get("generated_at", "")) < since:
                continue
            n += 1
        return n
    return 0


def _rotation_for(title, data):
    """이번 생성의 로테이션 번호(0부터)를 정합니다. 같은 실행 안에서는 고정."""
    if _variant_override is not None:
        return int(_variant_override)
    key = _norm_title(title)
    if key in _rotation_memo:
        return _rotation_memo[key]

    updated_at = str(data.get("updated_at", "") or "")
    rotation = None
    last = _read_last_marker(title)
    if last is not None:
        last_index, last_updated = last
        if not updated_at or not last_updated or last_updated == updated_at:
            rotation = last_index          # 직전 버전(1부터) = 다음 로테이션 번호(0부터)
        # 리서치가 그 사이 갱신됐으면 아래 처리 이력 기준으로 다시 셉니다
    if rotation is None:
        rotation = _count_generations_since(title, updated_at) + _start_offset(title, data)

    rotation = _avoid_sibling_versions(rotation, title, data)
    _rotation_memo[key] = rotation
    return rotation


def _start_offset(title, data):
    """variant_start_by_keyword(예: {"유튜브": 1}) — 제목에 그 단어가 있으면 시작 순서를 미룹니다."""
    starts = data.get("variant_start_by_keyword") or {}
    if not isinstance(starts, dict):
        return 0
    hay = str(title or "").upper().replace(" ", "")
    for kw, offset in starts.items():
        k = str(kw).upper().replace(" ", "")
        if k and k in hay:
            try:
                return int(offset)
            except (TypeError, ValueError):
                return 0
    return 0


def _angle_of(data, idx, v):
    """버전 앵글명 (작업 가이드 표식과 같은 규칙)."""
    if idx == 0:
        angle = data.get("section_angle") or "기본"
    else:
        angle = v.get("angle") or f"버전 {idx + 1}"
    return " ".join(str(angle).split())          # 줄바꿈이 표식 한 줄을 깨지 않도록


def _data_id(data):
    """같은 데이터인지 가리는 식별자 (앵글 목록 + 리서치 갱신일)."""
    vs = _variants(data)
    return (tuple(_angle_of(data, i, v) for i, v in enumerate(vs)),
            str(data.get("updated_at", "") or "미기재"))


def _sibling_versions(title, data):
    """같은 데이터(같은 리서치 갱신일)를 쓰는 '다른 과정'의 최신 블로그 글이 쓰고 있는 버전(0부터)."""
    angles, updated_at = _data_id(data)
    norm = _norm_title(title)
    taken = set()
    seen = set()
    for d in _output_dirs():
        real = os.path.realpath(d)
        if real in seen or not os.path.isdir(d):
            continue
        seen.add(real)
        try:
            names = os.listdir(d)
        except OSError:
            continue
        for name in names:
            if not name.endswith("_blog_naver.txt"):
                continue
            try:
                with open(os.path.join(d, name), "r", encoding="utf-8") as f:
                    text = f.read()
            except (IOError, UnicodeDecodeError):
                continue
            m_title = re.search(r"과정명:[ \t]*([^\n]+)", text)
            if not m_title or _norm_title(m_title.group(1)) == norm:
                continue
            m = _VARIANT_MARKER_FULL_RE.search(text)
            if not m or int(m.group(2)) != len(angles) or m.group(4) != updated_at:
                continue
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(angles) and " ".join(m.group(3).split()) == angles[idx]:
                taken.add(idx)
    return taken


def _avoid_sibling_versions(rotation, title, data):
    """다른 과정이 지금 쓰고 있는 버전과 겹치지 않게 로테이션을 앞으로 밉니다.
    후보 순서: 이번 차례 → 다음 → … → 자기 직전 버전(마지막). 모두 쓰이고 있으면 원래 차례."""
    n = len(_variants(data))
    if n <= 1:
        return rotation
    did = _data_id(data)
    key = _norm_title(title)
    chosen = _run_choices.setdefault(did, {})
    taken = {i for t, i in chosen.items() if t != key} | _sibling_versions(title, data)
    final = rotation
    for step in range(n):
        if (rotation + step) % n not in taken:
            final = rotation + step
            break
    chosen[key] = final % n
    return final


def _select_variant(data, title):
    """(버전 번호(0부터), 버전 dict, 전체 버전 수)를 반환합니다."""
    vs = _variants(data)
    if len(vs) == 1 or not title:
        return 0, vs[0], len(vs)
    idx = _rotation_for(title, data) % len(vs)
    return idx, vs[idx], len(vs)


def _variant_text(field, title, key, year=None):
    """선택된 버전에서 key 본문을 꺼냅니다. 버전에 없으면 기본값으로 폴백."""
    if year is None:
        year = datetime.now().year
    data = get_field_research(field, title)
    if not data:
        return None
    _, v, _ = _select_variant(data, title)
    text = v.get(key)
    if not isinstance(text, str):      # 버전에 없거나 형식이 잘못된 키 → 기본 버전 사용
        text = data.get(key)
    if not isinstance(text, str):
        return None
    return text.replace("{year}", str(year))


def get_variant_info(field, title=None):
    """작업 가이드 표시용 버전 정보를 반환합니다.

    Returns:
        {"index": 1부터, "total": 전체 버전 수, "angle": 앵글명,
         "updated_at": 리서치 갱신일, "marker": 작업 가이드 표식 문자열}
        리서치 데이터가 없으면 None
    """
    data = get_field_research(field, title)
    if not data:
        return None
    idx, v, total = _select_variant(data, title)
    angle = _angle_of(data, idx, v)
    updated_at = str(data.get("updated_at", "") or "미기재")
    info = {
        "index": idx + 1,
        "total": total,
        "angle": angle,
        "updated_at": updated_at,
    }
    info["marker"] = VARIANT_MARKER_FORMAT.format(**info)
    return info


def get_empathy_hooks(field, title=None):
    """
    분야별 공감형 도입부 후보 목록을 반환합니다.
    title이 주어지면 서브필드(예: "드론영상")를 먼저 찾습니다.
    """
    data = get_field_research(field, title)
    if data and "empathy_hooks" in data:
        return data["empathy_hooks"]
    return None


def get_seo_section(field, year=None, title=None):
    """
    분야별 SEO 섹션 본문을 반환합니다.
    title이 주어지면 서브필드를 먼저 찾습니다.
    section_variants가 있으면 이번 생성 차례의 버전 본문을 돌려줍니다 (v3).
    """
    return _variant_text(field, title, "seo_section_body", year)


def get_intro_context(field, year=None, title=None):
    """
    도입부(들어가며) 확장 단락을 반환합니다.

    공감형 훅(empathy_hooks) 뒤에 이어붙일 맥락 단락으로,
    '왜 이 과정이 필요한가'를 독자 관점에서 풀어씁니다.
    데이터·수치 나열은 SEO 섹션(seo_section_body)이 담당하므로
    여기서는 중복을 피하고 문제의식 중심으로 서술합니다.
    section_variants가 있으면 SEO 섹션과 같은 버전을 씁니다 (v3).
    """
    return _variant_text(field, title, "intro_context", year)


def get_training_need(field, year=None, title=None):
    """
    '왜 배워야 할까요?' 섹션의 두 번째 블록(훈련 필요성)을 반환합니다.

    seo_section_body가 산업 동향을 다룬다면,
    training_need_body는 '그래서 왜 이 훈련인가'를 다룹니다.
    section_variants가 있으면 SEO 섹션과 같은 버전을 씁니다 (v3).
    """
    return _variant_text(field, title, "training_need_body", year)


def get_skill_explanations(field, title=None):
    """
    훈련목표 키워드 → 해설 문장 매핑을 반환합니다.

    generate_blog._build_goal_explanation()이 이 딕셔너리를 사용해
    Work24에서 파싱한 trainingGoal 원문에 자체 해설을 붙입니다.

    Returns:
        dict {키워드: 해설문장} 또는 None
    """
    data = get_field_research(field, title)
    if data and "skill_explanations" in data:
        return data["skill_explanations"]
    return None


def get_education_trends(field, key=None, title=None):
    """
    분야별 교육 트렌드를 반환합니다.

    Args:
        field: 분야명
        key: "key_skills" | "career_paths" | "certification_note" (None이면 전체)
        title: 서브필드 매칭용 과정 제목
    """
    data = get_field_research(field, title)
    if not data or "education_trends" not in data:
        return None
    if key:
        return data["education_trends"].get(key)
    return data["education_trends"]


def get_instagram_keyword_sentence(field, year=None, title=None):
    """
    인스타그램 캡션에 삽입할 키워드 문장을 반환합니다.
    title이 주어지면 서브필드를 먼저 찾습니다.
    section_variants가 있으면 블로그와 같은 버전을 씁니다 (v3).
    """
    return _variant_text(field, title, "instagram_keyword_sentence", year)


def get_market_data(field, key=None):
    """
    분야별 시장 데이터를 반환합니다.

    Args:
        field: 분야명
        key: 특정 데이터 키 (None이면 전체 dict 반환)

    Returns:
        str, dict 또는 None
    """
    data = get_field_research(field)
    if not data or "market_data" not in data:
        return None
    if key:
        return data["market_data"].get(key)
    return data["market_data"]


def get_jeju_data(field, key=None):
    """분야별 제주 특화 데이터를 반환합니다."""
    data = get_field_research(field)
    if not data or "jeju_data" not in data:
        return None
    if key:
        return data["jeju_data"].get(key)
    return data["jeju_data"]


def has_research(field):
    """해당 분야에 리서치 캐시가 있는지 확인합니다."""
    return get_field_research(field) is not None


def list_researched_fields():
    """리서치 데이터가 있는 분야 목록을 반환합니다."""
    cache = _load_cache()
    return [k for k in cache.keys() if k != "_meta"]


def invalidate_cache():
    """메모리 캐시를 무효화합니다. 파일 갱신 후 호출."""
    global _cache
    _cache = None
    _rotation_memo.clear()
    _run_choices.clear()
