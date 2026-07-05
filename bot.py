"""
Server-Setup-Bot - globaler Discord-Bot für automatischen Server-Aufbau
=========================================================================
Läuft auf beliebig vielen Servern gleichzeitig (globaler Bot, keine
serverspezifische Konfiguration nötig).

Funktionen:
1. /server-erstellen thema:<text> - KI erstellt einen Bauplan (Kategorien,
   Kanäle, Rollen) passend zum Thema (z.B. "Polizei-Server"). Vorschau wird
   gezeigt, Nutzer bestätigt, passt an oder bricht ab, bevor irgendwas
   angelegt wird.
2. /server-vorlagen - Bibliothek fertiger Vorlagen (Polizei, Gaming,
   Support, Wirtschaft, Community) zur direkten Anwendung.
3. /server-backup-erstellen name:<text> - sichert die aktuelle Struktur
   (Kategorien, Kanäle, Rollen) des Servers unter einem Namen.
4. /server-backup-liste - zeigt gespeicherte Backups für diesen Server.
5. /server-backup-anwenden name:<text> - wendet ein gespeichertes Backup an.
   Ergänzt nur fehlende Kanäle/Rollen, löscht nie etwas Bestehendes.
6. /server-backup-loeschen name:<text> - löscht ein gespeichertes Backup.

Alle erstellenden Befehle brauchen "Server verwalten" beim ausführenden
Nutzer. Der Bot selbst braucht "Kanäle verwalten" + "Rollen verwalten"
(am einfachsten: Administrator) als Server-Berechtigung.

Stack: discord.py 2.7+, Groq API (Llama 3.1) für die KI-Generierung,
JSON-Storage für Backups (siehe storage.py).
"""

import os
import logging

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import ai
import templates
import storage

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("server-setup-bot")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# ---------------------------------------------------------------------------
# Plan anwenden (gemeinsam für KI-Pläne, Vorlagen und Backups)
# ---------------------------------------------------------------------------

def _hex_to_color(hex_str: str) -> discord.Color:
    try:
        return discord.Color(int(hex_str.lstrip("#"), 16))
    except (ValueError, AttributeError):
        return discord.Color.default()


async def apply_plan(guild: discord.Guild, plan: dict, merge: bool = False) -> dict:
    """
    Erstellt Rollen, Kategorien und Kanäle aus einem Plan.
    merge=True: bereits existierende Rollen/Kanäle (gleicher Name) werden
    übersprungen statt dupliziert - wichtig für Backup-Wiederherstellung,
    damit nichts Bestehendes verdoppelt oder überschrieben wird.
    """
    counts = {"roles": 0, "categories": 0, "channels": 0, "skipped": 0}

    for role_spec in plan.get("roles", []):
        name = role_spec.get("name", "Neue Rolle")[:100]
        if merge and discord.utils.get(guild.roles, name=name):
            counts["skipped"] += 1
            continue
        try:
            await guild.create_role(
                name=name,
                color=_hex_to_color(role_spec.get("color", "#99aab5")),
                hoist=bool(role_spec.get("hoist", False)),
                reason="Server-Setup-Bot: Rolle aus Plan erstellt",
            )
            counts["roles"] += 1
        except discord.Forbidden:
            log.warning(f"Keine Berechtigung, Rolle '{name}' zu erstellen.")

    for cat_spec in plan.get("categories", []):
        cat_name = cat_spec.get("name", "Kategorie")[:100]
        category = discord.utils.get(guild.categories, name=cat_name) if merge else None

        if category is None:
            try:
                category = await guild.create_category(
                    cat_name, reason="Server-Setup-Bot: Kategorie aus Plan erstellt"
                )
                counts["categories"] += 1
            except discord.Forbidden:
                log.warning(f"Keine Berechtigung, Kategorie '{cat_name}' zu erstellen.")
                continue

        for ch_spec in cat_spec.get("channels", []):
            ch_name = ch_spec.get("name", "kanal")[:100]
            ch_type = ch_spec.get("type", "text")

            if merge and discord.utils.get(category.channels, name=ch_name):
                counts["skipped"] += 1
                continue

            try:
                if ch_type == "voice":
                    await category.create_voice_channel(ch_name, reason="Server-Setup-Bot")
                else:
                    await category.create_text_channel(ch_name, reason="Server-Setup-Bot")
                counts["channels"] += 1
            except discord.Forbidden:
                log.warning(f"Keine Berechtigung, Kanal '{ch_name}' zu erstellen.")

    return counts


