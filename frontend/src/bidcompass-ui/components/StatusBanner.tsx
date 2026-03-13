import React from 'react';

interface StatusBannerProps {
  tone?: 'default' | 'success' | 'warning' | 'error';
  label: string;
  text: string;
}

export function StatusBanner({
  tone = 'default',
  label,
  text,
}: StatusBannerProps): JSX.Element {
  return (
    <div className={`bc-status-banner tone-${tone}`.trim()}>
      <span>{text}</span>
      <span className={`bc-status-pill tone-${tone}`.trim()}>{label}</span>
    </div>
  );
}
