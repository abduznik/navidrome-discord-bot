# Navidrome Discord Music Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![Discord.py 2.7](https://img.shields.io/badge/discord.py-2.7-7289DA.svg)](https://discordpy.readthedocs.io/)

A self-hosted Discord music bot that streams directly from your Navidrome library using the Subsonic API. Built for homelab enthusiasts who want full control over their music playback without third-party services.

## Features

- **Direct Streaming** -- Streams audio from Navidrome to Discord voice channels with zero local storage
- **Radio Mode** -- Infinite random playback from your entire library
- **Album Queuing** -- Queue entire albums with a single command
- **Search & Play** -- Search your library and play songs instantly
- **Role-Based Access Control** -- Restrict bot usage to specific Discord roles
- **DAVE Encryption** -- Full support for Discord's End-to-End Encryption (discord.py 2.7+)
- **Auto-Disconnect** -- Bot leaves voice channels when alone
- **Volume Control** -- Adjustable volume per session
- **Loop Mode** -- Repeat the current queue

## Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/abduznik/navidrome-discord-bot.git
cd navidrome-discord-bot
cp .env.example .env
```

Edit `.env` with your Discord bot token and Navidrome credentials:

```ini
DISCORD_TOKEN=your-bot-token-here
DISCORD_ALLOWED_ROLE_ID=1234567890123456789
NAVIDROME_URL=http://localhost:4533
NAVIDROME_USERNAME=navidrome-bot
NAVIDROME_PASSWORD=your-password
```

### 2. Run with Docker (Recommended)

```bash
docker compose up -d
```

### 3. Run Locally

```bash
pip install -r requirements.txt
python bot.py
```

## Commands

All commands use the `??` prefix (configurable via `DISCORD_COMMAND_PREFIX`).

| Command | Description |
|---------|-------------|
| `??play <query>` | Search and play a song |
| `??album <query>` | Queue an entire album |
| `??random` | Play a random song from your library |
| `??radio` | Start infinite random playback |
| `??skip` | Skip the current track |
| `??stop` | Stop playback and clear the queue |
| `??pause` / `??resume` | Pause or resume playback |
| `??volume <0-100>` | Set playback volume |
| `??loop` | Toggle loop mode |
| `??queue` | Show the current queue |
| `??nowplaying` | Show what is currently playing |
| `??join` / `??leave` | Join or leave your voice channel |

## Configuration

All configuration is via environment variables (loaded from `.env`):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_TOKEN` | Yes | -- | Discord bot token |
| `DISCORD_ALLOWED_ROLE_ID` | Yes | -- | Role ID allowed to use the bot |
| `DISCORD_GUILD_ID` | Yes | -- | Your Discord server ID |
| `NAVIDROME_URL` | Yes | -- | Navidrome server URL |
| `NAVIDROME_USERNAME` | Yes | -- | Navidrome username |
| `NAVIDROME_PASSWORD` | Yes | -- | Navidrome password |
| `DISCORD_COMMAND_PREFIX` | No | `??` | Command prefix |
| `BOT_DEFAULT_VOLUME` | No | `0.5` | Default volume (0.0 - 1.0) |
| `BOT_EMBED_COLOR` | No | `0x5865F2` | Embed color as hex |
| `BOT_MAX_QUEUE_SIZE` | No | `200` | Maximum queue size |

## Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application and bot
3. Enable **Message Content Intent** and **Server Members Intent**
4. Generate an invite URL with permissions: `Connect`, `Speak`, `Use Voice Activity`
5. Invite the bot to your server
6. Assign the allowed role to users who should have bot access

## Architecture

```
navidrome-bot/
  bot.py           -- Main bot logic, commands, and playback engine
  navidrome.py     -- Subsonic API client for Navidrome
  .env             -- Environment variables (not committed)
  .env.example     -- Template for environment variables
  Dockerfile       -- Container image definition
  docker-compose.yml -- Docker Compose configuration
  requirements.txt -- Python dependencies
```

## Tech Stack

- **Python 3.12** -- Runtime
- **discord.py 2.7** -- Discord API with DAVE encryption support
- **FFmpeg** -- Audio decoding and format conversion
- **Navidrome Subsonic API** -- Music library access
- **Docker** -- Containerized deployment

## License

MIT License -- see [LICENSE](LICENSE) for details.
