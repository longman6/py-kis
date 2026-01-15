# PyKIS - KIS API Reference

**국내 주식 전용**

---

## 1. 기본 정보

### Base URL

| 환경 | URL |
|------|-----|
| 실전투자 | https://openapi.koreainvestment.com:9443 |
| 모의투자 | https://openapivts.koreainvestment.com:29443 |

### 공통 헤더

```
authorization: Bearer {access_token}
appkey: {APP_KEY}
appsecret: {APP_SECRET}
tr_id: {TR_ID}
Content-Type: application/json; charset=utf-8
```

### 응답 형식

```json
{
    "rt_cd": "0",        // "0": 성공, "-1": 실패
    "msg_cd": "0000",
    "msg1": "정상처리",
    "output": { ... }    // 결과 데이터
}
```

---

## 2. 인증 API

### 토큰 발급

**POST** `/oauth2/tokenP`

```json
// Request
{
    "grant_type": "client_credentials",
    "appkey": "{APP_KEY}",
    "appsecret": "{APP_SECRET}"
}

// Response
{
    "access_token": "eyJ0eXAi...",
    "token_type": "Bearer",
    "expires_in": 86400
}
```

---

## 3. 시세 API

### 3.1 현재가 조회

**GET** `/uapi/domestic-stock/v1/quotations/inquire-price`

**TR_ID:** `FHKST01010100`

**Parameters:**
```
FID_COND_MRKT_DIV_CODE: "J"
FID_INPUT_ISCD: "005930"
```

**Response (주요 필드):**
```json
{
    "output": {
        "stck_prpr": "57500",       // 현재가
        "stck_oprc": "57000",       // 시가
        "stck_hgpr": "58000",       // 고가
        "stck_lwpr": "56500",       // 저가
        "acml_vol": "15000000",     // 거래량
        "prdy_vrss": "500",         // 전일대비
        "prdy_vrss_sign": "2",      // 부호 (2:상승, 5:하락)
        "prdy_ctrt": "0.88",        // 등락률
        "hts_kor_isnm": "삼성전자"  // 종목명
    }
}
```

**prdy_vrss_sign:**
- `"1"`: 상한
- `"2"`: 상승
- `"3"`: 보합
- `"4"`: 하한
- `"5"`: 하락

---

### 3.2 호가 조회

**GET** `/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn`

**TR_ID:** `FHKST01010200`

**Response (주요 필드):**
```json
{
    "output1": {
        "askp1": "57500",        // 매도1호가
        "askp2": "57600",
        // ... askp3 ~ askp10
        "bidp1": "57400",        // 매수1호가
        "bidp2": "57300",
        // ... bidp3 ~ bidp10
        "askp_rsqn1": "25000",   // 매도1호가 잔량
        "bidp_rsqn1": "50000"    // 매수1호가 잔량
    }
}
```

---

### 3.3 일별 시세 (OHLCV)

**GET** `/uapi/domestic-stock/v1/quotations/inquire-daily-price`

**TR_ID:** `FHKST01010400`

**Parameters:**
```
FID_COND_MRKT_DIV_CODE: "J"
FID_INPUT_ISCD: "005930"
FID_INPUT_DATE_1: ""           // 시작일 (YYYYMMDD)
FID_INPUT_DATE_2: ""           // 종료일
FID_PERIOD_DIV_CODE: "D"       // D:일, W:주, M:월
FID_ORG_ADJ_PRC: "0"           // 0:수정주가
```

**Response:**
```json
{
    "output2": [
        {
            "stck_bsop_date": "20260114",  // 일자
            "stck_oprc": "57000",          // 시가
            "stck_hgpr": "58000",          // 고가
            "stck_lwpr": "56500",          // 저가
            "stck_clpr": "57500",          // 종가
            "acml_vol": "15000000"         // 거래량
        }
    ]
}
```

---

## 4. 주문 API

### 4.1 주문 (매수/매도)

**POST** `/uapi/domestic-stock/v1/trading/order-cash`

**TR_ID:**
| 구분 | 실전 | 모의 |
|------|------|------|
| 매수 | TTTC0802U | VTTC0802U |
| 매도 | TTTC0801U | VTTC0801U |

