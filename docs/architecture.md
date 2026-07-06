# Архитектура и технологии

## Схема потоков данных

```
Водитель
  │
  ▼
Telegram-бот (aiogram)  ──HTTP (multipart)──►  FastAPI backend  ──►  PostgreSQL + PostGIS
  │                                                  │  │
  │                                                  │  └──► Redis (rate-limit)
  │                                                  └─────► S3/MinIO (фото)
  ▼
Веб-карта (React + MapLibre GL)  ◄──HTTP (JSON)──  FastAPI backend
  │
  └──► Панель модерации (тот же фронтенд, отдельный view, заголовок X-Moderator-Token)
```

## Технологический стек

| Слой | Технологии |
|---|---|
| Бэкенд API | Python 3.12, FastAPI, SQLAlchemy (async, `asyncpg`), Pydantic Settings |
| БД | PostgreSQL + расширение PostGIS (геометрия точек, `ST_DWithin`/`ST_Intersects` для дедупликации и bbox-выборок) |
| Кэш / rate-limit | Redis (sorted set, скользящее окно — `app/services/rate_limit.py`) |
| Объектное хранилище | S3-совместимое (MinIO в docker-compose) — фотографии обращений |
| Бот | Python 3.12, aiogram (FSM-сценарий), обращается к API как обычный HTTP-клиент |
| Фронтенд | React 19, TypeScript, Vite 6 |
| Карта | MapLibre GL JS, тайлы/стиль — публичный CARTO `dark-matter-gl-style` |
| Стили | Обычный CSS с токенами в `frontend/src/index.css` (без CSS-in-JS/Tailwind) |

## Backend (`backend/app`)

- `main.py` — точка входа FastAPI, регистрирует роутеры, CORS, фоновая задача `run_expiry_loop` (просрочка событий по `ttl_hours`).
- `event_types.py` — единый справочник типов событий (код, цвет, `requires_moderation`, `ttl_hours`, доп. атрибуты для бота). Отдаётся через `GET /api/v1/event-types` — и бот, и фронтенд читают его оттуда, а не хардкодят.
- `routers/` — `reports.py` (приём/выборка обращений), `moderation.py` (очередь, публикация/отклонение, авторизация по заголовку `X-Moderator-Token`), `stations.py` (справочник АЗС), `users.py`, `event_types.py`.
- `services/validation.py` — конвейер валидации нового обращения: рейт-лимит → проверка географической зоны покрытия (`region_bbox` в `config.py`) → давность события → дедупликация (тот же пользователь + тип события в радиусе `dedup_radius_m` за `dedup_window_minutes`) → публикация сразу или `status=pending`, если `event_type.requires_moderation` или есть `review_flags`.
- `services/rate_limit.py` — не чаще `rate_limit_per_hour` обращений в час с одного `telegram_id` (Redis ZSET со скользящим окном).
- `services/exif.py` + `check_exif_consistency` — читает EXIF фото (время съёмки, GPS), помечает `review_flags` (`exif_time_mismatch`, `exif_gps_mismatch`), если расходится с заявленными временем/координатами — это не отклоняет обращение, а просто отправляет его на ручную проверку.
- `services/serialization.py` — сборка `ReportFeature` (GeoJSON-подобная структура) для отдачи на фронтенд, включая фото и `review_flags`.

### Зона покрытия

`Settings.region_bbox` (`backend/app/config.py`) — bbox-заглушка (по умолчанию приблизительно европейская часть России — пилотный регион), `point_in_region()` отклоняет обращения вне неё. Это единственная область, где реально валидируются и хранятся данные; фронтенд предлагает выбор из всех регионов РФ, но данные вне заданного bbox бэкенд не примет.

## Бот (`bot/`)

- `main.py`, `handlers/start.py`, `handlers/report.py` — сценарий `/report`: тип события (кнопки по `event-types` из API) → марки топлива (если применимо) → доп. атрибуты по списку `attributes` конкретного типа (цена, лимит литров, время ожидания, номер колонки, причина, ссылка) → геолокация (обязательна, `reply-keyboard`) → до 2 фото файлом (чтобы сохранить EXIF) → описание → предпросмотр → отправка (`POST /reports`) → статус (опубликовано / на модерации / дубликат / отклонено).
- Никакого шага выбора сети/бренда АЗС в боте нет — привязка к станции (`station_id`) определяется бэкендом по геолокации (`find_nearest_station`, радиус `station_match_radius_m`), а не пользователем.
- `keyboards.py`, `states.py` — inline-клавиатуры и FSM-состояния диалога.

## Фронтенд (`frontend/src`)

SPA без роутера — переключение экранов через `useState<"landing" | "map" | "moderation">` в `App.tsx`.

- `components/Landing.tsx` — маркетинговая страница (лендинг), точка входа по умолчанию.
- `components/MapView.tsx` — MapLibre-карта: маркеры обращений/АЗС, попапы (React-компоненты, смонтированные через `createRoot` в `maplibregl.Popup`), региональный селектор (все субъекты РФ, камера-навигация), геолокация, локализация подписей карты на русский (`localizeLabelsToRussian`).
- `components/FilterPanel.tsx`, `PeriodControl.tsx`, `ReportList.tsx`, `Legend.tsx` — сворачиваемые вкладки-панели поверх карты (фильтры слева, список отчётов и легенда справа), период — сегмент-контрол в шапке.
- `components/ModerationPanel.tsx` — очередь модерации (таблица), вход по токену (`X-Moderator-Token`), публикация/отклонение.
- `api.ts` / `mocks/` — единая точка доступа к данным; `VITE_USE_MOCKS` (по умолчанию включён) переключает между реальным API и статичными демо-данными (`mocks/data.ts`) — удобно для разработки UI без поднятого бэкенда.
- `brands.ts`, `event_types` (приходят с бэкенда) — таблицы цветов/иконок для сетей АЗС и типов событий.

## Данные и модели (`backend/app/models`)

- `Report` — обращение: тип, координаты (`geom`, PostGIS `Point`), марки топлива, цена, доп. атрибуты (`extra`, JSON), статус (`pending` / `published` / `rejected` / `duplicate`), `review_flags`, привязка к станции, счётчик подтверждений.
- `Station` — справочник АЗС (имя, бренд, адрес, координаты).
- `User` — регистрация по `telegram_id`, никнейм (наружу отдаётся только он, не телефон/`user_id`).
- `ModerationLog` — журнал решений модератора (кто, когда, публикация/отклонение, комментарий).
