# BidCompass (입찰나침반)

나라장터(G2B) 적격심사 규칙 엔진 + 웹 MVP.

추정가격 100억 미만 건설공사 적격심사(별표 1~5)의 가격점수 계산, 3단계 전략 추천(Safe/Base/Aggressive), AI 전략 리포트를 제공합니다. 규칙 기반 엔진 위에 AI 해설을 올린 구조입니다.

## Stack

- **Backend**: Django 6.0 + PostgreSQL 15
- **Frontend**: React 18 + TypeScript + Vite (SPA)
- **AI**: OpenAI GPT-4o-mini (전략 리포트)
- **Deploy**: Docker Compose (db + web + scheduler)
- **Package**: uv (pyproject.toml)
- **Phase 2 (계획)**: + LangGraph (AI agent orchestration)

## Prerequisites

- Python 3.10+
- Node.js 18+ (프론트엔드 빌드)
- Docker (Compose 포함) — PostgreSQL 15는 docker-compose로 제공됨 (로컬 설치 불필요)

## Setup

```bash
git clone git@github.com:yongjunan111/bidcompass.git
cd bidcompass

# Backend
python -m venv .venv
source .venv/bin/activate
uv pip install -e .

# Frontend
cd frontend && npm install && npm run build && cd ..

cp .env.example .env
# .env 편집: DB_PASSWORD, SECRET_KEY 필수 / API_KEY는 수집 시 필요
# OPENAI_API_KEY는 AI 전략 리포트 사용 시 필요

docker volume create bidcompass_pgdata
docker compose up -d

python manage.py migrate
python manage.py runserver
```

## Docker Compose

3개 컨테이너로 구성:

| 컨테이너 | 역할 | 포트 |
|----------|------|------|
| `bidcompass_db` | PostgreSQL 15 | 5434 |
| `bidcompass_web` | Django + React SPA | 8010 |
| `bidcompass_scheduler` | 24h 자동 수집 파이프라인 (5단계) | - |

```bash
docker compose up -d        # 전체 실행
docker logs bidcompass_scheduler --tail 50  # 수집 로그 확인
```

## Test

```bash
python manage.py test g2b    # 184 tests, 35 classes
```

## Data Pipeline

`bidcompass_scheduler`가 24시간 주기로 5단계를 순차 실행:

| 단계 | 커맨드 | 설명 |
|------|--------|------|
| 1 | `fetch_announcements` | 공고 수집 (최근 2일) |
| 2 | `fetch_winning_bids` | 낙찰결과 수집 (최근 3일) |
| 3 | `fetch_contracts` | 계약정보 수집 (최근 3일) |
| 4 | `collect_bid_api_data` | A값 · 복수예비가격 수집 (일 1,000건) |
| 5 | `retry_pending_inputs` | 미확정 공고 재확인 |

## Management Commands

### 데이터 적재

| 커맨드 | 설명 |
|--------|------|
| `load_csv` | 나라장터 CSV 파일을 DB에 적재 |
| `load_api_json` | JSON 원본에서 A값 + 복수예비가격을 DB에 재적재 |

### API 수집

| 커맨드 | 설명 |
|--------|------|
| `fetch_announcements` | Pipeline 1: 건설공사 공고 수집 → BidAnnouncement + BidContract |
| `fetch_winning_bids` | Pipeline 2a: 낙찰결과 수집 → BidResult |
| `fetch_contracts` | Pipeline 2b: 계약정보 수집 → BidContract |
| `collect_bid_api_data` | Pipeline 4: A값 + 복수예비가격 API 수집 |
| `retry_pending_inputs` | Pipeline 5: 미확정 공고 재확인 |

### 검증

| 커맨드 | 설명 |
|--------|------|
| `verify_data` | 수집된 G2B 데이터 검증 |
| `verify_engine_db` | DB 대규모 코어엔진 검증 (3계층) |
| `verify_assessment_rate` | 사정률 검증 리포트 |

### 분석 (EDA)

