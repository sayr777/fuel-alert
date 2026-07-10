# Документация для установщиков и администраторов

## Требования

- Docker + Docker Compose (рекомендуемый способ запуска инфраструктуры и API/бота).
- Node.js 22+ и npm — для локальной разработки фронтенда без Docker.
- Токен Telegram-бота от [@BotFather](https://t.me/BotFather), если нужен приём обращений (не
  только просмотр карты).

## Быстрый старт — локальная разработка (Docker)

```bash
cp .env.example .env
# заполните BOT_TOKEN в .env, если планируете поднимать бота

docker compose up -d                 # PostgreSQL/PostGIS, Redis, MinIO, инициализация БД, API
docker compose --profile bot up -d   # + Telegram-бот (отдельный профиль, по желанию)
```

Что поднимается (`docker-compose.yml` в корне репо — только для локального dev):

| Сервис | Порт | Назначение |
|---|---|---|
| `db` (PostGIS 16) | 5432 | Основная БД |
| `redis` | 6379 | Rate-limit обращений |
| `minio` | 9000 (API), 9001 (консоль) | Хранилище фото (локально вместо Yandex Object Storage) |
| `api-init` | — | Разовая инициализация схемы + сид демо-данных, затем выходит |
| `api` (FastAPI) | 8000 | Backend API |
| `bot` (профиль `bot`) | — | Telegram-бот, требует `BOT_TOKEN` |

Проверка: `curl http://localhost:8000/health` → `{"status": "ok"}`.

## Деплой на сервер (Yandex Cloud VM)

Для производственного деплоя используется отдельный `deploy/docker-compose.yml`, который:
- Использует **Yandex Object Storage** вместо MinIO.
- Запускает **фронтенд в контейнере** (nginx на порту 80), проксирующем `/api/` на бэкенд.
- Не открывает порты БД/Redis наружу.

Полная инструкция: [`deploy/DEPLOY.md`](../deploy/DEPLOY.md).

## Переменные окружения (`.env`, см. `.env.example`)

| Переменная | Назначение |
|---|---|
| `DATABASE_URL` | Строка подключения к PostgreSQL (`postgresql+asyncpg://...`) |
| `REDIS_URL` | Подключение к Redis |
| `S3_ENDPOINT_URL` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` / `S3_BUCKET` / `S3_PUBLIC_URL` | Объектное хранилище фото (MinIO локально, любой S3-совместимый в проде) |
| `MODERATOR_TOKEN` | Общий секрет для входа в панель модерации (заголовок `X-Moderator-Token`) — **обязательно смените дефолтное значение перед продакшеном** |
| `BOT_TOKEN` | Токен Telegram-бота от BotFather |
| `API_BASE_URL` | Адрес API, который использует бот (внутри docker-сети — `http://api:8000/api/v1`) |

Дополнительные тонкие настройки валидации — в `backend/app/config.py` (не через `.env` по
умолчанию, но легко вынести): `region_bbox` (зона покрытия), `rate_limit_per_hour`,
`dedup_radius_m`, `dedup_window_minutes`, `station_match_radius_m`, `max_event_age_hours`,
`exif_gps_mismatch_km`, `max_photos_per_report`, `max_description_length`.

> ⚠️ `region_bbox` по умолчанию — приблизительный прямоугольник вокруг европейской части России
> (пилотный регион), без Калининградской области (эксклав, не влезает в общий bbox без захвата
> территории Белоруссии/Прибалтики). Это **единственная** зона, где бэкенд примет обращение
> (`point_in_region`). Перед запуском в другом регионе обязательно поменяйте это значение — иначе
> все обращения будут отклоняться как «вне зоны покрытия».

## Запуск фронтенда

```bash
cd frontend
npm install
npm run dev      # разработка, http://localhost:5173
npm run build    # прод-сборка в dist/
```

Приложение — SPA с тремя URL, переключаемыми через History API (без react-router): `/` (лендинг),
`/map` (карта), `/moderation` (панель модератора) — каждый открывается напрямую по ссылке. Для
статического хостинга нужен fallback всех путей на `index.html`; `frontend/public/_redirects`
(формат Netlify/Cloudflare Pages: `/*  /index.html  200`) уже включён в сборку.

