import React, { type ReactNode } from 'react';

interface Column<T> {
  key: keyof T | string;
  label: string;
  render?: (row: T) => ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string;
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
}: DataTableProps<T>): JSX.Element {
  return (
    <div className="bc-table-wrap">
      <table className="bc-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={String(column.key)} className={column.className}>
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={rowKey(row)}>
              {columns.map((column) => (
                <td key={String(column.key)} className={column.className}>
                  {column.render ? column.render(row) : (row as Record<string, ReactNode>)[String(column.key)]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
