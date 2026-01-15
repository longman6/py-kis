"""
삼성전자 일봉 데이터 수집 스크립트 (PyKIS 사용)

2020년 1월 1일부터 오늘까지의 일봉 데이터를 CSV로 저장합니다.
"""

import os
import csv
from dotenv import load_dotenv

# .env 로드
load_dotenv()

from pykis import KIS


def main():
    kis = KIS(
        app_key=os.getenv("KIS_APP_KEY"),
        app_secret=os.getenv("KIS_APP_SECRET"),
        account_no=os.getenv("KIS_ACCOUNT_NO"),
        is_paper=True,
    )
    
    symbol = "005930"  # 삼성전자
    
    print(f"삼성전자({symbol}) 일봉 데이터 수집 시작...")
    print("기간: 2020-01-01 ~ 오늘")
    print("(모의투자 Rate Limit으로 약 10초 소요)")
    print()
    
    try:
        # 2020년 1월 1일부터 오늘까지 조회
        ohlcv = kis.fetch_ohlcv_range(symbol, "20200101")
        
        print(f"수집 완료: {len(ohlcv)}개")
        
        # CSV 저장
        output_file = "samsung_daily_ohlcv.csv"
        
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "open", "high", "low", "close", "volume"])
            
            for o in ohlcv:
                writer.writerow([
                    o.datetime.strftime("%Y-%m-%d"),
                    int(o.open),
                    int(o.high),
                    int(o.low),
                    int(o.close),
                    o.volume,
                ])
        
        print()
        print(f"저장 완료: {output_file}")
        if ohlcv:
            print(f"기간: {ohlcv[0].datetime.strftime('%Y-%m-%d')} ~ {ohlcv[-1].datetime.strftime('%Y-%m-%d')}")
        
    finally:
        kis.close()


if __name__ == "__main__":
    main()
