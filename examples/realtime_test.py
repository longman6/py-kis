"""
PyKIS 실시간 시세 테스트

WebSocket을 통한 실시간 체결가 수신 테스트입니다.
5초간 실시간 시세를 수신합니다.
"""

import os
import asyncio
from dotenv import load_dotenv
from pykis import AsyncKIS


async def main():
    # .env 파일 로드
    load_dotenv()
    
    # 환경변수에서 설정 읽기
    app_key = os.getenv("KIS_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET")
    account_no = os.getenv("KIS_ACCOUNT_NO")
    is_paper = os.getenv("KIS_PAPER", "true").lower() == "true"
    
    if not app_key or not app_secret or not account_no:
        print("Error: .env 파일에 KIS_APP_KEY, KIS_APP_SECRET, KIS_ACCOUNT_NO를 설정하세요.")
        return
    
    mode = "모의투자" if is_paper else "실전투자"
    print(f"[{mode}] WebSocket 실시간 시세 테스트")
    print("=" * 50)
    print()
    
    async with AsyncKIS(
        app_key=app_key,
        app_secret=app_secret,
        account_no=account_no,
        is_paper=is_paper,
    ) as kis:
        
        symbol = "005930"  # 삼성전자
        print(f"종목: {symbol} (삼성전자)")
        print("5초간 실시간 체결가를 수신합니다...")
        print()
        
        # 5초간 실시간 시세 수신
        try:
            count = 0
            async for ticker in kis.watch_ticker(symbol):
                print(f"[{ticker.datetime.strftime('%H:%M:%S')}] "
                      f"현재가: {ticker.last:,.0f}원 "
                      f"({ticker.change_percent:+.2f}%) "
                      f"거래량: {ticker.volume:,}")
                count += 1
                
                # 5초 또는 10건 후 종료
                if count >= 10:
                    break
                    
        except asyncio.TimeoutError:
            print("타임아웃")
        except Exception as e:
            print(f"오류: {e}")
        
        print()
        print(f"수신 완료! ({count}건)")


if __name__ == "__main__":
    asyncio.run(main())
