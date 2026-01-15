"""
PyKIS 기본 사용 예제 (동기)

.env 파일에서 API 키를 로드합니다.

※ Rate Limit 유의:
  - 실전투자: 초당 20건 (1계좌당)
  - 모의투자: 초당 2건
"""

import os
import time
from dotenv import load_dotenv
from pykis import KIS


def main():
    # .env 파일 로드
    load_dotenv()
    
    # 환경변수에서 설정 읽기
    app_key = os.getenv("KIS_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET")
    account_no = os.getenv("KIS_ACCOUNT_NO")
    is_paper = os.getenv("KIS_PAPER", "true").lower() == "true"
    
    if not app_key or not app_secret or not account_no:
        print("Error: .env 파일에 KIS_APP_KEY, KIS_APP_SECRET, KIS_ACCOUNT_NO를 설정하세요.")
        print("       .env.example 파일을 참고하세요.")
        return
    
    # Rate Limit 설정 (모의투자: 초당 2건, 실전투자: 초당 20건)
    delay = 0.5 if is_paper else 0.05
    
    # 클라이언트 초기화
    kis = KIS(
        app_key=app_key,
        app_secret=app_secret,
        account_no=account_no,
        is_paper=is_paper,
    )
    
    mode = "모의투자" if is_paper else "실전투자"
    print(f"[{mode}] 계좌: {account_no}")
    print(f"Rate Limit: 초당 {2 if is_paper else 20}건 (딜레이: {delay}초)")
    print()

    # =========================================
    # 시세 조회
    # =========================================
    
    # 현재가
    ticker = kis.fetch_ticker("005930")
    print(f"=== {ticker.name} ({ticker.symbol}) ===")
    print(f"현재가: {ticker.last:,.0f}원")
    print(f"등락률: {ticker.change_percent:+.2f}%")
    print(f"거래량: {ticker.volume:,}주")
    print()
    
    time.sleep(delay)  # Rate Limit 대기

    # 호가
    ob = kis.fetch_order_book("005930")
    print("=== 호가 ===")
    print("매도호가:")
    for ask in ob.asks[:3]:
        print(f"  {ask.price:,.0f}원 - {ask.amount:,}주")
    print("매수호가:")
    for bid in ob.bids[:3]:
        print(f"  {bid.price:,.0f}원 - {bid.amount:,}주")
    print()
    
    time.sleep(delay)  # Rate Limit 대기

    # 일봉
    ohlcv = kis.fetch_ohlcv("005930", "1d", limit=5)
    print("=== 최근 5일 ===")
    for candle in ohlcv:
        print(f"{candle.datetime.strftime('%Y-%m-%d')}: "
              f"시{candle.open:,.0f} 고{candle.high:,.0f} "
              f"저{candle.low:,.0f} 종{candle.close:,.0f}")
    print()
    
    time.sleep(delay)  # Rate Limit 대기

    # =========================================
    # 잔고 조회
    # =========================================
    
    balance = kis.fetch_balance()
    print("=== 계좌 ===")
    print(f"총 평가: {balance.total:,.0f}원")
    print(f"예수금: {balance.deposit:,.0f}원")
    print(f"주문가능: {balance.free:,.0f}원")
    
    if balance.positions:
        print("\n보유 종목:")
        for pos in balance.positions:
            print(f"  {pos.name}: {pos.amount}주, {pos.unrealized_pnl_percent:+.2f}%")
    print()

    # =========================================
    # 주문 (주석 처리 - 실제 실행시 해제)
    # =========================================
    
    # time.sleep(delay)  # Rate Limit 대기
    # 
    # # 지정가 매수
    # order = kis.create_limit_order("005930", "buy", 10, 50000)
    # print(f"주문번호: {order.id}")
    # 
    # time.sleep(delay)  # Rate Limit 대기
    # 
    # # 미체결 조회
    # open_orders = kis.fetch_open_orders()
    # for o in open_orders:
    #     print(f"[{o.id}] {o.symbol} {o.side.value} {o.remaining}주 @ {o.price:,}원")
    # 
    # time.sleep(delay)  # Rate Limit 대기
    # 
    # # 주문 취소
    # kis.cancel_order(order.id, "005930")

    kis.close()


if __name__ == "__main__":
    main()


