#!/usr/bin/env python3
"""ONDA DJ — Virtual Music Curator

Entry point that initialises the database, wires up service layers,
and launches the PySide6 desktop application.
"""

import sys

from PySide6.QtWidgets import QApplication

from database.models import init_db
from services.auth_service import GoogleAuthService
from services.llm_service import LocalLLMClient
from services.music_service import YTMusicStreamer
from ui.main_window import DJMainWindow


def main():
    init_db()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    auth_service = GoogleAuthService()
    llm_service = LocalLLMClient()
    music_service = YTMusicStreamer(auth_service=auth_service)

    window = DJMainWindow(
        llm_service=llm_service,
        music_service=music_service,
        auth_service=auth_service,
    )
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