def scan_current_server(guild: discord.Guild) -> dict:
    """Baut einen Plan aus der aktuellen Serverstruktur (für Backups)."""
    categories = []
    for cat in guild.categories:
        channels = []
        for ch in cat.channels:
            if isinstance(ch, discord.TextChannel):
                channels.append({"name": ch.name, "type": "text"})
            elif isinstance(ch, discord.VoiceChannel):
                channels.append({"name": ch.name, "type": "voice"})
        categories.append({"name": cat.name, "channels": channels})

    uncategorized = [
        ch for ch in guild.channels
        if ch.category is None and isinstance(ch, (discord.TextChannel, discord.VoiceChannel))
    ]
    if uncategorized:
        categories.append({
            "name": "Ohne Kategorie",
            "channels": [
                {"name": ch.name, "type": "text" if isinstance(ch, discord.TextChannel) else "voice"}
                for ch in uncategorized
            ],
        })

    roles = []
    for r in guild.roles:
        if r.is_default() or r.managed:
            continue
        roles.append({
            "name": r.name,
            "color": f"#{r.color.value:06x}" if r.color.value else "#99aab5",
            "hoist": r.hoist,
        })

    return {"categories": categories, "roles": roles}


# ---------------------------------------------------------------------------
# Vorschau-Embed
# ---------------------------------------------------------------------------

def build_preview_embed(title: str, plan: dict) -> discord.Embed:
    embed = discord.Embed(title=title, color=discord.Color.blurple())

    for cat in plan.get("categories", []):
        lines = []
        for ch in cat.get("channels", []):
            icon = "🔊" if ch.get("type") == "voice" else "#"
            lines.append(f"{icon} {ch.get('name')}")
        embed.add_field(
            name=cat.get("name", "Kategorie"),
            value="\n".join(lines) if lines else "*(keine Kanäle)*",
            inline=True,
        )

    roles = plan.get("roles", [])
    if roles:
        role_lines = [f"● {r.get('name')}" for r in roles]
        embed.add_field(name="🎭 Rollen", value="\n".join(role_lines)[:1024], inline=False)

    total_channels = sum(len(c.get("channels", [])) for c in plan.get("categories", []))
    embed.set_footer(
        text=f"{len(plan.get('categories', []))} Kategorien · {total_channels} Kanäle · {len(roles)} Rollen"
    )
    return embed


# ---------------------------------------------------------------------------
# Views: Vorschau bestätigen / anpassen / abbrechen
# ---------------------------------------------------------------------------

class AdjustModal(discord.ui.Modal, title="Plan anpassen"):
    adjustment = discord.ui.TextInput(
        label="Was soll geändert werden?",
        style=discord.TextStyle.paragraph,
        placeholder="z.B. 'Füge einen Voice-Channel für Streife hinzu' oder 'Entferne die Rolle Anwärter'",
        required=True,
        max_length=300,
    )

    def __init__(self, thema: str, plan: dict, parent_view: "PlanPreviewView"):
        super().__init__()
        self.thema = thema
        self.plan = plan
        self.parent_view = parent_view

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            new_plan = await ai.adjust_plan(self.thema, self.plan, self.adjustment.value)
        except Exception as e:
            await interaction.followup.send(f"Anpassung fehlgeschlagen: {e}", ephemeral=True)
            return

        new_view = PlanPreviewView(self.thema, new_plan, merge=self.parent_view.merge)
        embed = build_preview_embed(f"📋 Vorschau (angepasst): {self.thema}", new_plan)
        await interaction.edit_original_response(embed=embed, view=new_view)


