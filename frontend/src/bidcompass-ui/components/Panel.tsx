import React, { type ReactNode } from 'react';

interface PanelProps {
  title: string;
  sub?: string;
  children: ReactNode;
  className?: string;
  key?: string;
}

export function Panel({ title, sub, children, className = '' }: PanelProps): JSX.Element {
  return (
    <section className={`bc-panel ${className}`.trim()}>
      <h2 className="bc-panel-title">{title}</h2>
      {sub ? <p className="bc-panel-sub">{sub}</p> : null}
      {children}
    </section>
  );
}
