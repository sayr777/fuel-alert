# Руководство по установке MAX-бота

Бот для мессенджера MAX — полный аналог Telegram-бота «Топливный Дозор»: принимает обращения
о ситуации на АЗС, хранит FSM-состояние в Redis, отправляет репорты в тот же backend API.

## Требования

| Компонент | Версия | Назначение |
|---|---|---|
| Docker + Docker Compose | 24+ / 2.24+ | Запуск бота в контейнере |
| Python | 3.12+ | Только для локального запуска без Docker |
| Redis | 7+ | Хранение FSM-состояния (db=1) |
| Работающий backend API | — | `http://api:8000/api/v1` (docker) или `http://localhost:8000/api/v1` |
| Аккаунт в MAX (ex-ICQ/MailRu) | — | Для регистрации бота |

> MAX-бот и Telegram-бот могут работать одновременно: они используют разные базы Redis (db=0 и
> db=1) и не конфликтуют. Никаких изменений в backend API не требуется — MAX user_id
> используется как `telegram_id` во внутренней модели (то же поле `int64`).

---

## Шаг 1. Регистрация бота в MAX

1. Откройте мессенджер MAX (мобильное приложение или web.max.ru).
2. Найдите чат **@BotHub** или перейдите в настройки → **Чат-боты → Создать бота**.
3. Укажите имя бота (например, `Топливный Дозор`) и имя пользователя (например, `toplivny_dozor_bot`).
4. В разделе **Расширенные настройки** скопируйте **токен доступа** — он выглядит как длинная строка
   типа `eyJ...` или `abc123xyz...`.
5. Опционально: загрузите аватар бота и заполните описание:
   > «Краудсорсинговая карта топливной ситуации по России. Сообщите об отсутствии топлива,
   > очереди или закрытой АЗС — это поможет другим водителям.»

---

## Шаг 2. Настройка переменных окружения

### Продакшн — `/opt/fuel-alert/deploy/.env`

Добавьте в существующий файл `.env` две строки:

```bash
# MAX-бот
MAX_BOT_TOKEN=ВАШ_ТОКЕН_ИЗ_BOTBUB

# Ссылка на бота для кнопки «Сообщить в MAX» на лендинге
# Формат: https://max.ru/chat/{username} или внутренняя ссылка приложения
VITE_MAX_BOT_URL=https://max.ru/chat/toplivny_dozor_bot
```

> `VITE_MAX_BOT_URL` нужна только если пересобираете фронтенд. Если фронтенд уже собран и
> развёрнут — добавьте переменную при следующей сборке `frontend`.

### Локальная разработка — `.env` в корне репозитория

```bash
MAX_BOT_TOKEN=ВАШ_ТОКЕН_ИЗ_BOTBUB
```

---

## Шаг 3. Деплой в продакшн (Yandex Cloud VM)

### 3.1. Обновить код

```bash
sudo git -C /opt/fuel-alert fetch origin
sudo git -C /opt/fuel-alert reset --hard origin/master
```

### 3.2. Добавить переменные в `.env`

```bash
echo "MAX_BOT_TOKEN=ВАШ_ТОКЕН" | sudo tee -a /opt/fuel-alert/deploy/.env
echo "VITE_MAX_BOT_URL=https://max.ru/chat/ВАШ_БОТ" | sudo tee -a /opt/fuel-alert/deploy/.env
```

### 3.3. Собрать и запустить контейнер бота

```bash
cd /opt/fuel-alert

# Собрать образ
sudo docker compose --profile bot_max -f deploy/docker-compose.yml build bot_max

# Запустить
sudo docker compose --profile bot_max -f deploy/docker-compose.yml up -d bot_max
```

### 3.4. Если нужно обновить лендинг (кнопка «Сообщить в MAX»)

Пересобрать и перезапустить `frontend`:

```bash
sudo docker compose -f deploy/docker-compose.yml build frontend
sudo docker compose -f deploy/docker-compose.yml up -d frontend
```

### 3.5. Проверить статус

```bash
sudo docker ps --format "table {{.Names}}\t{{.Status}}"
# deploy-bot_max-1   Up X seconds

sudo docker logs deploy-bot_max-1 --tail 30
# Ожидаемый вывод:
# INFO  Bot commands registered
# INFO  MAX bot started, long polling…
```

---

## Шаг 4. Локальный запуск без Docker

Для разработки или отладки без контейнеров:

```bash
cd bot_max

# Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate     # Linux/Mac
# или: .venv\Scripts\activate  # Windows

pip install -r requirements.txt

# Запустить (нужен работающий Redis и API)
MAX_BOT_TOKEN=ВАШ_ТОКЕН \
API_BASE_URL=http://localhost:8000/api/v1 \
REDIS_URL=redis://localhost:6379/1 \
python main.py
```

