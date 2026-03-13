import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { AppShell } from '../components/AppShell';
import { Panel } from '../components/Panel';
import { StatusBanner } from '../components/StatusBanner';
import { useNoticeSearchData } from '../data/mock';

const REGION_OPTIONS = [
  '',
  '서울',
  '부산',
  '대구',
  '인천',
  '광주',
  '대전',
  '울산',
  '세종',
  '경기',
  '강원',
  '충북',
  '충남',
  '전북',
  '전남',
  '경북',
  '경남',
  '제주',
];

export function NoticeSearchPage(): JSX.Element {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get('query') ?? '';
  const region = searchParams.get('region') ?? '';
  const [draftQuery, setDraftQuery] = useState(query);
  const [draftRegion, setDraftRegion] = useState(region);
  const { data, error, loading, reload } = useNoticeSearchData(query, region);

  useEffect(() => {
    setDraftQuery(query);
    setDraftRegion(region);
  }, [query, region]);

  function updateSearchParams(nextQuery: string, nextRegion: string): void {
    const params = new URLSearchParams();
    if (nextQuery) {
      params.set('query', nextQuery);
    }
    if (nextRegion) {
      params.set('region', nextRegion);
    }
    setSearchParams(params);
  }

  function handleSearch(event: React.FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const nextQuery = draftQuery.trim();
    updateSearchParams(nextQuery, draftRegion);
  }

  return (
    <AppShell
      activeKey="search"
      pageLabel="공고 조회 · 검색"
      title="공고번호, 키워드, 지역으로 대상 공고를 찾습니다"
      subtitle="건설공사 적격심사 대상만 조회하고, 지역 필터로 바로 좁혀볼 수 있습니다."
      actions={
        <div className="bc-inline-actions">
          <button className="bc-button" form="notice-search-form" type="submit">
            공고 조회
          </button>
          <button className="bc-ghost-button" type="button" onClick={reload}>
            새로고침
          </button>
        </div>
      }
      aside={
        <div className="bc-stack">
          <Panel title="최근 적재 공고">
            <div className="bc-list">
              {(data?.recent ?? []).map((item) => (
                <div key={`${item.label}-${item.value}`} className="bc-list-row">
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                </div>
              ))}
              {!loading && !data?.recent.length ? (
                <div className="bc-list-row">
                  <span>최근 적재 공고</span>
                  <strong>없음</strong>
                </div>
              ) : null}
            </div>
          </Panel>
        </div>
      }
    >
      <form id="notice-search-form" className="bc-toolbar bc-toolbar-search" onSubmit={handleSearch}>
        <input
          className="bc-input"
          placeholder="공고번호, 기관명, 키워드를 입력하세요"
          value={draftQuery}
          onChange={(event) => setDraftQuery(event.target.value)}
        />
        <select
          className="bc-input"
          value={draftRegion}
          onChange={(event) => setDraftRegion(event.target.value)}
          aria-label="지역 선택"
        >
          <option value="">전체 지역</option>
          {REGION_OPTIONS.filter((item) => item).map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <button className="bc-button" type="submit">
          검색
        </button>
        <button
          className="bc-ghost-button"
          type="button"
          onClick={() => {
            setDraftQuery('');
            setDraftRegion('');
            setSearchParams({});
          }}
        >
          초기화
        </button>
      </form>

      <StatusBanner
        tone={error ? 'error' : loading ? 'default' : data?.count ? 'success' : 'warning'}
        label={
          error
            ? '오류'
            : loading
              ? '조회 중'
              : `${data?.count ?? 0}건`
        }
        text={
          error
            ? error
            : loading
              ? '공고 검색 결과를 불러오는 중입니다.'
              : data?.count
                ? '조건에 맞는 건설공사 공고를 찾았습니다. 카드에서 공고를 선택하면 추천 결과 화면으로 이동합니다.'
                : '조건에 맞는 공고가 없습니다. 검색어를 조정해 다시 시도해 주세요.'
        }
      />

      <div className="bc-content-grid">
        <div className="bc-stack">
          <Panel title="검색 결과" sub="공고번호, 업종, 지역, 추정가격을 함께 확인할 수 있습니다.">
            {loading && !data ? (
              <div className="bc-state-card">검색 결과를 불러오는 중입니다.</div>
            ) : null}

            {!loading && !error && !data?.results.length ? (
              <div className="bc-state-card">조회된 공고가 없습니다.</div>
            ) : null}

            {data?.results.length ? (
              <div className="bc-notice-list">
                {data.results.map((notice) => (
                  <article key={notice.id} className="bc-notice-card compact">
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
                      <span>{notice.id}</span>
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

        <Panel title="조회 기준">
          <ul className="bc-bullet-list">
            <li>건설공사 적격심사 대상 공고만 조회합니다.</li>
            <li>검색어와 지역을 함께 지정해 빠르게 좁힐 수 있습니다.</li>
            <li>검색 결과는 최신 공고 순으로 최대 12건까지 표시합니다.</li>
            <li>선택한 공고는 추천 결과 화면으로 바로 이동할 수 있습니다.</li>
          </ul>
        </Panel>
      </div>
    </AppShell>
  );
}
