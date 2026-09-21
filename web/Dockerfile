FROM node:22-alpine AS frontend
WORKDIR /build
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src/ src/
COPY web/requirements.txt web/requirements.txt
RUN pip install --no-cache-dir . -r web/requirements.txt
COPY web/server.py web/server.py
COPY --from=frontend /build/dist web/dist
ENV PORT=8080
CMD exec gunicorn --bind :${PORT} --workers 1 --threads 4 web.server:application
