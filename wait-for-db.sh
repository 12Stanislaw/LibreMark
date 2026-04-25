#!/bin/sh

echo "Waiting for database..."

while ! python -c "import socket; s=socket.socket(); s.connect(('db', 5432))" 2>/dev/null; do
  sleep 1
done

echo "Database is up!"s