class PlanPreviewView(discord.ui.View):
    def __init__(self, thema: str, plan: dict, merge: bool = False):
        super().__init__(timeout=600)
        self.thema = thema
        self.plan = plan
        self.merge = merge
        if not ai.groq_client:
            # Ohne KI-Zugang kann nicht angepasst werden
            for item in list(self.children):
                if getattr(item, "custom_id", "") == "plan_anpassen":
                    self.remove_item(item)

    @discord.ui.button(label="✅ Erstellen", style=discord.ButtonStyle.success, custom_id="plan_erstellen")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        counts = await apply_plan(interaction.guild, self.plan, merge=self.merge)
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)
        skip_text = f", {counts['skipped']} übersprungen (bereits vorhanden)" if counts["skipped"] else ""
        await interaction.followup.send(
            f"✅ Fertig! Erstellt: {counts['roles']} Rollen, {counts['categories']} Kategorien, "
            f"{counts['channels']} Kanäle{skip_text}.",
            ephemeral=True,
        )

    @discord.ui.button(label="✏️ Anpassen", style=discord.ButtonStyle.secondary, custom_id="plan_anpassen")
    async def adjust(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdjustModal(self.thema, self.plan, self))

    @discord.ui.button(label="❌ Abbrechen", style=discord.ButtonStyle.danger, custom_id="plan_abbrechen")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="Abgebrochen, es wurde nichts erstellt.", view=self)


class TemplateSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=label, value=key)
            for key, label in templates.get_template_choices()
        ]
        super().__init__(placeholder="Vorlage auswählen...", options=options)

    async def callback(self, interaction: discord.Interaction):
        plan = templates.get_template_plan(self.values[0])
        label = dict(templates.get_template_choices())[self.values[0]]
        embed = build_preview_embed(f"📋 Vorschau: {label}", plan)
        view = PlanPreviewView(label, plan, merge=False)
        await interaction.response.edit_message(content=None, embed=embed, view=view)


class TemplateSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(TemplateSelect())


# ---------------------------------------------------------------------------
# Slash Commands
# ---------------------------------------------------------------------------

@bot.tree.command(name="server-erstellen", description="KI erstellt einen Serverbauplan zu einem freien Thema")
@app_commands.describe(thema="z.B. 'Polizei-Server', 'Anime-Community', 'Handwerksbetrieb RP'")
@app_commands.checks.has_permissions(manage_guild=True)
async def server_erstellen(interaction: discord.Interaction, thema: str):
    await interaction.response.defer(thinking=True)
    try:
        plan = await ai.generate_plan(thema)
    except Exception as e:
        await interaction.followup.send(f"KI-Generierung fehlgeschlagen: {e}", ephemeral=True)
        return

    embed = build_preview_embed(f"📋 Vorschau: {thema}", plan)
    view = PlanPreviewView(thema, plan, merge=False)
    await interaction.followup.send(embed=embed, view=view)


@bot.tree.command(name="server-vorlagen", description="Fertige Server-Vorlagen zur Auswahl")
@app_commands.checks.has_permissions(manage_guild=True)
async def server_vorlagen(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Wähl eine Vorlage aus der Liste:", view=TemplateSelectView(), ephemeral=True
    )


