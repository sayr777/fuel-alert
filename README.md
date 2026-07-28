# Топливный Дозор

Краудсорсинговая карта ситуации на АЗС — сообщения от водителей, модерация, Telegram-бот.

**Сайт: [dozor-fuel.online](https://dozor-fuel.online)**

Водители сообщают о проблемах на АЗС через Telegram-бота: нет топлива, лимит, очередь, завышенная цена, незаконная торговля. Сообщения проверяются модераторами и отображаются на общей карте.

![Карта сообщений](docs/images/screen-map.svg)

## Возможности

- **Telegram-бот** — подача сообщений: тип события → геолокация → фото → комментарий
- **MAX-бот** — полный аналог для мессенджера MAX (ex-ICQ/MailRu)
- **Карта** — все актуальные сообщения в реальном времени, фильтры по типу и дате
- **Панель модерации** — очередь, опубликованные, удалённые, мониторинг сервисов с логами контейнеров
- **Автобэкап** — ежедневный дамп БД и синхронизация фото в Yandex Object Storage

## Документация

- [docs/architecture.md](docs/architecture.md) — архитектура и технологии
- [docs/admin-guide.md](docs/admin-guide.md) — установка и эксплуатация
- [docs/user-guide.md](docs/user-guide.md) — для водителей
- [docs/max-bot-install-guide.md](docs/max-bot-install-guide.md) — установка MAX-бота
- [docs/max-bot-admin-guide.md](docs/max-bot-admin-guide.md) — эксплуатация MAX-бота

## Стек

| Компонент | Технологии |
|---|---|
| Backend API | FastAPI, SQLAlchemy async, PostgreSQL/PostGIS, Redis |
| Bot (Telegram) | Python 3.12, aiogram 3, FSM, Redis |
| Bot (MAX) | Python 3.12, aiohttp, Redis FSM (без SDK) |
| Frontend | React 18, TypeScript, Vite, MapLibre GL |
| Хранилище фото | Yandex Object Storage (прод) / MinIO (локально) |
| Инфраструктура | Docker Compose, Yandex Cloud VM, Cloudflare CDN |

## Быстрый старт

```bash
cp .env.example .env                        # заполнить BOT_TOKEN (и MAX_BOT_TOKEN опционально)
docker compose up -d                        # PostgreSQL, Redis, MinIO, API
docker compose --profile bot up -d          # + Telegram-бот
docker compose --profile bot_max up -d      # + MAX-бот
cd frontend && npm install && npm run dev   # фронтенд с моками: http://localhost:5173
```

## Тесты

```bash
# Backend
cd backend && pytest

# Frontend (unit)
cd frontend && npm test

# E2E (Playwright)
npx playwright test
```
