import React from 'react';
import { NavLink } from 'react-router-dom';

import type { NavItem, ShellProps } from '../types';

const NAV_ITEMS: NavItem[] = [
  { key: 'dashboard', label: '대시보드', desc: '공고 현황', href: '/dashboard' },
  { key: 'search', label: '공고 조회', desc: '공고 검색', href: '/notices/search' },
  { key: 'result', label: '추천 결과', desc: '추천안 확인', href: '/notices/recommendation' },
  { key: 'calculator', label: '가격 계산', desc: '숫자 검증', href: '/calculator' },
  { key: 'report', label: 'AI 리포트', desc: '설명과 근거', href: '/report/latest' },
  { key: 'history', label: '히스토리', desc: '최근 내역', href: '/history' },
  { key: 'settings', label: '설정', desc: '기본 옵션', href: '/settings' },
];

export function AppShell({
  activeKey,
  pageLabel,
  title,
  subtitle,
  children,
  aside,
  actions,
}: ShellProps): JSX.Element {
  return (
    <div className="bc-page">
      <div className="bc-stage">
        <div className="bc-window">
          <div className="bc-layout">
            <aside className="bc-sidebar">
              <div className="bc-brand">
                <div className="bc-brand-title">BidCompass</div>
                <div className="bc-brand-sub">공공입찰 추천 시스템</div>
              </div>

              <nav className="bc-nav" aria-label="주요 메뉴">
                {NAV_ITEMS.map((item) => (
                  <NavLink
                    key={item.key}
                    to={item.href ?? '/dashboard'}
                    className={`bc-nav-item ${activeKey === item.key ? 'is-active' : ''}`}
                  >
                    <span className="bc-nav-bullet" />
                    <span className="bc-nav-copy">
                      <strong>{item.label}</strong>
                      <small>{item.desc}</small>
                    </span>
                  </NavLink>
                ))}
              </nav>
            </aside>

            <main className="bc-main">
              <div className="bc-header-row">
                <div>
                  <div className="bc-eyebrow">{pageLabel}</div>
                  <h1 className="bc-page-title">{title}</h1>
                  <p className="bc-page-subtitle">{subtitle}</p>
                </div>
                {actions ? <div className="bc-header-actions">{actions}</div> : null}
              </div>

              {children}
            </main>

            <aside className="bc-aside">
              {aside ?? (
                <section className="bc-panel">
                  <h2 className="bc-panel-title">보조 패널</h2>
                  <p className="bc-panel-sub">필요한 페이지에서 우측 패널을 채워 사용합니다.</p>
                </section>
              )}
            </aside>
          </div>
        </div>
      </div>
    </div>
  );
}
