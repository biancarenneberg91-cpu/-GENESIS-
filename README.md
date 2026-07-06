# Server-Setup-Bot

Globaler Discord-Bot: läuft auf beliebig vielen Servern gleichzeitig und baut
per KI oder fertigen Vorlagen komplette Kategorien/Kanäle/Rollen auf.
Erstellt nie ungefragt etwas — es gibt immer erst eine Vorschau zum Bestätigen.

## Befehle

| Befehl | Was er macht |
|---|---|
| `/server-erstellen thema:` | KI erstellt einen Bauplan zum freien Thema (z.B. "Polizei-Server", "Anime-Community") |
| `/server-vorlagen` | Fertige Vorlagen zur Auswahl (jetzt 10 Stück) |
| `/server-backup-erstellen name:` | Sichert die aktuelle Serverstruktur unter einem Namen |
| `/server-backup-liste` | Zeigt gespeicherte Backups für diesen Server |
| `/server-backup-anwenden name:` | Wendet ein Backup an - ergänzt nur Fehlendes, löscht nie etwas |
| `/server-backup-loeschen name:` | Löscht ein gespeichertes Backup |
| `/server-loeschen ziel:` | Löscht Kanäle, Rollen oder alles - mit Vorschau und Bestätigung |
| `/genesis-stats` | Zeigt die globale Statistik über alle Server hinweg |
| `/credits` | Zeigt Infos zum Entwickler, Tech-Stack und weiteren Links |

## Gamification

- Beim Erstellen läuft erst eine kurze **Boot-Sequenz** im Terminal-Stil
  ("> genesis.core --init"), danach zufällige, augenzwinkernde Bau-Sprüche
  ("Kalibriere Hierarchie-Matrix...", "Bestechen die Rate-Limit-Gnome...")
- Jeder fertige Server bekommt ein **Tier-Ranking** je nach Größe:
  🌱 Starter · ✨ B-Tier · 🔥 A-Tier · 🌌 S-Tier
- **10% Chance auf einen 🌈 Critical Build** — ein seltener, besonderer Moment
  mit goldenem Embed und Sonderflair
- **Server-Level-System**: jeder Server sammelt über mehrere Nutzungen hinweg
  Lebenszeit-Punkte und steigt von 🌱 Rookie Architect bis 👑 GENESIS LEGEND auf,
  mit eigenem Fortschrittsbalken zur nächsten Stufe
- Bei besonders großen Builds (15+ Elemente) oder einem Critical Build feiert
  der Bot automatisch mit Reaktionen (⚡🎉🚀) auf der Abschlussnachricht
- `/genesis-stats` zeigt, wie viele Server, Kanäle und Rollen Genesis
  insgesamt schon über alle Server hinweg erschaffen hat — ein netter
  Showoff-Fakt für die eigene Community

## Der Löschbefehl (wichtig: unwiderruflich!)

`/server-loeschen` kann vier Dinge:

- **Eine bestimmte Kategorie** (inkl. ihrer Kanäle)
- **Alle Kanäle und Kategorien** (Rollen bleiben erhalten)
- **Alle selbst erstellten Rollen** (Kanäle bleiben erhalten)
- **ALLES** — kompletter Reset

Bei jeder Auswahl siehst du zuerst eine **Vorschau** mit genauer Auflistung, was
gelöscht würde, bevor irgendetwas passiert. Bei der Option "ALLES" gibt es eine
zusätzliche Sicherung: du musst das Wort **LÖSCHEN** in ein Textfeld eintippen,
bevor der Bot wirklich etwas löscht.

`@everyone` und vom System verwaltete Rollen (z.B. Integrationen, Bot-eigene
Rollen) werden nie angefasst, egal welche Option gewählt wird.

Dieser Befehl braucht **Administrator**-Rechte bei der ausführenden Person
(höhere Hürde als bei den anderen Befehlen, wegen der destruktiven Wirkung).

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

## Visuelle Extras

Beim Erstellen zeigt Genesis einen **Live-Fortschrittsbalken**, der sich Schritt
für Schritt aktualisiert (welche Rolle/Kanal gerade angelegt wird), gefolgt von
einem Abschluss-Embed mit Gesamtstatistik. Der Bot-Status in der Mitgliederliste
zeigt außerdem live, auf wie vielen Servern er aktiv ist ("👀 X Server erschaffen").

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

## KI-Verbesserungen

- Läuft jetzt auf **openai/gpt-oss-20b** (Groq hat `llama-3.1-8b-instant` am
  17.06.2026 als veraltet markiert) - schneller und deutlich bessere Ergebnisse
- Die KI vergibt jetzt **Kanal-Beschreibungen (Topics)** automatisch passend zum Thema
- Sensible Kanäle (z.B. Team-Besprechungen, interne Berichte) können automatisch
  auf bestimmte Rollen **beschränkt** werden (🔒-Symbol in der Vorschau) - für
  alle anderen Mitglieder unsichtbar, ganz ohne manuelles Nacharbeiten
- Ein Sicherheitscheck stellt sicher, dass sich die KI keine Rollennamen ausdenkt,
  die gar nicht existieren - eine erfundene Rolle in "visible_to" wird automatisch
  verworfen statt einen kaputten Verweis zu erzeugen

## Vorlagen-Bibliothek (10 Stück)

🚔 Polizei/Behörden-RP · 🎮 Gaming-Community · 🛠️ Support-Server ·
💼 Wirtschafts-RP · 🌐 Allgemeine Community · 🌸 Anime/Weeb-Community ·
🎨 Kunst & Design · 🎵 Musik-Community · 🎥 Streamer/Content Creator ·
💻 Tech/Programmierer-Community

Alle Vorlagen nutzen bereits gezielt gesetzte Emojis, Kanal-Beschreibungen
(Topics) und teils automatisch eingeschränkte Team-Kanäle - genau wie bei
der KI-Generierung.

## Emoji-Verhalten (KI + Vorlagen)

Kategorien bekommen immer ein passendes Emoji. Bei Kanälen wird gezielt
ausgewählt: die wichtigsten/auffälligsten Kanäle (Regeln, Ankündigungen,
besondere Voice-Channels, Highlights) bekommen ein treffendes Emoji als
Präfix, alltägliche Chat-Kanäle (allgemein, off-topic) bleiben schlicht -
Qualität vor Menge, damit es nicht überladen wirkt.
