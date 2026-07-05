"""
Speicherung von Server-Backups als JSON-Datei, pro Discord-Server (Guild) getrennt.
Atomare Writes über os.replace(), gleiches Pattern wie bei NEXUS.

Ein Backup ist ein gespeicherter Plan (siehe ai.py für das Format) mit Namen
und Zeitstempel, damit man ihn später wieder anwenden kann.

Hinweis: Diese Datei liegt im Container-Dateisystem. Auf Railway geht der
Inhalt bei jedem Redeploy verloren, wenn kein Volume gemountet ist (siehe
README). Für den Start reicht das meist aus.
"""

import os
import json
import asyncio
from datetime import datetime, timezone

DATA_FILE = os.getenv("BACKUPS_FILE", "backups.json")
_lock = asyncio.Lock()


def _load_raw() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save_raw(data: dict) -> None:
    tmp_path = f"{DATA_FILE}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, DATA_FILE)


async def save_backup(guild_id: int, name: str, plan: dict) -> None:
    async with _lock:
        data = _load_raw()
        key = str(guild_id)
        data.setdefault(key, [])
        # Gleicher Name wird überschrieben, damit keine Duplikate entstehen
        data[key] = [b for b in data[key] if b["name"] != name]
        data[key].append({
            "name": name,
            "plan": plan,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        _save_raw(data)


async def list_backups(guild_id: int) -> list[dict]:
    async with _lock:
        data = _load_raw()
        return data.get(str(guild_id), [])


async def get_backup(guild_id: int, name: str) -> dict | None:
    backups = await list_backups(guild_id)
    for b in backups:
        if b["name"] == name:
            return b
    return None


async def delete_backup(guild_id: int, name: str) -> bool:
    async with _lock:
        data = _load_raw()
        key = str(guild_id)
        if key not in data:
            return False
        before = len(data[key])
        data[key] = [b for b in data[key] if b["name"] != name]
        _save_raw(data)
        return len(data[key]) < before
