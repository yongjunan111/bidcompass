# BidCompass 시스템 아키텍처

## 1. 전체 시스템 구성도

```mermaid
graph TB
    subgraph EXTERNAL["외부 시스템"]
        G2B_API["🏛️ 나라장터 G2B API<br/>(3종 서비스)"]
        OPENAI["🤖 OpenAI API<br/>(GPT-4o-mini)"]
    end

    subgraph DOCKER["Docker Compose (3 컨테이너)"]
        subgraph SCHEDULER["📅 bidcompass_scheduler"]
            PIPELINE["run_all_pipelines.sh<br/>(24h 주기)"]
            P1["Stage 1<br/>공고 수집"]
            P2["Stage 2<br/>낙찰결과 수집"]
            P3["Stage 3<br/>계약정보 수집"]
            P4["Stage 4<br/>A값·기초금액 수집"]
            P5["Stage 5<br/>미확정 재확인"]
            PIPELINE --> P1 --> P2 --> P3 --> P4 --> P5
        end

        subgraph WEB["🌐 bidcompass_web (:8010)"]
            subgraph FRONTEND["Frontend — React 18 + TypeScript + Vite"]
                DASHBOARD["대시보드"]
                NOTICE_SEARCH["공고 검색"]
                RECOMMEND["추천 결과"]
                CALCULATOR["가격 계산기"]
                AI_REPORT_PAGE["AI 리포트"]
                HISTORY["분석 이력"]
            end

            subgraph API["API Layer — Django 6.0"]
                UI_API["ui_api.py<br/>(7개 JSON 엔드포인트)"]
            end

            subgraph ENGINE["규칙 엔진 (Service Layer)"]
                BID_ENGINE["bid_engine.py<br/>별표 판정 · 가격점수 · 하한율"]
                PREBID["prebid_recommend.py<br/>Safe / Base / Aggressive"]
                OPTIMAL["optimal_bid.py<br/>1,365 시나리오 최적화"]
                AI_REPORT["ai_report.py<br/>전략 리포트 생성"]
                STATS["report_stats.py<br/>유사공고 통계"]
            end

            subgraph SYNC["데이터 수집 모듈"]
                G2B_CLIENT["g2b_construction_client.py<br/>(httpx 비동기)"]
                G2B_SYNC["g2b_construction_sync.py<br/>(매핑 · 적재)"]
            end

            FRONTEND --> UI_API
            UI_API --> BID_ENGINE
            UI_API --> PREBID
            UI_API --> AI_REPORT
            UI_API --> STATS
            PREBID --> BID_ENGINE
            AI_REPORT --> OPENAI
        end

        subgraph DB["🗄️ bidcompass_db (:5434)"]
            PG["PostgreSQL 15"]
            subgraph TABLES["주요 테이블"]
                T_ANN["BidAnnouncement<br/>공고 104만건"]
                T_RES["BidResult<br/>낙찰결과 3,230만건"]
                T_CON["BidContract<br/>계약 89만건"]
                T_AVAL["BidApiAValue<br/>A값 (7항목)"]
                T_PREL["BidApiPrelimPrice<br/>복수예비가격"]
                T_LOG["BidApiCollectionLog<br/>수집 추적"]
            end
        end
    end

    G2B_API --> G2B_CLIENT
    G2B_CLIENT --> G2B_SYNC
    G2B_SYNC --> PG
    P1 & P2 & P3 & P4 & P5 --> G2B_CLIENT
    UI_API --> PG

    style EXTERNAL fill:#1a1a2e,stroke:#e94560,color:#fff
    style DOCKER fill:#0f0f23,stroke:#16213e,color:#fff
    style SCHEDULER fill:#1a1a3e,stroke:#e94560,color:#fff
    style WEB fill:#16213e,stroke:#0f3460,color:#fff
    style FRONTEND fill:#1a1a4e,stroke:#53a8b6,color:#fff
    style API fill:#1a2a3e,stroke:#53a8b6,color:#fff
    style ENGINE fill:#1a2a4e,stroke:#53a8b6,color:#fff
    style SYNC fill:#1a2a3e,stroke:#53a8b6,color:#fff
    style DB fill:#1a1a3e,stroke:#e94560,color:#fff
    style TABLES fill:#0f1a2e,stroke:#53a8b6,color:#fff
```

