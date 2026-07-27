import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchModerationQueue, fetchPublishedReports, fetchRejectedReports, fetchStations, publishReport, rejectReport, restoreReport, unpublishReport } from "../api";
import type { EventType, ReportFeature, Station } from "../types";
import { flagLabel, formatExtra, gradeLabel } from "../utils";
import "./ModerationPanel.css";

const TOKEN_KEY = "fuelwatch-mod-token";
const MOD_ID_KEY = "fuelwatch-mod-id";

type Tab = "queue" | "published" | "rejected";

interface Props {
  eventTypeMap: Record<string, EventType>;
  onClose: () => void;
}

export default function ModerationPanel({ eventTypeMap, onClose }: Props) {
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY) ?? "");
  const [moderatorId, setModeratorId] = useState(() => sessionStorage.getItem(MOD_ID_KEY) ?? "moderator");
  const [queue, setQueue] = useState<ReportFeature[]>([]);
  const [published, setPublished] = useState<ReportFeature[]>([]);
  const [rejected, setRejected] = useState<ReportFeature[]>([]);
  const [stations, setStations] = useState<Record<number, Station>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>("queue");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  useEffect(() => {
    fetchStations()
      .then((list) => setStations(Object.fromEntries(list.map((s) => [s.id, s]))))
      .catch(() => {});
  }, []);

  const loadAll = useCallback(async (tok: string) => {
    setLoading(true);
    setError(null);
    try {
      const [q, pub, rej] = await Promise.all([
        fetchModerationQueue(tok),
        fetchPublishedReports(tok),
        fetchRejectedReports(tok),
      ]);
      setQueue(q);
      setPublished(pub);
      setRejected(rej);
      setAuthenticated(true);
      sessionStorage.setItem(TOKEN_KEY, tok);
      sessionStorage.setItem(MOD_ID_KEY, moderatorId);
    } catch {
      setAuthenticated(false);
      setError("Неверный токен или ошибка API");
    } finally {
      setLoading(false);
    }
  }, [moderatorId]);

  useEffect(() => {
    const saved = sessionStorage.getItem(TOKEN_KEY);
    if (saved) {
      setToken(saved);
      loadAll(saved).catch(() => setAuthenticated(false));
    }
  }, []);

  const handlePublish = async (id: number) => {
    try {
      await publishReport(token, id, moderatorId);
      const item = queue.find((r) => r.properties.id === id);
      setQueue((q) => q.filter((r) => r.properties.id !== id));
      if (item) setPublished((prev) => [{ ...item, properties: { ...item.properties, status: "published" } }, ...prev]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка публикации");
    }
  };

  const handleReject = async (id: number) => {
    const reason = prompt("Причина отклонения:");
    if (!reason) return;
    try {
      await rejectReport(token, id, moderatorId, reason);
      const item = queue.find((r) => r.properties.id === id);
      setQueue((q) => q.filter((r) => r.properties.id !== id));
      if (item) setRejected((prev) => [{ ...item, properties: { ...item.properties, status: "rejected", reject_reason: reason } }, ...prev]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка отклонения");
    }
  };

  const handleUnpublish = async (id: number) => {
    const reason = prompt("Причина удаления с карты:");
    if (!reason) return;
    try {
      await unpublishReport(token, id, moderatorId, reason);
      const item = published.find((r) => r.properties.id === id);
      setPublished((p) => p.filter((r) => r.properties.id !== id));
      if (item) setRejected((prev) => [{ ...item, properties: { ...item.properties, status: "rejected", reject_reason: reason } }, ...prev]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка удаления");
    }
  };

  const handleRestore = async (id: number) => {
    try {
      await restoreReport(token, id, moderatorId);
      const item = rejected.find((r) => r.properties.id === id);
      setRejected((r) => r.filter((r) => r.properties.id !== id));
      if (item) setPublished((prev) => [{ ...item, properties: { ...item.properties, status: "published", reject_reason: null } }, ...prev]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка восстановления");
    }
  };

  const filteredPublished = useMemo(() => {
    return published.filter((r) => {
      const d = new Date(r.properties.event_at);
      if (dateFrom && d < new Date(dateFrom)) return false;
      if (dateTo) {
        const end = new Date(dateTo);
        end.setHours(23, 59, 59, 999);
        if (d > end) return false;
      }
      return true;
    });
  }, [published, dateFrom, dateTo]);

  if (!authenticated) {
    return (
      <div className="moderation-panel">
        <div className="mod-header">
          <h2>Модерация</h2>
          <button className="btn-ghost-sm" onClick={onClose}>← Карта</button>
        </div>
        <div className="mod-login">
          <p>Введите токен модератора</p>
          <input type="password" placeholder="Токен" value={token} onChange={(e) => setToken(e.target.value)} />
          <input type="text" placeholder="ID модератора" value={moderatorId} onChange={(e) => setModeratorId(e.target.value)} />
          {error && <div className="mod-error">{error}</div>}
          <button className="btn-primary" onClick={() => loadAll(token)} disabled={!token || loading}>
            {loading ? "Проверка…" : "Войти"}
          </button>
        </div>
      </div>
    );
  }

  const tabs: { id: Tab; label: string; count: number }[] = [
    { id: "queue", label: "Очередь", count: queue.length },
    { id: "published", label: "Опубликованные", count: filteredPublished.length },
    { id: "rejected", label: "Удалённые", count: rejected.length },
  ];

  const activeList = activeTab === "queue" ? queue : activeTab === "published" ? filteredPublished : rejected;
  const tabLabel = tabs.find((t) => t.id === activeTab)?.label ?? "";

  return (
    <div className="mod">
      <div className="msb">
        <div className="mlogo">ДОЗОР<span className="acc">.</span>админ</div>
        {tabs.map((t) => (
          <button key={t.id} className={`msi${activeTab === t.id ? " on" : ""}`} onClick={() => setActiveTab(t.id)}>
            <span>{t.label}</span>
            <span className="mono fs11">{t.count}</span>
          </button>
        ))}
        <button className="btn-ghost-sm mod-back" onClick={onClose}>← Карта</button>
      </div>

      <div className="mtb">
        <div className="mod-toolbar">
          <span className="fw6">{tabLabel}</span>
          <div className="mod-header-actions">
            {activeTab === "published" && (
              <div className="mod-date-filter">
                <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} title="От" />
                <span className="mut">—</span>
                <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} title="До" />
                {(dateFrom || dateTo) && (
                  <button className="btn-ghost-sm" onClick={() => { setDateFrom(""); setDateTo(""); }} title="Сбросить">✕</button>
                )}
              </div>
            )}
            {loading && <span className="status-pill">Обновление…</span>}
            <button className="btn-ghost-sm" onClick={() => loadAll(token)} disabled={loading}>↻</button>
          </div>
        </div>

        {error && <div className="mod-error">{error}</div>}

        {activeList.length === 0 ? (
          <div className="mod-empty">
            {activeTab === "queue" ? "Очередь пуста — все отчёты обработаны." : "Нет записей."}
          </div>
        ) : (
          <div className="mod-table">
            <div className={`mrow mhead${activeTab === "rejected" ? " mrow-rejected" : activeTab === "published" ? " mrow-published" : ""}`}>
              <span>ID</span>
              <span>Тип</span>
              <span>Описание</span>
              <span>Фото</span>
              <span>Автор</span>
              <span>АЗС</span>
              {activeTab === "queue" && <span>Флаги</span>}
              {activeTab === "rejected" && <span>Причина</span>}
              {activeTab === "published" && <span>Подтверждений</span>}
              <span>Действия</span>
            </div>
            {activeList.map((r) => {
              const p = r.properties;
              const et = eventTypeMap[p.event_type];
              const [lon, lat] = r.geometry.coordinates;
              const station = p.station_id != null ? stations[p.station_id] : undefined;
              const extraLines = formatExtra(p.extra);

              return (
                <div key={p.id} className={`mrow${activeTab === "rejected" ? " mrow-rejected" : activeTab === "published" ? " mrow-published" : ""}`}>
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
                  <span className="mphotos">
                    {p.photos.length > 0 ? p.photos.map((photo, i) => (
                      <a key={i} href={photo.url} target="_blank" rel="noopener noreferrer">
                        <img src={photo.url} alt="" className="mphoto-thumb" />
                      </a>
                    )) : <span className="mut">—</span>}
                  </span>
                  <span className="nick">{p.nickname}</span>
                  <span className="mstation">
                    {station ? station.name : `${lat.toFixed(4)}, ${lon.toFixed(4)}`}
                  </span>
                  {activeTab === "queue" && (
                    <span className="mflags">
                      {p.review_flags && p.review_flags.length > 0
                        ? p.review_flags.map((f) => <span key={f} className="flag">{flagLabel(f)}</span>)
                        : <span className="mut">—</span>}
                    </span>
                  )}
                  {activeTab === "rejected" && (
                    <span className="mreject-reason">{p.reject_reason ?? "—"}</span>
                  )}
                  {activeTab === "published" && (
                    <span className="mconfirm">{p.confirmations_count}</span>
                  )}
                  <span className="mactions">
                    {activeTab === "queue" && (
                      <>
                        <button className="abtn y" onClick={() => handlePublish(p.id)} title="Опубликовать">✓</button>
                        <button className="abtn n" onClick={() => handleReject(p.id)} title="Отклонить">✕</button>
                      </>
                    )}
                    {activeTab === "published" && (
                      <button className="abtn n" onClick={() => handleUnpublish(p.id)} title="Убрать с карты">🗑</button>
                    )}
                    {activeTab === "rejected" && (
                      <button className="abtn y" onClick={() => handleRestore(p.id)} title="Восстановить на карту">↩</button>
                    )}
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
