"""
Fertige Server-Vorlagen (Backups/Templates) im gleichen Planformat wie ai.py.
Jede Vorlage kann direkt per apply_plan() in bot.py angewendet werden.
"""

TEMPLATES = {
    "polizei": {
        "label": "🚔 Polizei / Behörden-RP",
        "plan": {
            "categories": [
                {"name": "📋 INFORMATIONEN", "channels": [
                    {"name": "regeln", "type": "text"},
                    {"name": "ankuendigungen", "type": "text"},
                    {"name": "dienstgrade", "type": "text"},
                ]},
                {"name": "🚔 EINSATZBEREICH", "channels": [
                    {"name": "einsatz-chat", "type": "text"},
                    {"name": "funkverkehr", "type": "voice"},
                    {"name": "streife-1", "type": "voice"},
                    {"name": "streife-2", "type": "voice"},
                ]},
                {"name": "📝 VERWALTUNG", "channels": [
                    {"name": "berichte", "type": "text"},
                    {"name": "bewerbungen", "type": "text"},
                    {"name": "team-besprechung", "type": "voice"},
                ]},
            ],
            "roles": [
                {"name": "Polizeipräsident", "color": "#e74c3c", "hoist": True},
                {"name": "Stellv. Polizeipräsident", "color": "#e67e22", "hoist": True},
                {"name": "Teamleitung", "color": "#f1c40f", "hoist": True},
                {"name": "Beamter", "color": "#3498db", "hoist": False},
                {"name": "Anwärter", "color": "#95a5a6", "hoist": False},
                {"name": "Bürger", "color": "#7f8c8d", "hoist": False},
            ],
        },
    },
    "gaming": {
        "label": "🎮 Gaming-Community",
        "plan": {
            "categories": [
                {"name": "📋 START", "channels": [
                    {"name": "regeln", "type": "text"},
                    {"name": "ankuendigungen", "type": "text"},
                    {"name": "rollen-vergabe", "type": "text"},
                ]},
                {"name": "💬 COMMUNITY", "channels": [
                    {"name": "allgemein", "type": "text"},
                    {"name": "clips-und-highlights", "type": "text"},
                    {"name": "memes", "type": "text"},
                ]},
                {"name": "🔊 VOICE", "channels": [
                    {"name": "Lounge 1", "type": "voice"},
                    {"name": "Lounge 2", "type": "voice"},
                    {"name": "Gaming Squad", "type": "voice"},
                ]},
            ],
            "roles": [
                {"name": "Owner", "color": "#e74c3c", "hoist": True},
                {"name": "Admin", "color": "#e67e22", "hoist": True},
                {"name": "Moderator", "color": "#f1c40f", "hoist": True},
                {"name": "Member", "color": "#3498db", "hoist": False},
            ],
        },
    },
    "support": {
        "label": "🛠️ Support-Server",
        "plan": {
            "categories": [
                {"name": "📋 INFO", "channels": [
                    {"name": "regeln", "type": "text"},
                    {"name": "faq", "type": "text"},
                ]},
                {"name": "🎫 SUPPORT", "channels": [
                    {"name": "ticket-erstellen", "type": "text"},
                    {"name": "support-chat", "type": "text"},
                ]},
                {"name": "🔧 TEAM", "channels": [
                    {"name": "team-chat", "type": "text"},
                    {"name": "team-voice", "type": "voice"},
                ]},
            ],
            "roles": [
                {"name": "Geschäftsführung", "color": "#e74c3c", "hoist": True},
                {"name": "Support-Team", "color": "#3498db", "hoist": True},
                {"name": "Kunde", "color": "#95a5a6", "hoist": False},
            ],
        },
    },
    "wirtschaft": {
        "label": "💼 Wirtschafts-RP",
        "plan": {
            "categories": [
                {"name": "📋 INFORMATIONEN", "channels": [
                    {"name": "regeln", "type": "text"},
                    {"name": "ankuendigungen", "type": "text"},
                    {"name": "boersen-kurse", "type": "text"},
                ]},
                {"name": "🏢 UNTERNEHMEN", "channels": [
                    {"name": "firmen-chat", "type": "text"},
                    {"name": "verhandlungen", "type": "voice"},
                    {"name": "vorstandssitzung", "type": "voice"},
                ]},
                {"name": "📈 VERWALTUNG", "channels": [
                    {"name": "bewerbungen", "type": "text"},
                    {"name": "finanzamt", "type": "text"},
                ]},
            ],
            "roles": [
                {"name": "CEO", "color": "#e74c3c", "hoist": True},
                {"name": "Vorstand", "color": "#e67e22", "hoist": True},
                {"name": "Abteilungsleitung", "color": "#f1c40f", "hoist": True},
                {"name": "Mitarbeiter", "color": "#3498db", "hoist": False},
                {"name": "Bewerber", "color": "#95a5a6", "hoist": False},
            ],
        },
    },
    "community": {
        "label": "🌐 Allgemeine Community",
        "plan": {
            "categories": [
                {"name": "📋 START", "channels": [
                    {"name": "regeln", "type": "text"},
                    {"name": "ankuendigungen", "type": "text"},
                    {"name": "vorstellung", "type": "text"},
                ]},
                {"name": "💬 CHAT", "channels": [
                    {"name": "allgemein", "type": "text"},
                    {"name": "off-topic", "type": "text"},
                ]},
                {"name": "🔊 VOICE", "channels": [
                    {"name": "Chillen", "type": "voice"},
                    {"name": "Talk", "type": "voice"},
                ]},
            ],
            "roles": [
                {"name": "Owner", "color": "#e74c3c", "hoist": True},
                {"name": "Moderator", "color": "#3498db", "hoist": True},
                {"name": "Mitglied", "color": "#95a5a6", "hoist": False},
            ],
        },
    },
}


def get_template_choices() -> list[tuple[str, str]]:
    """Gibt (key, label) Paare zurück, z.B. für Discord Select-Menüs."""
    return [(key, val["label"]) for key, val in TEMPLATES.items()]


def get_template_plan(key: str) -> dict | None:
    entry = TEMPLATES.get(key)
    return entry["plan"] if entry else None
