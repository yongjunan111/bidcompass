import { startTransition, useEffect, useState } from 'react';

import type {
  AiReportData,
  CalculatorData,
  CalculatorRequest,
  DashboardData,
  HistoryData,
  NoticeSearchData,
  RecommendationData,
  SettingsData,
} from '../types';

type QueryValue = string | number | boolean | null | undefined;

interface ApiRequestOptions extends Omit<RequestInit, 'body' | 'headers'> {
  params?: Record<string, QueryValue>;
  body?: unknown;
  headers?: Record<string, string>;
}

export interface ApiResource<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  reload: () => void;
}

function getCsrfToken(): string {
  const token = document.cookie
    .split('; ')
    .find((entry) => entry.startsWith('csrftoken='))
    ?.split('=')[1];
  return token ?? '';
}

function buildUrl(path: string, params?: Record<string, QueryValue>): string {
  const url = new URL(path, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '') {
        return;
      }
      url.searchParams.set(key, String(value));
    });
  }
  return url.toString();
}

function buildRequestKey(path: string, params?: Record<string, QueryValue>): string {
  const parts = Object.entries(params ?? {})
    .filter(([, value]) => value !== undefined && value !== null && value !== '')
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, value]) => `${key}=${String(value)}`);
  return `${path}?${parts.join('&')}`;
}

async function requestJson<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { params, body, headers, ...rest } = options;
  const response = await fetch(buildUrl(path, params), {
    credentials: 'same-origin',
    ...rest,
    headers: {
      Accept: 'application/json',
      ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
      ...(body !== undefined && getCsrfToken() ? { 'X-CSRFToken': getCsrfToken() } : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  const text = await response.text();
  let payload: unknown = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch (error) {
      if (!response.ok) {
        throw new Error(`요청 처리에 실패했습니다. (${response.status})`);
      }
      throw error;
    }
  }

  if (!response.ok) {
    const message =
      typeof (payload as { error?: string } | null)?.error === 'string'
        ? (payload as { error: string }).error
        : `요청 처리에 실패했습니다. (${response.status})`;
    throw new Error(message);
  }

  return payload as T;
}

function useApiResource<T>(path: string, params?: Record<string, QueryValue>): ApiResource<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [reloadToken, setReloadToken] = useState(0);
  const requestKey = buildRequestKey(path, params);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    requestJson<T>(path, { params, signal: controller.signal })
      .then((payload) => {
        if (controller.signal.aborted) {
          return;
        }
        startTransition(() => {
          setData(payload);
        });
      })
      .catch((nextError: unknown) => {
        if (controller.signal.aborted) {
          return;
        }
        setError(nextError instanceof Error ? nextError.message : '알 수 없는 오류가 발생했습니다.');
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return () => controller.abort();
  }, [path, requestKey, reloadToken]);

  return {
    data,
    error,
    loading,
    reload: () => setReloadToken((current) => current + 1),
  };
}

export function useDashboardData(): ApiResource<DashboardData> {
  return useApiResource<DashboardData>('/api/ui/dashboard/');
}

export function useNoticeSearchData(query: string, region?: string): ApiResource<NoticeSearchData> {
  return useApiResource<NoticeSearchData>('/api/ui/notices/search/', { query, region });
}

export function useRecommendationData(
  bidNoticeNo?: string,
): ApiResource<RecommendationData> {
  return useApiResource<RecommendationData>('/api/ui/notices/recommendation/', {
    bid_ntce_no: bidNoticeNo,
  });
}

export function useAiReportData(bidNoticeNo?: string): ApiResource<AiReportData> {
  return useApiResource<AiReportData>('/api/ui/report/latest/', {
    bid_ntce_no: bidNoticeNo,
  });
}

export function useHistoryData(): ApiResource<HistoryData> {
  return useApiResource<HistoryData>('/api/ui/history/');
}

export function useSettingsData(): ApiResource<SettingsData> {
  return useApiResource<SettingsData>('/api/ui/settings/');
}

export async function calculatePrice(payload: CalculatorRequest): Promise<CalculatorData> {
  return requestJson<CalculatorData>('/api/ui/calculator/', {
    method: 'POST',
    body: payload,
  });
}
