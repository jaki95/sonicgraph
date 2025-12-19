import hashlib
import json
import re
from functools import lru_cache

from sonicgraph import DATA_FOLDER
from sonicgraph.library.models import Album, Artist, Track


def make_id(prefix: str, *values: str) -> str:
    """Generate a stable hash-based ID from prefix and values."""
    raw = f"{prefix}:" + "|".join(v.lower().strip() for v in values if v)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def make_artist_id(artist_name: str) -> str:
    """Generate a unique ID for an artist."""
    return make_id("artist", artist_name)


def make_album_id(album_name: str, artist_id: str) -> str:
    """Generate a unique ID for an album."""
    return make_id("album", album_name, artist_id)


def make_track_id(
    track_name: str, album_id: str, artist_id: str, track_number: str
) -> str:
    """Generate a unique ID for a track."""
    return make_id("track", track_name, album_id, artist_id, track_number)


VARIOUS_ARTISTS_ID = make_artist_id("Various Artists")


@lru_cache(maxsize=None)
def get_artist_id(name: str) -> str:
    return make_artist_id(name)


def get_or_create_artist(artists: dict[str, Artist], name: str) -> str:
    aid = get_artist_id(name)
    if aid not in artists:
        artists[aid] = Artist(id=aid, name=name)
    return aid


def canonicalise_track_title(title: str) -> str:
    title = title.lower().strip()
    title = re.sub(r"\s+", " ", title)
    title = re.sub(r"\(.*?\)", "", title)
    return title


def track_fingerprint(
    title: str,
    album_id: str | None,
    duration: int | None,
    track_number: int | None,
) -> tuple:
    return (
        canonicalise_track_title(title),
        album_id,
        round(duration or 0, -2),
        track_number,
    )


def export_library_data(
    artists: dict[str, Artist],
    albums: dict[str, Album],
    tracks: dict[str, Track],
) -> None:
    """Export processed library data to JSON file."""
    output_path = DATA_FOLDER / "am_library_imported.json"
    with open(output_path, "w") as f:
        json.dump(
            {
                "artists": artists,
                "albums": albums,
                "tracks": tracks,
            },
            f,
            indent=2,
            default=str,
        )
