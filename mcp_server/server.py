"""
Serveur MCP pour le microservice Boxify.

Expose les outils suivants à tout client MCP (Claude, etc.) :
  - list_items            : lister toutes les boîtes
  - get_item              : détail d'une boîte (avec ses objets)
  - create_item           : créer une boîte
  - update_item           : modifier une boîte
  - delete_item           : supprimer une boîte (cascade sur ses objets)
  - list_objects          : lister tous les objets
  - get_object            : détail d'un objet
  - create_object         : créer un objet dans une boîte
  - update_object         : modifier un objet
  - delete_object         : supprimer un objet
  - list_item_infos       : lister toutes les métadonnées
  - get_item_info         : détail des métadonnées d'une boîte
  - create_item_info      : créer des métadonnées pour une boîte
  - update_item_info      : modifier des métadonnées
  - delete_item_info      : supprimer des métadonnées
  - get_honeypot_attempts : lister les tentatives enregistrées par le honeypot

Transport : SSE (HTTP) — le serveur écoute sur 0.0.0.0:${MCP_PORT}.

Variables d'environnement :
  BOXIFY_API_URL   : URL de base de l'API boxify (ex: http://boxify:8000)
  MCP_PORT         : port d'écoute du serveur MCP (défaut: 9000)
  MCP_API_KEY      : clé partagée attendue dans l'en-tête X-MCP-Key (optionnel)
  HONEYPOT_API_KEY : clé pour accéder à GET /api/honeypot/
"""

import os

import httpx
from mcp.server.fastmcp import FastMCP

# ── Configuration ─────────────────────────────────────────────────────────────

BOXIFY_API_URL = os.environ.get("BOXIFY_API_URL", "http://boxify:8000").rstrip("/")
MCP_PORT = int(os.environ.get("MCP_PORT", "9000"))
MCP_API_KEY = os.environ.get("MCP_API_KEY", "")
HONEYPOT_API_KEY = os.environ.get("HONEYPOT_API_KEY", "")

mcp = FastMCP(
    name="boxify-mcp",
    instructions=(
        "Serveur MCP du microservice Boxify. "
        "Permet de gérer les boîtes (Item) et les objets qu'elles contiennent (AssetObject). "
        "Chaque Item appartient à une sous-zone (référencée par son ID depuis le microservice Area). "
        "Chaque AssetObject appartient à un Item. "
        "ItemInfo stocke des métadonnées sur une boîte (fragile, en mouvement). "
        "Donne également accès aux tentatives honeypot enregistrées sur /admin/."
    ),
)


# ── Client HTTP ───────────────────────────────────────────────────────────────

def _client() -> httpx.Client:
    return httpx.Client(base_url=BOXIFY_API_URL, timeout=10.0)


def _check(response: httpx.Response) -> dict | list | None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise ValueError(
            f"Erreur API {e.response.status_code} : {e.response.text}"
        ) from e
    if response.status_code == 204:
        return None
    return response.json()


# ── OUTILS — ITEM ─────────────────────────────────────────────────────────────

@mcp.tool()
def list_items() -> list:
    """Liste toutes les boîtes."""
    with _client() as c:
        return _check(c.get("/api/items/"))


@mcp.tool()
def get_item(item_id: int) -> dict:
    """
    Retourne le détail d'une boîte.

    Args:
        item_id: Identifiant de la boîte.
    """
    with _client() as c:
        return _check(c.get(f"/api/items/{item_id}/"))


@mcp.tool()
def create_item(name: str, sub_area: int) -> dict:
    """
    Crée une nouvelle boîte.

    Args:
        name:     Nom de la boîte.
        sub_area: Identifiant de la sous-zone (depuis le microservice Area).
    """
    with _client() as c:
        return _check(c.post("/api/items/", json={"name": name, "sub_area": sub_area}))


@mcp.tool()
def update_item(item_id: int, name: str, sub_area: int) -> dict:
    """
    Met à jour une boîte existante.

    Args:
        item_id:  Identifiant de la boîte.
        name:     Nouveau nom.
        sub_area: Nouvel identifiant de sous-zone.
    """
    with _client() as c:
        return _check(
            c.put(f"/api/items/{item_id}/", json={"name": name, "sub_area": sub_area})
        )


