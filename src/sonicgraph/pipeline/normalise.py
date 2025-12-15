import hashlib
import json
import re

from sonicgraph.pipeline.am import (
    LIBRARY_PATH,
    extract_raw_tracks,
    load_apple_music_library,
)
from sonicgraph.pipeline.models import Album, Artist, RawAMTrack, Track

_ARTIST_SPLIT_RE = re.compile(
    r"""
    \s*                           # optional whitespace
    (?:                           # non-capturing group of separators
        ,\s+(?!\s*(?:the|dj)\b)   # comma (but avoid "DJ X, The Y"-style names)
      | \s+&\s+                   # ampersand
      | \s+and\s+                 # 'and'
      | \s+feat\.?\s+             # feat / feat.
      | \s+ft\.?\s+               # ft / ft.
      | \s+featuring\s+           # featuring
      | \s+x\s+                   # x (collabs)
      | \s*/\s*                   # slash
    )
    \s*
    """,
    re.IGNORECASE | re.VERBOSE,
)


def make_id(prefix: str, *values: str) -> str:
    raw = f"{prefix}:" + "|".join(v.lower().strip() for v in values if v)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def make_album_id(album_name: str, artist_id: str) -> str:
    return make_id("album", album_name, artist_id)


def make_artist_id(artist_name: str) -> str:
    return make_id("artist", artist_name)


def make_track_id(
    track_name: str, album_id: str, artist_id: str, track_number: str
) -> str:
    return make_id("track", track_name, album_id, artist_id, track_number)


def normalise_artist(name: str) -> list[str]:
    if not name:
        return []

    # Normalize whitespace
    name = " ".join(name.split())

    parts = _ARTIST_SPLIT_RE.split(name)

    # Final cleanup
    artists = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        artists.append(p)

    return artists


def normalise_tracks(
    raw_tracks: list[RawAMTrack],
) -> tuple[dict[str, Artist], dict[str, Album], dict[str, Track]]:
    artists: dict[str, Artist] = {}
    albums: dict[str, Album] = {}
    tracks: dict[str, Track] = {}

    for rt in raw_tracks:
        artist_names = normalise_artist(rt.artist)
        if not artist_names:
            continue
        artist_ids: list[str] = []
        album_artist_ids: list[str] = []

        for name in artist_names:
            aid = make_artist_id(name)
            artists.setdefault(aid, Artist(id=aid, name=name))
            artist_ids.append(aid)

        album_id: str | None = None

        if rt.album:
            if rt.album_artist:
                for name in normalise_artist(rt.album_artist):
                    aid = make_artist_id(name)
                    artists.setdefault(aid, Artist(id=aid, name=name))
                    album_artist_ids.append(aid)

            if not artist_ids:
                artist_ids.append(make_artist_id("Unknown Artist"))

            primary_artist_id = (
                album_artist_ids[0] if album_artist_ids else artist_ids[0]
            )

            album_id = make_album_id(rt.album, primary_artist_id)

            albums.setdefault(
                album_id,
                Album(
                    id=album_id,
                    title=rt.album,
                    artist_ids=album_artist_ids or artist_ids,
                    year=rt.year,
                ),
            )

        track_id = make_track_id(
            rt.name,
            album_id or "",
            rt.artist,
            str(rt.track_number) if rt.track_number else "",
        )

        tracks.setdefault(
            track_id,
            Track(
                id=track_id,
                title=rt.name,
                raw_artists_str=rt.artist,
                artist_ids=artist_ids,
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
            ),
        )

    json.dump(
        {
            "artists": artists,
            "albums": albums,
            "tracks": tracks,
        },
        open("normalised.json", "w"),
        indent=2,
        default=str,
    )

    return artists, albums, tracks


if __name__ == "__main__":
    lib = load_apple_music_library(LIBRARY_PATH)
    raw_tracks = extract_raw_tracks(lib)
    artists, albums, tracks = normalise_tracks(raw_tracks)
    print(
        f"Artist count: {len(artists)}\nAlbum count: {len(albums)}\nTrack count: {len(tracks)}"
    )

    album_name = "Paces of Places"
    album_artist = "Funk Assault"
    artist_id = make_artist_id(album_artist)
    album_id = make_album_id(album_name, artist_id)
    print(f"artist_id: {artist_id}\nalbum_id: {album_id}")
    print(f"album: {albums.get(album_id)}")

    for alb in albums.values():
        if alb.title == album_name:
            print(alb)

    # print(artists.get("cc36f85edf9d544c264a29a8ad82bc67d28cda8d"))
