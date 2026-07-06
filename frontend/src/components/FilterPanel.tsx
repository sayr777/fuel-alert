import type { CSSProperties } from "react";
import type { EventType, Filters, ReportFeature, Station } from "../types";
import { brandStyle, NO_BRAND } from "../brands";
import { gradeLabel, last24Hours } from "../utils";
import "./FilterPanel.css";

interface Props {
  eventTypes: EventType[];
  fuelGrades: string[];
  stations: Station[];
  allReports: ReportFeature[];
  filters: Filters;
  onChange: (f: Filters) => void;
  onRefresh: () => void;
  open: boolean;
  onToggle: () => void;
}

export default function FilterPanel({
  eventTypes,
  fuelGrades,
  stations,
  allReports,
  filters,
  onChange,
  onRefresh,
  open,
  onToggle,
}: Props) {
  const toggleType = (code: string) => {
    const types = filters.types.includes(code)
      ? filters.types.filter((t) => t !== code)
      : [...filters.types, code];
    onChange({ ...filters, types });
  };

  const toggleGrade = (code: string) => {
    const grades = filters.grades.includes(code)
      ? filters.grades.filter((g) => g !== code)
      : [...filters.grades, code];
    onChange({ ...filters, grades });
  };

  const toggleBrand = (brand: string) => {
    const brands = filters.brands.includes(brand)
      ? filters.brands.filter((b) => b !== brand)
      : [...filters.brands, brand];
    onChange({ ...filters, brands });
  };

  const reset = () => {
    onChange({ types: [], grades: [], brands: [], ...last24Hours(), showStations: true });
  };

  const typeCounts = Object.fromEntries(
    eventTypes.map((et) => [
      et.code,
      allReports.filter((r) => r.properties.event_type === et.code).length,
    ]),
  );

  const distinctBrandKeys = Array.from(new Set(stations.map((s) => s.brand ?? NO_BRAND))).sort(
    (a, b) => (a === NO_BRAND ? 1 : b === NO_BRAND ? -1 : a.localeCompare(b)),
  );

  return (
    <div className={`filter-panel ${open ? "open" : ""}`}>
      <button className="filter-panel-toggle" onClick={onToggle}>
        {open ? "◀" : "▶"} Фильтры
      </button>
      {open && (
        <div className="filter-panel-body">
          <div className="panel-section">
            <h2>Тип события</h2>
            <div className="chip-grid">
              {eventTypes.map((et) => (
                <button
                  key={et.code}
                  className={`chip ${filters.types.includes(et.code) ? "active" : ""}`}
                  style={{ "--chip-color": et.color } as CSSProperties}
                  onClick={() => toggleType(et.code)}
                >
                  <span className="chip-dot" />
                  {et.label_ru}
                  <span className="chip-count">{typeCounts[et.code] ?? 0}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="panel-section">
            <h2>Марка топлива</h2>
            <div className="chip-grid compact">
              {fuelGrades.map((g) => (
                <button
                  key={g}
                  className={`chip neutral ${filters.grades.includes(g) ? "active" : ""}`}
                  onClick={() => toggleGrade(g)}
                >
                  {gradeLabel(g)}
                </button>
              ))}
            </div>
          </div>

          {distinctBrandKeys.length > 0 && (
            <div className="panel-section">
              <h2>Сеть АЗС</h2>
              <div className="brand-row">
                {distinctBrandKeys.map((brand) => {
                  const style = brandStyle(brand === NO_BRAND ? null : brand);
                  const active = !filters.brands.length || filters.brands.includes(brand);
                  return (
                    <button
                      key={brand}
                      className={`brand-tog ${active ? "on" : ""}`}
                      title={brand === NO_BRAND ? "Без сети" : brand}
                      onClick={() => toggleBrand(brand)}
                    >
                      <span
                        className="brand-tog-icon"
                        style={{ background: style.color, color: style.textColor }}
                      >
                        {style.abbr}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          <div className="panel-section">
            <label className="toggle-row">
              <input
                type="checkbox"
                checked={filters.showStations}
                onChange={(e) => onChange({ ...filters, showStations: e.target.checked })}
              />
              Показать АЗС
            </label>
          </div>

          <div className="panel-actions">
            <button className="btn-primary" onClick={onRefresh}>
              Обновить
            </button>
            <button className="btn-ghost" onClick={reset}>
              Сбросить
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
