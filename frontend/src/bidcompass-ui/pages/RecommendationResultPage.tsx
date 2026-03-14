import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { AppShell } from '../components/AppShell';
import { Panel } from '../components/Panel';
import { StatusBanner } from '../components/StatusBanner';
import { StrategyGroup } from '../components/StrategyGroup';
import { useRecommendationData } from '../data/mock';

type StrategyKey = 'safe' | 'base' | 'aggressive';

export function RecommendationResultPage(): JSX.Element {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [draftNoticeNo, setDraftNoticeNo] = useState(searchParams.get('bid_ntce_no') ?? '');
  const [selectedKey, setSelectedKey] = useState<StrategyKey>('base');
  const noticeNo = searchParams.get('bid_ntce_no') ?? '';
  const { data, error, loading, reload } = useRecommendationData(noticeNo || undefined);

  useEffect(() => {
    setDraftNoticeNo(noticeNo);
  }, [noticeNo]);

  useEffect(() => {
    if (!data?.strategies.length) {
      return;
    }

    const selectedExists = data.strategies.some((item) => item.key === selectedKey);
    if (!selectedExists) {
      setSelectedKey('base');
    }
  }, [data, selectedKey]);

  const selected =
    data?.strategies.find((item) => item.key === selectedKey) ??
    data?.strategies.find((item) => item.key === 'base') ??
    data?.strategies[0] ??
    null;

  const rangeLeft =
    selectedKey === 'safe' ? '24%' : selectedKey === 'base' ? '52%' : '76%';

  function handleSearch(event: React.FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const nextNoticeNo = draftNoticeNo.trim();
    if (!nextNoticeNo) {
      setSearchParams({});
      return;
    }
    setSearchParams({ bid_ntce_no: nextNoticeNo });
  }

  async function handleCopy(): Promise<void> {
    if (!selected) {
      return;
    }
    try {
      await navigator.clipboard.writeText(
        `${selected.label} ${selected.rate}${selected.amount ? ` / ${selected.amount}` : ''}`,
      );
    } catch {
      // Ignore clipboard failures in unsupported environments.
    }
  }

  return (
    <AppShell
      activeKey="result"
      pageLabel="추천 결과"
      title="추천안 3개와 핵심 판단을 바로 확인하세요"
      subtitle="추천안 비교, 하한율 통과 여부, 주요 계산값을 한 화면에서 볼 수 있습니다."
      actions={
        <div className="bc-inline-actions">
          <button
            className="bc-button"
            type="button"
            onClick={() => navigate(`/report/latest${noticeNo ? `?bid_ntce_no=${noticeNo}` : ''}`)}
          >
            AI 리포트 생성
          </button>
          <button className="bc-ghost-button" type="button" onClick={handleCopy}>
            추천값 복사
          </button>
        </div>
      }
      aside={
        <div className="bc-stack">
          <Panel title="전략 요약">
            <ul className="bc-bullet-list">
              {(selected?.summary ?? []).map((item) => (
                <li key={item}>{item}</li>
              ))}
              {!loading && !selected ? <li>추천 전략을 불러오지 못했습니다.</li> : null}
            </ul>
          </Panel>

          <Panel title="분석 정보">
            <div className="bc-list">
              <div className="bc-list-row">
                <span>분석 상태</span>
                <strong>{data?.status.analysisStatus ?? '대기'}</strong>
              </div>
              <div className="bc-list-row">
                <span>갱신 시각</span>
                <strong>{data?.status.updatedAt ?? '-'}</strong>
              </div>
              {data?.status.reportVersion ? (
                <div className="bc-list-row">
                  <span>리포트 버전</span>
                  <strong>{data.status.reportVersion}</strong>
                </div>
              ) : null}
            </div>
          </Panel>

          <Panel title="바로가기">
            <div className="bc-action-stack">
              <button className="bc-button full" type="button" onClick={() => navigate(`/calculator${noticeNo ? `?bid_ntce_no=${noticeNo}` : ''}`)}>
                계산 상세 보기
              </button>
              <button className="bc-ghost-button full" type="button" onClick={reload}>
                다시 분석
              </button>
              <button className="bc-ghost-button full" type="button" onClick={() => navigate('/history')}>
                히스토리 보기
              </button>
            </div>
          </Panel>
        </div>
      }
    >
      <section className="bc-meta-grid">
        <article className="bc-meta-card">
          <div className="bc-meta-label">공고번호</div>
          <div className="bc-meta-value">{data?.notice.noticeNo ?? '-'}</div>
        </article>
        <article className="bc-meta-card">
          <div className="bc-meta-label">발주기관</div>
          <div className="bc-meta-value">{data?.notice.agency ?? '-'}</div>
        </article>
        <article className="bc-meta-card">
          <div className="bc-meta-label">개찰일자</div>
          <div className="bc-meta-value">{data?.notice.deadline ?? '-'}</div>
        </article>
        <article className="bc-meta-card">
          <div className="bc-meta-label">추정가격</div>
          <div className="bc-meta-value">{data?.notice.estimate ?? '-'}</div>
        </article>
      </section>

      <form className="bc-toolbar" onSubmit={handleSearch}>
        <input
          className="bc-input"
          value={draftNoticeNo}
          onChange={(event) => setDraftNoticeNo(event.target.value)}
          placeholder="공고번호를 입력하세요"
        />
        <button className="bc-button" type="submit">
          분석 시작
        </button>
        <button className="bc-ghost-button" type="button" onClick={reload}>
          다시 조회
        </button>
      </form>

      {data?.warnings?.map((w) => (
        <StatusBanner
          key={w.type}
          tone={w.severity === 'error' ? 'error' : w.severity === 'warning' ? 'warning' : 'default'}
          label={w.severity === 'info' ? '안내' : '주의'}
          text={w.message}
        />
      ))}

      {data && !data.canRecommend ? (
        <StatusBanner
          tone="warning"
          label="추천 불가"
          text={data.warningMessage ?? 'A값 또는 기초금액이 아직 공개되지 않아 정확한 추천이 불가능합니다.'}
        />
      ) : (
        <StatusBanner
          tone={error ? 'error' : loading ? 'default' : data?.judgement.passResult.includes('PASS') ? 'success' : 'warning'}
          label={
            error
              ? '오류'
              : loading
                ? '분석 중'
                : data?.judgement.passResult.includes('PASS')
                  ? '분석 완료'
                  : '재검토'
          }
          text={
            error
              ? error
              : loading
                ? '추천 결과를 불러오는 중입니다.'
                : '추천안을 선택하면 주요 계산값과 요약이 함께 바뀝니다.'
          }
        />
      )}

      {data && !data.canRecommend ? null : data?.strategies.length ? (
        <StrategyGroup
          items={data.strategies}
          selectedKey={selectedKey}
          onSelect={(key) => setSelectedKey(key)}
        />
      ) : null}

      <div className="bc-content-grid">
        <div className="bc-stack">
          <Panel title="가격 판단" sub="하한율 통과 여부와 핵심 계산값을 먼저 확인하세요.">
            {loading && !data ? (
              <div className="bc-state-card">추천 결과를 계산하는 중입니다.</div>
            ) : null}

            {!loading && !error && !data ? (
              <div className="bc-state-card">조회할 공고번호를 입력해 주세요.</div>
            ) : null}

            {data && !data.canRecommend ? (
              <div className="bc-state-card bc-state-pending">
                {data.warningMessage ?? 'A값 또는 기초금액이 아직 공개되지 않아 정확한 추천이 불가능합니다.'}
              </div>
            ) : data ? (
              <>
                <div className="bc-score-grid">
                  <article className="bc-score-card">
                    <div className="bc-score-label">기초금액</div>
                    <div className="bc-score-value">{data.judgement.baseAmount}</div>
                  </article>
                  <article className="bc-score-card">
                    <div className="bc-score-label">A값</div>
                    <div className="bc-score-value">{data.judgement.aValue}</div>
                  </article>
                  <article className="bc-score-card">
                    <div className="bc-score-label">가격점수</div>
                    <div className="bc-score-value">{data.judgement.priceScore}</div>
                  </article>
                  <article
                    className={`bc-score-card ${data.judgement.passResult.includes('PASS') ? 'tone-success' : ''}`.trim()}
                  >
                    <div className="bc-score-label">판정</div>
                    <div className="bc-score-value">{data.judgement.passResult}</div>
                  </article>
                </div>

                <div className="bc-range-box">
                  <div className="bc-range-head">
                    <div>
                      <div className="bc-range-title">추천 투찰률 위치</div>
                      <div className="bc-range-desc">선택한 전략의 위치를 최근 유사 공고 분포 위에 표시합니다.</div>
                    </div>
                    <strong>{selected?.rate ?? '-'}</strong>
                  </div>
                  <div className="bc-range-track">
                    <div className="bc-range-point" style={{ left: rangeLeft }} />
                  </div>
                  <div className="bc-range-scale">
                    <span>보수적</span>
                    <span>중간</span>
                    <span>공격적</span>
                  </div>
                </div>
              </>
            ) : null}
          </Panel>

          <Panel title="선택 전략 요약">
            <div className="bc-list">
              <div className="bc-list-row">
                <span>전략</span>
                <strong>{selected?.label ?? '-'}</strong>
              </div>
              <div className="bc-list-row">
                <span>추천 투찰률</span>
                <strong>{selected?.rate ?? '-'}</strong>
              </div>
              <div className="bc-list-row">
                <span>예상 위치</span>
                <strong>{selected?.expectedRange ?? '-'}</strong>
              </div>
              <div className="bc-list-row">
                <span>추천 금액</span>
                <strong>{selected?.amount ?? '-'}</strong>
              </div>
              <div className="bc-list-row">
                <span>권장 이유</span>
                <strong>{selected?.reason ?? '-'}</strong>
              </div>
            </div>
          </Panel>
        </div>

          <Panel title="유사 공고 기준">
          <div className="bc-list">
            <div className="bc-list-row">
              <span>표본</span>
              <strong>{data?.similar.count ?? '-'}</strong>
            </div>
            <div className="bc-list-row">
              <span>중앙 투찰률</span>
              <strong>{data?.similar.median ?? '-'}</strong>
            </div>
            <div className="bc-list-row">
              <span>분산</span>
              <strong>{data?.similar.variance ?? '-'}</strong>
            </div>
            <div className="bc-list-row">
              <span>최근 경쟁강도</span>
              <strong>{data?.similar.competition ?? '-'}</strong>
            </div>
            <div className="bc-list-row">
              <span>적용 별표</span>
              <strong>{data?.tableLabel ?? '-'}</strong>
            </div>
            <div className="bc-list-row">
              <span>낙찰하한율</span>
              <strong>{data?.floorRate ?? '-'}</strong>
            </div>
            <div className="bc-list-row">
              <span>하한 금액</span>
              <strong>{data?.floorBid ?? '-'}</strong>
            </div>
            <div className="bc-list-row">
              <span>추천 밴드</span>
              <strong>{data ? `${data.band.low} ~ ${data.band.high}` : '-'}</strong>
            </div>
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}
