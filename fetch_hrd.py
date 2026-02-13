"""
고용24 훈련과정 API → JSON 변환 스크립트
GitHub Actions에서 30분마다 실행되어 data/programs.json을 갱신합니다.
"""

import urllib.request
import xml.etree.ElementTree as ET
import json
import os
from datetime import datetime, timezone, timedelta

API_URL = (
    "https://www.work24.go.kr/cm/openApi/call/hr/callOpenApiSvcInfo310L01.do"
    "?authKey=24e8735a-f4b5-4537-9527-73759314444a"
    "&returnType=XML&outType=1&pageNum=1&pageSize=100"
    "&srchTraArea1=50&crseTracseSe=C0102"
    "&sort=ASC&sortCol=TRNG_BGDE"
)

# 추출할 필드 목록
FIELDS = [
    "address",
    "subTitle",
    "title",
    "traStartDate",
    "traEndDate",
    "titleLink",
]

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "programs.json")


def fetch_and_parse():
    """API를 호출하고 XML을 파싱하여 딕셔너리 리스트로 반환"""
    req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        xml_bytes = resp.read()

    root = ET.fromstring(xml_bytes)

    # 반복 요소 자동 감지: 자식이 3개 이상이고 5회 이상 반복되는 태그
    tag_count = {}
    for elem in root.iter():
        tag = elem.tag
        tag_count[tag] = tag_count.get(tag, 0) + 1

    best_tag = None
    best_score = -1
    for tag, cnt in tag_count.items():
        if tag == root.tag:
            continue
        nodes = root.iter(tag)
        sample = []
        for i, n in enumerate(nodes):
            if i >= 10:
                break
            sample.append(n)
        if not sample:
            continue
        avg_kids = sum(len(list(n)) for n in sample) / len(sample)
        score = cnt + avg_kids * 50
        if avg_kids >= 3 and cnt >= 5 and score > best_score:
            best_tag = tag
            best_score = score

    if not best_tag:
        raise ValueError("반복 요소를 찾을 수 없습니다. API 응답을 확인하세요.")

    rows = []
    for item in root.iter(best_tag):
        row = {}
        for child in item:
            row[child.tag] = (child.text or "").strip()
        # 필요한 필드만 추출
        filtered = {f: row.get(f, "") for f in FIELDS}
        rows.append(filtered)

    return rows


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        rows = fetch_and_parse()
    except Exception as e:
        print(f"❌ API 호출 실패: {e}")
        # 기존 파일이 있으면 유지, 없으면 빈 배열 저장
        if os.path.exists(OUTPUT_FILE):
            print("ℹ️  기존 데이터를 유지합니다.")
            return
        rows = []

    # KST 타임스탬프
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)

    output = {
        "updated": now.strftime("%Y-%m-%d %H:%M"),
        "count": len(rows),
        "data": rows,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(rows)}건 저장 완료 → {OUTPUT_FILE}")
    print(f"   갱신 시각: {output['updated']}")


if __name__ == "__main__":
    main()
