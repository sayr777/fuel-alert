import type { EventType, ReportFeature } from "../types";
import { formatDate, gradeLabel } from "../utils";
import "./ReportList.css";

interface Props {
  reports: ReportFeature[];
  eventTypeMap: Record<string, EventType>;
  open: boolean;
  onToggle: () => void;
}

export default function ReportList({ reports, eventTypeMap, open, onToggle }: Props) {
  return (
    <div className={`report-list ${open ? "open" : ""}`}>
      <button className="report-list-toggle" onClick={onToggle}>
        {open ? "▶" : "◀"} Список ({reports.length})
      </button>
      {open && (
        <div className="report-list-body">
          {reports.length === 0 ? (
            <p className="report-list-empty">Нет отчётов по фильтрам</p>
          ) : (
            reports.map((r) => {
              const p = r.properties;
              const et = eventTypeMap[p.event_type];
              return (
                <article
                  key={p.id}
                  className="report-list-item"
                  style={{ borderLeftColor: et?.color ?? "#64748b" }}
                >
                  <div className="rli-top">
                    <strong>{et?.label_ru ?? p.event_type}</strong>
                    <span>{formatDate(p.event_at)}</span>
                  </div>
                  {p.fuel_grades && (
                    <div className="rli-meta">{p.fuel_grades.map(gradeLabel).join(", ")}</div>
                  )}
                  {p.price != null && <div className="rli-meta">{p.price} ₽/л</div>}
                  {p.description && <p className="rli-desc">{p.description}</p>}
                  <div className="rli-footer">
                    <span>{p.nickname}</span>
                    {p.confirmations_count > 0 && <span>✓ {p.confirmations_count}</span>}
                  </div>
                </article>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}