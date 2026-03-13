import React from 'react';
import { useNavigate } from 'react-router-dom';

import { AppShell } from '../components/AppShell';
import { MetricStrip } from '../components/MetricStrip';
import { Panel } from '../components/Panel';
import { StatusBanner } from '../components/StatusBanner';
import { useDashboardData } from '../data/mock';

const LOADING_METRICS = [
  { label: '오늘 개찰 건설공고', value: '불러오는 중', tone: 'accent' as const, helper: '공고 집계 중' },
  { label: '추천 가능 공고', value: '불러오는 중', helper: '데이터 확인 중' },
  { label: '분석 준비율', value: '불러오는 중', tone: 'success' as const, helper: '수집 로그 확인 중' },
  { label: '건설 적격 공고', value: '불러오는 중', helper: '서비스 범위 확인 중' },
];

export function DashboardPage(): JSX.Element {
  const navigate = useNavigate();
  const { data, error, loading } = useDashboardData();

  return (
    <AppShell
      activeKey="dashboard"
      pageLabel="대시보드"
      title="오늘 검토할 공고를 바로 확인하세요"
      subtitle="추천 가능한 건설공사 공고만 모아 보여주고, 원하는 공고는 바로 분석으로 이어집니다."
      actions={
        <div className="bc-inline-actions">
          <button className="bc-button" type="button" onClick={() => navigate('/notices/search')}>
            새 공고 분석
          </button>
          <button className="bc-ghost-button" type="button" onClick={() => navigate('/report/latest')}>
            보고서 보기
          </button>
        </div>
      }
      aside={
        <div className="bc-stack">
          <Panel title="오늘 확인할 항목">
            <div className="bc-list">
              {(data?.checklist ?? []).map((item) => (
                <div key={item.label} className="bc-list-row">
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                </div>
              ))}
              {!loading && !data?.checklist.length ? (
                <div className="bc-list-row">
                  <span>표시 항목</span>
                  <strong>없음</strong>
                </div>
              ) : null}
            </div>
          </Panel>
        </div>
      }
    >
      <MetricStrip items={data?.metrics ?? LOADING_METRICS} />

      {error ? (
        <StatusBanner
          tone="error"
          label="오류"
          text={`${error} 새로고침 후 다시 시도해 주세요.`}
        />
      ) : null}

      <div className={`bc-content-grid ${data?.weeklyStats.length ? '' : 'single-column'}`.trim()}>
        <div className="bc-stack">
          <Panel title="오늘 개찰 공고" sub="바로 확인할 공고만 간단히 정리해 보여줍니다.">
            {loading && !data ? (
              <div className="bc-state-card">오늘 개찰 공고를 불러오는 중입니다.</div>
            ) : null}

            {!loading && !error && !data?.todayNotices.length ? (
              <div className="bc-state-card">오늘 개찰 공고가 없습니다.</div>
            ) : null}

            {data?.todayNotices.length ? (
              <div className="bc-notice-list">
                {data.todayNotices.map((notice) => (
                  <article key={notice.id} className="bc-notice-card">
                    <div className="bc-notice-top">
                      <div>
                        <h3>{notice.title}</h3>
                        <p>{notice.agency}</p>
                      </div>
                      <button
                        className="bc-chip-button"
                        type="button"
                        onClick={() =>
                          navigate(`/notices/recommendation?bid_ntce_no=${notice.id}`)
                        }
                      >
                        결과 보기
                      </button>
                    </div>
                    <div className="bc-notice-meta">
                      <span>공고번호 {notice.id}</span>
                      <span>{notice.sector}</span>
                      <span>{notice.region}</span>
                      <span>{notice.deadline}</span>
                      <span>{notice.estimate}</span>
                    </div>
                  </article>
                ))}
              </div>
            ) : null}
          </Panel>
        </div>

        {data?.weeklyStats.length ? (
          <Panel title="주간 지표">
            <div className="bc-stat-stack">
              {data.weeklyStats.map((item) => (
                <div key={item.label} className="bc-stat-card">
                  <div className="bc-stat-label">{item.label}</div>
                  <div className="bc-stat-value">{item.value}</div>
                  <div className="bc-progress">
                    <span style={{ width: `${item.progress}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        ) : null}
      </div>
    </AppShell>
  );
}
