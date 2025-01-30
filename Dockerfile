# Utiliser une image Python 3.9 slim pour minimiser la taille
FROM python:3.9-slim

# Définir les variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Europe/Paris

# Créer un utilisateur non-root
RUN useradd -m -r -u 1000 planeuser

# Installer les dépendances système et configurer le timezone
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

# Créer et définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Créer les répertoires pour les volumes et définir les permissions
RUN mkdir -p /app/logs /app/state \
    && chown -R planeuser:planeuser /app

# Utiliser l'utilisateur non-root
USER planeuser

# Définir les volumes
VOLUME ["/app/logs", "/app/state"]

# Commande par défaut
CMD ["python", "-m", "plane_to_teams"] 