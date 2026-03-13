import React, { useEffect, useState } from 'react';

import { AppShell } from '../components/AppShell';
import { Panel } from '../components/Panel';
import { StatusBanner } from '../components/StatusBanner';
import { useSettingsData } from '../data/mock';
import type { SettingsOutputs, SettingsTeamDefaults } from '../types';

const EMPTY_DEFAULTS: SettingsTeamDefaults = {
  defaultStrategy: '',
  comparisonCount: '',
  warningLevel: '',
  decimalDisplay: '',
};

const EMPTY_OUTPUTS: SettingsOutputs = {
  defaultFormat: '',
  mailAlert: '',
  savePolicy: '',
  teamScope: '',
};

export function SettingsPage(): JSX.Element {
  const { data, error, loading, reload } = useSettingsData();
  const [teamDefaults, setTeamDefaults] = useState<SettingsTeamDefaults>(EMPTY_DEFAULTS);
  const [outputs, setOutputs] = useState<SettingsOutputs>(EMPTY_OUTPUTS);

  useEffect(() => {
    if (!data) {
      return;
    }
    setTeamDefaults(data.teamDefaults);
    setOutputs(data.outputs);
  }, [data]);

  function updateTeamDefaults(field: keyof SettingsTeamDefaults, value: string): void {
    setTeamDefaults((current) => ({
      ...current,
      [field]: value,
    }));
  }

  function updateOutputs(field: keyof SettingsOutputs, value: string): void {
    setOutputs((current) => ({
      ...current,
      [field]: value,
    }));
  }

  const hasConfigData = Boolean(
    teamDefaults.defaultStrategy ||
      teamDefaults.comparisonCount ||
      teamDefaults.warningLevel ||
      teamDefaults.decimalDisplay ||
      outputs.defaultFormat ||
      outputs.mailAlert ||
      outputs.savePolicy ||
      outputs.teamScope ||
      data?.audit.length ||
      data?.environment.length,
  );

  return (
    <AppShell
      activeKey="settings"
      pageLabel="설정"
      title="기본 설정과 알림 방식을 관리합니다"
      subtitle="서비스 사용에 필요한 기본 옵션을 이곳에서 확인합니다."
      actions={
        <div className="bc-inline-actions">
          <button className="bc-button" type="button" onClick={reload}>
            설정 새로고침
          </button>
        </div>
      }
    >
      <StatusBanner
        tone={error ? 'error' : loading ? 'default' : hasConfigData ? 'success' : 'warning'}
        label={error ? '오류' : loading ? '조회 중' : hasConfigData ? '준비 완료' : '준비 중'}
        text={
          error
            ? error
            : loading
              ? '설정값을 불러오는 중입니다.'
              : hasConfigData
                ? '설정값을 불러왔습니다.'
                : '설정 기능은 준비 중입니다.'
        }
      />

      {!hasConfigData && !loading ? (
        <Panel title="설정 안내" className="top-gap">
          <div className="bc-state-card">
            설정 저장 기능은 준비 중입니다.
          </div>
        </Panel>
      ) : null}

      {hasConfigData ? (
        <>
          <div className="bc-two-column top-gap">
            <Panel title="팀 기본 전략">
              <div className="bc-form-grid">
                <label className="bc-field">
                  <span>기본 추천안</span>
                  <input
                    className="bc-input"
                    value={teamDefaults.defaultStrategy}
                    onChange={(event) => updateTeamDefaults('defaultStrategy', event.target.value)}
                  />
                </label>
                <label className="bc-field">
                  <span>비교안 개수</span>
                  <input
                    className="bc-input"
                    value={teamDefaults.comparisonCount}
                    onChange={(event) => updateTeamDefaults('comparisonCount', event.target.value)}
                  />
                </label>
                <label className="bc-field">
                  <span>하한율 경고 기준</span>
                  <input
                    className="bc-input"
                    value={teamDefaults.warningLevel}
                    onChange={(event) => updateTeamDefaults('warningLevel', event.target.value)}
                  />
                </label>
                <label className="bc-field">
                  <span>표시 소수점</span>
                  <input
                    className="bc-input"
                    value={teamDefaults.decimalDisplay}
                    onChange={(event) => updateTeamDefaults('decimalDisplay', event.target.value)}
                  />
                </label>
              </div>
            </Panel>

            <Panel title="출력 및 알림">
              <div className="bc-form-grid">
                <label className="bc-field">
                  <span>기본 출력 형식</span>
                  <input
                    className="bc-input"
                    value={outputs.defaultFormat}
                    onChange={(event) => updateOutputs('defaultFormat', event.target.value)}
                  />
                </label>
                <label className="bc-field">
                  <span>메일 알림</span>
                  <input
                    className="bc-input"
                    value={outputs.mailAlert}
                    onChange={(event) => updateOutputs('mailAlert', event.target.value)}
                  />
                </label>
                <label className="bc-field">
                  <span>저장 정책</span>
                  <input
                    className="bc-input"
                    value={outputs.savePolicy}
                    onChange={(event) => updateOutputs('savePolicy', event.target.value)}
                  />
                </label>
                <label className="bc-field">
                  <span>팀 공유 범위</span>
                  <input
                    className="bc-input"
                    value={outputs.teamScope}
                    onChange={(event) => updateOutputs('teamScope', event.target.value)}
                  />
                </label>
              </div>
            </Panel>
          </div>

          <Panel title="권한 및 사용 기록">
            <div className="bc-list">
              {(data?.audit ?? []).map((item) => (
                <div key={item.label} className="bc-list-row">
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                </div>
              ))}
            </div>
          </Panel>
        </>
      ) : null}
    </AppShell>
  );
}
