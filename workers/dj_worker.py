import json
import locale
import os
import threading
import time
from typing import List, Optional

_mpv_dll_path = os.path.join(os.path.expanduser("~"), "scoop", "apps", "mpv-git", "current")
if os.path.isdir(_mpv_dll_path):
    os.environ["PATH"] = _mpv_dll_path + os.pathsep + os.environ.get("PATH", "")

import mpv
import pyttsx3
from PySide6.QtCore import QThread, Signal

from database.models import get_session, PlaybackHistory

QUEUE_TARGET = 10


class VoiceEngine:
    def __init__(self):
        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty("voices")
            if voices:
                self.engine.setProperty("voice", voices[0].id)
        except Exception:
            self.engine = None

    def speak_comment(self, comment: str) -> bool:
        if not self.engine or not comment or not comment.strip():
            return False
        try:
            self.engine.say(comment)
            self.engine.runAndWait()
            time.sleep(0.05)
            return True
        except Exception:
            return False


class DJWorkerThread(QThread):
    status_changed = Signal(str)
    song_playing = Signal(str, str, str)
    log_message = Signal(str)
    dj_speaking = Signal(str)
    dj_commentary = Signal(str)
    dj_commentary_ready = Signal(str)
    finished_signal = Signal()
    pause_state_changed = Signal(bool)
    track_finished = Signal()
    shuffle_toggled = Signal(bool)
    repeat_toggled = Signal(bool)
    user_info_loaded = Signal(str, str)
    time_updated = Signal(float, float)
    queue_updated = Signal(list)

    def __init__(self, initial_query: str, llm_service, music_service, parent=None):
        super().__init__(parent)
        self.initial_query = initial_query
        self.current_query = initial_query
        self.llm_service = llm_service
        self.music_service = music_service

        self.is_paused = False
        self.skip_requested = False
        self.back_activated = False
        self.user_updated_context = False
        self.history_stack: List[str] = []
        self._shuffle = False
        self._repeat = False
        self._volume = 80
        self._next_video_id = None
        self._track_ended = False

        self._tts_thread: Optional[threading.Thread] = None
        self._fill_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # playback queue
        self.playback_queue: List[dict] = []
        self._queue_lock = threading.Lock()

        locale.setlocale(locale.LC_NUMERIC, "C")
        self.player = mpv.MPV(ytdl=True, video=False)
        self.player.register_event_callback(self._mpv_event_handler)
        self.player.volume = self._volume

    def _mpv_event_handler(self, event):
        if event.event_id == mpv.MpvEventID.END_FILE:
            self._track_ended = True

    # ---- Thread entry point ----

    def run(self):
        _pythoncom_module = None
        try:
            import pythoncom as _pythoncom_module
            _pythoncom_module.CoInitialize()
        except ImportError:
            pass

        name = self.music_service.get_account_name()
        avatar = self.music_service.get_account_avatar()
        self.user_info_loaded.emit(name, avatar)

        voice_engine = VoiceEngine()

        try:
            self._dj_loop(voice_engine)
        finally:
            try:
                self.player.terminate()
            except Exception:
                pass
            if _pythoncom_module:
                try:
                    _pythoncom_module.CoUninitialize()
                except Exception:
                    pass

    # ---- Context builders ----

    def _get_user_context(self) -> str:
        session = get_session()
        tracks = []
        artist_counter = {}
        try:
            recent = (
                session.query(PlaybackHistory)
                .order_by(PlaybackHistory.played_at.desc())
                .limit(10)
                .all()
            )
            for entry in recent:
                t = entry.track_title or "Unknown Track"
                a = entry.artist_name or "Unknown Artist"
                tracks.append({"title": t, "artist": a})
                artist_counter[a] = artist_counter.get(a, 0) + 1
        except Exception:
            pass
        finally:
            session.close()

        top_artists = sorted(artist_counter.items(), key=lambda x: -x[1])[:5]
        top_artists_list = [{"artist": a, "plays": c} for a, c in top_artists]

        context = {
            "recent_tracks": tracks,
            "top_artists": top_artists_list,
        }
        return json.dumps(context, indent=2, ensure_ascii=False)

    # ---- Voice helper ----

    def _speak(self, voice_engine: VoiceEngine, text: str):
        if self.stop_event.is_set():
            return
        def _do_speak():
            if self.stop_event.is_set():
                return
            voice_engine.speak_comment(text)
        self._tts_thread = threading.Thread(target=_do_speak, daemon=True)
        self._tts_thread.start()

    # ---- Volume crossfade ----

    def _fade_volume(self, from_v: int, to_v: int, steps: int = 8, delay: float = 0.025):
        for i in range(steps + 1):
            if self.stop_event.is_set():
                return
            v = from_v + (to_v - from_v) * i // steps
            self.player.volume = max(0, min(100, v))
            self.msleep(int(delay * 1000))
        self.player.volume = max(0, min(100, to_v))

    # ---- Queue buffer filling (background) ----

    def _fetch_one_recommendation(self, avoid_titles: list[str] = None) -> Optional[dict]:
        if not self.current_query or not self.current_query.strip():
            return None
        user_context = self._get_user_context()
        llm_result = self.llm_service.get_llm_response(
            self.current_query, user_context=user_context, timeout=120,
            avoid_list=avoid_titles,
        )
        if self.stop_event.is_set() or not llm_result:
            return None
        next_query = llm_result.get(
            "termino_busqueda_yt",
            llm_result.get("musica_elegida",
            llm_result.get("siguiente_cancion", self.current_query)),
        )
        commentary = llm_result.get(
            "comentario_personalizado",
            llm_result.get("comentario_dj", ""),
        ) or "Seguimos con el ritmo."
        stream_data = self.music_service.search_and_extract(next_query)
        if self.stop_event.is_set() or not stream_data:
            return None
        return {
            "stream_data": stream_data,
            "commentary": commentary,
            "query": next_query,
            "llm_result": llm_result,
        }

    def _fill_queue_buffer(self, count: int):
        if self.stop_event.is_set():
            return
        added = 0
        for _ in range(count):
            if self.stop_event.is_set():
                break
            with self._queue_lock:
                if len(self.playback_queue) >= QUEUE_TARGET:
                    break
                avoid_titles = [
                    item["stream_data"].get("title", "")
                    for item in self.playback_queue
                ]
            rec = self._fetch_one_recommendation(avoid_titles=avoid_titles)
            if rec is None:
                continue
            with self._queue_lock:
                self.playback_queue.append(rec)
                self.current_query = rec["query"]
            added += 1
            self.queue_updated.emit(self._queue_snapshot())
            time.sleep(1)  # brief rest between LLM calls
        if added:
            self.log_message.emit(f"[QUEUE] Added {added} tracks (total: {len(self.playback_queue)})")

    def _queue_snapshot(self) -> list:
        with self._queue_lock:
            return [
                {
                    "title": item["stream_data"].get("title", "Track"),
                    "artist": item["stream_data"].get("artist", "Artist"),
                    "thumbnail": item["stream_data"].get("thumbnail", ""),
                }
                for item in self.playback_queue
            ]

    # ---- mpv playback with fade, time tracking ----

    def _play_with_mpv(self, stream_url: str):
        self._track_ended = False

        if not stream_url:
            print(f"[DJTRACE] _play_with_mpv: empty stream_url, aborting")
            self.track_finished.emit()
            return

        print(f"[DJTRACE] _play_with_mpv: starting playback")
        self.player.volume = 5
        try:
            self.player.play(stream_url)
        except Exception as e:
            print(f"[DJTRACE] player.play() raised: {e}")
            self.log_message.emit(f"[PLAY ERROR] {e}")
            self.track_finished.emit()
            return
        try:
            self._fade_volume(5, self._volume, steps=10, delay=0.025)
        except Exception as e:
            print(f"[DJTRACE] _fade_volume raised: {e}")
        self.player.volume = self._volume

        self.is_paused = bool(self.player.pause)
        self.pause_state_changed.emit(self.is_paused)

        while True:
            if self.isInterruptionRequested() or self.stop_event.is_set():
                self._fade_volume(self._volume, 0)
                self.player.stop()
                return
            if self.skip_requested or self.user_updated_context:
                self.skip_requested = False
                self.back_activated = False
                self._fade_volume(self._volume, 0)
                self.player.stop()
                break
            if self._track_ended:
                self._track_ended = False
                break

            # Fallback: detect EOF via position vs duration
            try:
                tp = self.player.time_pos
                dur = self.player.duration
                if tp is not None and dur is not None and dur > 0 and tp >= dur - 1.0:
                    self._track_ended = True
                    continue
            except Exception:
                pass

            # Emit time-pos / duration for seek bar
            try:
                tp = self.player.time_pos
                dur = self.player.duration
                if tp is not None and dur is not None:
                    self.time_updated.emit(float(tp), float(dur))
            except Exception:
                pass

            self.msleep(200)

        self.player.volume = self._volume
        self.track_finished.emit()

    # ---- Main loop ----

    def _dj_loop(self, voice_engine: VoiceEngine):
        while True:
            if self.isInterruptionRequested():
                break

            if self.stop_event.is_set():
                self.stop_event.clear()
                self.skip_requested = False
                self.user_updated_context = False
                self.back_activated = False
                print(f"[DJTRACE] stop_event cleared, restarting")
                continue

            self.skip_requested = False
            self.user_updated_context = False

            # ── Path 1: Play from queue ──
            with self._queue_lock:
                if self.playback_queue:
                    item = self.playback_queue.pop(0)
                else:
                    item = None
            if item:
                stream_data = item["stream_data"]
                display_title = stream_data.get("title", "Track")
                display_artist = stream_data.get("artist", "Artist")
                dj_comment = item.get("commentary", "")
                next_song_query = item.get("query") or f"{display_title} {display_artist}"
                print(f"[DJTRACE] Path=QUEUE ({len(self.playback_queue)} remaining): {display_title} - {display_artist}")

                if self.stop_event.is_set():
                    self.stop_event.clear()
                    continue

                if dj_comment:
                    self.dj_speaking.emit(dj_comment)
                    self.dj_commentary.emit(dj_comment)
                    self.dj_commentary_ready.emit(dj_comment)
                    self.status_changed.emit("DJ speaking...")
                    self._speak(voice_engine, dj_comment)

                self.song_playing.emit(display_title, display_artist, stream_data.get("thumbnail", ""))
                self.status_changed.emit(f"Now Playing: {display_title} - {display_artist}")
                self.log_message.emit(f"Now playing: {display_title} - {display_artist}")

                self.music_service.record_playback(
                    display_title, display_artist,
                    video_id=stream_data.get("video_id", ""),
                )

                self._play_with_mpv(stream_data["stream_url"])
                print(f"[DJTRACE] _play_with_mpv returned")

                # Update query to keep the recommendation chain alive
                self.current_query = next_song_query

                # Refill queue in background (keep buffer at QUEUE_TARGET)
                if not self._fill_thread or not self._fill_thread.is_alive():
                    self._fill_thread = threading.Thread(
                        target=self._fill_queue_buffer, args=(1,), daemon=True
                    )
                    self._fill_thread.start()
                    self.queue_updated.emit(self._queue_snapshot())

                # Wait briefly for bg fill to add the next track (avoids gap)
                if not self.playback_queue:
                    for _ in range(30):
                        if self.stop_event.is_set() or self.isInterruptionRequested():
                            break
                        if self.playback_queue:
                            break
                        self.msleep(500)

                self.log_message.emit("Song finished. Moving to next turn...")

                if not self.history_stack or self.history_stack[-1] != self.current_query:
                    self.history_stack.append(self.current_query)
                if len(self.history_stack) > 100:
                    self.history_stack = self.history_stack[-100:]

                if self.stop_event.is_set():
                    self.stop_event.clear()
                continue

            # ── Path 2: Direct video ID (seed queue with this track) ──
            if self._next_video_id:
                print(f"[DJTRACE] Path=SEED_DIRECT_VIDEO")
                video_id = self._next_video_id
                self._next_video_id = None
                if self.stop_event.is_set():
                    self.stop_event.clear()
                    continue
                stream_data = self.music_service.extract_stream_url(video_id)
                if stream_data:
                    stream_data["video_id"] = video_id
                    display_title = stream_data.get("title", "Track")
                    display_artist = stream_data.get("artist", "Artist")
                    seed_query = f"{display_title} {display_artist}"
                    self.current_query = seed_query
                    with self._queue_lock:
                        self.playback_queue.clear()
                        self.playback_queue.append({
                            "stream_data": stream_data,
                            "commentary": "",
                            "query": seed_query,
                        })
                    self.queue_updated.emit(self._queue_snapshot())
                    self.log_message.emit(f"Seeding queue: {display_title} - {display_artist} (+ {QUEUE_TARGET - 1} more loading)")
                    threading.Thread(
                        target=self._fill_queue_buffer, args=(QUEUE_TARGET - 1,), daemon=True
                    ).start()
                    self.msleep(100)
                    continue
                else:
                    self.log_message.emit(f"Could not load video {video_id}")
                    self.msleep(3000)
                    continue

            # ── Path 3: First run — consult LLM + search (seed queue) ──
            # Double-check queue is still empty (bg fill might have caught up)
            with self._queue_lock:
                if self.playback_queue:
                    self.msleep(100)
                    continue

            print(f"[DJTRACE] Path=SEED_LLM query='{self.current_query}'")
            if self.stop_event.is_set():
                self.stop_event.clear()
                continue

            if not self.current_query or not self.current_query.strip():
                self.msleep(500)
                continue

            user_context = self._get_user_context()
            self.log_message.emit(f"--- Context -> '{self.current_query}' ---")
            self.status_changed.emit("Consulting the DJ AI...")

            llm_result = self.llm_service.get_llm_response(
                self.current_query, user_context=user_context
            )

            if self.stop_event.is_set():
                self.stop_event.clear()
                continue

            if llm_result:
                next_query = llm_result.get(
                    "termino_busqueda_yt",
                    llm_result.get("musica_elegida",
                    llm_result.get("siguiente_cancion", self.current_query)),
                )
                dj_comment = llm_result.get(
                    "comentario_personalizado",
                    llm_result.get("comentario_dj", ""),
                ) or f"Seguimos con el ritmo. Ahora viene algo de {self.current_query}."
                llm_title = llm_result.get("musica_elegida", next_query)
                llm_artist = llm_result.get("artista")

                self.dj_speaking.emit(dj_comment)
                self.dj_commentary.emit(dj_comment)
                self.dj_commentary_ready.emit(dj_comment)
                self.status_changed.emit("DJ speaking...")
                self._speak(voice_engine, dj_comment)

                if self.stop_event.is_set():
                    self.stop_event.clear()
                    continue

                self.status_changed.emit("Searching for the next track...")
                stream_data = self.music_service.search_and_extract(next_query)

                if self.stop_event.is_set():
                    self.stop_event.clear()
                    continue

                if stream_data:
                    display_title = stream_data.get("title") or (llm_title or next_query)
                    display_artist = stream_data.get("artist") or (llm_artist or "Unknown Artist")
                    with self._queue_lock:
                        self.playback_queue.clear()
                        self.playback_queue.append({
                            "stream_data": stream_data,
                            "commentary": dj_comment,
                            "query": next_query,
                        })
                    self.current_query = next_query
                    self.queue_updated.emit(self._queue_snapshot())
                    threading.Thread(
                        target=self._fill_queue_buffer, args=(QUEUE_TARGET - 1,), daemon=True
                    ).start()
                    self.msleep(100)
                    continue
                else:
                    self.log_message.emit(f"No results for '{next_query}', retrying...")
                    self.msleep(3000)
                    continue
            else:
                # LLM failed — fallback to raw search
                dj_comment = "Sintonizando la mejor musica en control local. Disfruta el siguiente tema."
                self.dj_commentary.emit(dj_comment)
                self.dj_commentary_ready.emit(dj_comment)
                self.status_changed.emit("Searching for the next track...")
                stream_data = self.music_service.search_and_extract(self.current_query)

                if self.stop_event.is_set():
                    self.stop_event.clear()
                    continue

                if stream_data:
                    display_title = stream_data.get("title", self.current_query)
                    display_artist = stream_data.get("artist", "Unknown Artist")
                    with self._queue_lock:
                        self.playback_queue.clear()
                        self.playback_queue.append({
                            "stream_data": stream_data,
                            "commentary": dj_comment,
                            "query": self.current_query,
                        })
                    self.queue_updated.emit(self._queue_snapshot())
                    threading.Thread(
                        target=self._fill_queue_buffer, args=(QUEUE_TARGET - 1,), daemon=True
                    ).start()
                    self.msleep(100)
                    continue
                else:
                    self.log_message.emit(f"No song found for '{self.current_query}'. Retrying...")
                    self.msleep(3000)
                    continue

    # ---- External controls ----

    def toggle_pause_process(self):
        new_state = not self.player.pause
        self.player.pause = new_state
        self.is_paused = new_state
        self.pause_state_changed.emit(self.is_paused)
        return self.is_paused

    def skip_current_song(self):
        self.skip_requested = True

    def go_previous(self) -> Optional[str]:
        if self.history_stack:
            self.current_query = self.history_stack.pop()
            self.back_activated = True
            self.skip_requested = True
            return self.current_query
        return None

    def set_volume(self, value: int):
        self._volume = max(0, min(100, value))
        self.player.volume = self._volume

    def set_speed(self, value: float):
        self.player.speed = value

    def toggle_shuffle(self) -> bool:
        self._shuffle = not self._shuffle
        self.shuffle_toggled.emit(self._shuffle)
        return self._shuffle

    def toggle_repeat(self) -> bool:
        self._repeat = not self._repeat
        self.repeat_toggled.emit(self._repeat)
        return self._repeat

    def play_video_id(self, video_id: str):
        self._next_video_id = video_id
        self.skip_requested = True
        self.stop_event.set()

    def update_query(self, new_query: str) -> bool:
        if new_query and new_query.strip():
            self.current_query = new_query.strip()
            self.user_updated_context = True
            self.skip_requested = True
            self.stop_event.set()
            return True
        return False

    def seek(self, position_seconds: float):
        try:
            self.player.time_pos = position_seconds
        except Exception:
            pass
