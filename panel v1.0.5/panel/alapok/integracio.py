# --- BOT_VEZERLO.PY (Helyezd a botod fő .py fájlja mellé) ---

BOT_VEZERLO_CODE = r'''import asyncio
import datetime
import json
import os
import uuid

import discord
from discord import app_commands
from discord.ext import commands, tasks

BOT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BOT_DIR, "bot_config.json")
STATS_PATH = os.path.join(BOT_DIR, "bot_stats.json")
VERSION = "1.0.0"

class BotVezerlo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.connected_panel_id = None
        self.connected_source = "Discord"
        self.stats_loop.start()

    def load_config(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
                return json.load(config_file)
        except (OSError, json.JSONDecodeError):
            return {"panel_id": "#00001", "test_mode": False}

    def panel_directory(self):
        configured_path = self.load_config().get("panel_dir", "")
        if configured_path and os.path.isdir(configured_path):
            return configured_path
        return os.path.dirname(os.path.abspath(__file__))

    async def request_panel(self, action, user, bot_name="Main Bot"):
        config = self.load_config()
        expected_id = config.get("panel_id", "#00001")
        if self.connected_panel_id != expected_id:
            return "Előbb használd a /connect parancsot."

        panel_dir = self.panel_directory()
        command_path = os.path.join(panel_dir, "panel_commands.json")
        response_dir = os.path.join(panel_dir, "panel_responses")
        os.makedirs(response_dir, exist_ok=True)
        request_id = uuid.uuid4().hex
        request = {
            "id": request_id,
            "action": action,
            "user": user,
            "source": self.connected_source,
            "bot": bot_name,
            "created_at": datetime.datetime.now().isoformat(timespec="seconds")
        }
        try:
            pending = []
            if os.path.exists(command_path):
                with open(command_path, "r", encoding="utf-8") as command_file:
                    pending = json.load(command_file)
            pending.append(request)
            temporary_path = command_path + ".tmp"
            with open(temporary_path, "w", encoding="utf-8") as command_file:
                json.dump(pending, command_file, ensure_ascii=False)
            os.replace(temporary_path, command_path)
        except (OSError, json.JSONDecodeError) as error:
            return f"A panel nem érhető el: {error}"

        response_path = os.path.join(response_dir, request_id + ".json")
        for _ in range(20):
            await asyncio.sleep(0.5)
            if os.path.exists(response_path):
                try:
                    with open(response_path, "r", encoding="utf-8") as response_file:
                        response = json.load(response_file)
                    os.remove(response_path)
                    return response.get("message", "Nincs válasz.")
                except (OSError, json.JSONDecodeError):
                    return "A panel válasza nem olvasható."
        return "A panel 10 másodpercen belül nem válaszolt."

    @tasks.loop(seconds=2)
    async def stats_loop(self):
        config = self.load_config()
        stats = {
            "panel_id": config.get("panel_id", "#00001"),
            "guilds": len(self.bot.guilds),
            "users": sum(g.member_count or 0 for g in self.bot.guilds),
            "api_ping": round(self.bot.latency * 1000),
            "test_mode_active": config.get("test_mode", False),
            "version": VERSION,
            "updated_at": datetime.datetime.now().isoformat(timespec="seconds")
        }
        try:
            with open(STATS_PATH, "w", encoding="utf-8") as stats_file:
                json.dump(stats, stats_file, ensure_ascii=False, indent=4)
            servers_dir = os.path.join(BOT_DIR, "data", "servers")
            os.makedirs(servers_dir, exist_ok=True)
            for guild in self.bot.guilds:
                with open(os.path.join(servers_dir, f"{guild.id}.json"), "w", encoding="utf-8") as server_file:
                    json.dump({
                        "guild_id": guild.id,
                        "name": guild.name,
                        "member_count": guild.member_count,
                        "owner": str(guild.owner),
                        "description": guild.description,
                        "created_at": guild.created_at.isoformat(),
                        "version": VERSION,
                        "updated_at": datetime.datetime.now().isoformat(timespec="seconds")
                    }, server_file, ensure_ascii=False, indent=4)
        except OSError:
            pass

    @stats_loop.before_loop
    async def before_stats(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="connect", description="Kapcsolódás a panelhez")
    @app_commands.describe(panel_id="A panel azonosítója, például #12345", device="Telefon vagy PC")
    @app_commands.choices(device=[
        app_commands.Choice(name="Telefon", value="Telefon"),
        app_commands.Choice(name="PC", value="PC")
    ])
    async def connect(self, interaction: discord.Interaction, panel_id: str, device: app_commands.Choice[str] = None):
        if panel_id.strip() != self.load_config().get("panel_id", "#00001"):
            await interaction.response.send_message("Hibás panelazonosító.", ephemeral=True)
            return
        self.connected_panel_id = panel_id.strip()
        self.connected_source = device.value if device else "Discord"
        await interaction.response.send_message("Kapcsolódva a panelhez.", ephemeral=True)

    async def remote_command(self, interaction, action, bot_name="Main Bot"):
        config = self.load_config()
        allowed_ids = {str(value) for value in config.get("allowed_discord_ids", [])}
        if config.get("test_mode", False) and str(interaction.user.id) not in allowed_ids:
            await interaction.response.send_message("A bot teszt módban van. Jelenleg csak a tesztelők használhatják.", ephemeral=True)
            return
        if not self.connected_panel_id:
            await interaction.response.send_message("Előbb használd a /connect parancsot.", ephemeral=True)
            return
        await interaction.response.defer()
        result = await self.request_panel(action, str(interaction.user), bot_name)
        await interaction.followup.send(result[:1900])

    @app_commands.command(name="vezerles", description="Panelen lévő bot kezelése")
    @app_commands.describe(muvelet="Művelet", bot_neve="A panelben lévő bot neve")
    @app_commands.choices(muvelet=[
        app_commands.Choice(name="Indítás", value="start"),
        app_commands.Choice(name="Leállítás", value="stop"),
        app_commands.Choice(name="Újraindítás", value="restart"),
        app_commands.Choice(name="Állapot", value="status"),
        app_commands.Choice(name="Napló", value="log")
    ])
    async def vezerles(self, interaction: discord.Interaction, muvelet: app_commands.Choice[str], bot_neve: str = "Main Bot"):
        await self.remote_command(interaction, muvelet.value, bot_neve)

    @app_commands.command(name="info", description="Panel információ")
    async def info(self, interaction: discord.Interaction):
        await self.remote_command(interaction, "info")

    @app_commands.command(name="status", description="Panel állapot")
    async def status(self, interaction: discord.Interaction):
        await self.remote_command(interaction, "status")

    @app_commands.command(name="stressz", description="Erőforrás ellenőrzés")
    async def stressz(self, interaction: discord.Interaction):
        await self.remote_command(interaction, "stressz")

    @app_commands.command(name="log", description="Panel napló")
    async def log(self, interaction: discord.Interaction):
        await self.remote_command(interaction, "log")

    @app_commands.command(name="start", description="Bot indítása")
    async def start(self, interaction: discord.Interaction):
        await self.remote_command(interaction, "start")

    @app_commands.command(name="stop", description="Bot leállítása")
    async def stop(self, interaction: discord.Interaction):
        await self.remote_command(interaction, "stop")

    @app_commands.command(name="restart", description="Bot újraindítása")
    async def restart(self, interaction: discord.Interaction):
        await self.remote_command(interaction, "restart")

    @app_commands.command(name="kilepes", description="A bot kilép egy Discord szerverről")
    @app_commands.describe(guild_id="A Discord szerver azonosítója")
    async def kilepes(self, interaction: discord.Interaction, guild_id: str):
        if not self.connected_panel_id:
            await interaction.response.send_message("Előbb használd a /connect parancsot.", ephemeral=True)
            return
        try:
            guild = self.bot.get_guild(int(guild_id))
        except ValueError:
            guild = None
        if guild is None:
            await interaction.response.send_message("Nem található ilyen szerver.", ephemeral=True)
            return
        await guild.leave()
        await interaction.response.send_message(f"A bot kilépett innen: {guild.name}")

async def setup(bot):
    await bot.add_cog(BotVezerlo(bot))
'''

