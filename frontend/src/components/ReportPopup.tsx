import type { EventType, ReportFeature } from "../types";
import { formatDate, formatExtra, gradeLabel } from "../utils";
import "./ReportPopup.css";

interface Props {
  report: ReportFeature;
  eventType?: EventType;
}

export default function ReportPopup({ report, eventType }: Props) {
  const p = report.properties;
  const extraLines = formatExtra(p.extra);

  return (
    <div className="report-popup">
      <div className="popup-header" style={{ borderColor: eventType?.color ?? "#3b82f6" }}>
        <span className="popup-type">{eventType?.label_ru ?? p.event_type}</span>
        <span className="popup-date">{formatDate(p.event_at)}</span>
      </div>

      <div className="popup-body">
        {p.fuel_grades && p.fuel_grades.length > 0 && (
          <div className="popup-row">
            <span className="label">Топливо</span>
            <span>{p.fuel_grades.map(gradeLabel).join(", ")}</span>
          </div>
        )}
        {p.price != null && (
          <div className="popup-row">
            <span className="label">Цена</span>
            <span>{p.price} ₽/л</span>
          </div>
        )}
        {extraLines.map((line) => (
          <div key={line} className="popup-row">
            {line}
          </div>
        ))}
        {p.description && <p className="popup-desc">{p.description}</p>}

        {p.photos.length > 0 && (
          <div className="popup-photos">
            {p.photos.map((photo) => (
              <a key={photo.url} href={photo.url} target="_blank" rel="noopener noreferrer">
                <img src={photo.url} alt="Фото отчёта" loading="lazy" />
              </a>
            ))}
          </div>
        )}
      </div>

      <div className="popup-footer">
        <span>{p.nickname}</span>
        {p.confirmations_count > 0 && (
          <span className="confirm-badge">✓ {p.confirmations_count}</span>
        )}
      </div>
    </div>
  );
}