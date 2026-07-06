import { useCallback, useEffect, useState } from "react";
import { fetchModerationQueue, fetchStations, publishReport, rejectReport } from "../api";
import type { EventType, ReportFeature, Station } from "../types";
import { flagLabel, formatExtra, gradeLabel } from "../utils";
import "./ModerationPanel.css";

const TOKEN_KEY = "fuelwatch-mod-token";
const MOD_ID_KEY = "fuelwatch-mod-id";

interface Props {
  eventTypeMap: Record<string, EventType>;
  onClose: () => void;
}

export default function ModerationPanel({ eventTypeMap, onClose }: Props) {
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY) ?? "");
  const [moderatorId, setModeratorId] = useState(() => sessionStorage.getItem(MOD_ID_KEY) ?? "moderator");
  const [queue, setQueue] = useState<ReportFeature[]>([]);
  const [stations, setStations] = useState<Record<number, Station>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    fetchStations()
      .then((list) => setStations(Object.fromEntries(list.map((s) => [s.id, s]))))
      .catch(() => {});
  }, []);

  const loadQueue = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const items = await fetchModerationQueue(token);
      setQueue(items);
      setAuthenticated(true);
      sessionStorage.setItem(TOKEN_KEY, token);
      sessionStorage.setItem(MOD_ID_KEY, moderatorId);
    } catch {
      setAuthenticated(false);
      setError("Неверный токен или ошибка API");
    } finally {
      setLoading(false);
    }
  }, [token, moderatorId]);

  useEffect(() => {
    const saved = sessionStorage.getItem(TOKEN_KEY);
    if (saved) {
      setToken(saved);
      fetchModerationQueue(saved)
        .then((items) => {
          setQueue(items);
          setAuthenticated(true);
        })
        .catch(() => setAuthenticated(false));
    }
  }, []);

  const handlePublish = async (id: number) => {
    try {
      await publishReport(token, id, moderatorId);
      setQueue((q) => q.filter((r) => r.properties.id !== id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка публикации");
    }
  };

  const handleReject = async (id: number) => {
    const reason = prompt("Причина отклонения:");
    if (!reason) return;
    try {
      await rejectReport(token, id, moderatorId, reason);
      setQueue((q) => q.filter((r) => r.properties.id !== id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка отклонения");
    }
  };

  if (!authenticated) {
    return (
      <div className="moderation-panel">
        <div className="mod-header">
          <h2>Модерация</h2>
          <button className="btn-ghost-sm" onClick={onClose}>← Карта</button>
        </div>
        <div className="mod-login">
          <p>Введите токен модератора (заголовок <code>X-Moderator-Token</code>)</p>
          <input
            type="password"
            placeholder="Токен"
            value={token}
            onChange={(e) => setToken(e.target.value)}
          />
          <input
            type="text"
            placeholder="ID модератора"
            value={moderatorId}
            onChange={(e) => setModeratorId(e.target.value)}
          />
          {error && <div className="mod-error">{error}</div>}
          <button className="btn-primary" onClick={loadQueue} disabled={!token || loading}>
            {loading ? "Проверка…" : "Войти"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mod">
      <div className="msb">
        <div className="mlogo">
          ДОЗОР<span className="acc">.</span>админ
        </div>
        <div className="msi on">
          <span>Очередь</span>
          <span className="mono fs11">{queue.length}</span>
        </div>
        <button className="btn-ghost-sm mod-back" onClick={onClose}>
          ← Карта
        </button>
      </div>

      <div className="mtb">
        <div className="mod-toolbar">
          <span className="fw6">Очередь проверки</span>
          <div className="mod-header-actions">
            {loading && <span className="status-pill">Обновление…</span>}
            <button className="btn-ghost-sm" onClick={loadQueue} disabled={loading}>
              ↻
            </button>
          </div>
        </div>

        {error && <div className="mod-error">{error}</div>}

        {queue.length === 0 ? (
          <div className="mod-empty">Очередь пуста — все отчёты обработаны.</div>
        ) : (
          <div className="mod-table">
            <div className="mrow mhead">
              <span>ID</span>
              <span>Тип</span>
              <span>Описание</span>
              <span>Автор</span>
              <span>АЗС</span>
              <span>Флаги</span>
              <span>Действия</span>
            </div>
            {queue.map((r) => {
              const p = r.properties;
              const et = eventTypeMap[p.event_type];
              const [lon, lat] = r.geometry.coordinates;
              const station = p.station_id != null ? stations[p.station_id] : undefined;
              const extraLines = formatExtra(p.extra);

              return (
                <div key={p.id} className="mrow">
                  <span className="mid">#{p.id}</span>
                  <span>
                    <span className="ebadge" style={{ "--c": et?.color } as React.CSSProperties}>
                      <span className="dot" />
                      {et?.label_ru ?? p.event_type}
                    </span>
                  </span>
                  <span className="mdesc">
                    {p.fuel_grades && <span className="mfuel">{p.fuel_grades.map(gradeLabel).join(", ")} · </span>}
                    {extraLines.length > 0 && <span className="mfuel">{extraLines.join(", ")} · </span>}
                    {p.description ?? "—"}
                  </span>
                  <span className="nick">{p.nickname}</span>
                  <span className="mstation">
                    {station
                      ? station.name
                      : `${lat.toFixed(4)}, ${lon.toFixed(4)}`}
                  </span>
                  <span className="mflags">
                    {p.review_flags && p.review_flags.length > 0 ? (
                      p.review_flags.map((f) => (
                        <span key={f} className="flag">
                          {flagLabel(f)}
                        </span>
                      ))
                    ) : (
                      <span className="mut">—</span>
                    )}
                  </span>
                  <span className="mactions">
                    <button className="abtn y" onClick={() => handlePublish(p.id)} title="Опубликовать">
                      ✓
                    </button>
                    <button className="abtn n" onClick={() => handleReject(p.id)} title="Отклонить">
                      ✕
                    </button>
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