## 2. 규칙 엔진 상세 흐름

```mermaid
flowchart LR
    INPUT["입력<br/>공고번호"] --> LOOKUP["DB 조회<br/>예정가격 · A값<br/>기초금액"]

    LOOKUP --> TABLE["별표 판정<br/>select_table()"]
    TABLE --> |"추정가격 기준"| T1["TABLE_1<br/>300억↑"]
    TABLE --> |"추정가격 기준"| T2A["TABLE_2A<br/>50~300억"]
    TABLE --> |"추정가격 기준"| T3["TABLE_3<br/>30~50억"]
    TABLE --> |"추정가격 기준"| T4["TABLE_4<br/>10~30억"]
    TABLE --> |"추정가격 기준"| T5["TABLE_5<br/>~10억"]

    T1 & T2A & T3 & T4 & T5 --> SCORE["가격점수 산출<br/>calc_price_score()"]

    SCORE --> |"투찰률 → 구간 판정<br/>→ 배점 계산"| RESULT["가격점수<br/>(0~100점)"]

    RESULT --> FLOOR["하한율 체크<br/>get_floor_rate()"]
    FLOOR --> |"기준율 90%<br/>+2%p 상향(2026)"| PASS{통과?}
    PASS --> |Yes| STRATEGY["전략 산출<br/>prebid_recommend()"]
    PASS --> |No| FAIL["❌ 즉시 탈락"]

    STRATEGY --> SAFE["🟢 Safe<br/>하한율 여유 확보"]
    STRATEGY --> BASE["🟡 Base<br/>균형 (기준율 90%)"]
    STRATEGY --> AGG["🔴 Aggressive<br/>최대 점수 추구"]

    SAFE & BASE & AGG --> AI["AI 리포트<br/>GPT-4o-mini"]
    AI --> REPORT["📄 전략 리포트<br/>근거 · 리스크 · 대응"]

    style INPUT fill:#0f3460,stroke:#53a8b6,color:#fff
    style TABLE fill:#1a1a3e,stroke:#e94560,color:#fff
    style SCORE fill:#1a1a3e,stroke:#e94560,color:#fff
    style FLOOR fill:#1a1a3e,stroke:#e94560,color:#fff
    style STRATEGY fill:#16213e,stroke:#53a8b6,color:#fff
    style SAFE fill:#1b4332,stroke:#52b788,color:#fff
    style BASE fill:#3d3200,stroke:#ffd60a,color:#fff
    style AGG fill:#461220,stroke:#e5383b,color:#fff
    style AI fill:#1a1a4e,stroke:#7209b7,color:#fff
    style REPORT fill:#1a1a4e,stroke:#7209b7,color:#fff
    style FAIL fill:#461220,stroke:#e5383b,color:#fff
```

## 3. 데이터 수집 파이프라인

