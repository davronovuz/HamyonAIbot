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

# entrypoint.sh executable bo'lishi kerak
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
