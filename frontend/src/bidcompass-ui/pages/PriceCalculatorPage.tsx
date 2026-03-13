import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { AppShell } from '../components/AppShell';
import { Panel } from '../components/Panel';
import { StatusBanner } from '../components/StatusBanner';
import { calculatePrice, useRecommendationData } from '../data/mock';
import type { CalculatorData, CalculatorFormValues } from '../types';

const EMPTY_FORM: CalculatorFormValues = {
  noticeNo: '',
  baseAmount: '',
  aValue: '',
  bidRate: '',
};

function stripPercent(value: string): string {
  return value.replace('%', '').trim();
}

export function PriceCalculatorPage(): JSX.Element {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const noticeNo = searchParams.get('bid_ntce_no') ?? '';
  const {
    data: seedData,
    error: seedError,
    loading: seedLoading,
  } = useRecommendationData(noticeNo || undefined);
  const [form, setForm] = useState<CalculatorFormValues>(EMPTY_FORM);
  const [result, setResult] = useState<CalculatorData | null>(null);
  const [calcLoading, setCalcLoading] = useState(false);
  const [calcError, setCalcError] = useState<string | null>(null);

  useEffect(() => {
    if (!seedData) {
      return;
    }

    const nextForm = {
      noticeNo: seedData.notice.noticeNo,
      baseAmount: String(seedData.baseAmountValue),
      aValue: String(seedData.aValueTotal),
      bidRate: stripPercent(seedData.judgement.selectedRate),
    };

    setForm(nextForm);
    void runCalculation(nextForm);
  }, [seedData]);

  async function runCalculation(nextForm: CalculatorFormValues): Promise<void> {
    setCalcLoading(true);
    setCalcError(null);

    try {
      const payload = await calculatePrice(nextForm);
      setResult(payload);
      setForm(payload.form);
    } catch (error) {
      setCalcError(error instanceof Error ? error.message : '계산 중 오류가 발생했습니다.');
    } finally {
      setCalcLoading(false);
    }
  }

  function handleChange(field: keyof CalculatorFormValues, value: string): void {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    void runCalculation(form);
  }

  function handleReset(): void {
    if (seedData) {
      const nextForm = {
        noticeNo: seedData.notice.noticeNo,
        baseAmount: String(seedData.baseAmountValue),
        aValue: String(seedData.aValueTotal),
        bidRate: stripPercent(seedData.judgement.selectedRate),
      };
      setForm(nextForm);
      void runCalculation(nextForm);
      return;
    }

    setForm(EMPTY_FORM);
    setResult(null);
    setCalcError(null);
  }

  const bannerTone = calcError
    ? 'error'
    : calcLoading || seedLoading
      ? 'default'
      : result?.status.tone ?? 'default';
  const bannerLabel = calcError
    ? '오류'
    : calcLoading || seedLoading
      ? '계산 중'
      : result?.status.label ?? '대기';
  const bannerText = calcError
    ? calcError
    : calcLoading || seedLoading
      ? '계산 결과를 확인하는 중입니다.'
      : result?.status.text ?? '공고번호 또는 금액 정보를 입력한 뒤 계산해 주세요.';

  return (
    <AppShell
      activeKey="calculator"
      pageLabel="가격 계산"
      title="투찰률과 금액을 바로 계산해 확인하세요"
      subtitle="공고번호를 입력하면 기본값을 불러오고, 직접 입력한 값도 바로 검증할 수 있습니다."
      actions={
        <div className="bc-inline-actions">
          <button className="bc-button" form="price-calculator-form" type="submit">
            계산 실행
          </button>
          <button className="bc-ghost-button" type="button" onClick={handleReset}>
            입력 초기화
          </button>
        </div>
      }
      aside={
        <div className="bc-stack">
          <Panel title="확인할 항목">
            <ul className="bc-bullet-list">
              <li>기초금액과 A값 입력을 다시 확인합니다.</li>
              <li>하한율 미달 여부를 색상과 텍스트로 함께 표시합니다.</li>
              <li>최종 제출 전 추천 결과 화면과 숫자가 일치해야 합니다.</li>
            </ul>
          </Panel>
          <Panel title="현재 상태">
            <div className="bc-list">
              <div className="bc-list-row">
                <span>추천 결과 불러오기</span>
                <strong>{seedError ? '오류' : seedLoading ? '조회 중' : '완료'}</strong>
              </div>
              <div className="bc-list-row">
                <span>계산 실행</span>
                <strong>{calcLoading ? '실행 중' : result ? '완료' : '대기'}</strong>
              </div>
              <div className="bc-list-row">
                <span>리포트 연계</span>
                <strong>{form.noticeNo ? '가능' : '대기'}</strong>
              </div>
            </div>
          </Panel>
        </div>
      }
    >
      <form id="price-calculator-form" onSubmit={handleSubmit}>
        <div className="bc-two-column">
          <Panel title="입력값" sub="필요한 값만 입력하면 바로 계산할 수 있습니다.">
            <div className="bc-form-grid">
              <label className="bc-field">
                <span>공고번호</span>
                <input
                  className="bc-input"
                  value={form.noticeNo}
                  onChange={(event) => handleChange('noticeNo', event.target.value)}
                />
              </label>
              <label className="bc-field">
                <span>기초금액</span>
                <input
                  className="bc-input"
                  value={form.baseAmount}
                  onChange={(event) => handleChange('baseAmount', event.target.value)}
                />
              </label>
              <label className="bc-field">
                <span>A값</span>
                <input
                  className="bc-input"
                  value={form.aValue}
                  onChange={(event) => handleChange('aValue', event.target.value)}
                />
              </label>
              <label className="bc-field">
                <span>투찰률</span>
                <input
                  className="bc-input"
                  value={form.bidRate}
                  onChange={(event) => handleChange('bidRate', event.target.value)}
                />
              </label>
            </div>

            <StatusBanner tone={bannerTone} label={bannerLabel} text={bannerText} />
          </Panel>

          <Panel title="계산 결과" sub="핵심 숫자와 판정을 먼저 보여줍니다.">
            {!result && !calcLoading ? (
              <div className="bc-state-card">공고번호와 계산 기준을 확인한 뒤 계산을 실행해 주세요.</div>
            ) : null}

            {result ? (
              <div className="bc-score-grid one-column">
                <article className="bc-score-card">
                  <div className="bc-score-label">예정가격</div>
                  <div className="bc-score-value">{result.result.plannedPrice}</div>
                </article>
                <article className="bc-score-card">
                  <div className="bc-score-label">투찰금액</div>
                  <div className="bc-score-value">{result.result.bidAmount}</div>
                </article>
                <article className="bc-score-card">
                  <div className="bc-score-label">가격점수</div>
                  <div className="bc-score-value">{result.result.priceScore}</div>
                </article>
                <article
                  className={`bc-score-card ${result.status.tone === 'success' ? 'tone-success' : ''}`.trim()}
                >
                  <div className="bc-score-label">최종 판정</div>
                  <div className="bc-score-value">{result.result.finalResult}</div>
                </article>
              </div>
            ) : null}
          </Panel>
        </div>
      </form>

      <div className="bc-content-grid">
        <Panel title="계산 순서">
          <div className="bc-timeline">
            <div className="bc-time-row">
              <b>01</b>
              <div>
                <strong>입력 검증</strong>
                <p>기초금액, A값, 투찰률 형식을 먼저 확인합니다.</p>
              </div>
            </div>
            <div className="bc-time-row">
              <b>02</b>
              <div>
                <strong>투찰금액 산출</strong>
                <p>기초금액과 투찰률을 기준으로 금액을 계산합니다.</p>
              </div>
            </div>
            <div className="bc-time-row">
              <b>03</b>
              <div>
                <strong>하한율 판정</strong>
                <p>하한율 통과 여부와 가격점수를 함께 표시합니다.</p>
              </div>
            </div>
          </div>
        </Panel>

        <Panel title="확인 결과">
          <div className="bc-list">
            {(result?.checks ?? []).map((item) => (
              <div key={item.label} className="bc-list-row">
                <span>{item.label}</span>
                <strong>{item.value}</strong>
              </div>
            ))}
            {!result && !calcLoading ? (
              <div className="bc-list-row">
                <span>검증 상태</span>
                <strong>대기</strong>
              </div>
            ) : null}
          </div>
          {form.noticeNo ? (
            <button
              className="bc-ghost-button top-gap"
              type="button"
              onClick={() => navigate(`/report/latest?bid_ntce_no=${form.noticeNo}`)}
            >
              AI 리포트로 이동
            </button>
          ) : null}
        </Panel>
      </div>
    </AppShell>
  );
}
