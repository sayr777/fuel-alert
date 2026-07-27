# Топливный Дозор

Краудсорсинговая карта ситуации на АЗС — сообщения от водителей, модерация, Telegram-бот.

**Сайт: [dozor-fuel.online](https://dozor-fuel.online)**

Водители сообщают о ситуации на АЗС через Telegram-бота: нет топлива, лимит, очередь, завышенная цена, незаконная торговля. Сервис проверяет обращения и показывает их на общей карте в реальном времени.

## Документация

- [docs/architecture.md](docs/architecture.md) — архитектура и технологии
- [docs/admin-guide.md](docs/admin-guide.md) — установка и эксплуатация
- [docs/user-guide.md](docs/user-guide.md) — для водителей
- [deploy/DEPLOY.md](deploy/DEPLOY.md) — деплой на Yandex Cloud

## Стек

| Компонент | Технологии |
|---|---|
| Backend | FastAPI, PostgreSQL/PostGIS, Redis |
| Bot | Python, aiogram |
| Frontend | React, TypeScript, Vite, Leaflet |
| Инфраструктура | Docker, Yandex Cloud, Yandex Object Storage |
