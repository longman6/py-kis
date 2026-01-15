import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 프로젝트 루트를 path에 추가하여 pykis 모듈을 찾을 수 있게 함
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/src")

from pykis import KIS

# .env 로드
load_dotenv()

def verify_minute_data():
    # KIS 클라이언트 초기화
    # 실전투자 계좌 정보가 필요함 (분봉 과거 조회는 실전만 가능)
    kis = KIS(
        app_key=os.getenv("KIS_APP_KEY"),
        app_secret=os.getenv("KIS_APP_SECRET"),
        account_no=os.getenv("KIS_ACCOUNT_NO"),
        is_paper=False
    )
    
    symbol = "005930" # 삼성전자
    
    # 한국 시간 기준 어제 날짜 계산 (UTC+9)
    kst_now = datetime.utcnow() + timedelta(hours=9)
    yesterday = kst_now - timedelta(days=1)
    target_date = yesterday.strftime("%Y%m%d")
    
    # 주말이면 금요일로 조정 (토=5, 일=6)
    if yesterday.weekday() == 5: # 토요일이면 하루 전(금)
        target_date = (yesterday - timedelta(days=1)).strftime("%Y%m%d")
    elif yesterday.weekday() == 6: # 일요일이면 이틀 전(금)
        target_date = (yesterday - timedelta(days=2)).strftime("%Y%m%d")

    print(f"검증 대상: {symbol} (삼성전자)")
    print(f"대상 날짜: {target_date}")
    print("데이터 요청 중... (이 과정은 API 호출 제한에 따라 시간이 걸릴 수 있습니다)")
    
    try:
        # 1분봉 조회
        ohlcv = kis.fetch_minute_ohlcv_range(symbol, target_date, interval=1)
        
        count = len(ohlcv)
        print(f"\n[검증 결과]")
        print(f"수신된 데이터 개수: {count}건 (예상치: 약 381건)")
        
        if count == 0:
            print("❌ 데이터가 없습니다.")
            return

        start_time = ohlcv[0].datetime.strftime("%H:%M:%S")
        end_time = ohlcv[-1].datetime.strftime("%H:%M:%S")
        
        print(f"시작 시간: {start_time}")
        print(f"종료 시간: {end_time}")
        
        # 갭 검사
        gaps = []
        expected_diff = timedelta(minutes=1)
        
        for i in range(1, count):
            prev = ohlcv[i-1].datetime
            curr = ohlcv[i].datetime
            diff = curr - prev
            
            if diff > expected_diff:
                gaps.append(f"{prev.strftime('%H:%M:%S')} -> {curr.strftime('%H:%M:%S')} (차이: {diff})")
        
        if gaps:
            print(f"\n❌ 발견된 시간 누락 구간 ({len(gaps)}건):")
            for gap in gaps:
                print(gap)
        else:
            print("\n✅ 시간 누락 구간이 없습니다. 데이터가 연속적입니다.")
            
        # 첫 데이터와 마지막 데이터 시간 검증
        # 09:00 ~ 09:05 사이 데이터가 있어야 함
        has_start = any("09:00" <= d.datetime.strftime("%H:%M") <= "09:05" for d in ohlcv)
        # 15:20 ~ 15:30 사이 데이터가 있어야 함
        has_end = any("15:20" <= d.datetime.strftime("%H:%M") <= "15:30" for d in ohlcv)
        
        if has_start:
            print("✅ 개장 초반(09:00~) 데이터 존재함")
        else:
            print("❌ 개장 초반 데이터 누락됨")
            
        if has_end:
            print("✅ 장 마감(15:30) 부근 데이터 존재함")
        else:
            print("❌ 장 마감 데이터 누락됨")

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        kis.close()

if __name__ == "__main__":
    verify_minute_data()
