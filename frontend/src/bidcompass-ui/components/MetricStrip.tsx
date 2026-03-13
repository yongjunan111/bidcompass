import React from 'react';
import type { MetricItem } from '../types';

interface MetricStripProps {
  items: MetricItem[];
}

export function MetricStrip({ items }: MetricStripProps): JSX.Element {
  return (
    <section className="bc-metric-grid">
      {items.map((item) => (
        <article key={`${item.label}-${item.value}`} className={`bc-metric-card ${item.tone ? `tone-${item.tone}` : ''}`.trim()}>
          <div className="bc-metric-label">{item.label}</div>
          <div className="bc-metric-value">{item.value}</div>
          {item.helper ? <div className="bc-metric-helper">{item.helper}</div> : null}
        </article>
      ))}
    </section>
  );
}
