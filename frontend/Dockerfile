FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG VITE_TELEGRAM_BOT_URL
ARG VITE_MAX_BOT_URL
ARG VITE_USE_MOCKS=false
ENV VITE_TELEGRAM_BOT_URL=$VITE_TELEGRAM_BOT_URL \
    VITE_MAX_BOT_URL=$VITE_MAX_BOT_URL \
    VITE_USE_MOCKS=$VITE_USE_MOCKS
RUN npm run build


FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
