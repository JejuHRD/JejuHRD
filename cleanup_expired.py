"""
만료 콘텐츠 자동 정리 - 훈련시작일이 지난 과정의 output 파일을 삭제합니다.

사용법:
  python cleanup_expired.py              # 실제 삭제 실행
  python cleanup_expired.py --dry-run    # 삭제 대상만 미리보기 (실제 삭제 안 함)
  python cleanup_expired.py --grace 7    # 시작일 + 7일까지 유지 (기본: 0일)

GitHub Actions에서 pipeline.py 실행 전에 호출하면 자동 정리됩니다.
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta

OUTPUT_DIR = "output"
PROCESSED_FILE = os.path.join(OUTPUT_DIR, ".processed_courses.json")


def parse_start_date(entry):
    """
    processed_courses 항목에서 훈련시작일을 추출합니다.
    
    시도 순서:
    1. period 필드에서 "YYYY.MM.DD ~ ..." 파싱
    2. course_key에서 날짜 패턴 추출 (YYYYMMDD)
    """
    # period 필드: "2025.06.01 ~ 2025.09.30"
    period = entry.get("period", "")
    if period:
        match = re.match(r"(\d{4})\.(\d{2})\.(\d{2})", period)
        if match:
            try:
                return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            except ValueError:
                pass

    return None


def parse_start_date_from_key(course_key):
    """course_key에서 훈련시작일 추출 (fallback)
    
    키 형식: {trprId}_{trprDegr}_{traStartDate}_{traEndDate}
    traStartDate는 보통 YYYYMMDD 형식
    """
    parts = course_key.split("_")
    for part in parts:
        if re.match(r"^\d{8}$", part):
            try:
                return datetime.strptime(part, "%Y%m%d")
            except ValueError:
                continue
    return None


def load_processed():
    """처리 완료된 과정 목록 로드"""
    if not os.path.exists(PROCESSED_FILE):
        print("  ℹ️  .processed_courses.json 파일이 없습니다. 정리할 항목 없음.")
        return None
    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def collect_files_to_delete(entry):
    """entry의 files 딕셔너리에서 삭제할 파일 경로 목록을 수집"""
    files_to_delete = []
    files_info = entry.get("files", {})

    for key, value in files_info.items():
        if value is None:
            continue
        if isinstance(value, str):
            files_to_delete.append(value)
        elif isinstance(value, list):
            files_to_delete.extend([v for v in value if isinstance(v, str)])

    return files_to_delete


def cleanup_expired(grace_days=0, dry_run=False):
    """
    훈련시작일이 지난 과정의 콘텐츠를 정리합니다.
    
    Args:
        grace_days: 시작일 이후 며칠간 유지할지 (기본 0 = 시작일 당일부터 삭제)
        dry_run: True면 삭제하지 않고 대상만 출력
    """
    processed = load_processed()
    if processed is None:
        return 0

    today = datetime.now()
    cutoff = today - timedelta(days=grace_days)

    print(f"\n  🧹 만료 콘텐츠 정리")
    print(f"  📅 기준일: {today.strftime('%Y-%m-%d')} (유예기간: {grace_days}일)")
    print(f"  📁 대상 디렉토리: {OUTPUT_DIR}/")
    if dry_run:
        print(f"  ⚠️  DRY RUN 모드 — 실제 삭제 없음\n")
    else:
        print()

    expired_keys = []
    deleted_files = 0
    kept_count = 0

    for course_key, entry in processed.items():
        # 시작일 파싱
        start_date = parse_start_date(entry)
        if start_date is None:
            start_date = parse_start_date_from_key(course_key)

        if start_date is None:
            print(f"  ⚠️  날짜 파싱 실패 (유지): {entry.get('title', course_key)[:40]}")
            kept_count += 1
            continue

        # 시작일이 cutoff 이전이면 만료
        if start_date < cutoff:
            title = entry.get("title", "제목 없음")[:40]
            period = entry.get("period", "기간 없음")
            files = collect_files_to_delete(entry)

            print(f"  🗑️  만료: {title}")
            print(f"      기간: {period} | 파일 {len(files)}개")

            if not dry_run:
                for fpath in files:
                    if os.path.exists(fpath):
                        try:
                            os.remove(fpath)
                            deleted_files += 1
                        except OSError as e:
                            print(f"      ❌ 삭제 실패: {fpath} ({e})")
                    else:
                        # 파일이 이미 없으면 카운트만
                        pass

            expired_keys.append(course_key)
        else:
            kept_count += 1

    # processed에서 만료 항목 제거
    if not dry_run and expired_keys:
        for key in expired_keys:
            del processed[key]
        with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
            json.dump(processed, f, ensure_ascii=False, indent=2)

    # 결과 요약
    print(f"\n  {'─' * 40}")
    if dry_run:
        print(f"  [DRY RUN] 삭제 예정: {len(expired_keys)}개 과정")
    else:
        print(f"  ✅ 삭제 완료: {len(expired_keys)}개 과정, {deleted_files}개 파일")
    print(f"  📌 유지 중: {kept_count}개 과정")
    print(f"  {'─' * 40}\n")

    return len(expired_keys)


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    grace_days = 0
    if "--grace" in sys.argv:
        try:
            idx = sys.argv.index("--grace") + 1
            grace_days = int(sys.argv[idx])
        except (IndexError, ValueError):
            print("  ❌ --grace 뒤에 숫자(일)를 지정하세요. 예: --grace 7")
            sys.exit(1)

    cleanup_expired(grace_days=grace_days, dry_run=dry_run)
