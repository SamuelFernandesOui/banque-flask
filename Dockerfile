FROM python:3.12-slim

WORKDIR /app

# Installer les dépendances système (netcat et gcc si besoin)
RUN apt-get update && apt-get install -y netcat-openbsd gcc && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier les fichiers du projet
COPY . .

# Exposer le port Flask
EXPOSE 5000

# Commande de démarrage avec le script d'attente
CMD ["./wait-for-db.sh"]
