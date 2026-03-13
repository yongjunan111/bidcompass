# BidCompass (입찰나침반)

나라장터(G2B) 적격심사 규칙 엔진 + 웹 MVP.

추정가격 100억 미만 건설공사 적격심사(별표 1~5)의 가격점수 계산, 최적투찰가 추천, 경쟁사 벤치마크를 제공합니다. AI 서비스가 아닌 **규칙 기반 엔진**입니다.

## Stack

- **Phase 1 (현재)**: Django 5.0 + PostgreSQL 15
- **Phase 2 (계획)**: + LangGraph (AI agent orchestration)

## Prerequisites

- Python 3.10+
- Docker (Compose 포함) — PostgreSQL 15는 docker-compose로 제공됨 (로컬 설치 불필요)

## Setup

```bash
git clone git@github.com:yongjunan111/bidcompass.git
cd bidcompass

python -m venv .venv
source .venv/bin/activate
pip install -e .          # 패키지 관리: pip (uv 전환은 별도 이슈로 예정)

cp .env.example .env
# .env 편집: DB_PASSWORD, SECRET_KEY 필수 / API_KEY는 수집 시 필요
# OPENAI_API_KEY는 AI 전략 리포트 사용 시 필요

docker volume create bidcompass_pgdata
docker compose up -d

python manage.py migrate
python manage.py runserver
```

배치 파이프라인(공고 수집, 낙찰/계약 수집, A값 수집)을 자동화하려면 `docker compose up -d`로 전체 서비스를 실행합니다. 개별 실행: `docker compose up -d scheduler_announcements scheduler_results scheduler_api_data`.

## Test

```bash
python manage.py test g2b    # 119 tests, 18 classes
```

## Management Commands

### 데이터 적재

| 커맨드 | 설명 |
|--------|------|
| `load_csv` | 나라장터 CSV 파일을 DB에 적재 |
| `load_api_json` | JSON 원본에서 A값 + 복수예비가격을 DB에 재적재 |

### API 수집

| 커맨드 | 설명 |
|--------|------|
| `fetch_announcements` | **Pipeline 1**: 서비스용 건설공사 공고 수집 → BidAnnouncement + BidContract(NOTICE) |
| `fetch_winning_bids` | **Pipeline 2a**: 낙찰결과 수집 → BidResult (DB 우선 notice enrichment) |
| `fetch_contracts` | **Pipeline 2b**: 계약정보 수집 → BidContract (범용 API, 건설공사 필터) |
| `collect_bid_api_data` | **Pipeline 3**: DB 기반 A값 + 복수예비가격 API 수집 |
| `sync_recent_construction_data` | 위 1~2 통합 래퍼 (개별 커맨드 권장) |
| `collect_bid_data` | [DEPRECATED] 엑셀 기반 수집 -> collect_bid_api_data 사용 |

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
| `explore_bid_clustering` | 컨설팅 업체 클러스터링 탐색 |

### 시뮬레이션

| 커맨드 | 설명 |
|--------|------|
| `simulate_historical` | 과거 낙찰 시뮬레이션 (558건) |
| `simulate_optimal_bid` | 최적투찰 백테스트 (558건) |
| `simulate_optimal_bid_db` | DB 기반 대규모 최적투찰 백테스트 |
| `simulate_floor_prevention` | 하한율 미달 방지 시뮬레이션 |

### 벤치마크

| 커맨드 | 설명 |
|--------|------|
| `benchmark_info21c` | 인포21C 15건 벤치마크 비교 |

## Project Structure

```
bidcompass/
├── config/              # Django settings, urls, wsgi
├── g2b/                 # Main app (models, views, services, commands)
│   ├── services/        # bid_engine.py, optimal_bid.py, ai_report.py, report_stats.py, g2b_client.py
│   ├── management/commands/  # 21 management commands
│   └── tests.py         # 119 tests (14 SimpleTestCase + 4 TestCase)
├── templates/g2b/       # 6 templates (calculator, recommend, ai_report, benchmark, ...)
├── static/g2b/          # style.css
├── scripts/             # pdf_to_markdown.py, test_api.py, test_new_apis.py
├── data/collected/      # API raw JSON, charts (gitignored)
└── docs/                # Input xlsx files (local only, gitignored)
```

## Key Domain Rules

- **기준율(base rate)**: 90% (88% 아님)
- **A값**: 7개 사회보험/안전관리비 항목만 해당 (이윤, 부가세 포함 안됨)
- **낙찰하한율**: +2%p 상향 (조달청 2026.1.30 시행)
- 자동입찰 금지 (지문보안토큰 정책 위반)
- 담합방지 4원칙 준수 필수
