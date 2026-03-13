import React from 'react';
// Example only. Replace imports with your router package.
import {
  DashboardPage,
  NoticeSearchPage,
  RecommendationResultPage,
  PriceCalculatorPage,
  AiReportPage,
  HistoryPage,
  SettingsPage,
} from './index';

export const bidCompassRouteMap = [
  { path: '/dashboard', element: <DashboardPage /> },
  { path: '/notices/search', element: <NoticeSearchPage /> },
  { path: '/notices/recommendation', element: <RecommendationResultPage /> },
  { path: '/calculator', element: <PriceCalculatorPage /> },
  { path: '/report/latest', element: <AiReportPage /> },
  { path: '/history', element: <HistoryPage /> },
  { path: '/settings', element: <SettingsPage /> },
];