BOT_PY_TEMPLATE = (
    "# --- SABLON A SAJÁT BOT.PY FÁJLODHOZ ---\n"
    "import os\n"
    "import discord\n"
    "from discord.ext import commands\n\n"
    "VERSION = '1.0.0'\n\n"
    "env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')\n"
    "if os.path.exists(env_path):\n"
    "    for line in open(env_path, encoding='utf-8'):\n"
    "        if line.strip().startswith('DISCORD_BOT_TOKEN='):\n"
    "            os.environ['DISCORD_BOT_TOKEN'] = line.strip().split('=', 1)[1]\n\n"
    "CURRENT_PREFIX = \"/\"\n\n"
    "async def get_prefix(bot, message):\n"
    "    return CURRENT_PREFIX\n\n"
    "intents = discord.Intents.default()\n"
    "intents.message_content = True\n\n"
    "bot = commands.Bot(command_prefix=get_prefix, intents=intents)\n\n"
    "@bot.event\n"
    "async def on_ready():\n"
    "    print(f'Bot bejelentkezve: {{bot.user}}')\n"
    "    try:\n"
    "        await bot.load_extension('bot_vezerlo')\n"
    "        await bot.tree.sync()\n"
    "        print('Bot vezérlő sikeresen betöltve.')\n"
    "    except Exception as e:\n"
    "        print(f'Hiba a vezérlő betöltésekor: {{e}}')\n\n"
    "@bot.command(name='teszt', aliases=['test'])\n"
    "async def teszt_parancs(ctx):\n"
    "    embed = discord.Embed(title='Bot teszt', description=f'✅ A bot működik! Verzió: {VERSION}', color=discord.Color.green())\n"
    "    await ctx.send(embed=embed)\n"
    "\n"
    "token = os.environ.get('DISCORD_BOT_TOKEN')\n"
    "if not token:\n"
    "    raise RuntimeError('A DISCORD_BOT_TOKEN környezeti változó nincs beállítva.')\n"
    "bot.run(token)\n"
)