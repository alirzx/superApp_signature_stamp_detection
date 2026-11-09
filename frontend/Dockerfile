FROM node:22-alpine AS build
ARG NPM_REGISTRY_URL=https://package-mirror.liara.ir/repository/npm/
WORKDIR /web
COPY frontend/package*.json ./
RUN npm install --registry="$NPM_REGISTRY_URL" --fetch-retries=3 --fetch-timeout=180000 --no-audit --no-fund
COPY frontend/ ./
RUN npm run build
FROM nginx:1.27-alpine
RUN apk add --no-cache gettext && mkdir -p /tmp /var/cache/nginx /var/run \
 && chown -R nginx:nginx /tmp /var/cache/nginx /var/run
COPY --from=build /web/dist /usr/share/nginx/html
COPY ops/nginx.conf.template /etc/nginx/nginx.conf.template
COPY ops/nginx-entrypoint.sh /entrypoint.sh
RUN chmod 0555 /entrypoint.sh
USER nginx
EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
