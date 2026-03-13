import React from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import BidCompassUnifiedWorkspace from './bidcompass-ui/BidCompassUnifiedWorkspace';
import { AiReportPage } from './bidcompass-ui/pages/AiReportPage';
import { DashboardPage } from './bidcompass-ui/pages/DashboardPage';
import { HistoryPage } from './bidcompass-ui/pages/HistoryPage';
import { NoticeSearchPage } from './bidcompass-ui/pages/NoticeSearchPage';
import { PriceCalculatorPage } from './bidcompass-ui/pages/PriceCalculatorPage';
import { RecommendationResultPage } from './bidcompass-ui/pages/RecommendationResultPage';
import { SettingsPage } from './bidcompass-ui/pages/SettingsPage';

export function App(): JSX.Element {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/notices/search" element={<NoticeSearchPage />} />
      <Route path="/notices/recommendation" element={<RecommendationResultPage />} />
      <Route path="/calculator" element={<PriceCalculatorPage />} />
      <Route path="/report/latest" element={<AiReportPage />} />
      <Route path="/history" element={<HistoryPage />} />
      <Route path="/settings" element={<SettingsPage />} />
      <Route path="/workspace" element={<BidCompassUnifiedWorkspace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
