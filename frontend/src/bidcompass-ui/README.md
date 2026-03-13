# BidCompass Unified UI Kit

현재 결과 화면의 톤을 기준으로 **전체 서비스 페이지 디자인을 통일한 프론트 기준안**입니다.
이 산출물은 실제 API 연결 전 단계의 **UI 골격 + 공통 컴포넌트 + Codex handoff 문서**로 구성되어 있습니다.

## 포함 범위
- 대시보드
- 공고 조회
- 추천 결과
- 가격 계산
- AI 리포트
- 히스토리
- 설정

## 핵심 파일
- `BidCompassUnifiedWorkspace.tsx`  
  한 파일에서 모든 페이지를 확인할 수 있는 데모 엔트리
- `bidcompass-ui.css`  
  공통 디자인 토큰과 페이지 스타일
- `components/`  
  AppShell, Panel, MetricStrip, StatusBanner, DataTable, StrategyGroup
- `pages/`  
  실제 화면 단위 컴포넌트
- `data/mock.ts`  
  더미 데이터
- `DESIGN_SYSTEM.md`  
  디자인 원칙과 화면별 우선순위
- `CODEX_TASK_PROMPT.md`  
  Codex에게 그대로 전달할 작업 지시문
- `AGENTS.md`  
  Codex가 repo 안에서 따라야 할 프로젝트 규칙

## 페이지 설계 의도
이 UI는 다음 원칙을 유지합니다.

1. **왼쪽은 이동, 가운데는 판단, 오른쪽은 보조 정보**
2. **문장은 짧게, 수치와 상태를 먼저 노출**
3. **추천 결과 페이지의 톤을 다른 페이지로 그대로 확장**
4. **공통 카드, 버튼, 배지, 입력창 규칙 유지**
5. **실제 연결 시 디자인보다 데이터 계층만 교체**

## 바로 붙이는 방법
### React
```tsx
import BidCompassUnifiedWorkspace from './BidCompassUnifiedWorkspace';

export default function App() {
  return <BidCompassUnifiedWorkspace />;
}
```

### 실제 서비스 라우터에 연결할 때
- `pages/` 아래 컴포넌트를 각 라우트에 연결
- `data/mock.ts` 대신 실제 API 응답을 매핑하는 adapter layer 추가
- `AppShell`과 `bidcompass-ui.css`는 그대로 유지
- 페이지 copy와 label은 가능하면 유지

## 권장 연결 순서
1. `bidcompass-ui.css` 추가
2. `components/` 추가
3. `pages/`를 기존 라우터에 연결
4. mock data → API adapter 교체
5. 버튼/검색/저장 액션 연결
6. 로딩/에러/빈 상태 추가 확장

## 주의
이전 업로드 파일 중 일부는 만료되었을 수 있습니다.  
이번 산출물은 **현재 남아 있는 결과 화면 시안과 대화 맥락을 기준으로 재구성한 통합 UI 키트**입니다.
