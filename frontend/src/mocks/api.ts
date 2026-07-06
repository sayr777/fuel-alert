import type { Filters, ReportFeature, ReportFeatureCollection, Station } from "../types";
import {
  MOCK_EVENT_TYPES,
  MOCK_FUEL_GRADES,
  MOCK_MODERATION_QUEUE,
  MOCK_REPORTS,
  MOCK_STATIONS,
} from "./data";

function inBbox(lon: number, lat: number, bbox?: string): boolean {
  if (!bbox) return true;
  const [minLon, minLat, maxLon, maxLat] = bbox.split(",").map(Number);
  return lon >= minLon && lon <= maxLon && lat >= minLat && lat <= maxLat;
}

function filterReports(features: ReportFeature[], filters: Filters, bbox?: string): ReportFeature[] {
  return features.filter((f) => {
    const [lon, lat] = f.geometry.coordinates;
    const p = f.properties;
    if (!inBbox(lon, lat, bbox)) return false;
    if (filters.types.length && !filters.types.includes(p.event_type)) return false;
    if (filters.grades.length) {
      if (!p.fuel_grades?.some((g) => filters.grades.includes(g))) return false;
    }
    if (filters.dateFrom && new Date(p.event_at) < new Date(filters.dateFrom)) return false;
    if (filters.dateTo) {
      const end = new Date(filters.dateTo);
      end.setHours(23, 59, 59, 999);
      if (new Date(p.event_at) > end) return false;
    }
    return true;
  });
}

const delay = () => new Promise((r) => setTimeout(r, 120));

export async function mockFetchEventTypes() {
  await delay();
  return MOCK_EVENT_TYPES;
}

export async function mockFetchFuelGrades() {
  await delay();
  return MOCK_FUEL_GRADES;
}

export async function mockFetchReports(filters: Filters, bbox?: string): Promise<ReportFeatureCollection> {
  await delay();
  const features = filterReports(MOCK_REPORTS, filters, bbox);
  return { type: "FeatureCollection", features, next_cursor: null };
}

export async function mockFetchStations(bbox?: string): Promise<Station[]> {
  await delay();
  return MOCK_STATIONS.filter((s) => inBbox(s.lon, s.lat, bbox));
}

export async function mockFetchModerationQueue(_token: string): Promise<ReportFeature[]> {
  await delay();
  return [...MOCK_MODERATION_QUEUE];
}

export async function mockPublishReport(reportId: number): Promise<void> {
  await delay();
  const idx = MOCK_MODERATION_QUEUE.findIndex((r) => r.properties.id === reportId);
  if (idx >= 0) MOCK_MODERATION_QUEUE.splice(idx, 1);
}

export async function mockRejectReport(reportId: number): Promise<void> {
  await delay();
  const idx = MOCK_MODERATION_QUEUE.findIndex((r) => r.properties.id === reportId);
  if (idx >= 0) MOCK_MODERATION_QUEUE.splice(idx, 1);
}