> Redis db=1 отличается от Telegram-бота (db=0) — можно запускать оба одновременно.

---

## Шаг 5. Проверка работы

1. Откройте мессенджер MAX, найдите своего бота.
2. Напишите `/start` — бот ответит приветственным сообщением с кнопками.
3. Нажмите **«📢 Сообщить о ситуации»** и пройдите весь сценарий до конца.
4. Убедитесь, что репорт появился в панели модерации: `https://dozor-fuel.online/moderation`.

В логах контейнера при успешной работе вы увидите:

```
INFO  MAX bot started, long polling…
INFO  Bot commands registered
```

При ошибке авторизации:

```
WARNING  send_message error 401: {"code": 401, "message": "Unauthorized"}
```

→ Проверьте правильность `MAX_BOT_TOKEN` в `.env`.

---

## Переменные окружения бота

| Переменная | Обязательна | По умолчанию | Описание |
|---|---|---|---|
| `MAX_BOT_TOKEN` | ✅ | — | Токен из MAX BotHub |
| `API_BASE_URL` | — | `http://localhost:8000/api/v1` | Адрес backend API |
| `REDIS_URL` | — | `redis://localhost:6379/0` | Адрес Redis; в проде указать `db=1` и пароль |
| `MAP_URL` | — | `https://dozor-fuel.online` | Ссылка на карту в сообщениях `/start` и `/help` |

### Правильный `REDIS_URL` в продакшне

В `deploy/docker-compose.yml` уже задано:

```yaml
REDIS_URL: redis://:${REDIS_PASSWORD}@localhost:6379/1
```

`/1` в конце — база Redis 1 (не конфликтует с Telegram-ботом на базе 0).

---

## Обновление бота

```bash
# 1. Обновить код
sudo git -C /opt/fuel-alert fetch origin
sudo git -C /opt/fuel-alert reset --hard origin/master

# 2. Пересобрать и перезапустить
sudo docker compose --profile bot_max -f /opt/fuel-alert/deploy/docker-compose.yml build bot_max
sudo docker compose --profile bot_max -f /opt/fuel-alert/deploy/docker-compose.yml up -d bot_max
```

---

## Остановка бота

```bash
sudo docker compose --profile bot_max -f /opt/fuel-alert/deploy/docker-compose.yml stop bot_max
```

Или полное удаление контейнера (состояние в Redis сохранится):

```bash
sudo docker compose --profile bot_max -f /opt/fuel-alert/deploy/docker-compose.yml rm -sf bot_max
```

---

## Запуск обоих ботов одновременно

Telegram-бот и MAX-бот имеют независимые профили и запускаются отдельными командами:

```bash
# Telegram-бот (db=0)
sudo docker compose --profile bot -f /opt/fuel-alert/deploy/docker-compose.yml up -d bot

# MAX-бот (db=1)
sudo docker compose --profile bot_max -f /opt/fuel-alert/deploy/docker-compose.yml up -d bot_max
```

Оба контейнера работают в `network_mode: host` и обращаются к API/Redis через `localhost`.

---

## Структура директории `bot_max/`

```
bot_max/
├── main.py          — точка входа, long polling loop
├── client.py        — HTTP-клиент MAX API (get_updates, send_message, answer_callback)
├── fsm.py           — FSM на Redis (get/set state + data, TTL 1 ч)
├── keyboards.py     — inline-клавиатуры (callback + request_geo_location)
├── api_client.py    — клиент backend API (register_user, submit_report и др.)
├── states.py        — константы состояний FSM
├── config.py        — pydantic-settings (MAX_BOT_TOKEN, api_base_url, redis_url)
├── handlers/
│   ├── __init__.py  — диспетчер update → нужный обработчик
│   ├── start.py     — /start, /help, приветствие
│   └── report.py    — полный FSM-флоу репорта
├── requirements.txt — aiohttp, pydantic-settings, redis
└── Dockerfile       — python:3.12-slim
```

---

## Известные ограничения

- **Документация MAX API неполная** — точная структура некоторых вложений (`image`, `location`)
  определена по аналогии с похожими API. При первом запуске возможны правки в `handlers/report.py`
  (`_extract_location`, `_extract_image_url`) под реальный формат ответов.
- **Long polling** — согласно документации MAX, это ограниченный по скорости механизм; для высокой
  нагрузки (> 10 к сообщений/сут.) рекомендован переход на Webhook (`POST /subscriptions`).
- **Загрузка фото** — URL фото скачивается при подтверждении репорта, а не сразу при получении;
  если URL истёк, фото будет пропущено без ошибки.
