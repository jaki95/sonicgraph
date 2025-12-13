import hashlib
from pydantic import BaseModel, Field, model_validator


class Track(BaseModel):
    """Represents a music track with metadata."""
    
    id: str | None = None
    title: str
    artist_ids: list[str]
    album_id: str
    bpm: int | None
    genre: str | None = None
    year: int | None
    source: str

    @model_validator(mode='after')
    def compute_id(self) -> 'Track':
        """Compute the id field as a hash of title and artist_ids."""
        if self.id is None:
            # Join artist_ids for hashing (sorted for consistency)
            artist_str = ','.join(sorted(self.artist_ids))
            self.id = hashlib.sha256(f"{self.title}{artist_str}".encode()).hexdigest()
        return self

class Artist(BaseModel):
    id: str
    name: str
    aliases: list[str]

class Album(BaseModel):
    id: str
    title: str
    artist_ids: list[str]
    year: int | None
    label: str