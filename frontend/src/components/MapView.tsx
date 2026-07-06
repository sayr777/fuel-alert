import { useEffect, useRef, useState } from "react";
import { createRoot, type Root } from "react-dom/client";
import maplibregl from "maplibre-gl";
import type { EventType, ReportFeature, Station } from "../types";
import { brandStyle } from "../brands";
import ReportPopup from "./ReportPopup";
import "maplibre-gl/dist/maplibre-gl.css";
import "./MapView.css";

const MAP_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

interface Region {
  name: string;
  center: [number, number]; // [lng, lat]
  zoom: number;
}

// Административные центры 89 субъектов РФ + обзорный пункт «Вся Россия».
// Камера просто перелетает к региону; пилот и реальная валидация — только европейская часть РФ.
const REGIONS: Record<string, Region> = {
  all: { name: "Вся Россия", center: [94, 62], zoom: 3 },
  adygea: { name: "Республика Адыгея", center: [39.9, 44.6], zoom: 8 },
  altai_krai: { name: "Алтайский край", center: [83.78, 53.35], zoom: 6 },
  altai_resp: { name: "Республика Алтай", center: [85.96, 51.96], zoom: 7 },
  amur: { name: "Амурская область", center: [127.54, 50.29], zoom: 5 },
  arkhangelsk: { name: "Архангельская область", center: [40.53, 64.54], zoom: 5 },
  astrakhan: { name: "Астраханская область", center: [48.04, 46.35], zoom: 7 },
  bashkortostan: { name: "Республика Башкортостан", center: [55.97, 54.74], zoom: 6 },
  belgorod: { name: "Белгородская область", center: [36.59, 50.6], zoom: 8 },
  bryansk: { name: "Брянская область", center: [34.42, 53.24], zoom: 7 },
  buryatia: { name: "Республика Бурятия", center: [107.6, 51.83], zoom: 5 },
  vladimir: { name: "Владимирская область", center: [40.41, 56.13], zoom: 7 },
  volgograd: { name: "Волгоградская область", center: [44.5, 48.71], zoom: 6 },
  vologda: { name: "Вологодская область", center: [39.89, 59.22], zoom: 6 },
  voronezh: { name: "Воронежская область", center: [39.21, 51.66], zoom: 7 },
  dagestan: { name: "Республика Дагестан", center: [47.5, 42.98], zoom: 7 },
  jao: { name: "Еврейская автономная область", center: [132.94, 48.79], zoom: 7 },
  zabaykalsky: { name: "Забайкальский край", center: [113.5, 52.03], zoom: 5 },
  ivanovo: { name: "Ивановская область", center: [40.98, 57.0], zoom: 8 },
  ingushetia: { name: "Республика Ингушетия", center: [44.81, 43.17], zoom: 9 },
  irkutsk: { name: "Иркутская область", center: [104.28, 52.29], zoom: 5 },
  kbr: { name: "Кабардино-Балкарская Республика", center: [43.6, 43.48], zoom: 8 },
  kaliningrad: { name: "Калининградская область", center: [20.51, 54.71], zoom: 8 },
  kalmykia: { name: "Республика Калмыкия", center: [44.27, 46.31], zoom: 6 },
  kaluga: { name: "Калужская область", center: [36.26, 54.51], zoom: 8 },
  kam: { name: "Камчатский край", center: [158.65, 53.04], zoom: 7 },
  kchr: { name: "Карачаево-Черкесская Республика", center: [41.9, 44.23], zoom: 8 },
  karelia: { name: "Республика Карелия", center: [34.36, 61.79], zoom: 6 },
  kemerovo: { name: "Кемеровская область", center: [86.09, 55.35], zoom: 6 },
  kirov: { name: "Кировская область", center: [49.67, 58.6], zoom: 6 },
  komi: { name: "Республика Коми", center: [50.84, 61.67], zoom: 5 },
  kostroma: { name: "Костромская область", center: [40.93, 57.77], zoom: 6 },
  krd: { name: "Краснодарский край", center: [38.98, 45.04], zoom: 7 },
  krasnoyarsk: { name: "Красноярский край", center: [92.87, 56.01], zoom: 4 },
  kurgan: { name: "Курганская область", center: [65.34, 55.45], zoom: 7 },
  kursk: { name: "Курская область", center: [36.19, 51.73], zoom: 7 },
  leningrad_obl: { name: "Ленинградская область", center: [30.9, 59.6], zoom: 7 },
  lipetsk: { name: "Липецкая область", center: [39.6, 52.6], zoom: 8 },
  magadan: { name: "Магаданская область", center: [150.8, 59.56], zoom: 5 },
  mari_el: { name: "Республика Марий Эл", center: [47.9, 56.63], zoom: 8 },
  mordovia: { name: "Республика Мордовия", center: [45.18, 54.18], zoom: 8 },
  moscow_city: { name: "Москва", center: [37.618, 55.751], zoom: 10 },
  msk: { name: "Московская область", center: [37.618, 55.751], zoom: 8 },
  murmansk: { name: "Мурманская область", center: [33.08, 68.97], zoom: 6 },
  nnov: { name: "Нижегородская область", center: [44.0, 56.33], zoom: 7 },
  novgorod: { name: "Новгородская область", center: [31.27, 58.52], zoom: 7 },
  nsk: { name: "Новосибирская область", center: [82.92, 55.03], zoom: 7 },
  omsk: { name: "Омская область", center: [73.37, 54.99], zoom: 6 },
  orenburg: { name: "Оренбургская область", center: [55.1, 51.77], zoom: 6 },
  oryol: { name: "Орловская область", center: [36.08, 52.97], zoom: 8 },
  penza: { name: "Пензенская область", center: [45.0, 53.2], zoom: 7 },
  perm: { name: "Пермский край", center: [56.23, 58.01], zoom: 6 },
  prm: { name: "Приморский край", center: [131.9, 43.12], zoom: 6 },
  pskov: { name: "Псковская область", center: [28.33, 57.82], zoom: 7 },
  rostov: { name: "Ростовская область", center: [39.7, 47.23], zoom: 6 },
  ryazan: { name: "Рязанская область", center: [39.72, 54.63], zoom: 7 },
  sakha: { name: "Республика Саха (Якутия)", center: [129.73, 62.03], zoom: 3 },
  sakhalin: { name: "Сахалинская область", center: [142.74, 46.96], zoom: 5 },
  samara: { name: "Самарская область", center: [50.15, 53.2], zoom: 7 },
  saratov: { name: "Саратовская область", center: [46.03, 51.53], zoom: 6 },
  ossetia: { name: "Республика Северная Осетия — Алания", center: [44.68, 43.02], zoom: 9 },
  svrd: { name: "Свердловская область", center: [60.597, 56.838], zoom: 6 },
  smolensk: { name: "Смоленская область", center: [32.05, 54.78], zoom: 7 },
  stavropol: { name: "Ставропольский край", center: [41.97, 45.04], zoom: 7 },
  tambov: { name: "Тамбовская область", center: [41.45, 52.72], zoom: 7 },
  tatarstan: { name: "Республика Татарстан", center: [49.11, 55.79], zoom: 6 },
  tver: { name: "Тверская область", center: [35.9, 56.86], zoom: 6 },
  tomsk: { name: "Томская область", center: [84.95, 56.49], zoom: 5 },
  tula: { name: "Тульская область", center: [37.62, 54.19], zoom: 8 },
  tuva: { name: "Республика Тыва", center: [94.45, 51.72], zoom: 6 },
  tyumen: { name: "Тюменская область", center: [65.53, 57.15], zoom: 5 },
  udmurtia: { name: "Удмуртская Республика", center: [53.23, 56.85], zoom: 7 },
  ulyanovsk: { name: "Ульяновская область", center: [48.4, 54.32], zoom: 7 },
  khabarovsk: { name: "Хабаровский край", center: [135.07, 48.48], zoom: 4 },
  khakassia: { name: "Республика Хакасия", center: [91.42, 53.72], zoom: 7 },
  khmao: { name: "Ханты-Мансийский АО — Югра", center: [69.0, 61.0], zoom: 5 },
  chelyabinsk: { name: "Челябинская область", center: [61.4, 55.16], zoom: 6 },
  chechnya: { name: "Чеченская Республика", center: [45.7, 43.32], zoom: 8 },
  chuvashia: { name: "Чувашская Республика", center: [47.25, 56.13], zoom: 8 },
  chukotka: { name: "Чукотский автономный округ", center: [177.5, 64.73], zoom: 4 },
  yanao: { name: "Ямало-Ненецкий автономный округ", center: [66.6, 66.53], zoom: 4 },
  yaroslavl: { name: "Ярославская область", center: [39.87, 57.63], zoom: 7 },
  spb: { name: "Санкт-Петербург", center: [30.314, 59.939], zoom: 10 },
  nenets: { name: "Ненецкий автономный округ", center: [53.0, 67.64], zoom: 5 },
  crimea: { name: "Республика Крым", center: [34.1, 44.95], zoom: 7 },
  sevastopol: { name: "Севастополь", center: [33.53, 44.6], zoom: 10 },
  dnr: { name: "Донецкая Народная Республика", center: [37.8, 48.0], zoom: 7 },
  lnr: { name: "Луганская Народная Республика", center: [39.31, 48.57], zoom: 7 },
  zaporizhzhia: { name: "Запорожская область", center: [35.37, 46.85], zoom: 7 },
  kherson: { name: "Херсонская область", center: [32.62, 46.64], zoom: 7 },
};

