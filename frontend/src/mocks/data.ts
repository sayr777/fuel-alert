import type { EventType, ReportFeature, Station } from "../types";

/** Моки из дизайна «Топливный Дозор» — Камчатский край, Московская и Тульская области */

export const MOCK_EVENT_TYPES: EventType[] = [
  { code: "NO_FUEL", label_ru: "Топливо отсутствует", color: "#FF4B3E", requires_moderation: false, ttl_hours: 24, attributes: ["fuel_grades"] },
  { code: "FUEL_AVAILABLE", label_ru: "Топливо в наличии", color: "#3DDC84", requires_moderation: false, ttl_hours: 12, attributes: ["fuel_grades", "price"] },
  { code: "LIMITED_SALE", label_ru: "Лимит отпуска", color: "#FFB020", requires_moderation: false, ttl_hours: 24, attributes: ["fuel_grades", "limit_liters"] },
  { code: "LONG_QUEUE", label_ru: "Большая очередь", color: "#5B8CFF", requires_moderation: false, ttl_hours: 6, attributes: ["wait_minutes"] },
  { code: "OVERPRICE", label_ru: "Завышенная цена", color: "#FF7A1A", requires_moderation: false, ttl_hours: 48, attributes: ["fuel_grades", "price"] },
  { code: "STATION_CLOSED", label_ru: "АЗС закрыта", color: "#8A939E", requires_moderation: false, ttl_hours: 24, attributes: ["reason"] },
  { code: "ILLEGAL_SALE", label_ru: "Незаконная торговля", color: "#C554FF", requires_moderation: true, ttl_hours: 720, attributes: ["description"] },
  { code: "SHORT_MEASURE", label_ru: "Подозрение на недолив", color: "#35C8E8", requires_moderation: true, ttl_hours: 168, attributes: ["fuel_grades", "pump_number"] },
  { code: "FAKE_FUEL", label_ru: "Контрафактное топливо", color: "#FF4FA0", requires_moderation: true, ttl_hours: 168, attributes: ["fuel_grades"] },
  { code: "FRAUD", label_ru: "Мошенничество", color: "#7C3AED", requires_moderation: true, ttl_hours: 720, attributes: ["description", "link"] },
];

export const MOCK_FUEL_GRADES = ["AI92", "AI95", "AI98", "AI100", "DT", "GAS"];

export const MOCK_STATIONS: Station[] = [
  // Камчатский край
  { id: 1, name: "АЗС Лукойл", brand: "Лукойл", address: "ул. Ленинская, 28", lat: 53.044, lon: 158.631 },
  { id: 2, name: "АЗС Роснефть", brand: "Роснефть", address: "пр. Победы, 12", lat: 53.019, lon: 158.658 },
  { id: 3, name: "АЗС Газпромнефть", brand: "Газпромнефть", address: "ул. Советская, 45", lat: 53.058, lon: 158.602 },
  { id: 4, name: "АЗС Тебойл", brand: "Teboil", address: "Елизово, ул. Заречная", lat: 52.988, lon: 158.378 },
  { id: 5, name: "АЗС Вилючинск", brand: "Роснефть", address: "Вилючинск, ул. Мира", lat: 52.931, lon: 158.404 },
  { id: 6, name: "АЗС Мильково", brand: "Лукойл", address: "с. Мильково, трасса Р-474", lat: 54.683, lon: 157.318 },
  { id: 7, name: "АЗС Усть-Камчатск", brand: "Роснефть", address: "Усть-Камчатск", lat: 56.227, lon: 162.417 },
  { id: 8, name: "АЗС Ессо", brand: "Газпромнефть", address: "с. Ессо", lat: 55.927, lon: 159.235 },
  // Московская область
  { id: 9, name: "АЗС Лукойл", brand: "Лукойл", address: "Химки, Ленинградское ш., 10", lat: 55.897, lon: 37.451 },
  { id: 10, name: "АЗС Роснефть", brand: "Роснефть", address: "Балашиха, ш. Энтузиастов, 5", lat: 55.796, lon: 37.939 },
  { id: 11, name: "АЗС Газпромнефть", brand: "Газпромнефть", address: "Подольск, Варшавское ш., 44", lat: 55.431, lon: 37.545 },
  { id: 12, name: "АЗС Shell", brand: "Shell", address: "Одинцово, Можайское ш., 88", lat: 55.673, lon: 37.276 },
  // Тульская область
  { id: 13, name: "АЗС Роснефть", brand: "Роснефть", address: "Тула, пр. Ленина, 100", lat: 54.193, lon: 37.617 },
  { id: 14, name: "АЗС Лукойл", brand: "Лукойл", address: "Новомосковск, ул. Первомайская, 3", lat: 54.033, lon: 38.316 },
  // АЗС без опознанной сети/названия
  { id: 15, name: "АЗС без вывески", brand: null, address: "Камчатский край, трасса А-401, 15 км", lat: 53.101, lon: 158.553 },
  { id: 16, name: "АЗС", brand: null, address: "Московская обл., Ленинградское ш., 40 км", lat: 55.948, lon: 37.403 },
  { id: 17, name: "АЗС", brand: null, address: "Тульская обл., трасса М-2, 210 км", lat: 54.052, lon: 37.551 },
];

