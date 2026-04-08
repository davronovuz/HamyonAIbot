#!/bin/sh
# Self-signed SSL sertifikat yaratish (development uchun)
# Production uchun: Let's Encrypt yoki boshqa CA dan oling

SSL_DIR="/etc/nginx/ssl"
mkdir -p "$SSL_DIR"

if [ ! -f "$SSL_DIR/cert.pem" ]; then
    echo "SSL sertifikat yaratilmoqda (self-signed)..."
    openssl req -x509 -nodes -days 365 \
        -newkey rsa:2048 \
        -keyout "$SSL_DIR/key.pem" \
        -out "$SSL_DIR/cert.pem" \
        -subj "/C=UZ/ST=Tashkent/L=Tashkent/O=HamyonAI/CN=hamyonai.local"
    echo "SSL sertifikat tayyor."
else
    echo "SSL sertifikat allaqachon mavjud."
fi
