import type { EventType } from "../types";
import "./Legend.css";

interface Props {
  eventTypes: EventType[];
  open: boolean;
  onToggle: () => void;
}

export default function Legend({ eventTypes, open, onToggle }: Props) {
  return (
    <div className={`map-legend ${open ? "open" : ""}`}>
      <button className="map-legend-toggle" onClick={onToggle}>
        {open ? "▶" : "◀"} Легенда
      </button>
      {open && (
        <div className="map-legend-body">
          {eventTypes.slice(0, 6).map((et) => (
            <div key={et.code} className="legend-item">
              <span className="legend-dot" style={{ background: et.color }} />
              <span>{et.label_ru}</span>
            </div>
          ))}
          {eventTypes.length > 6 && (
            <div className="legend-more">+{eventTypes.length - 6} типов</div>
          )}
        </div>
      )}
    </div>
  );
}
