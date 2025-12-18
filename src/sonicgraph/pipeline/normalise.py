import hashlib
import json
import re
from functools import lru_cache

import pandas as pd

from sonicgraph import DATA_FOLDER
from sonicgraph.pipeline.am import (
    LIBRARY_PATH,
    extract_raw_tracks,
    load_apple_music_library,
)
from sonicgraph.pipeline.models import Album, Artist, RawAMTrack, Track
from sonicgraph.pipeline.parse import parse_artists


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


@lru_cache(maxsize=None)
def get_artist_id(name: str) -> str:
    return make_artist_id(name)


VARIOUS_ARTISTS_ID = make_artist_id("Various Artists")


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


def normalise_tracks(
    raw_tracks: list[RawAMTrack],
) -> tuple[list[Artist], list[Album], list[Track]]:
    """
    Process raw Apple Music tracks into normalized Artist, Album, and Track objects.

    Creates unique entities for each artist and album, linking tracks to their
    respective artists and albums through IDs.
    """
    artists: dict[str, Artist] = {}
    albums: dict[str, Album] = {}
    tracks: dict[str, Track] = {}

    seen_tracks: dict[tuple, str] = {}

    for rt in raw_tracks:
        track_artist_names = parse_artists(rt.artist, rt.name)
        if not track_artist_names:
            continue

        track_artist_ids = [
            get_or_create_artist(artists, name) for name in track_artist_names
        ]

        # Album artists
        album_artist_ids: list[str] = []
        if rt.album_artist:
            for name in parse_artists(rt.album_artist, ""):
                album_artist_ids.append(get_or_create_artist(artists, name))

        # Fallback artist
        if not track_artist_ids:
            unknown_id = get_or_create_artist(artists, "Unknown Artist")
            track_artist_ids = [unknown_id]

        if rt.compilation:
            primary_album_artist_id = VARIOUS_ARTISTS_ID
            artists.setdefault(
                VARIOUS_ARTISTS_ID,
                Artist(
                    id=VARIOUS_ARTISTS_ID,
                    name="Various Artists",
                ),
            )
        else:
            primary_album_artist_id = (
                album_artist_ids[0] if album_artist_ids else track_artist_ids[0]
            )

        album_id = None
        if rt.album:
            album_id = make_album_id(rt.album, primary_album_artist_id)
            if album_id not in albums:
                albums[album_id] = Album(
                    id=album_id,
                    title=rt.album,
                    artist_ids=album_artist_ids or track_artist_ids,
                    year=rt.year,
                    is_compilation=bool(rt.compilation),
                )

        track_id = make_track_id(
            rt.name,
            album_id or "",
            primary_album_artist_id,
            str(rt.track_number or ""),
        )

        fingerprint = track_fingerprint(
            rt.name,
            album_id,
            rt.total_time,
            rt.track_number,
        )

        if fingerprint in seen_tracks:
            continue

        seen_tracks[fingerprint] = track_id

        if track_id not in tracks:
            tracks[track_id] = Track(
                id=track_id,
                title=rt.name,
                raw_artists_str=rt.artist,
                artist_ids=track_artist_ids,
                album_artist_ids=album_artist_ids,
                album_id=album_id,
                duration=rt.total_time,
                track_number=rt.track_number,
                track_count=rt.track_count,
                release_date=rt.release_date.date() if rt.release_date else None,
                date_added=rt.date_added.date() if rt.date_added else None,
                genre=rt.genre,
                year=rt.year,
                compilation=rt.compilation,
            )

    # Export to JSON for debugging/inspection
    _export_library_data(artists, albums, tracks)

    return (
        list(artists.values()),
        list(albums.values()),
        list(tracks.values()),
    )


def _export_library_data(
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


def main() -> None:
    """Load and process Apple Music library, print summary statistics."""
    # Load and process library
    lib = load_apple_music_library(LIBRARY_PATH)
    raw_tracks = extract_raw_tracks(lib)
    artists, albums, tracks = normalise_tracks(raw_tracks)

    artists_df = pd.DataFrame(artists)
    albums_df = pd.DataFrame(albums)
    tracks_df = pd.DataFrame(tracks)

    # Print summary
    print(f"Artist count: {len(artists)}")
    print(f"Album count: {len(albums)}")
    print(f"Track count: {len(tracks)}")

    print(f"{artists_df.head()}")
    print(f"{albums_df.head()}")
    print(f"{tracks_df.head()}")

    # Example: lookup specific album
    album_name = "Paces of Places"
    album_artist = "Funk Assault"
    artist_id = make_artist_id(album_artist)
    album_id = make_album_id(album_name, artist_id)

    print("\nExample lookup:")
    print(f"  Artist ID: {artist_id}")
    print(f"  Album ID: {album_id}")

    # Find album by ID
    album_by_id = next((a for a in albums if a.id == album_id), None)
    if album_by_id:
        print(f"  Album (by ID): {album_by_id}")

    # Find all albums with matching title
    matching_albums = [a for a in albums if a.title == album_name]
    if matching_albums:
        print(f"  Matching albums: {matching_albums}")


if __name__ == "__main__":
    main()
