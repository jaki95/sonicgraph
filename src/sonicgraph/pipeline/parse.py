import re

# Split artist names on common separators
_ARTIST_SPLIT_RE = re.compile(
    r"""
    \s*
    (?:
        ,\s+(?!\s*(?:the|dj)\b)  # Comma (but not before "the" or "dj")
      | \s+&\s+                   # Ampersand
      | \s+and\s+                 # "and"
      | \s+feat\.?\s+             # "feat" or "feat."
      | \s+ft\.?\s+               # "ft" or "ft."
      | \s+featuring\s+           # "featuring"
      | \s+x\s+                   # "x" (collaboration marker)
      | \s*/\s*                   # Forward slash
    )
    \s*
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Credit keywords used in track titles
_CREDIT_KEYWORDS = r"""
    remix|rework|edit|bootleg|version|
    feat\.?|ft\.?|featuring|with
"""

# Match artist credits within parentheses
_ARTIST_CREDIT_RE = re.compile(
    rf"""
    (?P<artists>.+?)
    \s+
    (?:{_CREDIT_KEYWORDS})
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Match inline credits at end of track name (fallback for malformed titles)
_INLINE_CREDIT_RE = re.compile(
    rf"""
    (?:{_CREDIT_KEYWORDS})
    \s+
    (?P<artists>.+)$
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Non-artist parenthetical content to ignore
_NON_ARTIST_PARENS = r"""
    original\s+mix|
    extended\s+mix|
    club\s+mix|
    radio\s+edit|
    instrumental|
    dub
"""

# Match all parenthetical content
_PARENS_RE = re.compile(
    r"""
    \(
        \s*
        (?P<content>[^()]+?)
        \s*
    \)
    """,
    re.VERBOSE,
)


def _clean_artist_token(token: str) -> str:
    """Remove extraneous punctuation and whitespace from artist name."""
    return token.strip().strip("()[]{}.,;:-")


def parse_artists(artist_name: str, track_name: str) -> list[str]:
    """
    Parse all artist names from artist field and track title.
    """
    artists: set[str] = set()

    # Parse main artist field
    for part in _ARTIST_SPLIT_RE.split(artist_name):
        part = _clean_artist_token(part)
        if part:
            artists.add(part)

    # Parse parenthetical credits
    found_credit = False
    for paren in _PARENS_RE.finditer(track_name):
        content = paren.group("content").strip().lower()

        # Skip non-artist parentheticals (e.g., "Original Mix")
        if re.search(_NON_ARTIST_PARENS, content, re.IGNORECASE):
            continue

        # Look for artist credit pattern
        match = _ARTIST_CREDIT_RE.search(paren.group("content"))
        if not match:
            continue

        found_credit = True
        credit_block = match.group("artists")

        for part in _ARTIST_SPLIT_RE.split(credit_block):
            part = _clean_artist_token(part)
            if part:
                artists.add(part)

    # Fallback: parse inline credits if no parenthetical credits found
    if not found_credit:
        match = _INLINE_CREDIT_RE.search(track_name)
        if match:
            credit_block = match.group("artists")
            for part in _ARTIST_SPLIT_RE.split(credit_block):
                part = _clean_artist_token(part)
                if part:
                    artists.add(part)

    return sorted(artists)
