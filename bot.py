"""Navidrome Discord Music Bot."""
import asyncio, logging, os, random as rng
from collections import deque
import discord
from discord.ext import commands
from dotenv import load_dotenv
from navidrome import NavidromeClient

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("bot")


def _require(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


TOKEN = _require("DISCORD_TOKEN")
ALLOWED_ROLE_ID = int(_require("DISCORD_ALLOWED_ROLE_ID"))
PREFIX = os.getenv("DISCORD_COMMAND_PREFIX", "??")
NAVI_URL = _require("NAVIDROME_URL")
NAVI_USER = _require("NAVIDROME_USERNAME")
NAVI_PASS = _require("NAVIDROME_PASSWORD")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)
navidrome = NavidromeClient(url=NAVI_URL, username=NAVI_USER, password=NAVI_PASS)

class GuildMusicState:
    def __init__(self):
        self.queue = deque()
        self.current = None
        self.volume = 0.5
        self.loop = False
        self.radio = False
        self._next_event = asyncio.Event()
        self._playing = False
        self.voice_channel = None
        self.text_channel = None

    def stop(self):
        self.current = None
        self.queue.clear()
        self.radio = False
        self._next_event.set()

    def skip(self):
        self._next_event.set()

    async def wait_for_next(self):
        await self._next_event.wait()
        self._next_event.clear()

states = {}

def get_state(guild_id):
    if guild_id not in states:
        states[guild_id] = GuildMusicState()
    return states[guild_id]

def has_allowed_role(ctx):
    if ctx.guild is None: return False
    role = ctx.guild.get_role(ALLOWED_ROLE_ID)
    return role in ctx.author.roles if role else False

def format_duration(seconds):
    if seconds <= 0: return "??:??"
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def song_id(song): return song.get("id") if isinstance(song, dict) else ""
def song_title(song): return song.get("title", "Unknown") if isinstance(song, dict) else "Unknown"
def song_artist(song): return song.get("artist", "Unknown") if isinstance(song, dict) else "Unknown"
def song_album(song): return song.get("album", "") if isinstance(song, dict) else ""
def song_duration(song): return int(song.get("duration", 0)) if isinstance(song, dict) else 0

async def _ensure_voice(guild, voice_channel):
    vc = guild.voice_client
    if vc and vc.is_connected():
        if vc.channel.id == voice_channel.id:
            return vc
        await vc.move_to(voice_channel)
        return vc
    try:
        return await voice_channel.connect(self_deaf=True)
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        return None

async def _play_song(guild, text_channel, state, song):
    vc = await _ensure_voice(guild, state.voice_channel)
    if not vc:
        await text_channel.send("Failed to connect to voice.")
        return False
    try:
        stream_url = await navidrome.get_stream_url(song_id(song))
        source = discord.FFmpegPCMAudio(stream_url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn")
        volume_source = discord.PCMVolumeTransformer(source, volume=state.volume)
    except Exception as e:
        logger.error(f"Audio error: {e}")
        return False
    embed = discord.Embed(title="Now Playing", description=f"**{song_title(song)}**\n{song_artist(song)} -- {song_album(song)}\nDuration: {format_duration(song_duration(song))}")
    try: await text_channel.send(embed=embed)
    except: pass
    state.current = song
    state._playing = True
    def after_playing(error):
        state._playing = False
        asyncio.run_coroutine_threadsafe(state._next_event.set(), bot.loop)
    vc.play(volume_source, after=after_playing)
    return True

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")

@bot.command(name="play")
async def play_command(ctx, *, query):
    if not has_allowed_role(ctx): return await ctx.send("No permission.")
    if not ctx.author.voice: return await ctx.send("Join voice first.")
    state = get_state(ctx.guild.id)
    state.voice_channel = ctx.author.voice.channel
    state.text_channel = ctx.channel
    results = await navidrome.search(query, song_count=5)
    songs = results.get("song", [])
    if not songs: return await ctx.send("No results.")
    if not isinstance(songs, list): songs = [songs]
    for song in songs[1:5]: state.queue.append(song)
    await _play_song(ctx.guild, ctx.channel, state, songs[0])
    asyncio.create_task(_playback_loop(ctx.guild, ctx.channel))

@bot.command(name="skip")
async def skip_command(ctx):
    state = get_state(ctx.guild.id)
    state.skip()
    await ctx.send("Skipped.")

@bot.command(name="stop")
async def stop_command(ctx):
    state = get_state(ctx.guild.id)
    state.stop()
    vc = ctx.guild.voice_client
    if vc: await vc.disconnect()
    await ctx.send("Stopped.")

@bot.command(name="radio")
async def radio_command(ctx):
    if not ctx.author.voice: return await ctx.send("Join voice first.")
    state = get_state(ctx.guild.id)
    state.radio = True
    state.voice_channel = ctx.author.voice.channel
    state.text_channel = ctx.channel
    await ctx.send("Radio mode ON")
    asyncio.create_task(_radio_loop(ctx.guild, ctx.channel))

async def _playback_loop(guild, text_channel):
    state = get_state(guild.id)
    while True:
        await state.wait_for_next()
        if state.queue: state.current = state.queue.popleft()
        elif not state.loop: return
        await _play_song(guild, text_channel, state, state.current)
        while state._playing: await asyncio.sleep(0.5)

async def _radio_loop(guild, text_channel):
    state = get_state(guild.id)
    while state.radio:
        albums = await navidrome.get_album_list("random", size=1)
        if not albums: continue
        album = albums[0] if isinstance(albums, list) else albums
        detail = await navidrome.get_album(song_id(album))
        tracks = detail.get("song", [])
        if not tracks: continue
        track = rng.choice(tracks if isinstance(tracks, list) else [tracks])
        success = await _play_song(guild, text_channel, state, track)
        if success:
            while state._playing: await asyncio.sleep(0.5)

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
