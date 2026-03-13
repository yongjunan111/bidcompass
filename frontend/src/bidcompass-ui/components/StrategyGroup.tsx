import React from 'react';
import type { StrategyCardData } from '../types';

interface StrategyGroupProps {
  items: StrategyCardData[];
  selectedKey: StrategyCardData['key'];
  onSelect: (key: StrategyCardData['key']) => void;
}

export function StrategyGroup({
  items,
  selectedKey,
  onSelect,
}: StrategyGroupProps): JSX.Element {
  return (
    <section className="bc-strategy-grid">
      {items.map((item) => (
        <button
          key={item.key}
          type="button"
          className={`bc-strategy-card tone-${item.key} ${selectedKey === item.key ? 'is-active' : ''}`.trim()}
          onClick={() => onSelect(item.key)}
        >
          <div className="bc-strategy-label">{item.label}</div>
          <div className="bc-strategy-rate">{item.rate}</div>
          <div className="bc-strategy-desc">{item.desc}</div>
          <div className="bc-strategy-foot">
            <span>{item.expectedRange}</span>
            <span>리스크 {item.risk}</span>
          </div>
        </button>
      ))}
    </section>
  );
}
