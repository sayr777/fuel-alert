import { USE_MOCKS } from "./config";
import * as mockApi from "./mocks/api";
import type { EventType, Filters, ReportFeature, ReportFeatureCollection, Station } from "./types";

const API_BASE = import.meta.env.VITE_API_URL ?? "/api/v1";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

function moderatorHeaders(token: string): HeadersInit {
  return { "X-Moderator-Token": token };
}

export function fetchEventTypes(): Promise<EventType[]> {
  if (USE_MOCKS) return mockApi.mockFetchEventTypes();
  return fetchJson("/event-types");
}

export function fetchFuelGrades(): Promise<string[]> {
  if (USE_MOCKS) return mockApi.mockFetchFuelGrades();
  return fetchJson("/fuel-grades");
}

export function fetchReports(filters: Filters, bbox?: string): Promise<ReportFeatureCollection> {
  if (USE_MOCKS) return mockApi.mockFetchReports(filters, bbox);
  const params = new URLSearchParams({ status: "published" });
  if (filters.types.length) params.set("types", filters.types.join(","));
  if (filters.grades.length) params.set("grades", filters.grades.join(","));
  if (filters.dateFrom) params.set("from", new Date(filters.dateFrom).toISOString());
  if (filters.dateTo) {
    const end = new Date(filters.dateTo);
    end.setHours(23, 59, 59, 999);
    params.set("to", end.toISOString());
  }
  if (bbox) params.set("bbox", bbox);
  return fetchJson(`/reports?${params}`);
}

export function fetchStations(bbox?: string): Promise<Station[]> {
  if (USE_MOCKS) return mockApi.mockFetchStations(bbox);
  const params = bbox ? `?bbox=${bbox}` : "";
  return fetchJson(`/stations${params}`);
}

export function fetchModerationQueue(token: string): Promise<ReportFeature[]> {
  if (USE_MOCKS) return mockApi.mockFetchModerationQueue(token);
  return fetchJson("/moderation/queue", { headers: moderatorHeaders(token) });
}

export async function publishReport(
  token: string,
  reportId: number,
  moderatorId: string,
  comment?: string,
): Promise<void> {
  if (USE_MOCKS) return mockApi.mockPublishReport(reportId);
  const form = new FormData();
  form.append("moderator_id", moderatorId);
  if (comment) form.append("comment", comment);
  const res = await fetch(`${API_BASE}/moderation/${reportId}/publish`, {
    method: "POST",
    headers: moderatorHeaders(token),
    body: form,
  });
  if (!res.ok) throw new Error(`API ${res.status}: publish`);
}

export async function rejectReport(
  token: string,
  reportId: number,
  moderatorId: string,
  reason: string,
): Promise<void> {
  if (USE_MOCKS) return mockApi.mockRejectReport(reportId);
  const form = new FormData();
  form.append("moderator_id", moderatorId);
  form.append("reason", reason);
  const res = await fetch(`${API_BASE}/moderation/${reportId}/reject`, {
    method: "POST",
    headers: moderatorHeaders(token),
    body: form,
  });
  if (!res.ok) throw new Error(`API ${res.status}: reject`);
}