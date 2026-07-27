import { describe, expect, it } from "vitest";
import { flagLabel, formatExtra, gradeLabel, isoDate, last24Hours } from "../utils";

describe("gradeLabel", () => {
  it("translates known codes", () => {
    expect(gradeLabel("AI92")).toBe("АИ-92");
    expect(gradeLabel("AI95")).toBe("АИ-95");
    expect(gradeLabel("DT")).toBe("ДТ");
    expect(gradeLabel("GAS")).toBe("Газ");
  });

  it("returns unknown code as-is", () => {
    expect(gradeLabel("UNKNOWN")).toBe("UNKNOWN");
  });
});

describe("formatExtra", () => {
  it("returns empty array for null", () => {
    expect(formatExtra(null)).toEqual([]);
  });

  it("returns empty array for empty object", () => {
    expect(formatExtra({})).toEqual([]);
  });

  it("formats limit_liters", () => {
    expect(formatExtra({ limit_liters: 20 })).toContain("Лимит: 20 л");
  });

  it("formats wait_minutes", () => {
    expect(formatExtra({ wait_minutes: 45 })).toContain("Ожидание: 45 мин");
  });

  it("formats pump_number", () => {
    expect(formatExtra({ pump_number: 3 })).toContain("Колонка: 3");
  });

  it("formats multiple fields", () => {
    const lines = formatExtra({ limit_liters: 10, wait_minutes: 30 });
    expect(lines).toHaveLength(2);
    expect(lines[0]).toContain("Лимит");
    expect(lines[1]).toContain("Ожидание");
  });
});

describe("flagLabel", () => {
  it("translates known flags", () => {
    expect(flagLabel("exif_time_mismatch")).toBe("EXIF-время расходится");
    expect(flagLabel("exif_gps_mismatch")).toBe("EXIF-гео ≠ точке");
  });

  it("returns unknown flag as-is", () => {
    expect(flagLabel("unknown_flag")).toBe("unknown_flag");
  });
});

describe("isoDate", () => {
  it("formats date as YYYY-MM-DD", () => {
    const d = new Date("2026-07-27T12:34:56Z");
    expect(isoDate(d)).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});

describe("last24Hours", () => {
  it("returns dateFrom and dateTo strings", () => {
    const { dateFrom, dateTo } = last24Hours();
    expect(dateFrom).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(dateTo).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it("dateFrom is before dateTo", () => {
    const { dateFrom, dateTo } = last24Hours();
    expect(new Date(dateFrom).getTime()).toBeLessThanOrEqual(new Date(dateTo).getTime());
  });
});
