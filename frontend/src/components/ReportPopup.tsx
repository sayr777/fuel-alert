import { useState } from "react";
import { createPortal } from "react-dom";
import type { EventType, ReportFeature } from "../types";
import { formatDate, formatExtra, gradeLabel } from "../utils";
import "./ReportPopup.css";

interface Props {
  report: ReportFeature;
  eventType?: EventType;
}

function PhotoViewer({ url, onClose }: { url: string; onClose: () => void }) {
  const filename = url.split("/").pop() ?? "photo.jpg";

  const handleDownload = async () => {
    try {
      const res = await fetch(url);
      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(blobUrl);
    } catch {
      window.open(url, "_blank");
    }
  };

  return createPortal(
    <div className="photo-overlay" onClick={onClose}>
      <div className="photo-viewer" onClick={(e) => e.stopPropagation()}>
        <img src={url} alt="Фото" className="photo-full" />
        <div className="photo-controls">
          <button className="photo-btn" onClick={handleDownload} title="Скачать">
            ↓ Сохранить
          </button>
          <button className="photo-btn photo-btn-close" onClick={onClose} title="Закрыть">
            ✕
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}

export default function ReportPopup({ report, eventType }: Props) {
  const p = report.properties;
  const extraLines = formatExtra(p.extra);
  const [viewerUrl, setViewerUrl] = useState<string | null>(null);

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
              <button
                key={photo.url}
                className="photo-thumb-btn"
                onClick={() => setViewerUrl(photo.url)}
                title="Нажмите для просмотра"
              >
                <img src={photo.url} alt="Фото отчёта" loading="lazy" />
              </button>
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

      {viewerUrl && <PhotoViewer url={viewerUrl} onClose={() => setViewerUrl(null)} />}
    </div>
  );
}
