import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchEventTypes, fetchFuelGrades, fetchReports, fetchStations } from "./api";
import FilterPanel from "./components/FilterPanel";
import Landing from "./components/Landing";
import Legend from "./components/Legend";
import MapView from "./components/MapView";
import ModerationPanel from "./components/ModerationPanel";
import PeriodControl from "./components/PeriodControl";
import ReportList from "./components/ReportList";
import type { EventType, Filters, ReportFeature, Station } from "./types";
import { NO_BRAND } from "./brands";
import { last24Hours } from "./utils";
import "./App.css";

const DEFAULT_FILTERS: Filters = {
  types: [],
  grades: [],
  brands: [],
  ...last24Hours(),
  showStations: true,
};

type View = "landing" | "map" | "moderation";

function pathToView(pathname: string): View {
  if (pathname.startsWith("/moderation")) return "moderation";
  if (pathname.startsWith("/map")) return "map";
  return "landing";
}

function viewToPath(view: View): string {
  if (view === "moderation") return "/moderation";
  if (view === "map") return "/map";
  return "/";
}

export default function App() {
  const [eventTypes, setEventTypes] = useState<EventType[]>([]);
  const [fuelGrades, setFuelGrades] = useState<string[]>([]);
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [allReports, setAllReports] = useState<ReportFeature[]>([]);
  const [stations, setStations] = useState<Station[]>([]);
  const [bbox, setBbox] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [panelOpen, setPanelOpen] = useState(false);
  const [listOpen, setListOpen] = useState(false);
  const [legendOpen, setLegendOpen] = useState(false);
  const [view, setViewState] = useState<View>(() => pathToView(window.location.pathname));

  const setView = useCallback((v: View) => {
    setViewState(v);
    const path = viewToPath(v);
    if (window.location.pathname !== path) {
      window.history.pushState(null, "", path);
    }
  }, []);

  useEffect(() => {
    const onPopState = () => setViewState(pathToView(window.location.pathname));
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    Promise.all([fetchEventTypes(), fetchFuelGrades()])
      .then(([types, grades]) => {
        setEventTypes(types);
        setFuelGrades(grades);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch ignoring the type filter so FilterPanel can show live per-type counts
      // even for types the user has currently unchecked; type filtering happens client-side.
      const [reportData, stationData] = await Promise.all([
        fetchReports({ ...filters, types: [] }, bbox),
        filters.showStations ? fetchStations(bbox) : Promise.resolve([]),
      ]);
      setAllReports(reportData.features);
      setStations(stationData);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }, [filters, bbox]);

  useEffect(() => {
    if (eventTypes.length) loadData();
  }, [loadData, eventTypes.length]);

  const reports = useMemo(
    () =>
      filters.types.length
        ? allReports.filter((r) => filters.types.includes(r.properties.event_type))
        : allReports,
    [allReports, filters.types],
  );

  const visibleStations = useMemo(
    () =>
      filters.showStations
        ? stations.filter((s) => !filters.brands.length || filters.brands.includes(s.brand ?? NO_BRAND))
        : [],
    [stations, filters.showStations, filters.brands],
  );

  const eventTypeMap = Object.fromEntries(eventTypes.map((t) => [t.code, t]));

  if (view === "landing") {
    return (
      <Landing
        eventTypes={eventTypes}
        onOpenMap={() => setView("map")}
      />
    );
  }

  if (view === "moderation") {
    return (
      <div className="app app--moderation">
        <ModerationPanel eventTypeMap={eventTypeMap} onClose={() => setView("map")} />
      </div>
    );
  }

  return (
    <div className="app app--map">
      <MapView
        reports={reports}
        stations={visibleStations}
        eventTypeMap={eventTypeMap}
        onBboxChange={setBbox}
      />

      <header className="overlay-header">
        <button className="header-brand header-brand-btn" onClick={() => setView("landing")}>
          <div className="logo-badge">⛽</div>
          <div>
            <h1>Топливный Дозор</h1>
            <p>Народный мониторинг АЗС</p>
          </div>
        </button>
        <div className="header-actions">
          {loading && <span className="status-pill">Загрузка…</span>}
          <PeriodControl filters={filters} onChange={setFilters} />
        </div>
      </header>

      <FilterPanel
        eventTypes={eventTypes}
        fuelGrades={fuelGrades}
        stations={stations}
        allReports={allReports}
        filters={filters}
        onChange={setFilters}
        onRefresh={loadData}
        open={panelOpen}
        onToggle={() => setPanelOpen((v) => !v)}
      />

      <ReportList
        reports={reports}
        eventTypeMap={eventTypeMap}
        open={listOpen}
        onToggle={() => setListOpen((v) => !v)}
      />

      <Legend
        eventTypes={eventTypes}
        open={legendOpen}
        onToggle={() => setLegendOpen((v) => !v)}
      />

      {error && <div className="error-banner">{error}</div>}
    </div>
  );
}