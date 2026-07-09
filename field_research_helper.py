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
"""

import json
import os
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
    """
    if year is None:
        year = datetime.now().year
    data = get_field_research(field, title)
    if data and "seo_section_body" in data:
        body = data["seo_section_body"]
        return body.replace("{year}", str(year))
    return None


def get_intro_context(field, year=None, title=None):
    """
    도입부(들어가며) 확장 단락을 반환합니다.

    공감형 훅(empathy_hooks) 뒤에 이어붙일 맥락 단락으로,
    '왜 이 과정이 필요한가'를 독자 관점에서 풀어씁니다.
    데이터·수치 나열은 SEO 섹션(seo_section_body)이 담당하므로
    여기서는 중복을 피하고 문제의식 중심으로 서술합니다.
    """
    if year is None:
        year = datetime.now().year
    data = get_field_research(field, title)
    if data and "intro_context" in data:
        return data["intro_context"].replace("{year}", str(year))
    return None


def get_training_need(field, year=None, title=None):
    """
    '왜 배워야 할까요?' 섹션의 두 번째 블록(훈련 필요성)을 반환합니다.

    seo_section_body가 산업 동향을 다룬다면,
    training_need_body는 '그래서 왜 이 훈련인가'를 다룹니다.
    """
    if year is None:
        year = datetime.now().year
    data = get_field_research(field, title)
    if data and "training_need_body" in data:
        return data["training_need_body"].replace("{year}", str(year))
    return None


def get_instagram_keyword_sentence(field, year=None, title=None):
    """
    인스타그램 캡션에 삽입할 키워드 문장을 반환합니다.
    title이 주어지면 서브필드를 먼저 찾습니다.
    """
    if year is None:
        year = datetime.now().year
    data = get_field_research(field, title)
    if data and "instagram_keyword_sentence" in data:
        return data["instagram_keyword_sentence"].replace("{year}", str(year))
    return None


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
