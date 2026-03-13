import React from 'react';
import { useSearchParams } from 'react-router-dom';

import { AppShell } from '../components/AppShell';
import { MetricStrip } from '../components/MetricStrip';
import { Panel } from '../components/Panel';
import { StatusBanner } from '../components/StatusBanner';
import { useAiReportData } from '../data/mock';

const LOADING_METRICS = [
  { label: '권장 기본안', value: '생성 중', tone: 'accent' as const, helper: '리포트 계산 중' },
  { label: '비교안', value: '생성 중', helper: '근거 정리 중' },
  { label: '표본', value: '생성 중', helper: '유사 공고 집계 중' },
  { label: '설명력', value: '생성 중', tone: 'success' as const, helper: '리스크 정리 중' },
];

export function AiReportPage(): JSX.Element {
  const [searchParams] = useSearchParams();
  const noticeNo = searchParams.get('bid_ntce_no') ?? '';
  const { data, error, loading, reload } = useAiReportData(noticeNo || undefined);

  return (
    <AppShell
      activeKey="report"
      pageLabel="AI 리포트"
      title="추천 결과를 설명과 근거로 정리합니다"
      subtitle="핵심 판단, 리스크, 실행 포인트를 나눠 보여줘 바로 공유하거나 검토할 수 있습니다."
      actions={
        <div className="bc-inline-actions">
          <button className="bc-button" type="button" onClick={reload}>
            리포트 새로 생성
          </button>
          <button className="bc-ghost-button" type="button" onClick={() => window.print()}>
            화면 출력
          </button>
        </div>
      }
      aside={
        <div className="bc-stack">
          <Panel title="생성 정보">
            <div className="bc-list">
              {(data?.actions ?? []).map((item) => (
                <div key={item.label} className="bc-list-row">
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                </div>
              ))}
              {!loading && !data?.actions.length ? (
                <div className="bc-list-row">
                  <span>생성 상태</span>
                  <strong>대기</strong>
                </div>
              ) : null}
            </div>
          </Panel>
        </div>
      }
    >
      <MetricStrip items={data?.metrics ?? LOADING_METRICS} />

      <StatusBanner
        tone={error ? 'error' : loading ? 'default' : 'success'}
        label={error ? '오류' : loading ? '생성 중' : '준비 완료'}
        text={
          error
            ? error
            : loading
              ? 'AI 리포트를 정리하는 중입니다.'
              : '추천 결과를 설명 문장과 근거로 정리했습니다.'
        }
      />

      <div className="bc-stack top-gap">
        {loading && !data ? (
          <Panel title="리포트 상태">
            <div className="bc-state-card">AI 리포트를 생성하는 중입니다.</div>
          </Panel>
        ) : null}

        {!loading && !error && !data?.blocks.length ? (
          <Panel title="리포트 상태">
            <div className="bc-state-card">표시할 리포트 블록이 없습니다.</div>
          </Panel>
        ) : null}

        {data?.blocks.map((block) => (
          <Panel key={block.title} title={block.title} sub={block.body}>
            <ul className="bc-bullet-list">
              {block.bullets.map((bullet) => (
                <li key={bullet}>{bullet}</li>
              ))}
            </ul>
          </Panel>
        ))}

        <div className="bc-two-column">
          <Panel title="공유용 문장">
            <div className="bc-quote-box">{data?.quoteText ?? '리포트 생성 후 문장 예시가 표시됩니다.'}</div>
          </Panel>

          <Panel title="근거 요약">
            <div className="bc-list">
              {(data?.evidenceRows ?? []).map((item) => (
                <div key={item.label} className="bc-list-row">
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                </div>
              ))}
              {!loading && !data?.evidenceRows.length ? (
                <div className="bc-list-row">
                  <span>근거 데이터</span>
                  <strong>없음</strong>
                </div>
              ) : null}
            </div>
          </Panel>
        </div>
      </div>
    </AppShell>
  );
}
