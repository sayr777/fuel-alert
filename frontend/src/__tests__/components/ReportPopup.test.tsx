import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ReportPopup from "../../components/ReportPopup";
import type { EventType, ReportFeature } from "../../types";

const EVENT_TYPE: EventType = {
  code: "NO_FUEL",
  label_ru: "Топливо отсутствует",
  color: "#FF4B3E",
  requires_moderation: false,
  ttl_hours: 120,
  attributes: ["fuel_grades"],
};

function makeReport(overrides: Partial<ReportFeature["properties"]> = {}): ReportFeature {
  return {
    type: "Feature",
    geometry: { type: "Point", coordinates: [37.62, 55.75] },
    properties: {
      id: 1,
      event_type: "NO_FUEL",
      fuel_grades: ["AI95", "DT"],
      description: "Нет топлива",
      price: null,
      extra: null,
      event_at: "2026-07-27T10:00:00Z",
      nickname: "testuser",
      station_id: null,
      photos: [],
      confirmations_count: 0,
      review_flags: null,
      ...overrides,
    },
  };
}

describe("ReportPopup", () => {
  it("renders event type label", () => {
    render(<ReportPopup report={makeReport()} eventType={EVENT_TYPE} />);
    expect(screen.getByText("Топливо отсутствует")).toBeInTheDocument();
  });

  it("renders fuel grades", () => {
    render(<ReportPopup report={makeReport()} eventType={EVENT_TYPE} />);
    expect(screen.getByText(/АИ-95/)).toBeInTheDocument();
    expect(screen.getByText(/ДТ/)).toBeInTheDocument();
  });

  it("renders nickname", () => {
    render(<ReportPopup report={makeReport()} eventType={EVENT_TYPE} />);
    expect(screen.getByText("testuser")).toBeInTheDocument();
  });

  it("renders price when present", () => {
    render(<ReportPopup report={makeReport({ price: 65.5 })} eventType={EVENT_TYPE} />);
    expect(screen.getByText(/65.5/)).toBeInTheDocument();
  });

  it("renders description", () => {
    render(<ReportPopup report={makeReport()} eventType={EVENT_TYPE} />);
    expect(screen.getByText("Нет топлива")).toBeInTheDocument();
  });

  it("renders confirmation badge when count > 0", () => {
    render(<ReportPopup report={makeReport({ confirmations_count: 3 })} eventType={EVENT_TYPE} />);
    expect(screen.getByText(/✓ 3/)).toBeInTheDocument();
  });

  it("does not show confirmation badge when count is 0", () => {
    render(<ReportPopup report={makeReport({ confirmations_count: 0 })} eventType={EVENT_TYPE} />);
    expect(screen.queryByText(/✓/)).not.toBeInTheDocument();
  });

  it("renders photo thumbnails", () => {
    const report = makeReport({
      photos: [{ url: "https://example.com/photo.jpg", taken_at: null }],
    });
    render(<ReportPopup report={report} eventType={EVENT_TYPE} />);
    expect(screen.getByRole("img", { name: "Фото отчёта" })).toBeInTheDocument();
  });

  it("renders extra fields — wait_minutes", () => {
    render(<ReportPopup report={makeReport({ extra: { wait_minutes: 30 } })} eventType={EVENT_TYPE} />);
    expect(screen.getByText(/30 мин/)).toBeInTheDocument();
  });

  it("falls back to event_type code when eventType prop is missing", () => {
    render(<ReportPopup report={makeReport()} />);
    expect(screen.getByText("NO_FUEL")).toBeInTheDocument();
  });
});