const h = (hoursAgo: number) => new Date(Date.now() - hoursAgo * 3600_000).toISOString();

export const MOCK_REPORTS: ReportFeature[] = [
  // Камчатский край
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [158.628, 53.045] },
    properties: {
      id: 1, event_type: "NO_FUEL", fuel_grades: ["AI95", "DT"],
      description: "На всех колонках табличка «топливо закончилось»", price: null,
      extra: null, event_at: h(2), nickname: "Водитель-4821", station_id: 1,
      photos: [], confirmations_count: 4, review_flags: null,
    },
  },
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [158.655, 53.018] },
    properties: {
      id: 2, event_type: "FUEL_AVAILABLE", fuel_grades: ["AI92", "AI95"],
      description: "Топливо появилось, очередь 3–4 машины", price: 68.9,
      extra: null, event_at: h(1), nickname: "Водитель-3102", station_id: 2,
      photos: [], confirmations_count: 2, review_flags: null,
    },
  },
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [158.595, 53.062] },
    properties: {
      id: 3, event_type: "LONG_QUEUE", fuel_grades: null,
      description: "Очередь до въезда на территорию", price: null,
      extra: { wait_minutes: 45 }, event_at: h(0.5), nickname: "Водитель-7744", station_id: 3,
      photos: [], confirmations_count: 6, review_flags: null,
    },
  },
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [158.702, 52.987] },
    properties: {
      id: 4, event_type: "LIMITED_SALE", fuel_grades: ["DT"],
      description: "Дизель — не более 40 л в одни руки", price: null,
      extra: { limit_liters: 40 }, event_at: h(260), nickname: "Водитель-1190", station_id: 4,
      photos: [], confirmations_count: 1, review_flags: null,
    },
  },
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [158.581, 53.091] },
    properties: {
      id: 5, event_type: "OVERPRICE", fuel_grades: ["AI95"],
      description: "Цена 89.5 ₽ — на соседней АЗС 68 ₽", price: 89.5,
      extra: null, event_at: h(100), nickname: "Водитель-5567", station_id: null,
      photos: [], confirmations_count: 3, review_flags: null,
    },
  },
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [158.404, 52.931] },
    properties: {
      id: 6, event_type: "STATION_CLOSED", fuel_grades: null,
      description: "АЗС закрыта на ремонт", price: null,
      extra: { reason: "ремонт колонок" }, event_at: h(30), nickname: "Водитель-2201", station_id: 5,
      photos: [], confirmations_count: 2, review_flags: null,
    },
  },
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [158.318, 54.683] },
    properties: {
      id: 7, event_type: "NO_FUEL", fuel_grades: ["AI92", "DT"],
      description: "Бензин и дизель закончились, ждут поставку", price: null,
      extra: null, event_at: h(50), nickname: "Водитель-9033", station_id: 6,
      photos: [], confirmations_count: 5, review_flags: null,
    },
  },
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [158.650, 53.038] },
    properties: {
      id: 8, event_type: "FUEL_AVAILABLE", fuel_grades: ["DT"],
      description: "Дизель в наличии, без очереди", price: 72.4,
      extra: null, event_at: h(0.25), nickname: "Водитель-6612", station_id: 1,
      photos: [], confirmations_count: 1, review_flags: null,
    },
  },
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [158.612, 53.051] },
    properties: {
      id: 9, event_type: "LIMITED_SALE", fuel_grades: ["AI95"],
      description: "Лимит 30 л на человека", price: null,
      extra: { limit_liters: 30 }, event_at: h(4), nickname: "Водитель-4488", station_id: 3,
      photos: [], confirmations_count: 7, review_flags: null,
    },
  },
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [158.670, 53.025] },
    properties: {
      id: 10, event_type: "LONG_QUEUE", fuel_grades: null,
      description: "Очередь на выезд с трассы", price: null,
      extra: { wait_minutes: 25 }, event_at: h(1.5), nickname: "Водитель-3355", station_id: 2,
      photos: [], confirmations_count: 2, review_flags: null,
    },
  },
  // Московская область
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [37.451, 55.897] },
    properties: {
      id: 14, event_type: "NO_FUEL", fuel_grades: ["AI95"],
      description: "95-го нет с обеда, привоз обещают к вечеру", price: null,
      extra: null, event_at: h(1.5), nickname: "Водитель-1204", station_id: 9,
      photos: [], confirmations_count: 3, review_flags: null,
    },
  },
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [37.939, 55.796] },
    properties: {
      id: 15, event_type: "FUEL_AVAILABLE", fuel_grades: ["AI92", "AI95"],
      description: "Все марки в наличии, очереди нет", price: 56.8,
      extra: null, event_at: h(0.5), nickname: "Водитель-8830", station_id: 10,
      photos: [], confirmations_count: 1, review_flags: null,
    },
  },
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [37.549, 55.428] },
    properties: {
      id: 16, event_type: "LONG_QUEUE", fuel_grades: null,
      description: "Очередь на въезд, минут 30", price: null,
      extra: { wait_minutes: 30 }, event_at: h(2), nickname: "Водитель-5521", station_id: 11,
      photos: [], confirmations_count: 4, review_flags: null,
    },
  },
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [37.276, 55.673] },
    properties: {
      id: 17, event_type: "OVERPRICE", fuel_grades: ["AI95"],
      description: "95-й дороже соседних АЗС на 8 рублей", price: 74.9,
      extra: null, event_at: h(90), nickname: "Водитель-9012", station_id: 12,
      photos: [], confirmations_count: 2, review_flags: null,
    },
  },
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [37.451, 55.897] },
    properties: {
      id: 18, event_type: "LIMITED_SALE", fuel_grades: ["DT"],
      description: "Дизель — лимит 40 литров в одни руки", price: null,
      extra: { limit_liters: 40 }, event_at: h(3), nickname: "Водитель-3344", station_id: 9,
      photos: [], confirmations_count: 1, review_flags: null,
    },
  },
  // Тульская область
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [37.617, 54.193] },
    properties: {
      id: 19, event_type: "NO_FUEL", fuel_grades: ["AI92", "AI95"],
      description: "92-й и 95-й закончились, ждут бензовоз", price: null,
      extra: null, event_at: h(170), nickname: "Водитель-7712", station_id: 13,
      photos: [], confirmations_count: 6, review_flags: null,
    },
  },
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [38.316, 54.033] },
    properties: {
      id: 20, event_type: "FUEL_AVAILABLE", fuel_grades: ["DT"],
      description: "Дизель в наличии, без очереди", price: 71.2,
      extra: null, event_at: h(0.75), nickname: "Водитель-2298", station_id: 14,
      photos: [], confirmations_count: 2, review_flags: null,
    },
  },
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [37.55, 54.15] },
    properties: {
      id: 21, event_type: "LONG_QUEUE", fuel_grades: null,
      description: "Очередь у выезда на М-4 «Дон»", price: null,
      extra: { wait_minutes: 20 }, event_at: h(1), nickname: "Водитель-6650", station_id: null,
      photos: [], confirmations_count: 3, review_flags: null,
    },
  },
  // АЗС без опознанной сети/названия
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [158.553, 53.101] },
    properties: {
      id: 23, event_type: "OVERPRICE", fuel_grades: ["AI92"],
      description: "Безымянная АЗС на трассе — 92-й дороже городского на 15 ₽", price: 82.0,
      extra: null, event_at: h(2.5), nickname: "Водитель-4470", station_id: 15,
      photos: [], confirmations_count: 1, review_flags: null,
    },
  },
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [37.403, 55.948] },
    properties: {
      id: 24, event_type: "FUEL_AVAILABLE", fuel_grades: ["AI92", "DT"],
      description: "Без вывески, но топливо есть, цена ниже сетевых", price: 54.5,
      extra: null, event_at: h(1), nickname: "Водитель-8801", station_id: 16,
      photos: [], confirmations_count: 2, review_flags: null,
    },
  },
];

