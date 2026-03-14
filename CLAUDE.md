# BidCompass (입찰나침반)

Rule-based bidding analysis engine for Korea's G2B public procurement system.

## Project Overview

- **Goal**: 중소건설사 대상 적격심사 규칙 엔진 + 웹 MVP (나라장터/G2B)
- **Target**: 추정가격 100억 미만 적격심사 전체 (별표 1-5)
- **Stack**: Django + PostgreSQL (Phase 1) → + LangGraph (Phase 2)
- **Phase**: Phase 1 Pilot (카카오톡/스프레드시트, 1~3개 클라이언트)
- **Key Regulation**: 조달청지침 #9269 (시행 2025.12.1 / 입찰가격평가 2026.1.30)

## Dev Machine Constraint

- **로컬**: M1 MacBook Air / RAM **8GB** — 메모리 여유 없음
- 수백만건 이상 데이터는 **절대 Python fetchall() 금지**
- DB 집계(SQL GROUP BY, PERCENTILE_CONT 등)로 처리, Python에는 결과만 반환
- pandas/list 로드도 수백만건 이상이면 OOM — chunked 처리 또는 SQL 선처리 필수

## Tech Stack

- Python 3.10
- Django 6.0 (backend)
- PostgreSQL 15 (database)
- React 18 + TypeScript + Vite (frontend)
- Docker Compose (deployment)
- LangGraph (Phase 2 계획)
- Package manager: uv (pyproject.toml)

## Key Domain Rules

- 기준율(base rate): **90%** (88% 아님)
- A값: 7개 사회보험/안전관리비 항목만 해당 (이윤, 부가세 포함 안됨)
- 낙찰하한율 +2%p 상향 (조달청 2026.1.30 시행)
- 자동입찰 금지 (지문보안토큰 정책 위반)
- 담합방지 4원칙 준수 필수

## Project Structure

```
bidcompass/
├── config/              # Django settings, urls, wsgi
├── g2b/                 # Main app (models, views, services, commands)
│   ├── services/        # bid_engine.py, optimal_bid.py, g2b_construction_client.py, g2b_construction_sync.py
│   ├── management/commands/  # 27 management commands
│   └── tests.py         # 35 test classes, 184+ tests
├── frontend/            # React 18 + TypeScript + Vite SPA
│   └── src/bidcompass-ui/  # Pages, components, types
├── templates/g2b/       # Legacy Django templates (/legacy/ prefix)
├── static/              # Built frontend assets + CSS
├── scripts/             # run_all_pipelines.sh, pdf_to_markdown.py
├── data/collected/      # API raw JSON, charts, analysis outputs (gitignored)
├── docs/                # Input xlsx files, API specs (local only, gitignored)
├── Dockerfile           # Multi-stage build (Node + Python)
└── docker-compose.yml   # db + web + scheduler (3 containers)
```

## Conventions

- Language: Korean comments, English code
- Commit: `[BC-N] type: 설명` (Conventional Commits + Notion 이슈 ID)
  - 형식: `[BC-11] feat: CSV 대량 적재 파이프라인 구현`
  - type: feat / fix / chore / docs / refactor / test
  - [BC-N]: Notion 이슈 트래커 ID (initial commit 등 해당 없으면 생략)
  - subject: 한글, 현재형
