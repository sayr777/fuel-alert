const GRADE_LABELS: Record<string, string> = {
  AI92: "АИ-92",
  AI95: "АИ-95",
  AI98: "АИ-98",
  AI100: "АИ-100",
  DT: "ДТ",
  GAS: "Газ",
};

export function gradeLabel(code: string): string {
  return GRADE_LABELS[code] ?? code;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("ru-RU", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatExtra(extra: Record<string, unknown> | null): string[] {
  if (!extra) return [];
  const lines: string[] = [];
  if (extra.limit_liters != null) lines.push(`Лимит: ${extra.limit_liters} л`);
  if (extra.wait_minutes != null) lines.push(`Ожидание: ${extra.wait_minutes} мин`);
  if (extra.pump_number != null) lines.push(`Колонка: ${extra.pump_number}`);
  if (extra.reason != null) lines.push(`Причина: ${extra.reason}`);
  if (extra.link != null) lines.push(`Ссылка: ${extra.link}`);
  return lines;
}

const FLAG_LABELS: Record<string, string> = {
  exif_time_mismatch: "EXIF-время расходится",
  exif_gps_mismatch: "EXIF-гео ≠ точке",
};

export function flagLabel(code: string): string {
  return FLAG_LABELS[code] ?? code;
}

export function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export function last24Hours(): { dateFrom: string; dateTo: string } {
  return { dateFrom: isoDate(new Date(Date.now() - 24 * 3600_000)), dateTo: isoDate(new Date()) };
}