export const MOCK_MODERATION_QUEUE: ReportFeature[] = [
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [158.640, 53.035] },
    properties: {
      id: 11, event_type: "ILLEGAL_SALE", fuel_grades: null,
      description: "Продажа канистрами у обочины М-11, без лицензии",
      price: null, extra: null, event_at: h(0.2), nickname: "Водитель-9901", station_id: null,
      photos: [], confirmations_count: 0, review_flags: null,
    },
  },
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [158.650, 53.041] },
    properties: {
      id: 12, event_type: "NO_FUEL", fuel_grades: ["AI95", "AI100"],
      description: "95-го и 100-го нет с самого утра, только ДТ",
      price: null, extra: null, event_at: h(0.5), nickname: "Водитель-2287", station_id: 1,
      photos: [], confirmations_count: 5, review_flags: null,
    },
  },
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [158.700, 52.990] },
    properties: {
      id: 13, event_type: "FAKE_FUEL", fuel_grades: ["AI92"],
      description: "После заправки двигатель троит, подозрение на разбавленный 92-й",
      price: null, extra: null, event_at: h(4), nickname: "Водитель-6120", station_id: null,
      photos: [], confirmations_count: 1, review_flags: ["exif_gps_mismatch"],
    },
  },
  {
    type: "Feature",
    geometry: { type: "Point", coordinates: [37.94, 55.80] },
    properties: {
      id: 22, event_type: "ILLEGAL_SALE", fuel_grades: null,
      description: "Продажа топлива из канистр у обочины А-108, без лицензии",
      price: null, extra: null, event_at: h(0.3), nickname: "Водитель-1300", station_id: null,
      photos: [], confirmations_count: 0, review_flags: null,
    },
  },
];
