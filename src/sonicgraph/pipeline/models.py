import datetime

from pydantic import BaseModel


class RawAMTrack(BaseModel):
    """Represents a track exported from Apple Music."""

    name: str
    artist: str
    album_artist: str | None
    album: str | None
    genre: str | None
    total_time: int
    track_number: int | None
    track_count: int | None
    year: int | None
    release_date: datetime.datetime | None
    date_added: datetime.datetime | None
    compilation: bool | None


class Track(BaseModel):
    """Represents a music track with metadata."""

    id: str | None = None
    title: str
    artist_ids: list[str]
    raw_artists_str: str
    album_id: str | None = None
    album_artist_ids: list[str] | None = None
    genre: str | None = None
    duration: int
    bpm: int | None = None
    track_number: int | None
    track_count: int | None
    year: int | None = None
    release_date: datetime.date | None = None
    date_added: datetime.date | None = None
    compilation: bool | None
    source: str = "apple-music"


class Artist(BaseModel):
    id: str
    name: str
    aliases: list[str] = []


class Album(BaseModel):
    id: str
    title: str
    artist_ids: list[str]
    year: int | None
    label: str | None = None