const DEFAULT_REGION = "msk";

// CARTO's carto.streets vector schema only has two name fields per feature: `name` (local
// language — Cyrillic for Russian places) and `name_en`. Country/state/continent/big-city-dot
// labels and waterway names are hardcoded to name_en at every zoom in the stock style, and the
// place/lake labels switch from name_en to name only above a zoom threshold. Force every one of
// those layers to always use the local `name` field instead.
function localizeLabelsToRussian(map: maplibregl.Map) {
  const style = map.getStyle();
  if (!style?.layers) return;
  for (const layer of style.layers) {
    if (layer.type !== "symbol") continue;
    const current = map.getLayoutProperty(layer.id, "text-field");
    if (current == null || !JSON.stringify(current).includes("name_en")) continue;
    map.setLayoutProperty(layer.id, "text-field", ["get", "name"]);
  }
}

interface MarkerHandle {
  marker: maplibregl.Marker;
  root: Root;
}

interface Props {
  reports: ReportFeature[];
  stations: Station[];
  eventTypeMap: Record<string, EventType>;
  onBboxChange: (bbox: string) => void;
}

export default function MapView({ reports, stations, eventTypeMap, onBboxChange }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<MarkerHandle[]>([]);
  const onBboxChangeRef = useRef(onBboxChange);
  onBboxChangeRef.current = onBboxChange;
  const [mapReady, setMapReady] = useState(false);
  const [region, setRegion] = useState(DEFAULT_REGION);

  useEffect(() => {
    if (!containerRef.current) return;
    const r = REGIONS[DEFAULT_REGION];
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: MAP_STYLE,
      center: r.center,
      zoom: r.zoom,
      attributionControl: false,
    });
    map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

    const emitBbox = () => {
      const b = map.getBounds();
      onBboxChangeRef.current(
        [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()].map((n) => n.toFixed(5)).join(","),
      );
    };
    map.on("load", () => {
      localizeLabelsToRussian(map);
      emitBbox();
      setMapReady(true);
    });
    map.on("moveend", emitBbox);
    map.on("zoomend", emitBbox);

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

    markersRef.current.forEach(({ marker, root }) => {
      marker.remove();
      root.unmount();
    });
    markersRef.current = [];

    stations.forEach((s) => {
      const brand = brandStyle(s.brand);
      const el = document.createElement("div");
      el.className = "dzmk";
      el.style.background = brand.color;

      const popupNode = document.createElement("div");
      const root = createRoot(popupNode);
      root.render(
        <div className="station-popup">
          <strong>{s.name}</strong>
          {s.brand && (
            <div className="muted">
              <span
                className="brand-chip"
                style={{ background: brand.color, color: brand.textColor }}
              >
                {brand.abbr}
              </span>{" "}
              {s.brand}
            </div>
          )}
          {s.address && <div className="muted">{s.address}</div>}
        </div>,
      );

      const marker = new maplibregl.Marker({ element: el, anchor: "center" })
        .setLngLat([s.lon, s.lat])
        .setPopup(new maplibregl.Popup({ offset: 14, maxWidth: "260px" }).setDOMContent(popupNode))
        .addTo(map);
      markersRef.current.push({ marker, root });
    });

    reports.forEach((r) => {
      const [lon, lat] = r.geometry.coordinates;
      const et = eventTypeMap[r.properties.event_type];
      const color = et?.color ?? "#3b82f6";
      const size = 15 + Math.min(r.properties.confirmations_count, 5) * 2;

      const el = document.createElement("div");
      el.className = "dzmk";
      el.style.background = color;
      el.style.width = `${size}px`;
      el.style.height = `${size}px`;

      const popupNode = document.createElement("div");
      const root = createRoot(popupNode);
      root.render(<ReportPopup report={r} eventType={et} />);

      const marker = new maplibregl.Marker({ element: el, anchor: "center" })
        .setLngLat([lon, lat])
        .setPopup(new maplibregl.Popup({ offset: 14, maxWidth: "300px" }).setDOMContent(popupNode))
        .addTo(map);
      markersRef.current.push({ marker, root });
    });
  }, [reports, stations, eventTypeMap, mapReady]);

  const gotoRegion = (key: string) => {
    setRegion(key);
    const r = REGIONS[key];
    mapRef.current?.flyTo({ center: r.center, zoom: r.zoom, duration: 900 });
  };

  const locate = () => {
    if (!navigator.geolocation) {
      alert("Геолокация недоступна");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        mapRef.current?.flyTo({ center: [longitude, latitude], zoom: 12, duration: 1000 });
        const el = document.createElement("div");
        el.className = "dzmk big";
        new maplibregl.Marker({ element: el, anchor: "center" })
          .setLngLat([longitude, latitude])
          .setPopup(new maplibregl.Popup({ offset: 14 }).setHTML('<b style="color:#FFC800">Вы здесь</b>'))
          .addTo(mapRef.current!);
      },
      () => alert("Не удалось определить местоположение"),
      { enableHighAccuracy: true, timeout: 8000 },
    );
  };

  return (
    <div className="map-container">
      <div ref={containerRef} className="map-canvas" />

      <div className="map-toolbar">
        <div className="rsel">
          <select value={region} onChange={(e) => gotoRegion(e.target.value)}>
            {Object.entries(REGIONS).map(([key, r]) => (
              <option key={key} value={key}>
                {r.name}
              </option>
            ))}
          </select>
          <div className="geoloc" onClick={locate}>
            <svg className="pin-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.4}>
              <path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11z" />
              <circle cx="12" cy="10" r="2.4" />
            </svg>
            Я здесь
          </div>
        </div>
      </div>
    </div>
  );
}