@bot.tree.command(name="server-backup-erstellen", description="Sichert die aktuelle Serverstruktur unter einem Namen")
@app_commands.describe(name="Name für dieses Backup, z.B. 'vor-umbau-2026'")
@app_commands.checks.has_permissions(manage_guild=True)
async def server_backup_erstellen(interaction: discord.Interaction, name: str):
    await interaction.response.defer(ephemeral=True)
    plan = scan_current_server(interaction.guild)
    await storage.save_backup(interaction.guild.id, name, plan)
    total_channels = sum(len(c["channels"]) for c in plan["categories"])
    await interaction.followup.send(
        f"✅ Backup **{name}** gespeichert ({len(plan['categories'])} Kategorien, "
        f"{total_channels} Kanäle, {len(plan['roles'])} Rollen).",
        ephemeral=True,
    )


@bot.tree.command(name="server-backup-liste", description="Zeigt gespeicherte Backups für diesen Server")
@app_commands.checks.has_permissions(manage_guild=True)
async def server_backup_liste(interaction: discord.Interaction):
    backups = await storage.list_backups(interaction.guild.id)
    if not backups:
        await interaction.response.send_message("Noch keine Backups für diesen Server gespeichert.", ephemeral=True)
        return
    lines = [f"**{b['name']}** — erstellt {b['created_at'][:10]}" for b in backups]
    await interaction.response.send_message("**Gespeicherte Backups:**\n" + "\n".join(lines), ephemeral=True)


async def backup_name_autocomplete(interaction: discord.Interaction, current: str):
    backups = await storage.list_backups(interaction.guild.id)
    return [
        app_commands.Choice(name=b["name"], value=b["name"])
        for b in backups if current.lower() in b["name"].lower()
    ][:25]


@bot.tree.command(name="server-backup-anwenden", description="Wendet ein gespeichertes Backup an (ergänzt nur Fehlendes)")
@app_commands.describe(name="Name des Backups")
@app_commands.autocomplete(name=backup_name_autocomplete)
@app_commands.checks.has_permissions(manage_guild=True)
async def server_backup_anwenden(interaction: discord.Interaction, name: str):
    backup = await storage.get_backup(interaction.guild.id, name)
    if not backup:
        await interaction.response.send_message(f"Kein Backup namens '{name}' gefunden.", ephemeral=True)
        return
    embed = build_preview_embed(f"📋 Backup wiederherstellen: {name}", backup["plan"])
    embed.description = "Bereits vorhandene Kanäle/Rollen (gleicher Name) werden übersprungen, nichts wird gelöscht."
    view = PlanPreviewView(name, backup["plan"], merge=True)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name="server-backup-loeschen", description="Löscht ein gespeichertes Backup")
@app_commands.describe(name="Name des Backups")
@app_commands.autocomplete(name=backup_name_autocomplete)
@app_commands.checks.has_permissions(manage_guild=True)
async def server_backup_loeschen(interaction: discord.Interaction, name: str):
    deleted = await storage.delete_backup(interaction.guild.id, name)
    if deleted:
        await interaction.response.send_message(f"🗑️ Backup '{name}' gelöscht.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Kein Backup namens '{name}' gefunden.", ephemeral=True)


# ---------------------------------------------------------------------------
# Fehlerbehandlung (fehlende Berechtigung etc.)
# ---------------------------------------------------------------------------

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        msg = "Dafür brauchst du die Berechtigung 'Server verwalten'."
    else:
        msg = f"Es ist ein Fehler aufgetreten: {error}"
        log.error(f"Command-Fehler: {error}")
    try:
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
    except discord.HTTPException:
        pass


# ---------------------------------------------------------------------------
# Bot Events
# ---------------------------------------------------------------------------

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        log.info(f"{len(synced)} Slash-Commands global synchronisiert (kann bis zu 1h dauern, bis sie überall sichtbar sind).")
    except Exception as e:
        log.error(f"Sync fehlgeschlagen: {e}")
    log.info(f"Eingeloggt als {bot.user} (ID: {bot.user.id}) - aktiv auf {len(bot.guilds)} Server(n).")


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise SystemExit("DISCORD_TOKEN fehlt in den Environment Variables!")
    bot.run(DISCORD_TOKEN)
