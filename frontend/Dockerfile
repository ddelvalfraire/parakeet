# syntax=docker/dockerfile:1

# --- Build stage: install deps + build static assets ---
FROM node:22-slim AS build

WORKDIR /app

COPY package.json package-lock.json ./

RUN --mount=type=cache,target=/root/.npm \
    npm ci

COPY . .

ENV VITE_API_URL="" \
    VITE_WS_URL=""

RUN npm run build

# --- Runtime stage: serve with nginx ---
FROM nginx:stable-alpine AS runtime

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
