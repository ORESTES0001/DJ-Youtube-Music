import os
import json
import subprocess
import yt_dlp
import ytmusicapi
import time
import requests
import pyttsx3
from typing import Dict, Any, Optional, List

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QTextCursor

# --- Configuration ---
LOCAL_LLM_ENDPOINT = "http://192.168.1.28:1234/v1/chat/completions"
SYSTEM_PROMPT = """Eres "Onda", un DJ virtual experto en curaduría musical. Tu objetivo es crear transiciones perfectas.
REGLAS:
1. Tu respuesta DEBE ser estrictamente un objeto JSON válido.
2. Formato esperado: {"comentario_dj": "...", "siguiente_cancion": "...", "artista": "...", "termino_busqueda_yt": "..."}"""


class LocalLLMClient:
    """Manages connection and interaction with the local LLM endpoint (LM Studio API Compatible)."""
    def __init__(self, endpoint: str = "http://192.168.1.28:1234/v1/chat/completions"):
        self.endpoint = endpoint

    def get_llm_response(self, prompt: str, user_history: str = "") -> Optional[Dict[str, Any]]:
        user_content = (
            f"<system>\n{SYSTEM_PROMPT}\n"
            f"PERFIL DE GUSTOS REALES DEL USUARIO:\n{user_history}\n</system>\n\n"
            f"<user>\nCONTEXTO ACTUAL: El usuario quiere escuchar música relacionada con: '{prompt}'.\n"
            f"Genera tu respuesta estrictamente en el formato JSON solicitado. No agregues texto introductorio ni conclusiones.</user>"
        )

        payload = {
            "model": "local-model",
            "messages": [
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.2,
            "max_tokens": 300,
            "stream": False
        }

        try:
            response = requests.post(self.endpoint, json=payload, timeout=30)
            response.raise_for_status()
            choices = response.json().get("choices", [])
            if not choices:
                return None
            raw_json = choices[0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            print(f"[LLM ERROR] Connection failed: {e}")
            return None

        raw_json = raw_json.strip()
        if raw_json.startswith("```"):
            try:
                if "json" in raw_json:
                    raw_json = raw_json.split("json", 1)[1]
                raw_json = raw_json.strip("`").strip()
            except Exception:
                pass

        try:
            return json.loads(raw_json)
        except json.JSONDecodeError:
            return {
                "comentario_dj": f"¡Alineando frecuencias musicales! Directo a la cabina con algo de {prompt}.",
                "siguiente_cancion": f"{prompt} hit",
                "artista": "Various Artists",
                "termino_busqueda_yt": f"{prompt}"
            }


class YTMusicController:
    """Handles interaction with YouTube Music for song search and management."""
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        auth_path = os.path.join(base_dir, "browser.json")

        if not os.path.exists(auth_path):
            user_home = os.path.expanduser("~")
            auth_path = os.path.join(user_home, "browser.json")

        if os.path.exists(auth_path):
            try:
                self.api = ytmusicapi.YTMusic(auth_path)
            except Exception:
                self.Central = None
                self.api = ytmusicapi.YTMusic()
        else:
            self.api = ytmusicapi.YTMusic()

    def get_recent_history(self, limit: int = 10) -> str:
        if not getattr(self.api, 'auth', None):
            return ""
        try:
            history_items = self.api.get_history()
            if not history_items or not isinstance(history_items, list):
                return ""
            recent_items = history_items[:limit]
            history_list = []
            for item in recent_items:
                try:
                    title = item.get('title', 'Unknown Title')
                    artists = item.get('artists', [])
                    artist_name = artists[0].get('name', 'Unknown Artist') if artists else 'Unknown Artist'
                    history_list.append(f"{title} by {artist_name}")
                except Exception:
                    continue
            return "\n".join(history_list)
        except Exception:
            return ""

    def search_song_id(self, keyword: str) -> Optional[str]:
        try:
            results = self.api.search(query=keyword, limit=3, filter="songs")
            if results and len(results) > 0:
                video_id = results[0].get('videoId')
                if video_id:
                    return video_id
            return None
        except Exception:
            return None


class VoiceEngine:
    """Handles text-to-speech generation and playback on Windows."""
    def __init__(self):
        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty('voices')
            if voices:
                self.engine.setProperty('voice', voices[0].id)
        except Exception:
            self.engine = None

    def speak_comment(self, comment: str):
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

    def __init__(self, initial_query: str, parent=None):
        super().__init__(parent)
        self.initial_query = initial_query
        self.current_query = initial_query
        self.is_paused = False
        self.skip_requested = False
        self.back_activated = False
        self.history_stack: List[str] = []
        self.process = None

    def run(self):
        llm_client = LocalLLMClient(LOCAL_LLM_ENDPOINT)
        yt_controller = YTMusicController()
        voice_engine = VoiceEngine()

        user_history = yt_controller.get_recent_history()
        if not user_history or not user_history.strip():
            user_history = "Generic preference for good music flow."
            self.log_message.emit("💡 Continuing with a balanced general context profile.")
        else:
            self.log_message.emit(f"🧠 Loaded {len(user_history.splitlines())} tracks of listening history.")

        max_turns = 5

        for turn in range(1, max_turns + 1):
            if turn > 1:
                self.history_stack.append(self.current_query)

            self.log_message.emit(f"--- Turn {turn}: Context Seed -> '{self.current_query}' ---")

            self.status_changed.emit("🤔 Consulting the DJ AI...")
            llm_result = llm_client.get_llm_response(self.current_query, user_history=user_history)

            if llm_result:
                dj_comment = llm_result.get('comentario_dj', f"¡Seguimos con el ritmo! Ahora viene algo de {self.current_query}.")
                next_song_query = llm_result.get('siguiente_cancion', self.current_query)
                song_title = llm_result.get('siguiente_cancion', 'Unknown')
                artist = llm_result.get('artista', 'Unknown Artist')
            else:
                dj_comment = f"Sintonizando la mejor música en control local. ¡Disfruta el siguiente tema!"
                next_song_query = f"{self.initial_query} éxitos" if turn == 1 else f"{self.initial_query} lo mejor"
                song_title = next_song_query
                artist = "Various Artists"

            self.dj_speaking.emit(dj_comment)
            self.status_changed.emit("🎙️ DJ speaking...")
            voice_engine.speak_comment(dj_comment)

            self.status_changed.emit("🔍 Searching for the next track...")
            next_song_id = yt_controller.search_song_id(next_song_query)

            if next_song_id:
                youtube_url = f"https://www.youtube.com/watch?v={next_song_id}"
                try:
                    ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'no_warnings': True}
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info_dict = ydl.extract_info(youtube_url, download=False)
                        direct_audio_stream_url = info_dict.get('url')
                except Exception as e:
                    self.log_message.emit(f"⚠️ [STREAM ERROR] {e}")
                    direct_audio_stream_url = None

                if direct_audio_stream_url:
                    self.song_playing.emit(song_title, artist)
                    self.status_changed.emit(f"▶️ Playing: {song_title} - {artist}")
                    self.log_message.emit(f"🎵 Now playing: {song_title} - {artist}")

                    user_home = os.path.expanduser("~")
                    scoop_mpv_path = os.path.join(user_home, "scoop", "apps", "mpv", "current", "mpv.exe")
                    if os.path.exists(scoop_mpv_path):
                        mpv_cmd = scoop_mpv_path
                    else:
                        shim_path = os.path.join(user_home, "scoop", "shims", "mpv.exe")
                        mpv_cmd = shim_path if os.path.exists(shim_path) else 'mpv'

                    try:
                        self.process = subprocess.Popen(
                            [mpv_cmd, '--no-video', '--no-terminal', direct_audio_stream_url],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL,
                            text=True
                        )
                        self.is_paused = False

                        while self.process.poll() is None:
                            if self.skip_requested:
                                self.process.kill()
                                self.process.wait()
                                break
                            self.msleep(500)

                        self.process = None
                        self.log_message.emit("✅ Song finished. Moving to next turn...")
                    except FileNotFoundError:
                        self.log_message.emit("⚠️ mpv executable not found.")
                else:
                    self.log_message.emit("⚠️ Could not extract audio stream URL.")
            else:
                next_song_query = f"music related to {self.current_query}"
                self.log_message.emit(f"⚠️ No song found. Trying '{next_song_query}'...")

            if self.back_activated:
                self.back_activated = False
                self.skip_requested = False
            else:
                self.skip_requested = False
                self.current_query = next_song_query

        self.status_changed.emit("✅ DJ Session Complete!")
        self.log_message.emit("🎧 The DJ set has ended. Start a new session!")
        self.is_paused = False
        self.pause_state_changed.emit(False)
        self.finished_signal.emit()

    def toggle_pause_process(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.stdin.write("p\n")
                self.process.stdin.flush()
                self.is_paused = not self.is_paused
                self.pause_state_changed.emit(self.is_paused)
                return self.is_paused
            except Exception as e:
                self.log_message.emit(f"⚠️ [PAUSE ERROR] Could not communicate with mpv: {e}")
        return self.is_paused

    def skip_current_song(self):
        self.skip_requested = True

    def go_previous(self):
        if self.history_stack:
            self.current_query = self.history_stack.pop()
            self.back_activated = True
            self.skip_requested = True
            return self.current_query
        return None

    def update_query(self, new_query: str) -> bool:
        if new_query and new_query.strip():
            self.current_query = new_query.strip()
            return True
        return False


class DJMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Onda DJ — Virtual Music Curator")
        self.setMinimumSize(800, 600)
        self.setStyleSheet(self._load_stylesheet())

        self.worker_thread = None
        self._setup_ui()
        self._set_controls_enabled(False)

    def _load_stylesheet(self):
        return """
            QMainWindow, QWidget#centralWidget {
                background-color: #121212;
            }
            QLabel#headerLabel {
                font-size: 32px;
                font-weight: bold;
                color: #1DB954;
            }
            QLabel#subtitleLabel {
                font-size: 14px;
                color: #B3B3B3;
            }
            QFrame#statusFrame {
                background-color: #181818;
                border: 1px solid #282828;
                border-radius: 12px;
                padding: 10px;
            }
            QLabel#statusHeader {
                font-size: 16px;
                font-weight: bold;
                color: #FFFFFF;
            }
            QLabel#statusLabel {
                font-size: 18px;
                color: #1DB954;
                padding: 8px 0px;
            }
            QLabel#nowPlayingLabel {
                font-size: 14px;
                color: #B3B3B3;
            }
            QLabel#logHeader {
                font-size: 16px;
                font-weight: bold;
                color: #FFFFFF;
            }
            QLineEdit {
                background-color: #282828;
                color: #FFFFFF;
                border: 2px solid #535353;
                border-radius: 22px;
                padding: 10px 22px;
                font-size: 14px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #1DB954;
            }
            QLineEdit::placeholder {
                color: #727272;
            }
            QPushButton {
                color: #FFFFFF;
                border: none;
                border-radius: 22px;
                padding: 10px 32px;
                font-size: 14px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton#startBtn {
                background-color: #1DB954;
            }
            QPushButton#startBtn:hover {
                background-color: #1ed760;
            }
            QPushButton#startBtn:pressed {
                background-color: #169c46;
            }
            QPushButton#startBtn:disabled {
                background-color: #535353;
                color: #727272;
            }
            QPushButton#ctrlBtn {
                background-color: #2a2a2a;
                border: 1px solid #535353;
                border-radius: 22px;
                padding: 10px 20px;
                min-width: 80px;
            }
            QPushButton#ctrlBtn:hover {
                background-color: #3a3a3a;
                border-color: #1DB954;
            }
            QPushButton#ctrlBtn:pressed {
                background-color: #1DB954;
                border-color: #1DB954;
            }
            QPushButton#ctrlBtn:disabled {
                background-color: #181818;
                color: #535353;
                border-color: #282828;
            }
            QTextEdit {
                background-color: #181818;
                color: #B3B3B3;
                border: 1px solid #282828;
                border-radius: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                padding: 8px;
            }
            QScrollBar:vertical {
                background-color: #181818;
                width: 10px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #535353;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #727272;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """

    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(18)

        # Header
        header = QLabel("🎧  ONDA DJ")
        header.setObjectName("headerLabel")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        subtitle = QLabel("Virtual Music Curator")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # Input row
        input_layout = QHBoxLayout()
        input_layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter an artist, mood, or song... (e.g., Juanes, Lo-fi, Rock)")
        self.search_input.returnPressed.connect(self._toggle_session)

        self.start_btn = QPushButton("▶  Start Session")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self._toggle_session)

        input_layout.addWidget(self.search_input, stretch=1)
        input_layout.addWidget(self.start_btn)
        layout.addLayout(input_layout)

        # Status frame
        status_frame = QFrame()
        status_frame.setObjectName("statusFrame")
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(18, 14, 18, 14)
        status_layout.setSpacing(6)

        status_header = QLabel("DJ Booth Status")
        status_header.setObjectName("statusHeader")
        status_layout.addWidget(status_header)

        self.status_label = QLabel("💡 Ready — enter a query to start")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)

        self.now_playing_label = QLabel("")
        self.now_playing_label.setObjectName("nowPlayingLabel")
        status_layout.addWidget(self.now_playing_label)

        # Playback controls
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(10)

        self.back_btn = QPushButton("⏮  Back")
        self.back_btn.setObjectName("ctrlBtn")
        self.back_btn.clicked.connect(self._back)

        self.pause_btn = QPushButton("⏸  Pause")
        self.pause_btn.setObjectName("ctrlBtn")
        self.pause_btn.clicked.connect(self._toggle_pause)

        self.next_btn = QPushButton("⏭  Next")
        self.next_btn.setObjectName("ctrlBtn")
        self.next_btn.clicked.connect(self._next)

        ctrl_layout.addWidget(self.back_btn)
        ctrl_layout.addWidget(self.pause_btn)
        ctrl_layout.addWidget(self.next_btn)

        status_layout.addLayout(ctrl_layout)
        layout.addWidget(status_frame)

        # Log section
        log_header = QLabel("Session Log")
        log_header.setObjectName("logHeader")
        layout.addWidget(log_header)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMinimumHeight(200)
        layout.addWidget(self.log_area, stretch=1)

    def _set_controls_enabled(self, enabled: bool):
        self.back_btn.setEnabled(enabled)
        self.pause_btn.setEnabled(enabled)
        self.next_btn.setEnabled(enabled)

    @Slot()
    def _toggle_session(self):
        query = self.search_input.text().strip()
        if not query:
            query = "lo-fi programming music"

        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.update_query(query)
            self.log_area.append(f"✎ Context updated to: '{query}'")
            self.status_label.setText(f"✎ Context updated to '{query}' — will apply on next transition")
        else:
            self.start_btn.setText("✎  Update Context")
            self.log_area.clear()
            self.status_label.setText("🚀 Launching DJ session...")
            self.now_playing_label.setText("")
            self._set_controls_enabled(True)
            self.pause_btn.setText("⏸  Pause")

            self.worker_thread = DJWorkerThread(query)
            self.worker_thread.status_changed.connect(self._on_status_changed)
            self.worker_thread.song_playing.connect(self._on_song_playing)
            self.worker_thread.log_message.connect(self._on_log_message)
            self.worker_thread.dj_speaking.connect(self._on_dj_speaking)
            self.worker_thread.finished_signal.connect(self._on_session_finished)
            self.worker_thread.pause_state_changed.connect(self._on_pause_state_changed)
            self.worker_thread.start()

    @Slot(str)
    def _on_status_changed(self, status):
        self.status_label.setText(status)

    @Slot(str, str)
    def _on_song_playing(self, title, artist):
        self.now_playing_label.setText(f"🎵 Now Playing: {title} — {artist}")

    @Slot(str)
    def _on_log_message(self, msg):
        self.log_area.append(msg)
        cursor = self.log_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_area.setTextCursor(cursor)

    @Slot(str)
    def _on_dj_speaking(self, comment):
        self.log_area.append(f'🎙️ DJ: "{comment}"')
        cursor = self.log_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_area.setTextCursor(cursor)

    @Slot(bool)
    def _on_pause_state_changed(self, paused):
        self.pause_btn.setText("▶  Play" if paused else "⏸  Pause")

    @Slot()
    def _on_session_finished(self):
        self.start_btn.setText("▶  Start Session")
        self._set_controls_enabled(False)
        self.pause_btn.setText("⏸  Pause")

    @Slot()
    def _back(self):
        if self.worker_thread and self.worker_thread.isRunning():
            result = self.worker_thread.go_previous()
            if result:
                self.log_area.append(f"⏮ Going back to context: '{result}'")
                self.status_label.setText(f"⏮ Returning to previous context...")
            else:
                self.log_area.append("⏮ No previous context available")

    @Slot()
    def _toggle_pause(self):
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.toggle_pause_process()

    @Slot()
    def _next(self):
        if self.worker_thread and self.worker_thread.isRunning():
            self.log_area.append("⏭ Skipping to next song...")
            self.status_label.setText("⏭ Skipping current track...")
            self.worker_thread.skip_current_song()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = DJMainWindow()
    window.show()
    sys.exit(app.exec())
