from typing import Optional

import yt_dlp
from ytmusicapi import YTMusic

from database.models import get_session, PlaybackHistory


class YTMusicStreamer:
    def __init__(self, auth_service=None):
        self.auth_service = auth_service
        self._fallback_api = YTMusic()

    @property
    def _api(self):
        if self.auth_service and self.auth_service.is_authenticated:
            return self.auth_service.api
        return self._fallback_api

    @property
    def is_authenticated(self) -> bool:
        return bool(self.auth_service and self.auth_service.is_authenticated)

    # ---- playback transport control ----

    _worker_thread = None

    def _call_worker(self, method_name: str, *args):
        if self._worker_thread is not None:
            method = getattr(self._worker_thread, method_name, None)
            if method and callable(method):
                return method(*args)
        return None

    def toggle_pause(self) -> bool:
        return bool(self._call_worker("toggle_pause_process") or False)

    def set_volume(self, value: int):
        self._call_worker("set_volume", value)

    def skip_next(self):
        self._call_worker("skip_current_song")

    def go_previous(self):
        self._call_worker("go_previous")

    # ---- search & stream extraction ----

    def search_song(self, keyword: str) -> Optional[str]:
        if not keyword or not keyword.strip():
            return None
        try:
            results = self._api.search(query=keyword.strip(), limit=3, filter="songs")
            if isinstance(results, list):
                for r in results:
                    if isinstance(r, dict) and r.get("videoId"):
                        return r["videoId"]
                print(f"[MUSIC-SERVICE] search_song('{keyword}'): results have no videoId")
            else:
                print(f"[MUSIC-SERVICE] search_song('{keyword}'): no results returned")
            return None
        except Exception as e:
            print(f"[MUSIC-SERVICE ERROR] search_song('{keyword}'): {e}")
            return None

    def extract_stream_url(self, video_id: str) -> Optional[dict]:
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "noplaylist": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=False)
                stream_url = info_dict.get("url")
                meta_title = info_dict.get("title", "").strip()
                meta_artist = (
                    info_dict.get("artist")
                    or info_dict.get("channel")
                    or info_dict.get("uploader")
                    or ""
                )
                if stream_url:
                    return {
                        "stream_url": stream_url,
                        "title": meta_title,
                        "artist": meta_artist,
                    }
                print(f"[MUSIC-SERVICE] extract_stream_url({video_id}): no stream_url in yt-dlp result")
            return None
        except Exception as e:
            print(f"[YT-DLP ERROR] extract_stream_url({video_id}): {e}")
            return None

    def search_and_extract(self, keyword: str) -> Optional[dict]:
        if not keyword or not keyword.strip():
            keyword = "lo-fi programming music"
        print(f"[MUSIC-SERVICE] search_and_extract: keyword='{keyword}'")
        video_id = self.search_song(keyword)
        if not video_id:
            print(f"[MUSIC-SERVICE] search_and_extract: search_song returned None for '{keyword}'")
            return None
        print(f"[MUSIC-SERVICE] search_and_extract: found video_id={video_id}")
        result = self.extract_stream_url(video_id)
        if result:
            result["video_id"] = video_id
            return result
        print(f"[MUSIC-SERVICE] search_and_extract: extract_stream_url returned None for {video_id}")
        return None

    # ---- playback history ----

    def record_playback(self, track_title: str, artist_name: str, user_id: int = None) -> None:
        session = get_session()
        try:
            entry = PlaybackHistory(
                user_id=user_id,
                track_title=track_title,
                artist_name=artist_name,
            )
            session.add(entry)
            session.commit()
        except Exception as e:
            print(f"[DB ERROR] record_playback('{track_title}', '{artist_name}'): {e}")
            session.rollback()
        finally:
            session.close()

    # ---- YTM history ----

    def get_recent_history(self, limit: int = 10) -> str:
        try:
            items = self._api.get_history()
            if not items or not isinstance(items, list):
                print(f"[MUSIC-SERVICE] get_recent_history: returned {type(items).__name__}")
                return ""
            lines = []
            for item in items[:limit]:
                try:
                    title = item.get("title", "Unknown Title")
                    artists = item.get("artists", [])
                    artist = artists[0].get("name", "Unknown Artist") if artists else "Unknown Artist"
                    lines.append(f"{title} by {artist}")
                except Exception as e:
                    print(f"[MUSIC-SERVICE] get_recent_history: skipping item due to {e}")
                    continue
            return "\n".join(lines)
        except Exception as e:
            if "access_token" in str(e) or "400" in str(e):
                print(f"[MUSIC-SERVICE] get_recent_history: auth error (public mode), returning empty")
            else:
                print(f"[MUSIC-SERVICE ERROR] get_recent_history: {e}")
            return ""

    def get_user_history(self, limit: int = 30) -> list[dict]:
        try:
            items = self._api.get_history()
            if not items or not isinstance(items, list):
                print(f"[MUSIC-SERVICE] get_user_history: returned {type(items).__name__} (expected list)")
                return []
            print(f"[MUSIC-SERVICE] get_user_history: got {len(items)} history items")
            result = []
            for item in items[:limit]:
                try:
                    title = item.get("title", "Unknown Title")
                    artists = item.get("artists") or []
                    artist = artists[0].get("name", "") if artists else ""
                    album = item.get("album")
                    album_name = album.get("name", "") if isinstance(album, dict) else (album or "")
                    duration = item.get("duration", "")
                    thumbnails = item.get("thumbnails") or []
                    result.append({
                        "title": title,
                        "artist": artist,
                        "album": album_name,
                        "duration": str(duration) if duration else "",
                        "thumbnails": thumbnails,
                        "videoId": item.get("videoId", ""),
                    })
                except Exception as e:
                    print(f"[MUSIC-SERVICE] get_user_history: skipping item due to {e}")
                    continue
            return result
        except Exception as e:
            if "access_token" in str(e) or "400" in str(e):
                print(f"[MUSIC-SERVICE] get_user_history: auth error (public mode), returning empty")
            else:
                print(f"[MUSIC-SERVICE ERROR] get_user_history: {e}")
            return []

    def get_user_playlists(self) -> list:
        try:
            result = self._api.get_library_playlists(limit=50)
            if result and isinstance(result, list):
                print(f"[MUSIC-SERVICE] get_user_playlists: got {len(result)} playlists")
            else:
                print(f"[MUSIC-SERVICE] get_user_playlists: returned {type(result).__name__}")
            return result if isinstance(result, list) else []
        except Exception as e:
            if "access_token" in str(e) or "400" in str(e):
                print(f"[MUSIC-SERVICE] get_user_playlists: auth error (public mode), returning empty")
            else:
                print(f"[MUSIC-SERVICE ERROR] get_user_playlists: {e}")
            return []

    def get_explore_charts(self) -> dict:
        result = {"moods": [], "trending": []}
        try:
            moods = self._api.get_mood_categories()
            if moods and isinstance(moods, list):
                for m in moods[:8]:
                    result["moods"].append({
                        "name": m.get("title", "Mood"),
                        "params": m.get("params", ""),
                    })
        except Exception as e:
            if "access_token" in str(e) or "400" in str(e):
                pass  # expected in public mode
            else:
                print(f"[MUSIC-SERVICE ERROR] get_explore_charts (moods): {e}")
        try:
            charts = self._api.get_charts(country="US")
            if charts and isinstance(charts, dict):
                for section in ("trending", "viral", "genres"):
                    items = charts.get(section, [])
                    if isinstance(items, list):
                        for item in items[:6]:
                            artists = item.get("artists") or []
                            thumbnails = item.get("thumbnails") or []
                            result["trending"].append({
                                "title": item.get("title", ""),
                                "artist": artists[0].get("name", "") if artists else "",
                                "video_id": item.get("videoId", ""),
                                "plays": str(item.get("views", "") or ""),
                                "thumbnails": thumbnails,
                            })
        except Exception as e:
            if "access_token" in str(e) or "400" in str(e):
                pass  # expected in public mode
            else:
                print(f"[MUSIC-SERVICE ERROR] get_explore_charts (charts): {e}")
        return result

    def get_playlist_tracks(self, playlist_id: str) -> list:
        try:
            data = self._api.get_playlist(playlist_id)
            if not isinstance(data, dict):
                return []
            tracks = data.get("tracks", [])
            result = []
            for t in tracks:
                if not isinstance(t, dict):
                    continue
                video_id = t.get("videoId", "")
                if not video_id:
                    continue
                artists = t.get("artists") or []
                result.append({
                    "videoId": video_id,
                    "title": t.get("title", "Unknown"),
                    "artist": artists[0].get("name", "") if artists else "",
                })
            return result
        except Exception as e:
            print(f"[MUSIC-SERVICE] get_playlist_tracks({playlist_id}): {e}")
            return []

    def create_remote_playlist(self, title: str, description: str = "") -> Optional[str]:
        if not self.is_authenticated:
            print("[MUSIC-SERVICE] create_remote_playlist: not authenticated")
            return None
        try:
            result = self._api.create_playlist(title, description, privacy_status="PRIVATE")
            print(f"[MUSIC-SERVICE] create_remote_playlist: created '{title}' -> {result}")
            return result
        except Exception as e:
            print(f"[MUSIC-SERVICE ERROR] create_remote_playlist('{title}'): {e}")
            return None
