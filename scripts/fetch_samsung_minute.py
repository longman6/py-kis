"""
삼성전자 분봉 데이터 수집 스크립트

특정 날짜의 분봉 데이터를 CSV로 저장합니다.
라이브러리의 fetch_minute_ohlcv_range 메서드를 사용합니다.

사용법:
    python scripts/fetch_samsung_minute.py [날짜]
    
예시:
    python scripts/fetch_samsung_minute.py 20260115
    python scripts/fetch_samsung_minute.py 2026-01-15
"""

import os
import sys
import csv
from datetime import datetime
from dotenv import load_dotenv

# .env 로드
load_dotenv()

from pykis import KIS


def main():
    # 날짜 인자 처리 (기본: 오늘)
    if len(sys.argv) > 1:
        target_date = sys.argv[1].replace("-", "")
    else:
        target_date = datetime.now().strftime("%Y%m%d")
    
    # 과거 분봉 조회는 실전투자만 가능
    kis = KIS(
        app_key=os.getenv("KIS_APP_KEY"),
        app_secret=os.getenv("KIS_APP_SECRET"),
        account_no=os.getenv("KIS_ACCOUNT_NO"),
        is_paper=False,
    )
    
    symbol = "005930"  # 삼성전자
    
    print(f"삼성전자({symbol}) 분봉 데이터 수집 시작...")
    print(f"대상 날짜: {target_date}")
    print()
    
    try:
        # 라이브러리의 fetch_minute_ohlcv_range 사용 (동적 시간 조회)
        ohlcv_list = kis.fetch_minute_ohlcv_range(symbol, target_date, target_date, interval=1)
        
        print(f"수집 완료: {len(ohlcv_list)}건")
        
        # 딕셔너리 리스트로 변환
        data_list = [
            {
                "datetime": o.datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "open": int(o.open),
                "high": int(o.high),
                "low": int(o.low),
                "close": int(o.close),
                "volume": int(o.volume),
            }
            for o in ohlcv_list
        ]
        
    except Exception as e:
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()
        data_list = []
    finally:
        kis.close()
    
    if not data_list:
        print("데이터가 없습니다.")
        return
    
    # CSV 저장
    output_file = f"samsung_minute_{target_date}.csv"
    
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["datetime", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(data_list)
    
    print()
    print("=" * 50)
    print(f"저장 완료: {output_file}")
    print(f"기간: {data_list[0]['datetime']} ~ {data_list[-1]['datetime']}")
    print(f"총 {len(data_list)}개 레코드")


if __name__ == "__main__":
    main()
