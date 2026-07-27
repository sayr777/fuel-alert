# Топливный Дозор

Краудсорсинговая карта ситуации на АЗС — сообщения от водителей, модерация, Telegram-бот.

**Сайт: [dozor-fuel.online](https://dozor-fuel.online)**

Водители сообщают о проблемах на АЗС через Telegram-бота: нет топлива, лимит, очередь, завышенная цена, незаконная торговля. Сообщения проверяются модераторами и отображаются на общей карте.

![Карта сообщений](docs/images/screen-map.svg)

## Возможности

- **Telegram-бот** — подача сообщений: тип события → геолокация → фото → комментарий
- **Карта** — все актуальные сообщения в реальном времени, фильтры по типу и дате
- **Панель модерации** — очередь, опубликованные, удалённые, мониторинг сервисов с логами контейнеров
- **Автобэкап** — ежедневный дамп БД и синхронизация фото в Yandex Object Storage

## Документация

- [docs/architecture.md](docs/architecture.md) — архитектура и технологии
- [docs/admin-guide.md](docs/admin-guide.md) — установка и эксплуатация
- [docs/user-guide.md](docs/user-guide.md) — для водителей

## Стек

| Компонент | Технологии |
|---|---|
| Backend | FastAPI, PostgreSQL/PostGIS, Redis |
| Bot | Python, aiogram 3, FSM |
| Frontend | React 18, TypeScript, Vite, MapLibre GL |
| Инфраструктура | Docker, Yandex Cloud, Yandex Object Storage |

## Быстрый старт

```bash
cp .env.example .env          # заполнить BOT_TOKEN
docker compose up -d          # PostgreSQL, Redis, MinIO, API
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
