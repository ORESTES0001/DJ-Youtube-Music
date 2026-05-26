import os
import json
import subprocess
import sys
import yt_dlp
import ytmusicapi
import requests
import pyttsx3
from typing import Dict, Any, Optional, List

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QKeyEvent, QFont

# ---- Configuration ----
LOCAL_LLM_ENDPOINT = "http://192.168.1.28:1234/v1/chat/completions"
SYSTEM_PROMPT = """Eres "Onda", un DJ virtual experto en curaduría musical. Tu objetivo es crear transiciones perfectas.
REGLAS:
1. Tu respuesta DEBE ser estrictamente un objeto JSON válido.
2. Formato esperado: {"comentario_dj": "...", "siguiente_cancion": "...", "artista": "...", "termino_busqueda_yt": "..."}"""


class LocalLLMClient:
    def __init__(self, endpoint: str = LOCAL_LLM_ENDPOINT):
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
            "messages": [{"role": "user", "content": user_content}],
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

        # Strip markdown code fences
        if raw_json.startswith("```"):
            lines = raw_json.split("\n")
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            raw_json = "\n".join(lines).strip()

        # Find outermost JSON object boundaries
        if "{" in raw_json:
            start = raw_json.find("{")
            end = raw_json.rfind("}")
            if end >= start:
                raw_json = raw_json[start:end + 1]

        if not raw_json.startswith("{"):
            return None

        try:
            return json.loads(raw_json)
        except json.JSONDecodeError:
            return None


class YTMusicController:
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
                self.api = ytmusicapi.YTMusic()
        else:
            self.api = ytmusicapi.YTMusic()

    def get_recent_history(self, limit: int = 10) -> str:
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
    def __init__(self):
        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty('voices')
            if voices:
                self.engine.setProperty('voice', voices[0].id)
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

    def __init__(self, initial_query: str, parent=None):
        super().__init__(parent)
        self.initial_query = initial_query
        self.current_query = initial_query
        self.is_paused = False
        self.skip_requested = False
        self.back_activated = False
        self.user_updated_context = False
        self.history_stack: List[str] = []
        self.process = None

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

    def _dj_loop(self):
        llm_client = LocalLLMClient(LOCAL_LLM_ENDPOINT)
        yt_controller = YTMusicController()
        voice_engine = VoiceEngine()

        user_history = yt_controller.get_recent_history()
        if not user_history or not user_history.strip():
            user_history = "Generic preference for good music flow."
            self.log_message.emit("Continuing with a balanced general context profile.")
        else:
            self.log_message.emit(f"Loaded {len(user_history.splitlines())} tracks of listening history.")

        while True:
            if self.isInterruptionRequested():
                break

            self.log_message.emit(f"--- Context -> '{self.current_query}' ---")
            self.status_changed.emit("Consulting the DJ AI...")

            llm_result = llm_client.get_llm_response(self.current_query, user_history=user_history)

            if llm_result:
                dj_comment = llm_result.get('comentario_dj', f"Seguimos con el ritmo. Ahora viene algo de {self.current_query}.")
                next_song_query = llm_result.get('siguiente_cancion', self.current_query)
                llm_title = llm_result.get('siguiente_cancion')
                llm_artist = llm_result.get('artista')
            else:
                dj_comment = "Sintonizando la mejor musica en control local. Disfruta el siguiente tema."
                next_song_query = self.current_query
                llm_title = None
                llm_artist = None

            self.dj_speaking.emit(dj_comment)
            self.status_changed.emit("DJ speaking...")

            # Voice synthesis with per-call COM init on Windows
            if sys.platform == "win32":
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                    voice_engine.speak_comment(dj_comment)
                finally:
                    pythoncom.CoUninitialize()
            else:
                voice_engine.speak_comment(dj_comment)

            self.status_changed.emit("Searching for the next track...")
            next_song_id = yt_controller.search_song_id(next_song_query)

            display_title = next_song_query
            display_artist = "Unknown Artist"

            if next_song_id:
                youtube_url = f"https://www.youtube.com/watch?v={next_song_id}"
                direct_audio_stream_url = None
                try:
                    ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'no_warnings': True}
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info_dict = ydl.extract_info(youtube_url, download=False)
                        direct_audio_stream_url = info_dict.get('url')

                    meta_title = info_dict.get('title', '').strip()
                    meta_artist = (
                        info_dict.get('artist')
                        or info_dict.get('channel')
                        or info_dict.get('uploader')
                        or ''
                    )

                    display_title = meta_title or (llm_title or next_song_query)
                    display_artist = meta_artist or (llm_artist or 'Unknown Artist')

                except Exception as e:
                    self.log_message.emit(f"[STREAM ERROR] {e}")

                if direct_audio_stream_url:
                    self.song_playing.emit(display_title, display_artist)
                    self.status_changed.emit(f"Now Playing: {display_title} - {display_artist}")
                    self.log_message.emit(f"Now playing: {display_title} - {display_artist}")

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
                        self.log_message.emit("Song finished. Moving to next turn...")
                    except FileNotFoundError:
                        self.log_message.emit("mpv executable not found.")
                else:
                    self.log_message.emit("Could not extract audio stream URL.")
            else:
                self.log_message.emit(f"No song found for query '{next_song_query}'. Retrying...")
                self.msleep(3000)

            # Push current context to history before updating
            if not self.history_stack or self.history_stack[-1] != self.current_query:
                self.history_stack.append(self.current_query)
            if len(self.history_stack) > 100:
                self.history_stack = self.history_stack[-100:]

            # Determine next query
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
            self.user_updated_context = True
            return True
        return False


class DJMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ONDA DJ — Virtual Music Curator")
        self.setMinimumSize(960, 680)
        self.setStyleSheet(self._load_stylesheet())

        self.worker_thread = None
        self._setup_ui()
        self._set_controls_enabled(False)

    # ---- QSS (Vibe Velocity Theme) ----
    @staticmethod
    def _load_stylesheet():
        return """
            QMainWindow, QWidget#centralWidget {
                background-color: #131318;
            }

            /* ---- Header ---- */
            QLabel#brandLabel {
                font-size: 24px;
                font-weight: 700;
                color: #b4c5ff;
                font-family: 'Montserrat', 'Segoe UI', sans-serif;
                letter-spacing: -0.01em;
            }
            QLabel#navLink {
                font-size: 14px;
                font-weight: 600;
                color: #c5c6d2;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                padding: 6px 14px;
            }
            QLabel#navLink:hover {
                color: #b4c5ff;
            }

            /* ---- Cards ---- */
            QFrame#cardFrame {
                background-color: #1b1b20;
                border: 1px solid #444650;
                border-radius: 12px;
            }

            /* ---- Section Headers ---- */
            QLabel#sectionHeader {
                font-size: 13px;
                font-weight: 700;
                color: #c5c6d2;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                letter-spacing: 0.05em;
                text-transform: uppercase;
            }

            /* ---- Input Fields ---- */
            QLineEdit {
                background-color: #1f1f24;
                color: #e4e1e8;
                border: 1px solid #444650;
                border-radius: 22px;
                padding: 11px 22px;
                font-size: 14px;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                min-height: 20px;
                selection-background-color: #5f74b7;
                selection-color: #131318;
            }
            QLineEdit:focus {
                border-color: #b4c5ff;
                background-color: #29292f;
            }
            QLineEdit::placeholder {
                color: #8f909b;
            }

            /* ---- Buttons ---- */
            QPushButton {
                border: none;
                border-radius: 22px;
                padding: 11px 32px;
                font-size: 14px;
                font-weight: 700;
                min-height: 20px;
                font-family: 'Montserrat', 'Segoe UI', sans-serif;
            }
            QPushButton#updateBtn {
                background-color: #5f74b7;
                color: #ffffff;
            }
            QPushButton#updateBtn:hover {
                background-color: #6d82c9;
            }
            QPushButton#updateBtn:pressed {
                background-color: #465b9d;
            }
            QPushButton#updateBtn:disabled {
                background-color: #343439;
                color: #6f7692;
            }

            QPushButton#ctrlBtn {
                background-color: transparent;
                color: #c5c6d2;
                border: 1px solid #8f909b;
                border-radius: 22px;
                padding: 10px 20px;
                min-width: 80px;
                font-weight: 600;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
            QPushButton#ctrlBtn:hover {
                background-color: #29292f;
                border-color: #b4c5ff;
                color: #b4c5ff;
            }
            QPushButton#ctrlBtn:disabled {
                background-color: #1b1b20;
                color: #444650;
                border-color: #343439;
            }

            /* ---- Now Playing ---- */
            QLabel#nowPlayingTitle {
                font-size: 20px;
                font-weight: 700;
                color: #b4c5ff;
                font-family: 'Montserrat', 'Segoe UI', sans-serif;
            }
            QLabel#nowPlayingArtist {
                font-size: 14px;
                color: #c5c6d2;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
            QLabel#statusLabel {
                font-size: 14px;
                color: #c5c6d2;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                padding: 2px 0px;
            }

            /* ---- Session Log ---- */
            QTextEdit {
                background-color: #0d0e12;
                color: #e4e1e8;
                border: 1px solid #444650;
                border-radius: 8px;
                font-family: 'JetBrains Mono', 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                padding: 12px;
                line-height: 1.6;
            }

            /* ---- Scrollbar ---- */
            QScrollBar:vertical {
                background-color: #0d0e12;
                width: 8px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #343439;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #444650;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """

    # ---- UI Setup ----
    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(32, 20, 32, 24)
        root.setSpacing(16)

        # ── Top Header Bar ──
        header_bar = QHBoxLayout()
        header_bar.setSpacing(8)

        brand = QLabel("ONDA DJ")
        brand.setObjectName("brandLabel")
        header_bar.addWidget(brand)

        header_bar.addStretch()

        mixes_link = QLabel("Mixes")
        mixes_link.setObjectName("navLink")
        header_bar.addWidget(mixes_link)

        lib_link = QLabel("Library")
        lib_link.setObjectName("navLink")
        header_bar.addWidget(lib_link)

        root.addLayout(header_bar)

        # ── Main Two-Column Body ──
        body = QHBoxLayout()
        body.setSpacing(24)

        # ---- Left Column (4/12) ----
        left_col = QVBoxLayout()
        left_col.setSpacing(12)

        context_card = QFrame()
        context_card.setObjectName("cardFrame")
        context_card_layout = QVBoxLayout(context_card)
        context_card_layout.setContentsMargins(18, 16, 18, 18)
        context_card_layout.setSpacing(10)

        context_header = QLabel("Context")
        context_header.setObjectName("sectionHeader")
        context_card_layout.addWidget(context_header)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Artist, mood, or song...")
        self.search_input.returnPressed.connect(self._toggle_session)
        context_card_layout.addWidget(self.search_input)

        self.start_btn = QPushButton("Start Session")
        self.start_btn.setObjectName("updateBtn")
        self.start_btn.clicked.connect(self._toggle_session)
        context_card_layout.addWidget(self.start_btn)

        left_col.addWidget(context_card)
        left_col.addStretch()

        # ---- Right Column (8/12) ----
        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        # Now Playing card
        np_card = QFrame()
        np_card.setObjectName("cardFrame")
        np_card_layout = QVBoxLayout(np_card)
        np_card_layout.setContentsMargins(18, 16, 18, 14)
        np_card_layout.setSpacing(4)

        np_header = QLabel("Now Playing")
        np_header.setObjectName("sectionHeader")
        np_card_layout.addWidget(np_header)

        self.now_playing_title = QLabel("")
        self.now_playing_title.setObjectName("nowPlayingTitle")
        np_card_layout.addWidget(self.now_playing_title)

        self.now_playing_artist = QLabel("")
        self.now_playing_artist.setObjectName("nowPlayingArtist")
        np_card_layout.addWidget(self.now_playing_artist)

        self.status_label = QLabel("Ready — enter a query to start")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        np_card_layout.addWidget(self.status_label)

        right_col.addWidget(np_card)

        # Playback Controls
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(10)

        self.back_btn = QPushButton("Back")
        self.back_btn.setObjectName("ctrlBtn")
        self.back_btn.clicked.connect(self._back)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setObjectName("ctrlBtn")
        self.pause_btn.clicked.connect(self._toggle_pause)

        self.next_btn = QPushButton("Next")
        self.next_btn.setObjectName("ctrlBtn")
        self.next_btn.clicked.connect(self._next)

        ctrl_layout.addWidget(self.back_btn)
        ctrl_layout.addWidget(self.pause_btn)
        ctrl_layout.addWidget(self.next_btn)

        right_col.addLayout(ctrl_layout)

        # Session Log
        log_header = QLabel("Session Log")
        log_header.setObjectName("sectionHeader")
        right_col.addWidget(log_header)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMinimumHeight(200)
        right_col.addWidget(self.log_area, stretch=1)

        # Assemble columns into body
        left_container = QVBoxLayout()
        left_container.addLayout(left_col)

        right_container = QVBoxLayout()
        right_container.addLayout(right_col)

        body.addLayout(left_container, stretch=4)
        body.addLayout(right_container, stretch=8)

        root.addLayout(body, stretch=1)

    # ---- Keyboard Shortcuts ----
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Space and not self.search_input.hasFocus():
            self._toggle_pause()
        elif event.key() == Qt.Key_Right:
            self._next()
        elif event.key() == Qt.Key_Left:
            self._back()
        else:
            super().keyPressEvent(event)

    # ---- Helpers ----
    def _set_controls_enabled(self, enabled: bool):
        self.back_btn.setEnabled(enabled)
        self.pause_btn.setEnabled(enabled)
        self.next_btn.setEnabled(enabled)

    def _append_log_colored(self, msg: str):
        cursor = self.log_area.textCursor()
        cursor.movePosition(QTextCursor.End)

        fmt = QTextCharFormat()
        if msg.startswith("[STREAM ERROR]") or msg.startswith("[PAUSE ERROR]"):
            fmt.setForeground(QColor("#ffb4ab"))
        elif msg.startswith("No song found") or msg.startswith("Could not extract"):
            fmt.setForeground(QColor("#fcb970"))
        elif msg.startswith("Now playing"):
            fmt.setForeground(QColor("#b4c5ff"))
            fmt.setFontWeight(QFont.Bold)
        elif msg.startswith("DJ speaking") or msg.startswith("Song finished"):
            fmt.setForeground(QColor("#b4c5ff"))
        elif msg.startswith("---"):
            fmt.setForeground(QColor("#8f909b"))
        else:
            fmt.setForeground(QColor("#c5c6d2"))

        cursor.insertText(msg + "\n", fmt)
        self.log_area.setTextCursor(cursor)

    # ---- Slots ----
    @Slot()
    def _toggle_session(self):
        query = self.search_input.text().strip()
        if not query:
            query = "lo-fi programming music"

        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.update_query(query)
            self._append_log_colored(f"Context updated to: '{query}'")
            self.status_label.setText(f"Context updated to '{query}' \u2014 will apply on next transition")
        else:
            self.start_btn.setText("Update Vibe")
            self.log_area.clear()
            self.status_label.setText("Launching DJ session...")
            self.now_playing_title.setText("")
            self.now_playing_artist.setText("")
            self._set_controls_enabled(True)
            self.pause_btn.setText("Pause")

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
        self.now_playing_title.setText(title)
        self.now_playing_artist.setText(artist)

    @Slot(str)
    def _on_log_message(self, msg):
        self._append_log_colored(msg)

    @Slot(str)
    def _on_dj_speaking(self, comment):
        cursor = self.log_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#b4c5ff"))
        cursor.insertText(f'DJ: "{comment}"\n', fmt)
        self.log_area.setTextCursor(cursor)

    @Slot(bool)
    def _on_pause_state_changed(self, paused):
        self.pause_btn.setText("Play" if paused else "Pause")

    @Slot()
    def _on_session_finished(self):
        self.start_btn.setText("Start Session")
        self._set_controls_enabled(False)
        self.pause_btn.setText("Pause")

    @Slot()
    def _back(self):
        if self.worker_thread and self.worker_thread.isRunning():
            result = self.worker_thread.go_previous()
            if result:
                self._append_log_colored(f"Returning to previous context: '{result}'")
                self.status_label.setText("Returning to previous context...")
            else:
                self._append_log_colored("No previous context available")

    @Slot()
    def _toggle_pause(self):
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.toggle_pause_process()

    @Slot()
    def _next(self):
        if self.worker_thread and self.worker_thread.isRunning():
            self._append_log_colored("Skipping to next song...")
            self.status_label.setText("Skipping current track...")
            self.worker_thread.skip_current_song()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = DJMainWindow()
    window.show()
    sys.exit(app.exec())
