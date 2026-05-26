import os
import subprocess
import sys
from typing import List, Optional

import pyttsx3
from PySide6.QtCore import QThread, Signal

from database.models import get_session, PlaybackHistory


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
        if not self.engine:
            return False
        try:
            self.engine.say(comment)
            self.engine.runAndWait()
            return True
        except Exception:
            return False


class DJWorkerThread(QThread):
    status_changed = Signal(str)
    song_playing = Signal(str, str)
    log_message = Signal(str)
    dj_speaking = Signal(str)
    finished_signal = Signal()
    pause_state_changed = Signal(bool)

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
        self.process = None

    # ---- Thread entry point ----

    def run(self):
        _pythoncom = None
        try:
            import pythoncom as _pythoncom
            _pythoncom.CoInitialize()
        except ImportError:
            pass

        try:
            self._dj_loop()
        finally:
            if _pythoncom:
                try:
                    _pythoncom.CoUninitialize()
                except Exception:
                    pass

    # ---- Context builders ----

    def _build_local_history_context(self) -> str:
        session = get_session()
        try:
            recent = (
                session.query(PlaybackHistory)
                .order_by(PlaybackHistory.played_at.desc())
                .limit(5)
                .all()
            )
            if not recent:
                return ""
            lines = []
            for entry in recent:
                name = entry.artist_name or "Unknown"
                lines.append(f"- {entry.track_title} by {name}")
            return "\n".join(lines)
        except Exception:
            return ""
        finally:
            session.close()

    def _build_combined_context(self) -> str:
        parts = []

        local = self._build_local_history_context()
        if local:
            parts.append("Últimas canciones reproducidas localmente:")
            parts.append(local)
            parts.append("")

        yt = self.music_service.get_recent_history()
        if yt:
            parts.append("Historial de YouTube Music:")
            parts.append(yt)

        return "\n".join(parts).strip()

    # ---- Voice helper ----

    def _speak(self, voice_engine: VoiceEngine, text: str):
        if sys.platform == "win32":
            try:
                import pythoncom
                pythoncom.CoInitialize()
                voice_engine.speak_comment(text)
            finally:
                pythoncom.CoUninitialize()
        else:
            voice_engine.speak_comment(text)

    # ---- mpv playback ----

    def _play_with_mpv(self, stream_url: str):
        user_home = os.path.expanduser("~")
        scoop_mpv_path = os.path.join(user_home, "scoop", "apps", "mpv", "current", "mpv.exe")
        if os.path.exists(scoop_mpv_path):
            mpv_cmd = scoop_mpv_path
        else:
            shim_path = os.path.join(user_home, "scoop", "shims", "mpv.exe")
            mpv_cmd = shim_path if os.path.exists(shim_path) else "mpv"

        try:
            self.process = subprocess.Popen(
                [mpv_cmd, "--no-video", "--no-terminal", stream_url],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            self.is_paused = False
            self.pause_state_changed.emit(False)

            while self.process.poll() is None:
                if self.isInterruptionRequested():
                    self.process.kill()
                    self.process.wait()
                    return
                if self.skip_requested:
                    self.process.kill()
                    self.process.wait()
                    break
                self.msleep(500)

            self.process = None
        except FileNotFoundError:
            self.log_message.emit("mpv executable not found.")
            self.process = None

    # ---- Main loop ----

    def _dj_loop(self):
        voice_engine = VoiceEngine()

        while True:
            if self.isInterruptionRequested():
                break

            combined_context = self._build_combined_context()
            self.log_message.emit(f"--- Context -> '{self.current_query}' ---")
            self.status_changed.emit("Consulting the DJ AI...")

            llm_result = self.llm_service.get_llm_response(
                self.current_query, user_history=combined_context
            )

            if llm_result:
                dj_comment = llm_result.get(
                    "comentario_dj",
                    f"Seguimos con el ritmo. Ahora viene algo de {self.current_query}.",
                )
                next_song_query = llm_result.get("siguiente_cancion", self.current_query)
                llm_title = llm_result.get("siguiente_cancion")
                llm_artist = llm_result.get("artista")
            else:
                dj_comment = "Sintonizando la mejor musica en control local. Disfruta el siguiente tema."
                next_song_query = self.current_query
                llm_title = None
                llm_artist = None

            self.dj_speaking.emit(dj_comment)
            self.status_changed.emit("DJ speaking...")
            self._speak(voice_engine, dj_comment)

            self.status_changed.emit("Searching for the next track...")
            stream_data = self.music_service.search_and_extract(next_song_query)

            if stream_data:
                display_title = stream_data.get("title") or (llm_title or next_song_query)
                display_artist = stream_data.get("artist") or (llm_artist or "Unknown Artist")

                self.song_playing.emit(display_title, display_artist)
                self.status_changed.emit(f"Now Playing: {display_title} - {display_artist}")
                self.log_message.emit(f"Now playing: {display_title} - {display_artist}")

                self.music_service.record_playback(display_title, display_artist)
                self._play_with_mpv(stream_data["stream_url"])

                self.log_message.emit("Song finished. Moving to next turn...")
            else:
                self.log_message.emit(
                    f"No song found for query '{next_song_query}'. Retrying..."
                )
                self.msleep(3000)

            if not self.history_stack or self.history_stack[-1] != self.current_query:
                self.history_stack.append(self.current_query)
            if len(self.history_stack) > 100:
                self.history_stack = self.history_stack[-100:]

            if self.back_activated:
                self.back_activated = False
            elif self.user_updated_context:
                self.user_updated_context = False
            else:
                self.current_query = next_song_query

        self.status_changed.emit("DJ Session Complete!")
        self.log_message.emit("The DJ set has ended. Start a new session!")
        self.is_paused = False
        self.pause_state_changed.emit(False)
        self.finished_signal.emit()

    # ---- External controls ----

    def toggle_pause_process(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.stdin.write("p\r\n")
                self.process.stdin.flush()
                self.is_paused = not self.is_paused
                self.pause_state_changed.emit(self.is_paused)
                return self.is_paused
            except Exception as e:
                self.log_message.emit(f"[PAUSE ERROR] Could not communicate with mpv: {e}")
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

    def update_query(self, new_query: str) -> bool:
        if new_query and new_query.strip():
            self.current_query = new_query.strip()
            self.user_updated_context = True
            return True
        return False