| 커맨드 | 설명 |
|--------|------|
| `analyze_bid_distribution` | 예정가격 분포 EDA + 제도 변경 비교 |
| `analyze_bid_advanced` | 투찰 전략 + 시장 구조 심층 분석 |
| `analyze_competitor_behavior` | 경쟁자 행동 분석 |
| `analyze_cross_table` | 크로스테이블 종합 EDA + 세그먼트 정책 |
| `analyze_prelim_selection` | 복수예비가격 선택 패턴 분석 |
| `analyze_info21c_history` | 인포21C 5년 이력 분석 |
| `explore_bid_clustering` | 투찰 패턴 클러스터링 탐색 |

### 시뮬레이션

| 커맨드 | 설명 |
|--------|------|
| `simulate_historical` | 과거 낙찰 시뮬레이션 |
| `simulate_optimal_bid` | 최적투찰 백테스트 |
| `simulate_optimal_bid_db` | DB 기반 대규모 최적투찰 백테스트 |
| `simulate_floor_prevention` | 하한율 미달 방지 시뮬레이션 |

### 벤치마크

| 커맨드 | 설명 |
|--------|------|
| `benchmark_info21c` | 인포21C 15건 벤치마크 비교 |

### AI

| 커맨드 | 설명 |
|--------|------|
| `evaluate_ai_report` | AI 전략 리포트 품질 평가 |

## Project Structure

```
bidcompass/
├── config/              # Django settings, urls, wsgi
├── g2b/                 # Main app (models, views, services, commands)
│   ├── services/        # bid_engine.py, optimal_bid.py, prebid_recommend.py,
│   │                    # ai_report.py, report_stats.py, g2b_construction_client.py,
│   │                    # g2b_construction_sync.py
│   ├── management/commands/  # 27 management commands
│   ├── ui_api.py        # 7 JSON API endpoints (React SPA용)
│   └── tests.py         # 35 test classes, 184+ tests
├── frontend/            # React 18 + TypeScript + Vite SPA
│   └── src/bidcompass-ui/  # Pages, components, types
├── templates/g2b/       # Legacy Django templates (/legacy/ prefix)
├── static/              # Built frontend assets + CSS
├── scripts/             # run_all_pipelines.sh, pdf_to_markdown.py
├── data/collected/      # API raw JSON, charts, analysis outputs (gitignored)
├── docs/                # API specs, architecture diagrams (gitignored)
├── Dockerfile           # Multi-stage build (Node + Python)
└── docker-compose.yml   # db + web + scheduler (3 containers)
```

## API Endpoints

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/ui/dashboard/` | 대시보드 (오늘의 공고, 지표) |
| GET | `/api/ui/notices/search/` | 공고 검색 (업종, 지역, 금액 필터) |
| GET | `/api/ui/notices/recommendation/` | 사전 투찰 추천 (3단계 전략) |
| POST | `/api/ui/calculator/` | 가격점수 계산기 |
| GET | `/api/ui/report/latest/` | AI 전략 리포트 |
| GET | `/api/ui/history/` | 분석 이력 |
| GET | `/api/ui/settings/` | 설정 |

## Key Domain Rules

- **기준율(base rate)**: 90% (88% 아님)
- **A값**: 7개 사회보험/안전관리비 항목만 해당 (이윤, 부가세 포함 안됨)
- **낙찰하한율**: +2%p 상향 (조달청 2026.1.30 시행)
- **반올림**: Decimal 전용, round() 금지, 사사오입(ROUND_HALF_UP)
- **경계 규칙**: [하한, 상한) 통일
- 자동입찰 금지 (지문보안토큰 정책 위반)
- 담합방지 4원칙 준수 필수

## Data Scale

| 테이블 | 건수 |
|--------|------|
| BidAnnouncement (공고) | 1,038,639 |
| BidContract (계약) | 886,322 |
| BidResult (투찰결과) | ~32,300,000 |

## Backtest Results (1,207건)

- 1순위 대비 평균 **+9.12점** 개선
- **100%** 5점 이내 정확도
- **84.5%** 1점 이내 정확도
- 하한율 미달 **65% → 94.7% 방어**
