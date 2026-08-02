export interface EventType {
  code: string;
  label_ru: string;
  color: string;
  requires_moderation: boolean;
  ttl_hours: number;
  attributes: string[];
}

export interface Photo {
  url: string;
  taken_at: string | null;
}

export interface ReportProperties {
  id: number;
  event_type: string;
  fuel_grades: string[] | null;
  description: string | null;
  price: number | null;
  extra: Record<string, unknown> | null;
  event_at: string;
  nickname: string;
  station_id: number | null;
  photos: Photo[];
  confirmations_count: number;
  review_flags: string[] | null;
  status?: string | null;
  reject_reason?: string | null;
}

export interface ReportFeature {
  type: "Feature";
  geometry: { type: "Point"; coordinates: [number, number] };
  properties: ReportProperties;
}

export interface ReportFeatureCollection {
  type: "FeatureCollection";
  features: ReportFeature[];
  next_cursor: string | null;
}

export interface Station {
  id: number;
  name: string;
  brand: string | null;
  address: string | null;
  lat: number;
  lon: number;
}

export interface ServiceHealth {
  status: "ok" | "error" | "unknown";
  latency_ms?: number;
  detail?: string;
}

export interface ContainerStatus {
  name: string;
  status: string;
  running: boolean;
}

export interface SystemMetrics {
  load_avg: { "1m": number; "5m": number; "15m": number } | null;
  memory: { total_mb: number; used_mb: number; available_mb: number; percent: number } | null;
  disk: { total_gb: number; used_gb: number; free_gb: number; percent: number } | null;
}

export interface HealthStatus {
  timestamp: string;
  database: ServiceHealth;
  redis: ServiceHealth;
  telegram: ServiceHealth;
  containers: ContainerStatus[];
  system?: SystemMetrics;
}

export interface Filters {
  types: string[];
  grades: string[];
  brands: string[];
  dateFrom: string;
  dateTo: string;
  showStations: boolean;
}