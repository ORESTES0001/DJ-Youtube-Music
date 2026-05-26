import os
from typing import Optional

import yt_dlp
import ytmusicapi

from database.models import get_session, PlaybackHistory


class YTMusicStreamer:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        auth_path = os.path.join(base_dir, "..", "browser.json")

        if not os.path.exists(auth_path):
            user_home = os.path.expanduser("~")
            auth_path = os.path.join(user_home, "browser.json")

        if os.path.exists(auth_path):
            try:
                self.api = ytmusicapi.YTMusic(auth_path)
            except Exception:
                self.api = ytmusicapi.YTMusic()
        else:
            self.api = ytmusicapi.YTMusic()

    # ---- YouTube Music search ----

    def search_song(self, keyword: str) -> Optional[str]:
        try:
            results = self.api.search(query=keyword, limit=3, filter="songs")
            if results and len(results) > 0:
                video_id = results[0].get("videoId")
                if video_id:
                    return video_id
            return None
        except Exception:
            return None

    # ---- yt-dlp stream extraction ----

    def extract_stream_url(self, video_id: str) -> Optional[dict]:
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        try:
            ydl_opts = {"format": "bestaudio/best", "quiet": True, "no_warnings": True}
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
            return None
        except Exception:
            return None

    def search_and_extract(self, keyword: str) -> Optional[dict]:
        video_id = self.search_song(keyword)
        if not video_id:
            return None
        result = self.extract_stream_url(video_id)
        if result:
            result["video_id"] = video_id
            return result
        return None

    # ---- Playback history persistence ----

    def record_playback(
        self, track_title: str, artist_name: str, user_id: int = None
    ) -> None:
        session = get_session()
        try:
            entry = PlaybackHistory(
                user_id=user_id,
                track_title=track_title,
                artist_name=artist_name,
            )
            session.add(entry)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    # ---- YouTube Music listening history ----

    def get_recent_history(self, limit: int = 10) -> str:
        if not getattr(self.api, "auth", None):
            return ""
        try:
            history_items = self.api.get_history()
            if not history_items or not isinstance(history_items, list):
                return ""
            recent_items = history_items[:limit]
            history_list = []
            for item in recent_items:
                try:
                    title = item.get("title", "Unknown Title")
                    artists = item.get("artists", [])
                    artist_name = (
                        artists[0].get("name", "Unknown Artist") if artists else "Unknown Artist"
                    )
                    history_list.append(f"{title} by {artist_name}")
                except Exception:
                    continue
            return "\n".join(history_list)
        except Exception:
            return ""
