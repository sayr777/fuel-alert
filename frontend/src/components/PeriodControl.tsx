import { useState } from "react";
import type { Filters } from "../types";
import { isoDate } from "../utils";
import "./PeriodControl.css";

const PERIOD_PRESETS = [
  { label: "24 часа", days: 1 },
  { label: "3 дня", days: 3 },
  { label: "Неделя", days: 7 },
];

interface Props {
  filters: Filters;
  onChange: (f: Filters) => void;
}

export default function PeriodControl({ filters, onChange }: Props) {
  const [customOpen, setCustomOpen] = useState(false);

  const applyPreset = (days: number) => {
    const to = new Date();
    const from = new Date();
    from.setDate(from.getDate() - days);
    setCustomOpen(false);
    onChange({ ...filters, dateFrom: isoDate(from), dateTo: isoDate(to) });
  };

  const today = isoDate(new Date());
  const activePresetDays = PERIOD_PRESETS.find(
    (p) => filters.dateFrom === isoDate(new Date(Date.now() - p.days * 86_400_000)) && filters.dateTo === today,
  )?.days;
  const isCustomActive = !activePresetDays && Boolean(filters.dateFrom || filters.dateTo);

  return (
    <div className="period-control">
      <div className="seg-row">
        {PERIOD_PRESETS.map((p) => (
          <button
            key={p.label}
            className={`segb ${activePresetDays === p.days ? "on" : ""}`}
            onClick={() => applyPreset(p.days)}
          >
            {p.label}
          </button>
        ))}
        <button
          className={`segb ${customOpen || isCustomActive ? "on" : ""}`}
          onClick={() => setCustomOpen((v) => !v)}
        >
          Период…
        </button>
      </div>
      {customOpen && (
        <div className="period-popover">
          <label>
            <span>С</span>
            <input
              type="date"
              value={filters.dateFrom}
              onChange={(e) => onChange({ ...filters, dateFrom: e.target.value })}
            />
          </label>
          <label>
            <span>По</span>
            <input
              type="date"
              value={filters.dateTo}
              onChange={(e) => onChange({ ...filters, dateTo: e.target.value })}
            />
          </label>
        </div>
      )}
    </div>
  );
}
