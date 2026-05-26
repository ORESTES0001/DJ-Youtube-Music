from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, DateTime, Text, ForeignKey, create_engine
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    google_id = Column(String(255), unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    display_name = Column(String(255), nullable=True)

    playlists = relationship("Playlist", back_populates="user")
    playback_history = relationship("PlaybackHistory", back_populates="user")


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="playlists")
    tracks = relationship("Track", back_populates="playlist", cascade="all, delete-orphan")


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"), nullable=False)
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=True)
    youtube_id = Column(String(255), nullable=True)
    duration = Column(Integer, nullable=True)

    playlist = relationship("Playlist", back_populates="tracks")


class PlaybackHistory(Base):
    __tablename__ = "playback_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    track_title = Column(String(255), nullable=False)
    artist_name = Column(String(255), nullable=True)
    played_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="playback_history")


# ---- Session management ----

_SessionFactory = None


def init_db(db_path: str = "sqlite:///onda_dj.db") -> None:
    global _SessionFactory
    engine = create_engine(db_path, echo=False)
    Base.metadata.create_all(engine)
    _SessionFactory = sessionmaker(bind=engine)


def get_session():
    if _SessionFactory is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _SessionFactory()
