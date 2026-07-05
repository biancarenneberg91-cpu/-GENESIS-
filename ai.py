"""
KI-Generierung von Server-Bauplänen (Kategorien, Kanäle, Rollen) per Groq.

Ein "Plan" ist immer ein Dict in diesem Format:
{
  "categories": [
    {"name": "📋 INFORMATIONEN", "channels": [
        {"name": "regeln", "type": "text"},
        {"name": "ankuendigungen", "type": "text"}
    ]},
    ...
  ],
  "roles": [
    {"name": "Admin", "color": "#e74c3c", "hoist": true},
    ...
  ]
}

Dieses Format wird sowohl von der KI-Generierung als auch von den
vorgefertigten Templates (templates.py) und von Backups (storage.py)
verwendet, damit apply_plan() in bot.py überall gleich funktioniert.
"""

import os
import json
import asyncio
import logging

try:
    from groq import Groq
except ImportError:
    Groq = None

log = logging.getLogger("server-setup-bot")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if (Groq and GROQ_API_KEY) else None

SCHEMA_HINWEIS = """Antworte AUSSCHLIESSLICH mit validem JSON, keine Markdown-Codeblöcke,
kein Fließtext davor oder danach. Halte dich exakt an dieses Format:

{
  "categories": [
    {"name": "KATEGORIE-NAME", "channels": [
        {"name": "kanal-name", "type": "text"},
        {"name": "sprachkanal-name", "type": "voice"}
    ]}
  ],
  "roles": [
    {"name": "Rollen-Name", "color": "#RRGGBB", "hoist": true}
  ]
}

Regeln:
- Maximal 6 Kategorien, maximal 6 Kanäle pro Kategorie, maximal 10 Rollen
- Kanalnamen klein geschrieben, mit Bindestrichen statt Leerzeichen (Discord-Konvention)
- "type" ist entweder "text" oder "voice"
- "color" ist ein Hex-Code, sinnvoll passend zur Rolle (z.B. rot für Admin/Leitung)
- "hoist" = true bei wichtigen/sichtbaren Rollen (Leitung, Team), sonst false
- Passe Kategorien, Kanäle und Rollen inhaltlich sinnvoll an das gewünschte Thema an
"""


def _clean_json(raw: str) -> str:
    return raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()


async def generate_plan(thema: str) -> dict:
    """Erstellt per KI einen kompletten Serverplan zu einem freien Thema."""
    if not groq_client:
        raise RuntimeError("Kein GROQ_API_KEY konfiguriert - KI-Generierung nicht verfügbar.")

    prompt = f"""Erstelle einen Discord-Server-Bauplan für folgendes Thema: "{thema}"

{SCHEMA_HINWEIS}"""

    completion = await asyncio.to_thread(
        groq_client.chat.completions.create,
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=1500,
    )
    raw = completion.choices[0].message.content
    return json.loads(_clean_json(raw))


async def adjust_plan(thema: str, previous_plan: dict, adjustment: str) -> dict:
    """Passt einen bestehenden Plan anhand einer Anweisung des Nutzers an."""
    if not groq_client:
        raise RuntimeError("Kein GROQ_API_KEY konfiguriert - KI-Generierung nicht verfügbar.")

    prompt = f"""Ursprüngliches Thema: "{thema}"

Aktueller Bauplan (JSON):
{json.dumps(previous_plan, ensure_ascii=False)}

Der Nutzer möchte folgende Änderung: "{adjustment}"

Gib den KOMPLETTEN aktualisierten Bauplan zurück (nicht nur die Änderung),
mit der Anpassung eingearbeitet.

{SCHEMA_HINWEIS}"""

    completion = await asyncio.to_thread(
        groq_client.chat.completions.create,
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=1500,
    )
    raw = completion.choices[0].message.content
    return json.loads(_clean_json(raw))
