import type { ReactNode } from 'react';

export type NavKey =
  | 'dashboard'
  | 'search'
  | 'result'
  | 'calculator'
  | 'report'
  | 'history'
  | 'settings';

export interface NavItem {
  key: NavKey;
  label: string;
  desc: string;
  href?: string;
}

export interface ShellProps {
  activeKey: NavKey;
  pageLabel: string;
  title: string;
  subtitle: string;
  children: ReactNode;
  aside?: ReactNode;
  actions?: ReactNode;
}

export interface MetricItem {
  label: string;
  value: string;
  tone?: 'default' | 'accent' | 'success' | 'warning';
  helper?: string;
}

export interface NoticeSummary {
  id: string;
  title: string;
  agency: string;
  deadline: string;
  estimate: string;
  sector: string;
  region: string;
}

export interface StrategyCardData {
  key: 'safe' | 'base' | 'aggressive';
  label: string;
  rate: string;
  risk: string;
  desc: string;
  summary: string[];
  reason: string;
  expectedRange: string;
  amount?: string;
}

export interface HistoryRow {
  id: string;
  noticeNo: string;
  title: string;
  strategy: string;
  bidRate: string;
  status: '완료' | '검토중' | '보관';
  updatedAt: string;
}

export interface ReportBlock {
  title: string;
  body: string;
  bullets: string[];
}

export interface KeyValueItem {
  label: string;
  value: string;
}

export interface ProgressItem extends KeyValueItem {
  progress: number;
}

export interface DashboardData {
  metrics: MetricItem[];
  todayNotices: NoticeSummary[];
  checklist: KeyValueItem[];
  memos: string[];
  weeklyStats: ProgressItem[];
}

export interface NoticeSearchData {
  query: string;
  count: number;
  results: NoticeSummary[];
  recent: KeyValueItem[];
  sourceStatus: KeyValueItem[];
}

export interface RecommendationNotice extends NoticeSummary {
  noticeNo: string;
}

export interface RecommendationJudgement {
  baseAmount: string;
  aValue: string;
  priceScore: string;
  passResult: string;
  selectedRate: string;
}

export interface RecommendationSimilar {
  count: string;
  median: string;
  variance: string;
  competition: string;
}

export interface RecommendationStatus {
  analysisStatus: string;
  updatedAt: string;
  reportVersion: string;
}

export interface RecommendationBand {
  low: string;
  high: string;
  halfWidth: string;
}

export interface RecommendationWarning {
  type: string;
  message: string;
  severity: 'info' | 'warning' | 'error';
}

export interface RecommendationData {
  notice: RecommendationNotice;
  strategies: StrategyCardData[];
  judgement: RecommendationJudgement;
  similar: RecommendationSimilar;
  status: RecommendationStatus;
  floorRate: string;
  floorBid: string;
  band: RecommendationBand;
  tableLabel: string;
  estimatedPrice: number;
  aValueTotal: number;
  baseAmountValue: number;
  floorRateBidValue: number;
  canRecommend: boolean;
  isExact: boolean;
  warningMessage: string | null;
  pendingReason: 'a_value' | 'base_amount' | 'both' | null;
  warnings?: RecommendationWarning[];
}

export interface BannerState {
  tone: 'default' | 'success' | 'warning' | 'error';
  label: string;
  text: string;
}

export interface CalculatorFormValues {
  noticeNo: string;
  baseAmount: string;
  aValue: string;
  bidRate: string;
}

export interface CalculatorRequest extends CalculatorFormValues {
  estimatedPrice?: string;
  workType?: string;
  netConstructionCost?: string;
}

export interface CalculatorData {
  form: CalculatorFormValues;
  status: BannerState;
  result: {
    plannedPrice: string;
    bidAmount: string;
    priceScore: string;
    finalResult: string;
  };
  checks: KeyValueItem[];
}

export interface AiReportData {
  metrics: MetricItem[];
  blocks: ReportBlock[];
  quoteText: string;
  evidenceRows: KeyValueItem[];
  actions: KeyValueItem[];
}

export interface HistoryData {
  rows: HistoryRow[];
  summary: KeyValueItem[];
  notes: string[];
}

export interface SettingsTeamDefaults {
  defaultStrategy: string;
  comparisonCount: string;
  warningLevel: string;
  decimalDisplay: string;
}

export interface SettingsOutputs {
  defaultFormat: string;
  mailAlert: string;
  savePolicy: string;
  teamScope: string;
}

export interface SettingsData {
  teamDefaults: SettingsTeamDefaults;
  outputs: SettingsOutputs;
  audit: KeyValueItem[];
  environment: KeyValueItem[];
}
