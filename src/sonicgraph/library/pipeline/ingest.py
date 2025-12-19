from sonicgraph.library.builder.apple_music import AppleMusicLibraryBuilder
from sonicgraph.library.loader.apple_music import AppleMusicLibraryLoader
from sonicgraph.library.models import Library


def ingest_apple_music() -> Library:
    raw = AppleMusicLibraryLoader().parse()
    library = AppleMusicLibraryBuilder().build(raw)
    print(f"First track: {library.tracks[0]}")
    return library


if __name__ == "__main__":
    ingest_apple_music()
