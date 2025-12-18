import hashlib
import json

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

    for rt in raw_tracks:
        artist_names = parse_artists(rt.artist, rt.name)
        if not artist_names:
            continue

        artist_ids: list[str] = []
        album_artist_ids: list[str] = []

        # Create/retrieve artist entities for track artists
        for name in artist_names:
            aid = make_artist_id(name)
            artists.setdefault(aid, Artist(id=aid, name=name))
            artist_ids.append(aid)

        # Process album information
        album_id: str | None = None
        if rt.album:
            # Parse album artist if different from track artist
            if rt.album_artist:
                for name in parse_artists(rt.album_artist, ""):
                    aid = make_artist_id(name)
                    artists.setdefault(aid, Artist(id=aid, name=name))
                    album_artist_ids.append(aid)

            # Ensure we have at least one artist ID
            if not artist_ids:
                artist_ids.append(make_artist_id("Unknown Artist"))

            # Use album artist if available, otherwise primary track artist
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

        # Create track entity
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

    # Print summary
    print(f"Artist count: {len(artists)}")
    print(f"Album count: {len(albums)}")
    print(f"Track count: {len(tracks)}")

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
