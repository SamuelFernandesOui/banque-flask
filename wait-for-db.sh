#!/bin/sh
echo "⏳ Attente de PostgreSQL sur $DB_HOST..."

while ! nc -z $DB_HOST 5432; do
  sleep 1
done

echo "✅ PostgreSQL est prêt. Lancement de Flask..."
exec flask run --host=0.0.0.0
