"""
삼성전자 분봉 데이터 수집 스크립트

어제부터 오늘까지의 분봉 데이터를 CSV로 저장합니다.
"""

import os
import csv
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env 로드
load_dotenv()

from pykis import KIS


def fetch_minute_data(kis, symbol: str, date: str, start_time: str = "153000") -> list:
    """
    특정 날짜/시간 기준으로 분봉 데이터를 조회합니다.
    
    Args:
        kis: KIS 클라이언트
        symbol: 종목 코드
        date: 날짜 (YYYYMMDD)
        start_time: 시작 시간 (HHMMSS)
    
    Returns:
        분봉 데이터 리스트
    """
    data = kis._http.get(
        "/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice",
        "FHKST03010200",
        params={
            "FID_ETC_CLS_CODE": "",
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol,
            "FID_INPUT_HOUR_1": start_time,
            "FID_PW_DATA_INCU_YN": "N",
        },
    )
    
    return data.get("output2", [])


def main():
    kis = KIS(
        app_key=os.getenv("KIS_APP_KEY"),
        app_secret=os.getenv("KIS_APP_SECRET"),
        account_no=os.getenv("KIS_ACCOUNT_NO"),
        is_paper=True,
    )
    
    # 모의투자 Rate Limit: 초당 2건
    delay = 0.6
    
    symbol = "005930"  # 삼성전자
    
    # 어제 날짜
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    today = datetime.now().strftime("%Y%m%d")
    
    print(f"삼성전자({symbol}) 분봉 데이터 수집 시작...")
    print(f"기간: {yesterday} ~ {today}")
    print()
    
    all_data = {}  # 중복 제거용
    
    try:
        # 여러 시간대로 나누어 조회 (장 시작~종료)
        # 장 시간: 09:00 ~ 15:30
        times = [
            "153000",  # 오늘 마감
            "140000",
            "120000",
            "100000",
            "093000",
        ]
        
        for start_time in times:
            print(f"시간 {start_time[:2]}:{start_time[2:4]} 기준 조회 중...")
            
            items = fetch_minute_data(kis, symbol, today, start_time)
            
            for item in items:
                date_str = item.get("stck_bsop_date", "")
                time_str = item.get("stck_cntg_hour", "")
                
                if date_str and time_str:
                    key = f"{date_str}_{time_str}"
                    all_data[key] = {
                        "datetime": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} {time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}",
                        "open": int(item.get("stck_oprc", 0)),
                        "high": int(item.get("stck_hgpr", 0)),
                        "low": int(item.get("stck_lwpr", 0)),
                        "close": int(item.get("stck_prpr", 0)),
                        "volume": int(item.get("cntg_vol", 0)),
                    }
            
            print(f"    -> {len(items)}개 조회, 현재까지 총 {len(all_data)}개")
            time.sleep(delay)
        
    except Exception as e:
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        kis.close()
    
    # 시간순 정렬
    sorted_data = sorted(all_data.values(), key=lambda x: x["datetime"])
    
    # CSV 저장
    output_file = "samsung_minute_ohlcv.csv"
    
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["datetime", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(sorted_data)
    
    print()
    print("=" * 50)
    print(f"저장 완료: {output_file}")
    if sorted_data:
        print(f"기간: {sorted_data[0]['datetime']} ~ {sorted_data[-1]['datetime']}")
        print(f"총 {len(sorted_data)}개 레코드")


if __name__ == "__main__":
    main()
