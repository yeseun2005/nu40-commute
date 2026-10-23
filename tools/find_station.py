#!/usr/bin/env python3
"""
find_station.py — .env 에 넣을 역코드·호선·방향 값을 찾아 준다

    .venv/bin/python tools/find_station.py 공덕

1) 시간표용 STATION_CODE : 역 이름으로 호선별 역코드를 보여 준다
2) 실시간용 SUBWAY_ID / UPDN_LINE / LINE_HINT : 지금 그 역에 오는 열차들을 호선·방향별로 보여 준다
   (열차가 안 다니는 새벽에는 2번이 비어 있을 수 있어요)
인증키는 프로젝트 루트 .env 또는 host/.env 의 SEOUL_SUBWAY_KEY 를 씁니다. 키는 화면에 찍지 않습니다.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "host"))
from commute import read_env_file  # noqa: E402

import requests  # noqa: E402

CODE_URL = "http://openapi.seoul.go.kr:8088/{key}/json/SearchInfoBySubwayNameService/1/20/{name}"
REALTIME_URL = "http://swopenAPI.seoul.go.kr/api/subway/{key}/json/realtimeStationArrival/0/30/{name}"
LINES = {"1001": "1호선", "1002": "2호선", "1003": "3호선", "1004": "4호선", "1005": "5호선",
         "1006": "6호선", "1007": "7호선", "1008": "8호선", "1009": "9호선", "1063": "경의중앙선",
         "1065": "공항철도", "1075": "수인분당선", "1077": "신분당선"}


def main():
    if len(sys.argv) < 2:
        print("사용법: python tools/find_station.py 역이름   (예: 공덕)")
        return 1
    name = sys.argv[1].removesuffix("역")
    env = {}
    for p in (ROOT / ".env", ROOT / "host/.env"):
        env.update(read_env_file(p))
    key = env.get("SEOUL_SUBWAY_KEY", "").strip()
    if not key:
        print("SEOUL_SUBWAY_KEY 가 .env 에 없습니다.")
        return 1

    print(f"\n[1] '{name}' 역코드 (→ STATION_CODE)")
    try:
        body = requests.get(CODE_URL.format(key=key, name=name), timeout=10).json()
        for r in body.get("SearchInfoBySubwayNameService", {}).get("row", []):
            print(f"    {r.get('LINE_NUM'):>8}  STATION_CODE={r.get('STATION_CD')}")
    except Exception as e:
        print(f"    호출 실패: {type(e).__name__}")

    print(f"\n[2] 지금 '{name}'에 오는 열차 (→ SUBWAY_ID / UPDN_LINE / LINE_HINT)")
    try:
        rt_key = env.get("SEOUL_REALTIME_KEY", "").strip() or key
        body = requests.get(REALTIME_URL.format(key=rt_key, name=name), timeout=10).json()
        seen = set()
        for it in body.get("realtimeArrivalList") or []:
            sid = str(it.get("subwayId"))
            row = (sid, it.get("updnLine"), it.get("trainLineNm"))
            if row in seen:
                continue
            seen.add(row)
            print(f"    {LINES.get(sid, sid):>6}  SUBWAY_ID={sid}  UPDN_LINE={row[1]}  ({row[2]})")
        if not seen:
            print(f"    결과 없음: {body.get('message') or body.get('errorMessage')}")
    except Exception as e:
        print(f"    호출 실패: {type(e).__name__}")
    print("\nLINE_HINT 는 괄호 안 '○○방면' 부분을 그대로 쓰면 됩니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())