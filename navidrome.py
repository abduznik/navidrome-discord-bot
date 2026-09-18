"""
Navidrome Subsonic API Client

Async client for interacting with a Navidrome server via the Subsonic API.
Supports password-based authentication (salted MD5) and direct stream URLs.
"""

import hashlib
import logging
import random
import string

import aiohttp

logger = logging.getLogger("navidrome")


class NavidromeClient:
    """Async client for Navidrome's Subsonic API."""

    def __init__(self, url: str, username: str, password: str):
        self.base_url = url.rstrip("/") + "/rest"
        self.username = username
        self.password = password
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def _get_auth_params(self) -> dict:
        """Build authentication parameters using salted MD5."""
        salt = "".join(random.choices(string.ascii_letters + string.digits, k=16))
        token = hashlib.md5((self.password + salt).encode()).hexdigest()
        return {
            "u": self.username,
            "t": token,
            "s": salt,
            "v": "1.16.1",
            "c": "navidrome-bot",
            "f": "json",
        }

    async def _request(self, endpoint: str, params: dict | None = None) -> dict:
        """Make an authenticated request to the Subsonic API."""
        url = f"{self.base_url}/{endpoint}"
        all_params = {**self._get_auth_params()}
        if params:
            all_params.update(params)

        session = await self._get_session()
        try:
            async with session.get(url, params=all_params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                data = await resp.json()
                if data.get("subsonic-response", {}).get("status") == "failed":
                    error = data["subsonic-response"].get("error", {})
                    raise Exception(
                        f"Subsonic error: {error.get('message', 'Unknown')} (code {error.get('code', '?')})"
                    )
                return data.get("subsonic-response", {})
        except aiohttp.ClientError as e:
            logger.error(f"Request failed: {e}")
            raise

    async def ping(self) -> bool:
        """Test connection to Navidrome."""
        try:
            result = await self._request("ping")
            return result.get("status") == "ok"
        except Exception:
            return False

    async def search(self, query: str, artist_count: int = 5, album_count: int = 5, song_count: int = 10) -> dict:
        """Search across artists, albums, and songs."""
        params = {
            "query": query,
            "artistCount": artist_count,
            "albumCount": album_count,
            "songCount": song_count,
        }
        result = await self._request("search3", params)
        return result.get("searchResult3", {})

    async def get_song(self, song_id: str) -> dict:
        """Get details for a specific song."""
        result = await self._request("getSong", {"id": song_id})
        return result.get("song", {})

    async def get_album(self, album_id: str) -> dict:
        """Get album details including tracks."""
        result = await self._request("getAlbum", {"id": album_id})
        return result.get("album", {})

    async def get_album_list(self, list_type: str = "recent", size: int = 20, offset: int = 0) -> list:
        """Get a list of albums (recent, frequent, random, etc.)."""
        params = {"type": list_type, "size": size, "offset": offset}
        result = await self._request("getAlbumList2", params)
        return result.get("albumList2", {}).get("album", [])

    async def get_stream_url(self, song_id: str) -> str:
        """Get the streaming URL for a song."""
        params = {"id": song_id, **self._get_auth_params()}
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.base_url}/stream?{query}"

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