```mermaid
flowchart TB
    subgraph PIPELINE["📅 24시간 주기 파이프라인 (Docker Scheduler)"]
        direction TB
        S1["Stage 1 — fetch_announcements<br/>공고 수집 (최근 2일)"]
        S2["Stage 2 — fetch_winning_bids<br/>낙찰결과 수집 (최근 3일)"]
        S3["Stage 3 — fetch_contracts<br/>계약정보 보강 (최근 3일)"]
        S4["Stage 4 — collect_bid_api_data<br/>A값 · 기초금액 수집 (일 900건)"]
        S5["Stage 5 — retry_pending_inputs<br/>미확정 공고 재확인"]
        S1 --> S2 --> S3 --> S4 --> S5
    end

    subgraph G2B["🏛️ G2B API (3종)"]
        API1["BidPublicInfoService<br/>공고 + A값 + 기초금액"]
        API2["ScsbidInfoService<br/>낙찰결과"]
        API3["PubDataOpnStdService<br/>계약정보"]
    end

    subgraph DB["🗄️ PostgreSQL"]
        ANN["BidAnnouncement"]
        RES["BidResult"]
        CON["BidContract"]
        AVAL["BidApiAValue"]
        PREL["BidApiPrelimPrice"]
        LOG["BidApiCollectionLog"]
        JSON["📁 data/collected/<br/>JSON 원본 백업"]
    end

    S1 --> API1
    S2 --> API2
    S3 --> API3
    S4 --> API1
    S5 --> API1

    API1 --> ANN & AVAL & PREL & LOG
    API2 --> RES
    API3 --> CON
    API1 & API2 & API3 --> JSON

    subgraph STATUS["수집 상태 추적"]
        PENDING["pending<br/>미수집"]
        MISSING["checked_missing<br/>API에 없음"]
        CONFIRMED["confirmed<br/>수집 완료"]
        ERROR["error<br/>수집 실패"]
        PENDING --> CONFIRMED
        PENDING --> MISSING
        PENDING --> ERROR
    end

    style PIPELINE fill:#0f0f23,stroke:#e94560,color:#fff
    style G2B fill:#1a1a2e,stroke:#e94560,color:#fff
    style DB fill:#1a1a3e,stroke:#53a8b6,color:#fff
    style STATUS fill:#16213e,stroke:#ffd60a,color:#fff
```

## 4. 사용자 요청 흐름 (추천 API)

```mermaid
sequenceDiagram
    participant U as 👤 사용자
    participant F as ⚛️ React SPA
    participant A as 🐍 Django API
    participant E as ⚙️ 규칙 엔진
    participant DB as 🗄️ PostgreSQL
    participant GPT as 🤖 OpenAI

    U->>F: 공고번호 입력
    F->>A: GET /api/ui/notices/recommendation/?bid_ntce_no=...

    A->>DB: BidAnnouncement 조회
    A->>DB: BidContract 조회
    A->>DB: BidApiAValue 조회 (A값 7항목 합산)
    A->>DB: BidApiPrelimPrice 조회 (기초금액)
    DB-->>A: NoticeBundle 반환

    A->>E: select_table(추정가격, 공종)
    E-->>A: TABLE_2A (예: 50~300억)

    A->>E: prebid_recommend(기초금액, A값, TABLE, 추정가격)
    E->>E: optimal = A + 0.90 × (基 - A)
    E->>E: safe = band_high / aggressive = band_low
    E->>E: floor_rate_bid 계산
    E-->>A: Safe 89.745% / Base 89.801% / Aggressive 89.842%

    A->>DB: 유사공고 통계 (report_stats)
    DB-->>A: 표본 1,207건, 중앙값 89.803%

    A-->>F: JSON (strategies, judgement, similar, band)
    F-->>U: 3단계 전략 카드 + 통계 표시

    U->>F: AI 리포트 요청
    F->>A: GET /api/ui/report/latest/?bid_ntce_no=...
    A->>GPT: generate_report(추천결과 + 통계)
    GPT-->>A: 전략 요약 · 리스크 · 대응
    A-->>F: AI 리포트 JSON
    F-->>U: AI 전략 리포트 렌더링
```

## 5. 기술 스택 요약

| 계층 | 기술 | 용도 |
|------|------|------|
| **Frontend** | React 18 + TypeScript + Vite | SPA, 다크테마 UI |
| **Backend** | Django 6.0 + Python 3.10 | API, 규칙 엔진 |
| **Database** | PostgreSQL 15 | 공고/낙찰/계약 데이터 |
| **AI** | OpenAI GPT-4o-mini | 전략 리포트 생성 |
| **외부 API** | G2B 나라장터 API 3종 | 공공조달 데이터 수집 |
| **배포** | Docker Compose (3 컨테이너) | db + web + scheduler |
| **패키지** | uv (pyproject.toml) | Python 의존성 관리 |
| **정밀연산** | Decimal (ROUND_HALF_UP) | 1원 단위 정확도 |
| **테스트** | 184개 자동화 테스트 | 35 클래스, 전 계층 검증 |