**Request:**
```json
{
    "CANO": "12345678",        // 계좌번호 앞 8자리
    "ACNT_PRDT_CD": "01",      // 계좌번호 뒤 2자리
    "PDNO": "005930",          // 종목코드
    "ORD_DVSN": "00",          // 주문구분
    "ORD_QTY": "10",           // 주문수량
    "ORD_UNPR": "57000"        // 주문가격 (시장가시 "0")
}
```

**ORD_DVSN (주문구분):**
- `"00"`: 지정가
- `"01"`: 시장가

**Response:**
```json
{
    "output": {
        "ODNO": "0000123456",   // 주문번호
        "ORD_TMD": "090000"     // 주문시각
    }
}
```

---

### 4.2 주문 취소

**POST** `/uapi/domestic-stock/v1/trading/order-rvsecncl`

**TR_ID:**
| 구분 | 실전 | 모의 |
|------|------|------|
| 정정/취소 | TTTC0803U | VTTC0803U |

**Request:**
```json
{
    "CANO": "12345678",
    "ACNT_PRDT_CD": "01",
    "KRX_FWDG_ORD_ORGNO": "",
    "ORGN_ODNO": "0000123456",   // 원주문번호
    "ORD_DVSN": "00",
    "RVSE_CNCL_DVSN_CD": "02",   // 02:취소
    "ORD_QTY": "0",
    "ORD_UNPR": "0",
    "QTY_ALL_ORD_YN": "Y"
}
```

---

### 4.3 미체결 조회

**GET** `/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl`

**TR_ID:**
| 실전 | 모의 |
|------|------|
| TTTC8036R | VTTC8036R |

**Parameters:**
```
CANO: "12345678"
ACNT_PRDT_CD: "01"
CTX_AREA_FK100: ""
CTX_AREA_NK100: ""
INQR_DVSN_1: "0"     // 0:전체, 1:매도, 2:매수
INQR_DVSN_2: "0"
```

**Response:**
```json
{
    "output": [
        {
            "odno": "0000123456",        // 주문번호
            "pdno": "005930",            // 종목코드
            "prdt_name": "삼성전자",     // 종목명
            "sll_buy_dvsn_cd": "02",     // 01:매도, 02:매수
            "ord_qty": "10",             // 주문수량
            "ord_unpr": "57000",         // 주문가격
            "tot_ccld_qty": "0",         // 체결수량
            "psbl_qty": "10"             // 취소가능수량
        }
    ]
}
```

---

## 5. 계좌 API

### 5.1 잔고 조회

**GET** `/uapi/domestic-stock/v1/trading/inquire-balance`

**TR_ID:**
| 실전 | 모의 |
|------|------|
| TTTC8434R | VTTC8434R |

**Parameters:**
```
CANO: "12345678"
ACNT_PRDT_CD: "01"
AFHR_FLPR_YN: "N"
OFL_YN: ""
INQR_DVSN: "02"
UNPR_DVSN: "01"
FUND_STTL_ICLD_YN: "N"
FNCG_AMT_AUTO_RDPT_YN: "N"
PRCS_DVSN: "00"
CTX_AREA_FK100: ""
CTX_AREA_NK100: ""
```

**Response:**

**output1 (보유종목):**
```json
{
    "output1": [
        {
            "pdno": "005930",              // 종목코드
            "prdt_name": "삼성전자",       // 종목명
            "hldg_qty": "100",             // 보유수량
            "pchs_avg_pric": "55000.0000", // 평균매입가
            "prpr": "57500",               // 현재가
            "evlu_amt": "5750000",         // 평가금액
            "evlu_pfls_amt": "250000",     // 평가손익
            "evlu_pfls_rt": "4.55"         // 수익률
        }
    ]
}
```

**output2 (요약):**
```json
{
    "output2": [
        {
            "dnca_tot_amt": "50000000",      // 예수금
            "prvs_rcdl_excc_amt": "50000000", // 주문가능금액
            "tot_evlu_amt": "55750000",      // 총평가금액
            "evlu_pfls_smtl_amt": "250000",  // 총평가손익
            "asst_icdc_erng_rt": "0.45"      // 수익률
        }
    ]
}
```

---

## 6. 에러 코드

| 코드 | 설명 |
|------|------|
| EGW00001 | 인증 실패 |
| EGW00002 | 토큰 만료 |
| OPSP0001 | 잔고 부족 |
| OPSP0010 | 장 마감 |

---

## 7. Rate Limit

- 초당 최대 **20건** 요청
- 초과 시 HTTP 429 응답
