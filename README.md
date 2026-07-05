# Server-Setup-Bot

Globaler Discord-Bot: läuft auf beliebig vielen Servern gleichzeitig und baut
per KI oder fertigen Vorlagen komplette Kategorien/Kanäle/Rollen auf.
Erstellt nie ungefragt etwas — es gibt immer erst eine Vorschau zum Bestätigen.

## Befehle

| Befehl | Was er macht |
|---|---|
| `/server-erstellen thema:` | KI erstellt einen Bauplan zum freien Thema (z.B. "Polizei-Server", "Anime-Community") |
| `/server-vorlagen` | Fertige Vorlagen zur Auswahl (Polizei, Gaming, Support, Wirtschaft, Community) |
| `/server-backup-erstellen name:` | Sichert die aktuelle Serverstruktur unter einem Namen |
| `/server-backup-liste` | Zeigt gespeicherte Backups für diesen Server |
| `/server-backup-anwenden name:` | Wendet ein Backup an - ergänzt nur Fehlendes, löscht nie etwas |
| `/server-backup-loeschen name:` | Löscht ein gespeichertes Backup |

Alle Befehle brauchen bei der ausführenden Person die Berechtigung
**"Server verwalten"**.

## Wie die Vorschau funktioniert

Bei `/server-erstellen` und `/server-vorlagen` bekommst du zuerst ein Embed
mit allen geplanten Kategorien, Kanälen und Rollen, dazu drei Buttons:

- **✅ Erstellen** — legt alles wirklich an
- **✏️ Anpassen** — öffnet ein Textfeld, in das du deine Änderungswünsche
  schreibst (z.B. "Entferne die Rolle X" oder "Füge einen Voice-Channel
  hinzu"), die KI baut daraufhin einen neuen Plan, den du wieder bestätigen
  oder weiter anpassen kannst
- **❌ Abbrechen** — nichts wird erstellt

## Setup

### 1. Bot im Discord Developer Portal anlegen
- https://discord.com/developers/applications -> New Application
- Bot -> Token kopieren
- Keine privilegierten Intents nötig (kein Message Content)

### 2. Bot einladen (wichtig: richtige Berechtigungen)
- OAuth2 -> URL Generator -> Scopes: `bot`, `applications.commands`
- Bei Bot Permissions am einfachsten **Administrator** anhaken. Falls du es
  genauer einschränken willst, mindestens:
  - Manage Roles (Rollen verwalten)
  - Manage Channels (Kanäle verwalten)
  - View Channels, Send Messages, Embed Links, Use Slash Commands
- Generierten Link öffnen, auf jeden gewünschten Server einladen

**Wichtig:** Da dieser Bot Rollen erstellen soll, muss seine eigene Bot-Rolle
in den Server-Rollen-Einstellungen weit oben stehen (über den Rollen, die er
verwalten soll) - bei neu erstellten Rollen ist das für den Start meist kein
Problem, wird aber relevant, falls du dem Bot später erlauben willst,
bestehende Rollen zu bearbeiten.

### 3. GitHub-Repo + Railway
- Diesen Ordner in ein GitHub-Repo hochladen (`.env` nicht mit hochladen)
- railway.app -> "New Project" -> "Deploy from GitHub repo" -> Repo auswählen
- Unter "Variables" eintragen:
  ```
  DISCORD_TOKEN=dein_bot_token
  GROQ_API_KEY=dein_groq_key
  ```
- Fertig — Railway erkennt Python automatisch und startet über `Procfile`

### 4. Slash Commands erscheinen erst nach etwas Zeit
Da die Befehle **global** (nicht serverspezifisch) registriert werden,
kann es bis zu einer Stunde dauern, bis sie beim ersten Start überall
sichtbar sind. Das ist normales Discord-Verhalten, kein Fehler.

## Wichtiger Hinweis zu Backups

Backups werden aktuell als einfache Datei (`backups.json`) im
Container-Dateisystem von Railway gespeichert. Bei jedem Redeploy geht der
Inhalt verloren, wenn kein Railway Volume gemountet ist (Settings ->
Volumes -> Mount Path z.B. `/data`, dann `BACKUPS_FILE=/data/backups.json`
als Variable setzen). Für den Einstieg reicht die einfache Variante meist
aus, für dauerhafte Backups über viele Monate empfiehlt sich das Volume.

## Sicherheit / Verhalten

- Es wird **nie automatisch etwas gelöscht** - weder bei der KI-Erstellung
  noch bei Vorlagen noch bei Backup-Wiederherstellung
- Backup-Wiederherstellung ergänzt nur fehlende Kanäle/Rollen (erkannt am
  exakt gleichen Namen), bestehende bleiben unangetastet
- Ohne `GROQ_API_KEY` funktionieren `/server-vorlagen` und Backups weiterhin
  normal, nur `/server-erstellen` und der "Anpassen"-Button brauchen die KI
