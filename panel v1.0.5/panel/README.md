# Discord Bot Manager Panel

A Windows desktop panel for managing Discord bots.

## Requirements

- Windows 10/11
- Python 3.10 or newer
- A Discord bot project with a Python entry file

## Installation

```powershell
py -m pip install -r requirements.txt
py panel.pyw
```

The panel creates its local `settings.json` and `bots.json` state automatically. Copy the example files only when you want to start with an explicit configuration:

```powershell
Copy-Item settings.example.json settings.json
Copy-Item bots.example.json bots.json
```

## First setup

1. Start the panel.
2. Select or browse to the bot's main `.py` file.
3. Open **Basics / Integration**.
4. Generate or save `Panel.py`, `version.py` and `info.py` in the bot folder.
5. Load `Panel.py` from the bot's `bot.py` as a Discord extension.
6. Use the panel's copy button for the `/connect panel_id:... device:PC` command.
7. Configure the bot token and metadata in `version.py` through **Bot Data**.

## Public repository safety

Never commit these files or folders:

- `settings.json`
- `bots.json`
- `version.py`
- `.env`
- `logs/`
- `backups/`
- `panel_responses/`
- `panel_commands.json`
- `panel_broadcast_requests.json`

They can contain tokens, passwords, panel IDs, machine-specific paths or private bot data. The included `.gitignore` excludes them for new repositories. If a secret was committed before, remove it from Git history and rotate the token.

## Features

- Multi-bot start, stop, restart and crash recovery
- Auto-start, scheduled restart and midnight restart
- Log search and filtering
- RAM, CPU and temperature monitoring
- Performance charts and PNG export
- SQLite viewer
- ZIP backup and restore
- Discord Activity loop
- Broadcast messages through `Panel.py`
- English and Hungarian UI
- Plugin folder for panel extensions

## Plugin API

Place a Python file in `plugins/` with a `setup_panel(panel)` function:

```python
def setup_panel(panel):
    panel.log_event("EVENT", "Plugin loaded")
```

Keep plugins trusted. They run with the same permissions as the panel.
