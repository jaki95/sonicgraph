from sonicgraph.library.builder.builder import Builder
from sonicgraph.library.builder.credits import extract_artists
from sonicgraph.library.builder.helpers import (
    VARIOUS_ARTISTS_ID,
    export_library_data,
    get_or_create_artist,
    make_album_id,
    make_track_id,
    track_fingerprint,
)
from sonicgraph.library.loader.apple_music import AppleMusicLibraryLoader
from sonicgraph.library.models import Album, Artist, Library, RawTrack, Track


class AppleMusicLibraryBuilder(Builder):
    def build(self, raw_tracks: list[RawTrack]) -> Library:
        """
        Process raw Apple Music tracks into a Library object.

        Creates unique entities for each artist and album, linking tracks to their
        respective artists and albums through IDs.
        """
        artists: dict[str, Artist] = {}
        albums: dict[str, Album] = {}
        tracks: dict[str, Track] = {}

        seen_tracks: dict[tuple, str] = {}

        for rt in raw_tracks:
            track_artist_names = extract_artists(rt.artist, rt.name)
            if not track_artist_names:
                continue

            track_artist_ids = [
                get_or_create_artist(artists, name) for name in track_artist_names
            ]

            # Album artists
            album_artist_ids: list[str] = []
            if rt.album_artist:
                for name in extract_artists(rt.album_artist, ""):
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
        export_library_data(artists, albums, tracks)

        return Library(
            artists=list(artists.values()),
            albums=list(albums.values()),
            tracks=list(tracks.values()),
        )


if __name__ == "__main__":
    loader = AppleMusicLibraryLoader()
    raw_tracks = loader.parse()
    builder = AppleMusicLibraryBuilder()
    library = builder.build(raw_tracks)
    print(f"First track: {library.tracks[0]}")