### Бесплатный хостинг фронтенда

`dist/` — статические файлы, деплою куда угодно. Бесплатные варианты с готовой поддержкой SPA-fallback:

- **Cloudflare Pages** — `_redirects` уже лежит в `frontend/public/`, ничего доп. настраивать не надо; build command `npm run build`, output `dist`.
- **Netlify** — тот же `_redirects` работает как есть.
- **Vercel** — тоже подходит, но нужен свой `vercel.json` с rewrite на `/index.html` (формат `_redirects` не поддерживается).
- **GitHub Pages** — SPA-роутинг не поддерживает нативно (нет server-side fallback), нужен трюк с `404.html` — для этого проекта проще одна из площадок выше.

Не забудьте задать `VITE_USE_MOCKS=false` и `VITE_API_URL` при сборке для этих площадок, если нужен
реальный бэкенд, а не демо-данные (по умолчанию сборка использует моки).

Переменные окружения фронтенда (Vite, префикс `VITE_`):

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `VITE_USE_MOCKS` | включено (кроме явных `false`/`0`) | Использовать статичные демо-данные (`src/mocks/`) вместо реального API — удобно для UI-разработки без бэкенда |
| `VITE_API_URL` | `/api/v1` | Адрес backend API, если моки выключены |
| `VITE_TELEGRAM_BOT_URL` | `https://t.me/fuelwatch_bot` | Ссылка на бота для кнопок «Сообщить в боте» |

Для прод-сборки с реальным бэкендом: `VITE_USE_MOCKS=false VITE_API_URL=https://ваш-домен/api/v1 npm run build`.

Карта использует внешний тайл-сервис CARTO (`basemaps.cartocdn.com`) — фронтенду нужен исходящий
доступ в интернет. Для продакшена с высоким трафиком стоит учитывать, что это бесплатный демо-стиль
CARTO с ограничениями по нагрузке — рассмотреть самостоятельный хостинг тайлов при росте аудитории.

## Доступ модератора

Модерация защищена одним общим токеном (`MODERATOR_TOKEN` / заголовок `X-Moderator-Token`) — это
осознанное упрощение для небольшой команды на этапе MVP (см. комментарий в
`backend/app/deps.py:require_moderator`). Перед расширением круга модераторов стоит заменить на
полноценные аккаунты с логированием личности модератора (сейчас в лог решений `ModerationLog`
пишется произвольная строка `moderator_id`, которую вводит сам модератор — не аутентифицированная
личность).

Как выдать доступ модератору сейчас: сообщить ему значение `MODERATOR_TOKEN` и адрес панели
(«Модерация» на сайте) — он вводит токен и любой ID на экране входа.

## Демо-данные и сиды

- `backend/scripts/init_db.py` — создание схемы БД.
- `backend/scripts/seed_demo.py` — демонстрационные обращения.
- `backend/scripts/seed_stations.py` — справочник АЗС.

В локальном `docker-compose.yml` `api-init` вызывает все три: `init_db.py` + `seed_demo.py` + `seed_stations.py`. В продовом `deploy/docker-compose.yml` — только `init_db.py` (демо-данные на проде не нужны).

## Эксплуатационные заметки

- Устаревание событий — фоновая задача `run_expiry_loop` (`backend/app/services/expiry.py`),
  запускается в `lifespan` FastAPI-приложения, срок жизни берётся из `ttl_hours` каждого типа
  события (`event_types.py`).
- `region_bbox` — грубый прямоугольник, а не полигон (пропускает точки на границе соседних
  регионов, попадающие в тот же bbox) — для продакшена стоит заменить на честную геометрию региона.
- CORS: в локальном dev открыт (`cors_origins: ["*"]` в `config.py`). В продовом `deploy/docker-compose.yml` передаётся `CORS_ORIGINS: '["${DOMAIN_ORIGIN}"]'`, где `DOMAIN_ORIGIN` задаётся в `.env` — сразу закрытый список.
