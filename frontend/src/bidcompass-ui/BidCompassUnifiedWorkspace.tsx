import React from 'react';
import { NavLink } from 'react-router-dom';

import type { NavKey } from './types';

const MENU: Array<{ key: NavKey; label: string; href: string }> = [
  { key: 'dashboard', label: '대시보드', href: '/dashboard' },
  { key: 'search', label: '공고 조회', href: '/notices/search' },
  { key: 'result', label: '추천 결과', href: '/notices/recommendation' },
  { key: 'calculator', label: '가격 계산', href: '/calculator' },
  { key: 'report', label: 'AI 리포트', href: '/report/latest' },
  { key: 'history', label: '히스토리', href: '/history' },
  { key: 'settings', label: '설정', href: '/settings' },
];

export default function BidCompassUnifiedWorkspace(): JSX.Element {
  return (
    <div className="bc-demo-wrap">
      <div className="bc-demo-switcher">
        {MENU.map((item) => (
          <NavLink key={item.key} to={item.href} className="bc-demo-tab">
            {item.label}
          </NavLink>
        ))}
      </div>

      <div className="bc-stage">
        <div className="bc-window">
          <div className="bc-main">
            <div className="bc-header-row">
              <div>
                <div className="bc-eyebrow">Unified Workspace</div>
                <h1 className="bc-page-title">연결된 화면군으로 바로 이동할 수 있습니다</h1>
                <p className="bc-page-subtitle">
                  Unified UI Kit는 실제 서비스 라우트에 연결되어 있습니다. 아래 메뉴로
                  대시보드, 공고 조회, 추천 결과, 계산기, 리포트, 히스토리, 설정 화면을
                  바로 확인할 수 있습니다.
                </p>
              </div>
            </div>

            <div className="bc-chip-row">
              {MENU.map((item) => (
                <NavLink key={item.href} to={item.href} className="bc-chip tone-accent">
                  <b />
                  {item.label}
                </NavLink>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
