from sonicgraph.pipeline.parse import parse_artists


def test_single_artist():
    assert parse_artists("Chlär", "") == ["Chlär"]


def test_ampersand_split():
    assert parse_artists("Ben Klock & Marcel Dettmann", "") == [
        "Ben Klock",
        "Marcel Dettmann",
    ]


def test_feat_split():
    assert parse_artists("Regal feat. Amelie Lens", "") == [
        "Amelie Lens",
        "Regal",
    ]
    assert parse_artists("Regal", "Track (feat. Amelie Lens") == [
        "Amelie Lens",
        "Regal",
    ]
    assert parse_artists(
        "Ben Klock & Marcel Dettmann", "Track (feat. Marcel Dettmann & Ben Klock)"
    ) == [
        "Ben Klock",
        "Marcel Dettmann",
    ]


def test_x_split():
    assert parse_artists("DVS1 x Oscar Mulero", "") == [
        "DVS1",
        "Oscar Mulero",
    ]


def test_slash_split():
    assert parse_artists("Jeff Mills / Robert Hood", "") == [
        "Jeff Mills",
        "Robert Hood",
    ]


def test_empty_artist():
    assert parse_artists("", "") == []
