FROM node:22-alpine@sha256:76789712cd1ae89a1225eac9077010d68987a423588042dac30446f502f1858c AS builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json /app/frontend/
RUN cd frontend && npm ci
COPY frontend /app/frontend
COPY scripts/sync_public_data.mjs /app/scripts/sync_public_data.mjs
COPY public-data /app/public-data
RUN cd frontend && npm run build

FROM nginxinc/nginx-unprivileged:stable-alpine@sha256:b8c179cd3c2ae222a873dd59fbae240fadc03836cae5198afc9e9c19919c3880
ARG BUILD_SHA
LABEL org.opencontainers.image.revision=$BUILD_SHA
COPY frontend/nginx.conf /etc/nginx/nginx.conf
COPY --from=builder /app/frontend/dist /usr/share/nginx/html
USER 101:101
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1:8080/healthz || exit 1
ENTRYPOINT ["nginx","-g","daemon off;"]
