import React from 'react';

interface PageChipProps {
  items: string[];
  tone?: 'default' | 'accent';
}

export function PageChips({ items, tone = 'default' }: PageChipProps): JSX.Element {
  return (
    <div className="bc-chip-row">
      {items.map((item) => (
        <span key={item} className={`bc-chip tone-${tone}`.trim()}>
          <b />
          {item}
        </span>
      ))}
    </div>
  );
}
