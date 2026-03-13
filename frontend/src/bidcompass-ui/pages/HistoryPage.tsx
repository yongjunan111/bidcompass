import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AppShell } from '../components/AppShell';
import { DataTable } from '../components/DataTable';
import { Panel } from '../components/Panel';
import { StatusBanner } from '../components/StatusBanner';
import { useHistoryData } from '../data/mock';
import type { HistoryRow } from '../types';

const columns = [
  { key: 'noticeNo', label: '공고번호' },
  { key: 'title', label: '공고명' },
  { key: 'strategy', label: '선택 전략' },
  { key: 'bidRate', label: '투찰률' },
  {
    key: 'status',
    label: '상태',
    render: (row: HistoryRow) => (
      <span
        className={`bc-tag tone-${row.status === '완료' ? 'success' : row.status === '검토중' ? 'warning' : 'default'}`}
      >
        {row.status}
      </span>
    ),
  },
  { key: 'updatedAt', label: '수정 시각' },
];

export function HistoryPage(): JSX.Element {
  const navigate = useNavigate();
  const { data, error, loading, reload } = useHistoryData();
  const [keyword, setKeyword] = useState('');
  const [filteredRows, setFilteredRows] = useState<HistoryRow[]>([]);

  useEffect(() => {
    const rows = data?.rows ?? [];
    const normalized = keyword.trim().toLowerCase();
    if (!normalized) {
      setFilteredRows(rows);
      return;
    }

    setFilteredRows(
      rows.filter((row) => {
        const haystack = [row.noticeNo, row.title, row.strategy].join(' ').toLowerCase();
        return haystack.includes(normalized);
      }),
    );
  }, [data, keyword]);

  return (
    <AppShell
      activeKey="history"
      pageLabel="히스토리"
      title="최근에 본 공고와 추천 결과를 다시 확인하세요"
      subtitle="검토했던 공고를 다시 열고 이어서 분석할 수 있습니다."
      actions={
        <div className="bc-inline-actions">
          <button className="bc-button" type="button" onClick={reload}>
            내역 새로고침
          </button>
          <button className="bc-ghost-button" type="button" onClick={() => navigate('/notices/search')}>
            새 공고 조회
          </button>
        </div>
      }
      aside={
        <div className="bc-stack">
          <Panel title="요약">
            <div className="bc-list">
              {(data?.summary ?? []).map((item) => (
                <div key={item.label} className="bc-list-row">
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                </div>
              ))}
              {!loading && !data?.summary.length ? (
                <div className="bc-list-row">
                  <span>요약</span>
                  <strong>없음</strong>
                </div>
              ) : null}
            </div>
          </Panel>
        </div>
      }
    >
      <div className="bc-toolbar">
        <input
          className="bc-input"
          placeholder="공고번호 또는 공고명 검색"
          value={keyword}
          onChange={(event) => setKeyword(event.target.value)}
        />
        <button className="bc-ghost-button" type="button" onClick={() => setKeyword('')}>
          검색어 초기화
        </button>
        <button className="bc-button" type="button" onClick={reload}>
          새로고침
        </button>
      </div>

      <StatusBanner
        tone={error ? 'error' : loading ? 'default' : 'success'}
        label={error ? '오류' : loading ? '조회 중' : `${filteredRows.length}건`}
        text={
          error
            ? error
            : loading
              ? '최근 분석 내역을 불러오는 중입니다.'
              : '최근 확인한 공고와 추천 결과를 다시 볼 수 있습니다.'
        }
      />

      <Panel title="최근 분석 기록">
        {loading && !data ? (
          <div className="bc-state-card">저장된 분석 내역을 불러오는 중입니다.</div>
        ) : null}

        {!loading && !error && !filteredRows.length ? (
          <div className="bc-state-card">조건에 맞는 내역이 없습니다.</div>
        ) : null}

        {filteredRows.length ? (
          <DataTable columns={columns} rows={filteredRows} rowKey={(row) => row.id} />
        ) : null}
      </Panel>
    </AppShell>
  );
}
