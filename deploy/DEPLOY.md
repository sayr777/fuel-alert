# Деплой Fuel Alert на Yandex Cloud VM

## Что получим

```
Internet → VM:80 → nginx (frontend container)
                 → /api/ → api container:8000
                         → db (PostGIS)
                         → redis
                         → Yandex Object Storage (фото)
Telegram → bot container → api
```

---

## Шаг 1 — Создать VM в Yandex Cloud

1. Консоль → **Compute Cloud** → **Создать ВМ**
2. Параметры:
   - ОС: **Ubuntu 24.04 LTS**
   - vCPU: 2, RAM: 4 GB (минимум; 8 GB комфортнее)
   - Диск: 30 GB SSD
   - Публичный IP: **Присвоить** (или зарезервировать статический)
3. SSH-ключ: вставьте свой публичный ключ (`~/.ssh/id_rsa.pub`)
4. Запомните **публичный IP** созданной VM.

---

## Шаг 2 — Yandex Object Storage (вместо MinIO)

1. Консоль → **Object Storage** → **Создать бакет**
   - Имя: `fuel-watch-photos`
   - Доступ: **Публичный** (чтобы фото были доступны по URL)

2. Консоль → **IAM** → **Сервисные аккаунты** → **Создать**
   - Роль: `storage.editor`

3. На странице сервисного аккаунта → **Создать статический ключ доступа**
   - Сохраните `Key ID` и `Secret` — они нужны для `.env`

---

## Шаг 3 — Подключиться к VM и запустить setup

```bash
ssh ubuntu@<ВАШ_IP>

# Скачать и запустить скрипт первичной настройки
curl -fsSL https://raw.githubusercontent.com/sayr777/fuel-alert/master/deploy/setup-vm.sh | sudo bash
```

Скрипт установит Docker, склонирует репозиторий и создаст шаблон `.env`.

---

## Шаг 4 — Заполнить .env

```bash
sudo nano /opt/fuel-alert/deploy/.env
```

| Переменная | Что вписать |
|---|---|
| `DB_PASSWORD` | Придумайте надёжный пароль |
| `REDIS_PASSWORD` | Придумайте надёжный пароль |
| `S3_ACCESS_KEY` | Key ID из шага 2 |
| `S3_SECRET_KEY` | Secret из шага 2 |
| `S3_BUCKET` | `fuel-watch-photos` |
| `S3_PUBLIC_URL` | `https://storage.yandexcloud.net/fuel-watch-photos` |
| `DOMAIN_ORIGIN` | `http://<ВАШ_IP>` (или `https://ваш.домен` если есть) |
| `MODERATOR_TOKEN` | `openssl rand -hex 32` |
| `BOT_TOKEN` | Токен от @BotFather |
| `VITE_TELEGRAM_BOT_URL` | `https://t.me/ВАШ_БОТ` |

---

## Шаг 5 — Запустить сервисы

```bash
cd /opt/fuel-alert/deploy

# Только API + фронтенд (без бота):
sudo docker compose up -d --build

# С Telegram-ботом:
sudo docker compose --profile bot up -d --build
```

Первый запуск займёт 3–5 минут (сборка образов + seed БД).

Проверка:
```bash
sudo docker compose ps
sudo docker compose logs -f api
```

Сайт будет доступен по адресу: `http://<ВАШ_IP>`

---

## Шаг 6 — VPN для доступа к Telegram

Yandex Cloud блокирует исходящие соединения к серверам Telegram. Для работы бота нужен VPN.

**Вариант: AdGuard VPN CLI** (требует платный аккаунт):

```bash
# Установка
curl -fsSL https://raw.githubusercontent.com/AdguardTeam/AdGuardVPNCLI/master/scripts/release/install.sh | sudo sh -s -- -v

# Авторизация
adguardvpn-cli login --username ВАШ_EMAIL --password ВАШ_ПАРОЛЬ

# Подключение (TUN-режим, например Вильнюс)
adguardvpn-cli connect -l "Vilnius"
adguardvpn-cli config set-mode tun

# Проверка
curl -s https://api.telegram.org  # должен вернуть 200
```

После подключения перезапустите бота:
```bash
cd /opt/fuel-alert/deploy && sudo docker compose restart bot
```

> VPN-сессия живёт до перезагрузки VM. После рестарта сервера нужно переподключиться вручную
> или настроить автозапуск через systemd.

---

## Шаг 7 (опционально) — HTTPS через Certbot

Если есть домен, привязанный к IP вашей VM:

```bash
sudo apt-get install -y certbot

# Остановить frontend чтобы освободить порт 80
cd /opt/fuel-alert/deploy && sudo docker compose stop frontend

# Получить сертификат
sudo certbot certonly --standalone -d ваш.домен

# Запустить снова
sudo docker compose start frontend
```

Затем добавьте в `nginx.conf` listen 443 + ssl и пересоберите образ:
```bash
sudo docker compose up -d --build frontend
```

---

## Обновление приложения

```bash
cd /opt/fuel-alert
sudo git pull
cd deploy
sudo docker compose up -d --build
```

---

## Полезные команды

```bash
# Логи
sudo docker compose logs -f api
sudo docker compose logs -f bot

# Перезапустить один сервис
sudo docker compose restart api

# Остановить всё
sudo docker compose down

# Остановить и удалить данные (ОСТОРОЖНО!)
sudo docker compose down -v
```
