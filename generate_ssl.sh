#!/bin/bash
# Generate self-signed SSL certificate for development
# For production, replace with certificates from Let's Encrypt or your CA

SSL_DIR="$(dirname "$0")/ssl"
mkdir -p "$SSL_DIR"

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$SSL_DIR/key.pem" \
  -out "$SSL_DIR/cert.pem" \
  -subj "/C=CN/ST=HK/L=HongKong/O=TestMaster/CN=testmaster.local" \
  -addext "subjectAltName=DNS:testmaster.local,IP:34.150.26.84"

echo "SSL certificates generated in $SSL_DIR/"
echo "For production, replace with real certificates from Let's Encrypt or your CA."
