# -- Stage 1: Build the React Frontend --
FROM node:18-alpine AS frontend-builder

WORKDIR /app
COPY dtos/ ./dtos/

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# -- Stage 2: Setup Flask Backend --
FROM python:3.10-slim
WORKDIR /app/service

RUN pip install --no-cache-dir flask flask-socketio eventlet mysql-connector-python matplotlib uuid

COPY service/ .

COPY --from=frontend-builder /app/frontend/dist ../frontend/dist

EXPOSE 5000

CMD ["python3", "app.py"]
