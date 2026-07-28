# Руководство администратора MAX-бота

Операционная документация по сопровождению MAX-бота «Топливный Дозор» в продакшне.
По установке и первоначальной настройке — [max-bot-install-guide.md](max-bot-install-guide.md).

---

## Архитектура бота

```
Пользователь MAX
      │
      ▼
MAX API (platform-api2.max.ru)   ← long polling GET /updates
      │
      ▼
bot_max/ (Docker, network_mode: host)
      │
      ├──► Redis db=1          — FSM-состояния диалогов (TTL 1 ч)
      │      ключи: max_fsm:{user_id}:state / :data
      │
      └──► backend API :8000   — регистрация пользователя, типы событий, сабмит репорта
```

MAX-бот работает по принципу **long polling**: каждые 30 секунд опрашивает `GET /updates`
с параметром `marker` (курсор) и обрабатывает пришедшие обновления. После рестарта курсор
сбрасывается — бот увидит только новые сообщения (события, пришедшие в офлайне, не обрабатываются).

---

## Мониторинг

### Статус контейнера

```bash
sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.RunningFor}}"
```

Бот должен быть в статусе `Up` без перезапусков (`Restarting` или `Exited` — сигнал проблемы).

### Логи в реальном времени

```bash
sudo docker logs deploy-bot_max-1 --tail 50 -f
```

Нормальная работа выглядит как тишина (long polling не пишет лог на каждый пустой ответ).
При входящих сообщениях появляются строки:

```
2026-07-29 10:15:03 INFO  handlers.__init__ dispatch_update — обработка update_type=message_created
```

### Что означают строки в логах

| Строка | Значение | Действие |
|---|---|---|
| `INFO  MAX bot started, long polling…` | Штатный старт | — |
| `INFO  Bot commands registered` | Команды `/start` `/help` зарегистрированы в MAX | — |
| `WARNING  send_message error 401` | Неверный токен | Проверить `MAX_BOT_TOKEN` в `.env` |
| `WARNING  send_message error 429` | Превышен rate limit MAX API (30 rps) | Снизить частоту рассылок |
| `WARNING  Failed to download photo` | URL фото недоступен | Пользователь не получит ошибку, фото пропущено |
| `ERROR  Error handling update` | Исключение при обработке update | Смотреть traceback ниже |
| `WARNING  Polling error, retrying in 5 s` | Сетевой сбой на запросе к MAX API | Самовосстанавливается |
| `WARNING  Could not register bot commands` | MAX API недоступен при старте | Команды не зарегистрированы, бот работает |

### Проверка доступности MAX API

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: ВАШ_MAX_BOT_TOKEN" \
  https://platform-api2.max.ru/me
# 200 — OK, 401 — неверный токен
```

---

## Управление контейнером

### Перезапуск

```bash
sudo docker compose --profile bot_max -f /opt/fuel-alert/deploy/docker-compose.yml restart bot_max
```

### Остановка

```bash
sudo docker compose --profile bot_max -f /opt/fuel-alert/deploy/docker-compose.yml stop bot_max
```

### Просмотр переменных окружения

```bash
sudo docker inspect deploy-bot_max-1 | grep -A 20 '"Env"'
```

### Удаление FSM-состояний всех пользователей (экстренная очистка)

```bash
# Посмотреть сколько активных сессий
sudo docker exec deploy-redis-1 redis-cli -a "${REDIS_PASSWORD}" -n 1 KEYS "max_fsm:*" | wc -l

# Очистить всю базу 1 (только MAX FSM — Telegram на базе 0)
sudo docker exec deploy-redis-1 redis-cli -a "${REDIS_PASSWORD}" -n 1 FLUSHDB
```

> Это прервёт незавершённые диалоги всех пользователей. Используйте только в экстренных случаях.

### Удаление FSM конкретного пользователя

```bash
USER_ID=123456789
sudo docker exec deploy-redis-1 redis-cli -a "${REDIS_PASSWORD}" -n 1 \
  DEL "max_fsm:${USER_ID}:state" "max_fsm:${USER_ID}:data"
```

---

## FSM — диагностика зависших диалогов

### Посмотреть все активные сессии и их состояния

```bash
sudo docker exec deploy-redis-1 redis-cli -a "${REDIS_PASSWORD}" -n 1 \
  KEYS "max_fsm:*:state" | head -20
