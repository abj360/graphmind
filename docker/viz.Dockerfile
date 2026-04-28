FROM node:22-alpine AS build

WORKDIR /app
COPY viz/package.json viz/package-lock.json ./
RUN npm ci

COPY viz/index.html viz/vite.config.js ./
COPY viz/src ./src
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/viz.nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
