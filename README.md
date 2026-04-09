# Boxify — Microservice de gestion des boîtes

Le microservice **Boxify** gère les contenants physiques de Lokio : les **boîtes** et les **objets** qu'elles contiennent.

Une boîte (Item) est rattachée à une sous-zone gérée par le microservice Area. Chaque boîte peut contenir plusieurs objets (AssetObject). Des métadonnées optionnelles (ItemInfo) permettent d'indiquer si une boîte est fragile ou en cours de déplacement.

Le microservice expose une API REST sécurisée par JWT, un honeypot sur `/admin/`, et un serveur MCP permettant aux LLM de consulter et manipuler les boîtes directement en langage naturel.

---

## Stack

| Composant | Version |
|---|---|
| Python | 3.12 |
| Django | 6.0 |
| Django REST Framework | 3.16.1 |
| SimpleJWT | 5.5.1 |
| drf-yasg (Swagger) | 1.21.11 |
| FastMCP | — |
| Gunicorn | — |

---

## Installation

### Avec Docker (recommandé)

**Prérequis :** Docker et Docker Compose installés.

```bash
./deploy.sh
```

Le script `deploy.sh` fait tout automatiquement :

1. Vérifie que Docker est disponible
2. Crée le `.env` depuis `.env.example` si absent et ouvre l'éditeur pour le remplir
3. Valide que `DJANGO_SECRET_KEY` et `DJANGO_SUPERUSER_PASSWORD` sont bien définies
4. Build l'image et démarre les conteneurs (`boxify` + `boxify-mcp`)
5. Applique les migrations Django
6. Crée le superutilisateur (ignoré s'il existe déjà)
7. Attend que les services soient sains et affiche les URLs

Pour arrêter les services :

```bash
docker compose down
```

---

### Sans Docker (développement local)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cd boxify
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8002
```

L'API est accessible sur `http://localhost:8002`.

---

## Variables d'environnement

Copier `.env.example` en `.env` et remplir les valeurs. Ne jamais committer `.env`.

| Variable | Description | Exemple |
|---|---|---|
| `DJANGO_SECRET_KEY` | Clé secrète Django | — |
| `DJANGO_DEBUG` | Mode debug | `false` |
| `DJANGO_ALLOWED_HOSTS` | Hosts autorisés | `localhost,127.0.0.1` |
| `DJANGO_ADMIN_URL` | URL secrète de la vraie interface admin | `mon-panneau-secret` |
| `DJANGO_SUPERUSER_USERNAME` | Login du superutilisateur | `admin` |
| `DJANGO_SUPERUSER_EMAIL` | Email du superutilisateur | `admin@example.com` |
| `DJANGO_SUPERUSER_PASSWORD` | Mot de passe du superutilisateur | — |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Durée du token d'accès (minutes) | `60` |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Durée du token de rafraîchissement (jours) | `7` |
| `HONEYPOT_API_KEY` | Clé pour protéger `GET /api/honeypot/` | — |
| `GUNICORN_WORKERS` | Nombre de workers Gunicorn | `3` |
| `GUNICORN_TIMEOUT` | Timeout des requêtes (secondes) | `30` |
| `HOST_PORT` | Port exposé pour l'API | `8002` |
| `MCP_PORT` | Port interne du serveur MCP | `9000` |
| `MCP_HOST_PORT` | Port exposé pour le serveur MCP | `9003` |
| `MCP_API_KEY` | Clé optionnelle pour sécuriser l'accès MCP | — |

---

## Endpoints API

### Boîtes (Item)

| Méthode | URL | Description |
|---|---|---|
| `GET` | `/api/items/` | Liste toutes les boîtes |
| `POST` | `/api/items/` | Crée une boîte |
| `GET` | `/api/items/{id}/` | Détail d'une boîte |
| `PUT` / `PATCH` | `/api/items/{id}/` | Modifie une boîte |
| `DELETE` | `/api/items/{id}/` | Supprime une boîte (cascade sur ses objets) |

### Objets (AssetObject)

| Méthode | URL | Description |
|---|---|---|
| `GET` | `/api/objects/` | Liste tous les objets (filtre possible : `?item=<id>`) |
| `POST` | `/api/objects/` | Crée un objet |
| `GET` | `/api/objects/{id}/` | Détail d'un objet |
| `PUT` / `PATCH` | `/api/objects/{id}/` | Modifie un objet |
| `DELETE` | `/api/objects/{id}/` | Supprime un objet |

### Métadonnées (ItemInfo)

| Méthode | URL | Description |
|---|---|---|
| `GET` | `/api/item-infos/` | Liste toutes les métadonnées |
| `POST` | `/api/item-infos/` | Crée des métadonnées pour une boîte |
| `GET` | `/api/item-infos/{id}/` | Détail des métadonnées |
| `PUT` / `PATCH` | `/api/item-infos/{id}/` | Modifie des métadonnées |
| `DELETE` | `/api/item-infos/{id}/` | Supprime des métadonnées |

### Authentification JWT

| Méthode | URL | Description |
|---|---|---|
| `POST` | `/api/token/` | Obtenir un token |
| `POST` | `/api/token/refresh/` | Rafraîchir un token |

### Sécurité — Honeypot

| Méthode | URL | Description |
|---|---|---|
| `GET` | `/api/honeypot/` | Liste les tentatives enregistrées |

> Protégé par l'en-tête `X-Honeypot-Key: <HONEYPOT_API_KEY>`.

---

## Documentation interactive

| Interface | URL |
|---|---|
| Swagger UI | `http://localhost:8002/swagger/` |
| ReDoc | `http://localhost:8002/redoc/` |
| JSON (OpenAPI) | `http://localhost:8002/swagger.json` |

---

## Sécurité — Honeypot

L'URL `/admin/` est un honeypot : fausse page de connexion Django qui enregistre chaque tentative (IP, User-Agent, identifiants, horodatage) en base de données et dans `honeypot.log`.

La vraie interface d'administration est disponible à l'URL définie dans `DJANGO_ADMIN_URL`.

```bash
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

---

## Serveur MCP

Le microservice inclut un serveur MCP permettant à Claude d'interagir en langage naturel.

Accessible via SSE sur `http://localhost:9003/sse` (avec Docker).

### Outils disponibles

| Outil | Description |
|---|---|
| `list_items` | Liste toutes les boîtes |
| `get_item` | Détail d'une boîte |
| `create_item` | Crée une boîte |
| `update_item` | Modifie une boîte |
| `delete_item` | Supprime une boîte (cascade) |
| `list_objects` | Liste les objets (filtre optionnel par boîte) |
| `get_object` | Détail d'un objet |
| `create_object` | Crée un objet dans une boîte |
| `update_object` | Modifie un objet |
| `delete_object` | Supprime un objet |
| `list_item_infos` | Liste toutes les métadonnées |
| `get_item_info` | Détail des métadonnées |
| `create_item_info` | Crée des métadonnées pour une boîte |
| `update_item_info` | Modifie des métadonnées |
| `delete_item_info` | Supprime des métadonnées |
| `get_honeypot_attempts` | Liste les tentatives honeypot |

### Configurer le client MCP

```json
{
  "mcpServers": {
    "boxify": {
      "type": "sse",
      "url": "http://localhost:9003/sse"
    }
  }
}
```

---

## Tests

```bash
cd boxify
python manage.py test api.tests --verbosity=2
```

Tests unitaires couvrant :

- `ItemTests` : list, create (champs manquants), retrieve (404), update, partial_update, delete, cascade sur les objets
- `AssetObjectTests` : list, filtrage par boîte, create (FK invalide), retrieve, update, partial_update, delete
- `ItemInfoTests` : list, create (FK invalide), retrieve, update, partial_update, delete

---

## Linter

```bash
ruff check boxify/
```

---

## Auteur

Projet **Lokio** — développé par **Clément Chermeux**.

---

## Améliorations futures

- [ ] Authentification sur les endpoints MCP via `MCP_API_KEY`
- [ ] Pagination des résultats
- [ ] Filtrage par sous-zone sur `/api/items/`
- [ ] Export CSV / JSON des tentatives honeypot
- [ ] Cohérence des données si une sous-zone (Area) est supprimée
- [ ] Cohérence des données si un propriétaire est supprimé
- [ ] Mettre différents droits en fonction des utilisateurs pour pas qu'ils puissent tout modifier/voir etc
- [ ] Assignation d'un ou plusieurs propriétaires à une boîte
- [ ] Migration vers PostgreSQL pour la production
- [ ] Mise en place du CI/CD
- [ ] Système de connexion commune Lokio (Keycloak)
- [ ] Rajouter système de bande cookie etc pour être aux normes