```

### Посмотреть состояние конкретного пользователя

```bash
USER_ID=123456789
sudo docker exec deploy-redis-1 redis-cli -a "${REDIS_PASSWORD}" -n 1 \
  GET "max_fsm:${USER_ID}:state"

sudo docker exec deploy-redis-1 redis-cli -a "${REDIS_PASSWORD}" -n 1 \
  GET "max_fsm:${USER_ID}:data"
```

Возможные значения `state`:

| Значение | Что ждёт бот |
|---|---|
| `choosing_type` | Нажатие кнопки типа события |
| `choosing_grades` | Выбор марок топлива |
| `entering_description` | Текст описания (тип «Другое») |
| `waiting_location` | Геолокацию (кнопка «Отправить геолокацию») |
| `waiting_photos` | Фото или кнопку «Пропустить фото» |
| `entering_comment` | Текст или кнопку «Без комментария» |
| `confirming` | Кнопку «✅ Отправить» или «❌ Отмена» |

TTL сессии — 1 час с последнего действия; если пользователь не отвечает, сессия автоматически
удаляется из Redis.

---

## Обновление бота

### Стандартное обновление кода

```bash
# 1. Получить изменения
sudo git -C /opt/fuel-alert fetch origin
sudo git -C /opt/fuel-alert reset --hard origin/master

# 2. Пересобрать образ (обязательно — иначе работает старый код)
sudo docker compose --profile bot_max -f /opt/fuel-alert/deploy/docker-compose.yml build bot_max

# 3. Перезапустить
sudo docker compose --profile bot_max -f /opt/fuel-alert/deploy/docker-compose.yml up -d bot_max

# 4. Проверить логи
sudo docker logs deploy-bot_max-1 --tail 20
```

> ⚠️ Шаг 2 (`build`) обязателен. `up -d` без `build` запускает старый образ из кеша Docker.

### Обновление токена

```bash
# Отредактировать .env
sudo nano /opt/fuel-alert/deploy/.env
# заменить значение MAX_BOT_TOKEN

# Перезапустить (без пересборки — только env меняется)
sudo docker compose --profile bot_max -f /opt/fuel-alert/deploy/docker-compose.yml up -d bot_max
```

---

## Сценарий работы FSM

Полный флоу репорта — тот же, что и в Telegram-боте:

```
/start или bot_started
    │
    ▼
[ГЛАВНОЕ МЕНЮ] 📢 Сообщить о ситуации | ℹ️ Помощь
    │ кнопка «Сообщить»
    ▼
[CHOOSING_TYPE] — кнопки типов событий
    │ etype:{code}
    ▼ (если тип имеет fuel_grades)
[CHOOSING_GRADES] — мультивыбор марок, клавиатура обновляется in-place через /answers
    │ grades_done
    ▼
[WAITING_LOCATION] — кнопка request_geo_location
    │ location attachment
    ▼
[WAITING_PHOTOS] — пользователь присылает image attachment (до 2 шт)
    │ кнопка skip_photo или 2-е фото
    ▼
[ENTERING_COMMENT] — текст сообщения или кнопка skip_comment
    │
    ▼
[CONFIRMING] — сводка + кнопки confirm_send / cancel
    │ confirm_send
    ▼