@mcp.tool()
def delete_item(item_id: int) -> str:
    """
    Supprime une boîte et tous ses objets (cascade).

    Args:
        item_id: Identifiant de la boîte.
    """
    with _client() as c:
        _check(c.delete(f"/api/items/{item_id}/"))
    return f"Boîte {item_id} supprimée."


# ── OUTILS — ASSET OBJECT ─────────────────────────────────────────────────────

@mcp.tool()
def list_objects(item_id: int | None = None) -> list:
    """
    Liste les objets. Si item_id est fourni, filtre par boîte.

    Args:
        item_id: Identifiant de la boîte (optionnel).
    """
    with _client() as c:
        params = {"item": item_id} if item_id else {}
        return _check(c.get("/api/objects/", params=params))


@mcp.tool()
def get_object(object_id: int) -> dict:
    """
    Retourne le détail d'un objet.

    Args:
        object_id: Identifiant de l'objet.
    """
    with _client() as c:
        return _check(c.get(f"/api/objects/{object_id}/"))


@mcp.tool()
def create_object(name: str, item_id: int) -> dict:
    """
    Crée un objet dans une boîte.

    Args:
        name:    Nom de l'objet.
        item_id: Identifiant de la boîte parente.
    """
    with _client() as c:
        return _check(c.post("/api/objects/", json={"name": name, "item": item_id}))


@mcp.tool()
def update_object(object_id: int, name: str, item_id: int) -> dict:
    """
    Met à jour un objet.

    Args:
        object_id: Identifiant de l'objet.
        name:      Nouveau nom.
        item_id:   Identifiant de la boîte parente.
    """
    with _client() as c:
        return _check(
            c.put(f"/api/objects/{object_id}/", json={"name": name, "item": item_id})
        )


@mcp.tool()
def delete_object(object_id: int) -> str:
    """
    Supprime un objet.

    Args:
        object_id: Identifiant de l'objet.
    """
    with _client() as c:
        _check(c.delete(f"/api/objects/{object_id}/"))
    return f"Objet {object_id} supprimé."


# ── OUTILS — ITEM INFO ────────────────────────────────────────────────────────

@mcp.tool()
def list_item_infos() -> list:
    """Liste toutes les métadonnées de boîtes."""
    with _client() as c:
        return _check(c.get("/api/item-infos/"))


@mcp.tool()
def get_item_info(item_info_id: int) -> dict:
    """
    Retourne les métadonnées d'une boîte.

    Args:
        item_info_id: Identifiant des métadonnées.
    """
    with _client() as c:
        return _check(c.get(f"/api/item-infos/{item_info_id}/"))


@mcp.tool()
def create_item_info(item_id: int, fragile: bool = False, moving: bool = False) -> dict:
    """
    Crée des métadonnées pour une boîte.

    Args:
        item_id: Identifiant de la boîte.
        fragile: La boîte contient des objets fragiles.
        moving:  La boîte est en cours de déplacement.
    """
    with _client() as c:
        return _check(
            c.post("/api/item-infos/", json={"item": item_id, "fragile": fragile, "moving": moving})
        )


@mcp.tool()
def update_item_info(item_info_id: int, item_id: int, fragile: bool, moving: bool) -> dict:
    """
    Met à jour les métadonnées d'une boîte.

    Args:
        item_info_id: Identifiant des métadonnées.
        item_id:      Identifiant de la boîte.
        fragile:      La boîte contient des objets fragiles.
        moving:       La boîte est en cours de déplacement.
    """
    with _client() as c:
        return _check(
            c.put(
                f"/api/item-infos/{item_info_id}/",
                json={"item": item_id, "fragile": fragile, "moving": moving},
            )
        )


@mcp.tool()
def delete_item_info(item_info_id: int) -> str:
    """
    Supprime les métadonnées d'une boîte.

    Args:
        item_info_id: Identifiant des métadonnées.
    """
    with _client() as c:
        _check(c.delete(f"/api/item-infos/{item_info_id}/"))
    return f"Métadonnées {item_info_id} supprimées."


# ── OUTILS — HONEYPOT ─────────────────────────────────────────────────────────

@mcp.tool()
def get_honeypot_attempts() -> list:
    """
    Retourne toutes les tentatives enregistrées par le honeypot /admin/.

    Chaque entrée contient : ip, user_agent, path, method, username, timestamp.
    """
    with _client() as c:
        return _check(
            c.get("/api/honeypot/", headers={"X-Honeypot-Key": HONEYPOT_API_KEY})
        )


# ── Entrée ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="sse")
