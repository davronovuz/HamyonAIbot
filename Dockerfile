# ═══ Stage 1: Frontend build ═══
FROM node:20-alpine AS frontend

WORKDIR /webapp
COPY webapp/package.json webapp/package-lock.json* ./
RUN npm install
COPY webapp/ .
RUN npm run build

# ═══ Stage 2: Python app ═══
FROM python:3.12-slim

# ffmpeg — pydub uchun (voice .ogg → .mp3 konvertatsiya)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Avval faqat requirements — layer cache ishlaydi
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Keyin kod
COPY . .

# Frontend build natijasini ko'chirish
COPY --from=frontend /webapp/dist /app/webapp/dist

# entrypoint.sh executable bo'lishi kerak
RUN chmod +x entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