Скачать фото → POST /reports → статус ответа → ГЛАВНОЕ МЕНЮ
```

**Особенности относительно Telegram-бота:**
- Все кнопки — inline (нет reply-клавиатуры)
- Геолокация запрашивается через кнопку `type: request_geo_location` (MAX-специфика)
- Обновление клавиатуры выбора марок — через `POST /answers?callback_id=...` с заменой сообщения
  (не отдельное новое сообщение, как в Telegram через `edit_reply_markup`)

---

## Типичные проблемы и решения

### Бот не отвечает на сообщения

1. Проверить, запущен ли контейнер: `sudo docker ps | grep bot_max`
2. Если нет — запустить: `sudo docker compose --profile bot_max -f /opt/fuel-alert/deploy/docker-compose.yml up -d bot_max`
3. Если есть — смотреть логи: `sudo docker logs deploy-bot_max-1 --tail 50`
4. Проверить доступность MAX API:
   ```bash
   curl -s -H "Authorization: ВАШ_ТОКЕН" https://platform-api2.max.ru/me | python3 -m json.tool
   ```

### Бот отвечает, но не обрабатывает кнопки геолокации

Пользователь должен разрешить доступ к геолокации в MAX. Это разовое разрешение на уровне
приложения — попросите пользователя проверить настройки приложения MAX.

### Репорты от MAX-бота не появляются на карте

1. Проверить, что backend запущен: `sudo docker logs deploy-api-1 --tail 20`
2. Проверить через панель модерации (вкладка «Очередь» или «Опубликованные»)
3. Проверить логи бота на ошибку `submit_report failed`:
   ```bash
   sudo docker logs deploy-bot_max-1 --tail 100 | grep "submit_report"
   ```
4. Убедиться, что `API_BASE_URL` в `.env` правильный для сетевого режима `host`:
   ```bash
   sudo docker inspect deploy-bot_max-1 | grep API_BASE_URL
   # Должно быть: http://127.0.0.1:8000/api/v1
   ```

### Ошибка 401 от MAX API

Токен недействителен или истёк. Получите новый токен в MAX BotHub и обновите `MAX_BOT_TOKEN` в `.env`:

```bash
sudo nano /opt/fuel-alert/deploy/.env    # изменить MAX_BOT_TOKEN
sudo docker compose --profile bot_max -f /opt/fuel-alert/deploy/docker-compose.yml up -d bot_max
```

### Ошибка `Polling error, retrying in 5 s` в логах

Временная недоступность MAX API — бот автоматически повторяет запрос каждые 5 секунд. Если
ошибка не исчезает в течение нескольких минут:

```bash
# Проверить сетевой доступ с хоста
curl -v https://platform-api2.max.ru/me -H "Authorization: ВАШ_ТОКЕН" 2>&1 | head -30
```

MAX-бот не требует VPN (в отличие от Telegram-бота) — MAX доступен с серверов Yandex Cloud напрямую.

### Пользователь застрял в состоянии FSM

Если пользователь написал `/start` а бот не отвечает (застрял в середине флоу):

```bash
# Сбросить состояние конкретного пользователя
USER_ID=ВАШ_USER_ID
sudo docker exec deploy-redis-1 redis-cli -a "${REDIS_PASSWORD}" -n 1 \
  DEL "max_fsm:${USER_ID}:state" "max_fsm:${USER_ID}:data"
```

После этого следующее сообщение от пользователя вернёт его в главное меню.

---

## Отличие от Telegram-бота (для сравнения)

| Аспект | Telegram-бот | MAX-бот |
|---|---|---|
| Фреймворк | aiogram 3 | aiohttp (чистый HTTP) |
| SDK | aiogram FSM | Самодельный FSM на Redis |
| Polling | aiogram встроенный | `GET /updates?marker=...` |
| Auth | `Bot <token>` заголовок | `Authorization: <token>` (без слова Bot/Bearer) |
| Reply-клавиатура | `is_persistent=True` | Отсутствует — только inline |
| Геолокация | `KeyboardButton(request_location=True)` | `{"type": "request_geo_location"}` |
| Ответ на кнопку | `callback_query.answer()` | `POST /answers?callback_id={id}` |
| Обновление сообщения | `edit_reply_markup()` | `POST /answers?callback_id={id}` с телом `message` |
| Redis база | db=0 | db=1 |
| VPN нужен | Да (Yandex Cloud блокирует Telegram) | Нет |

---

## Справка по командам

```bash
# Статус
sudo docker ps | grep bot_max

# Логи (последние 50 строк)
sudo docker logs deploy-bot_max-1 --tail 50

# Логи в реальном времени
sudo docker logs deploy-bot_max-1 -f

# Перезапуск
sudo docker compose --profile bot_max -f /opt/fuel-alert/deploy/docker-compose.yml restart bot_max

# Пересборка и запуск (после обновления кода)
sudo docker compose --profile bot_max -f /opt/fuel-alert/deploy/docker-compose.yml build bot_max
sudo docker compose --profile bot_max -f /opt/fuel-alert/deploy/docker-compose.yml up -d bot_max

# Остановка
sudo docker compose --profile bot_max -f /opt/fuel-alert/deploy/docker-compose.yml stop bot_max

# Активные FSM-сессии
sudo docker exec deploy-redis-1 redis-cli -a "${REDIS_PASSWORD}" -n 1 KEYS "max_fsm:*:state"

# Проверка токена
curl -s -H "Authorization: ${MAX_BOT_TOKEN}" https://platform-api2.max.ru/me | python3 -m json.tool
```
