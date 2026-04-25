"""
reels_v2_helper.py - Grok 영상 v2 패키지 생성 모듈

가이드 v2 (3 segments × 10s, Grok 네이티브 한국어 음성, 컷 전환) 기반.
video_profiles_v2.json 프로파일을 로드하고 훈련과정 데이터로 치환해
Grok 프롬프트 세트(.md) + 메타데이터(.json)를 출력한다.

사용:
    from reels_v2_helper import generate_reels_v2_package

    course = {
        "title": "배송형 드론 운용 전문가 과정",
        "start_date": "2026-05-01",
        # ... 기타 표준 course 필드
    }
    paths = generate_reels_v2_package(course, field_key="드론배송", output_dir="output")

출력 파일:
    - grok_prompts_v2_{safe_name}.md  : Grok에 입력할 8-블록 프롬프트 세트
    - reels_metadata_v2_{safe_name}.json : 평가 로그 추적용 메타데이터
"""

import json
import os
from datetime import datetime
from typing import Optional

from reels_validators import validate_v2_prompt_full


PROFILES_PATH = os.path.join(os.path.dirname(__file__), "video_profiles_v2.json")


# ── 프로파일 로딩 ───────────────────────────────────────────────
def load_v2_profile(field_key: str) -> dict:
    """video_profiles_v2.json에서 분야별 프로파일 로드.

    Args:
        field_key: 분야 키 (예: "드론배송", "조경", "지게차" 등)

    Returns:
        해당 분야의 프로파일 dict

    Raises:
        FileNotFoundError: video_profiles_v2.json 파일이 없을 때
        KeyError: 해당 field_key가 프로파일에 없을 때
    """
    if not os.path.exists(PROFILES_PATH):
        raise FileNotFoundError(
            f"v2 프로파일 파일을 찾을 수 없습니다: {PROFILES_PATH}"
        )

    with open(PROFILES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    profiles = data.get("profiles", {})
    if field_key not in profiles:
        available = list(profiles.keys())
        raise KeyError(
            f"'{field_key}' 프로파일이 없습니다. 사용 가능한 분야: {available}"
        )

    profile = profiles[field_key]
    profile["_meta"] = data.get("_meta", {})  # UI settings 등 메타 정보 첨부
    profile["_field_key"] = field_key
    return profile


def detect_v2_field_key(course_title: str, ncs_cd: Optional[str] = None) -> Optional[str]:
    """과정 제목에서 v2 프로파일 키 자동 감지.

    video_profiles_v2.json의 각 프로파일에 정의된 title_keywords를
    제목과 매칭해 가장 적합한 분야 키를 반환.

    Args:
        course_title: 훈련과정 제목
        ncs_cd: NCS 코드 (현재 미사용, 향후 확장 여지)

    Returns:
        매칭된 v2 프로파일 키 (예: "드론배송"), 없으면 None
    """
    if not os.path.exists(PROFILES_PATH):
        return None
    with open(PROFILES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    profiles = data.get("profiles", {})
    title_upper = course_title.upper()

    # 키워드 매칭 — 더 길고 구체적인 키워드를 우선 매칭
    candidates = []
    for field_key, profile in profiles.items():
        for kw in profile.get("title_keywords", []):
            if kw.upper() in title_upper:
                candidates.append((len(kw), field_key))
                break  # 같은 분야 내에서는 한 번만

    if not candidates:
        return None
    # 가장 긴 키워드로 매칭된 분야 우선 (구체성 우선)
    candidates.sort(reverse=True)
    return candidates[0][1]


# ── 프롬프트 렌더링 ─────────────────────────────────────────────
def _render_segment_prompt(seg: dict, segment_role: str) -> str:
    """세그먼트 데이터를 Grok에 입력할 8-블록 프롬프트 텍스트로 렌더.

    가이드 v2.4 기준 8-블록 구조:
        [IMAGE REFERENCE] / [TRANSITION NOTE] (옵션) /
        [SCENE & LOCATION] / [CAMERA & FRAMING] /
        [SUBJECTS & WARDROBE] / [ACTION & MOVEMENT] /
        [LIGHTING & MOOD] / [AUDIO & NARRATION] / [CUT RULES]
    """
    lines = []

    if seg.get("image_reference_en"):
        lines.append("[IMAGE REFERENCE]")
        lines.append(seg["image_reference_en"])
        lines.append("")

    if seg.get("transition_note_en"):
        lines.append("[TRANSITION NOTE]")
        lines.append(seg["transition_note_en"])
        lines.append("")

    lines.append("[SCENE & LOCATION]")
    lines.append(seg["scene_location_en"])
    lines.append("")

    lines.append("[CAMERA & FRAMING]")
    lines.append(seg["camera_framing_en"])
    lines.append("")

    lines.append("[SUBJECTS & WARDROBE]")
    lines.append(seg["subjects_wardrobe_en"])
    lines.append("")

    lines.append("[ACTION & MOVEMENT]")
    lines.append(seg["action_movement_en"])
    lines.append("")

    lines.append("[LIGHTING & MOOD]")
    lines.append(seg["lighting_mood_en"])
    lines.append("")

    lines.append("[AUDIO & NARRATION]")
    lines.append(seg["audio_narration_directive_en"])
    lines.append("")

    # 한국어 나레이션 또는 대사
    if segment_role == "cta":
        if seg.get("_resolved_dialogue_kr"):
            lines.append("Korean dialogue:")
            lines.append(f'"{seg["_resolved_dialogue_kr"]}"')
            lines.append("")
    else:
        if seg.get("narration_kr"):
            lines.append("Korean narration:")
            lines.append(f'"{seg["narration_kr"]}"')
            lines.append("")

    lines.append("[CUT RULES]")
    lines.append(seg["cut_rules_en"])

    return "\n".join(lines)


def _resolve_cta_dialogue(profile: dict, course: dict) -> str:
    """CTA 세그먼트의 dialogue_kr_template을 course 정보로 치환."""
    template = profile["segments"]["3_cta"].get(
        "dialogue_kr_template",
        "{course_title}, {start_date} 개강! 내일배움카드로 지금 신청하세요!",
    )
    course_title = course.get("title", "본 과정")
    start_date = course.get("start_date") or course.get("period") or "곧"

    return template.format(course_title=course_title, start_date=start_date)


# ── 마크다운 출력 ───────────────────────────────────────────────
def _build_markdown(profile: dict, course: dict, segment_prompts: dict) -> str:
    """완성된 프롬프트 세트를 마크다운으로 조립."""
    field_key = profile["_field_key"]
    course_title = course.get("title", "(과정명 미정)")
    start_date = course.get("start_date") or course.get("period") or "(개강일 미정)"
    ui = profile.get("_meta", {}).get("ui_settings", {})

    md = []
    md.append(f"# Grok 프롬프트 세트: {course_title}")
    md.append("")
    md.append(f"**v2 자동 생성 — 분야: {field_key}**")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 과정 요약")
    md.append("")
    md.append("| 항목 | 값 |")
    md.append("|---|---|")
    md.append(f"| 분야 | {field_key} |")
    md.append(f"| 과정명 | {course_title} |")
    md.append(f"| 개강일 | {start_date} |")
    md.append(f"| 훈련 맥락 | {profile.get('training_context_label', '-')} |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Grok UI 사전 설정")
    md.append("")
    md.append(f"- **비율**: {ui.get('aspect_ratio', '9:16')}")
    md.append(f"- **세그먼트 길이**: {ui.get('duration_per_segment_sec', 10)}초")
    md.append("- **이미지 업로드**: 세그먼트별 레퍼런스 이미지 (각 세그먼트 [IMAGE REFERENCE] 블록 참고)")
    md.append("")
    md.append("---")
    md.append("")

    # 각 세그먼트 출력
    role_titles = {
        "1_hook": ("세그먼트 1 — 훅 (0–10초)", "hook"),
        "2_demo": ("세그먼트 2 — 시연 (10–20초)", "demo"),
        "3_cta": ("세그먼트 3 — CTA (20–30초)", "cta"),
    }

    for seg_key, (title, _role) in role_titles.items():
        md.append(f"## {title}")
        md.append("")
        md.append("```")
        md.append(segment_prompts[seg_key])
        md.append("```")
        md.append("")

    md.append("---")
    md.append("")
    md.append("## 생성·편집 워크플로우")
    md.append("")
    md.append("1. Grok UI에서 9:16 / 10초 설정")
    md.append("2. 권장 생성 순서: **세그먼트 3 → 1 → 2** (CTA 립싱크 실패 여부를 먼저 확인)")
    md.append("3. 각 세그먼트 결과물을 Vrew에서 임포트해 하드 컷으로 이어붙임")
    md.append("4. Vrew에서 자막·오디오 균일화 등 후반 작업 (자막 가이드는 별도 작성 안 함)")
    md.append("")

    return "\n".join(md)


# ── 메인 함수 ──────────────────────────────────────────────────
def generate_reels_v2_package(
    course: dict,
    field_key: str,
    output_dir: str = "output",
) -> dict:
    """훈련과정 + 분야 키 입력으로 v2 Grok 프롬프트 세트와 메타데이터 생성.

    Args:
        course: 훈련과정 dict (title, start_date 등 표준 필드)
        field_key: video_profiles_v2.json의 프로파일 키 (예: "드론배송")
        output_dir: 출력 디렉토리

    Returns:
        생성된 파일 경로를 담은 dict
            {
                "prompts_md": "...",
                "metadata_json": "...",
                "validation_issues": [...]  # 검증 결과 (빈 리스트=통과)
            }
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. 프로파일 로드
    profile = load_v2_profile(field_key)

    # 2. CTA 대사 치환
    resolved_dialogue = _resolve_cta_dialogue(profile, course)
    profile["segments"]["3_cta"]["_resolved_dialogue_kr"] = resolved_dialogue

    # 3. 각 세그먼트 프롬프트 렌더링
    segment_prompts = {}
    role_map = {"1_hook": "hook", "2_demo": "demo", "3_cta": "cta"}
    for seg_key, role in role_map.items():
        seg_data = profile["segments"][seg_key]
        segment_prompts[seg_key] = _render_segment_prompt(seg_data, role)

    # 4. 검증 (모든 세그먼트)
    all_issues = []
    for seg_key, role in role_map.items():
        seg_data = profile["segments"][seg_key]
        narration_or_dialogue = (
            seg_data.get("_resolved_dialogue_kr")
            if role == "cta"
            else seg_data.get("narration_kr", "")
        )
        issues = validate_v2_prompt_full(
            segment_prompts[seg_key],
            narration_kr=narration_or_dialogue,
            segment_role=role,
        )
        for issue in issues:
            all_issues.append({"segment": seg_key, "issue": issue})

    # 5. 마크다운 조립
    markdown = _build_markdown(profile, course, segment_prompts)

    # 6. 파일 출력
    safe_name = course.get("title", "course")[:30].replace(" ", "_").replace("/", "_")
    md_path = os.path.join(output_dir, f"grok_prompts_v2_{safe_name}.md")
    metadata_path = os.path.join(output_dir, f"reels_metadata_v2_{safe_name}.json")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    metadata = {
        "course_id": course.get("id") or safe_name,
        "course_title": course.get("title"),
        "start_date": course.get("start_date") or course.get("period"),
        "field": field_key,
        "training_context": profile.get("training_context_label"),
        "generated_at": datetime.now().isoformat(),
        "schema_version": profile.get("_meta", {}).get("schema_version"),
        "ui_settings": profile.get("_meta", {}).get("ui_settings", {}),
        "narration": {
            "1_hook": profile["segments"]["1_hook"].get("narration_kr"),
            "2_demo": profile["segments"]["2_demo"].get("narration_kr"),
            "3_cta_dialogue": resolved_dialogue,
        },
        "explicit_negations": {
            seg_key: profile["segments"][seg_key].get("explicit_negations", [])
            for seg_key in role_map
        },
        "image_reference_hints": {
            seg_key: profile["segments"][seg_key].get("image_reference_filename_hint")
            for seg_key in role_map
        },
        "validation": {
            "passed": len(all_issues) == 0,
            "issue_count": len(all_issues),
            "issues": all_issues,
        },
        "evaluation_log": [],  # 영상 결과물 평가 결과를 누적할 자리 (장기 로드맵 4.3)
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return {
        "prompts_md": md_path,
        "metadata_json": metadata_path,
        "validation_issues": all_issues,
    }


# ── CLI 테스트 ──────────────────────────────────────────────────
if __name__ == "__main__":
    test_course = {
        "id": "TEST_DRONE_2026Q2",
        "title": "배송형 드론 운용 전문가 과정",
        "start_date": "5월 1일",
    }
    result = generate_reels_v2_package(
        test_course,
        field_key="드론배송",
        output_dir="./test_output",
    )
    print(f"✅ 프롬프트 마크다운: {result['prompts_md']}")
    print(f"✅ 메타데이터 JSON: {result['metadata_json']}")
    if result["validation_issues"]:
        print(f"⚠️  검증 이슈 {len(result['validation_issues'])}개:")
        for item in result["validation_issues"]:
            print(f"  [{item['segment']}] {item['issue']}")
    else:
        print("✅ 검증 통과")
