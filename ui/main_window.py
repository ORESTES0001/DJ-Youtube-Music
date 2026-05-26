from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QFrame,
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QKeyEvent, QFont

from workers.dj_worker import DJWorkerThread


class DJMainWindow(QMainWindow):
    def __init__(self, llm_service, music_service, auth_service):
        super().__init__()
        self.llm_service = llm_service
        self.music_service = music_service
        self.auth_service = auth_service

        self.setWindowTitle("ONDA DJ \u2014 Virtual Music Curator")
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

            QFrame#cardFrame {
                background-color: #1b1b20;
                border: 1px solid #444650;
                border-radius: 12px;
            }

            QLabel#sectionHeader {
                font-size: 13px;
                font-weight: 700;
                color: #c5c6d2;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                letter-spacing: 0.05em;
                text-transform: uppercase;
            }

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

        # Header bar
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

        # Two-column body
        body = QHBoxLayout()
        body.setSpacing(24)

        # Left column (4/12)
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

        # Right column (8/12)
        right_col = QVBoxLayout()
        right_col.setSpacing(12)

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

        self.status_label = QLabel("Ready \u2014 enter a query to start")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        np_card_layout.addWidget(self.status_label)

        right_col.addWidget(np_card)

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

        log_header = QLabel("Session Log")
        log_header.setObjectName("sectionHeader")
        right_col.addWidget(log_header)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMinimumHeight(200)
        right_col.addWidget(self.log_area, stretch=1)

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
            self.status_label.setText(
                f"Context updated to '{query}' \u2014 will apply on next transition"
            )
        else:
            self.start_btn.setText("Update Vibe")
            self.log_area.clear()
            self.status_label.setText("Launching DJ session...")
            self.now_playing_title.setText("")
            self.now_playing_artist.setText("")
            self._set_controls_enabled(True)
            self.pause_btn.setText("Pause")

            self.worker_thread = DJWorkerThread(
                query,
                llm_service=self.llm_service,
                music_service=self.music_service,
            )
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
